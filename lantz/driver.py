# -*- coding: utf-8 -*-
"""
    lantz.driver
    ~~~~~~~~~~~~

    Implements the Driver base class.

    :copyright: 2013 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import time
import copy
import atexit
import logging
import threading

from functools import wraps
from concurrent import futures
from collections import defaultdict

from .utils.qt import MetaQObject, SuperQObject, QtCore

from .feat import Feat, DictFeat, MISSING, FeatProxy
from .action import Action, ActionProxy
from .stats import RunningStats
from .errors import LantzTimeoutError
from .processors import ParseProcessor
from .log import get_logger

logger = get_logger('lantz.driver', False)

def _merge_dicts(*args):
    """ _merge_dicts(dict1, [dict2 [...]]) -> dict1.update(dict2);dict1.update ...

    Merge argument dictionaries into the first treating None as an empty
    dictionary.
    """

    args = [arg for arg in args if arg]

    if not args:
        return {}

    out = copy.copy(args[0])
    for arg in args[1:]:
        out.update(arg)

    return out


class MetaSelf(type):
    """Metaclass for Self object
    """

    def __getattr__(self, item):
        return Self(item)


class Self(metaclass=MetaSelf):
    """Self objects are used in during Driver class declarations
    to refer to the object that is going to be instantiated.

    >>> Self.units('s')
    <Self.units('ms')>
    """

    def __init__(self, item, default=MISSING):
        self.item = item
        self.default = default

    def __get__(self, instance, owner=None):
        return getattr(instance, self.item)

    def __call__(self, default_value):
        self.default = default_value
        return self

    def __repr__(self):
        return "<Self.{}('{}')>".format(self.item, self.default)


class Proxy(object):
    """Read only dictionary that maps feat name to Proxy objects
    """

    def __init__(self, instance, collection, callable):
        self.instance = instance
        self.collection = collection
        self.callable = callable

    def __contains__(self, item):
        return item in self.collection

    def __getattr__(self, item):
        return self.callable(self.instance, self.collection[item])

    def __getitem__(self, item):
        return self.callable(self.instance, self.collection[item])

    def items(self):
        for key, value in self.collection.items():
            yield key, self.callable(self.instance, value)

    def keys(self):
        for key in self.collection.keys():
            yield key


def repartial(func, *parameters, **kparms):
    """Well behaved partial for bound methods.
    """
    @wraps(func)
    def wrapped(self, *args, **kw):
        kw.update(kparms)
        return func(self, *(args + parameters), **kw)
    return wrapped


def repartial_submit(fname):
    """Used to create an async bound method in Driver.
    """
    def wrapped(self, *args, **kwargs):
        return self._submit(getattr(self, fname), *args, **kwargs)
    return wrapped


class _DriverType(MetaQObject):
    """Base metaclass for all drivers.
    """

    def __new__(cls, classname, bases, class_dict):
        feats = dict()
        actions = dict()
        dicts = [class_dict, ] + [base.__dict__ for base in bases
                                  if not isinstance(base, _DriverType)]
        for one_dict in dicts:
            for key, value in one_dict.items():
                if isinstance(value, (Feat, DictFeat)):
                    value.name = key
                    feats[key] = value
                elif isinstance(value, Action):
                    value.rebuild()
                    actions[key] = value

        for key in feats.keys():
            class_dict[key + '_changed'] = QtCore.Signal(object, object)

        for key, action in actions.items():
            async_action = repartial_submit(key)
            async_action.__doc__ = '(Async) ' + action.__doc__ if action.__doc__ else ''
            class_dict[key + '_async'] = async_action

        if '_lantz_features' in class_dict:
            class_dict['_lantz_features'].update(feats)
        else:
            class_dict['_lantz_features'] = feats

        if '_lantz_actions' in class_dict:
            class_dict['_lantz_actions'].update(actions)
        else:
            class_dict['_lantz_actions'] = actions

        return super().__new__(cls, classname, bases, class_dict)


_REGISTERED = defaultdict(int)

def _set(inst, feat_name, feat_attr):
    def _inner(value, *args):
        proxy = inst.feats[feat_name]
        setattr(proxy, feat_attr, value)
    return _inner

def _raise_must_change(dependent, feat_name, operation):
    def _inner(value):
        raise Exception("You must get or set '{}' before trying to {} '{}'".format(dependent, operation, feat_name))
    return _inner


class Driver(SuperQObject, metaclass=_DriverType):
    """Base class for all drivers.

    :params name: easy to remember identifier given to the instance for logging
                  purposes
    """

    def __new__(cls, *args, **kwargs):
        inst = SuperQObject.__new__(cls)
        name = kwargs.pop('name', None)

        inst._executor = None
        inst._lock = threading.RLock()
        inst.__unfinished_tasks = 0
        inst.timing = RunningStats()

        if hasattr(inst, 'name'):
            pass
        elif name:
            inst.name = name
        else:
            inst.name = '{}{:d}'.format(cls.__name__, _REGISTERED[cls.__name__])
            _REGISTERED[cls.__name__] += 1

        inst.log_extra = {'lantz_driver': cls.__name__,
                          'lantz_name': inst.name}

        for feat_name, feat in cls._lantz_features.items():
            for attr_name, attr_value in feat.modifiers[MISSING][MISSING].items():
                if not isinstance(attr_value, Self):
                    continue
                getattr(inst, attr_value.item + '_changed').connect(_set(inst, feat_name, attr_name))
                if attr_value.default is MISSING:
                    feat.get_processors[MISSING][MISSING] = (_raise_must_change(attr_value.item, feat_name, 'get'), )
                    feat.set_processors[MISSING][MISSING] = (_raise_must_change(attr_value.item, feat_name, 'set'), )
                else:
                    feat.modifiers[MISSING][MISSING][attr_name] = attr_value.default
                    feat.rebuild(build_doc=False, store=True)

        inst.log_info('Created ' + inst.name)
        return inst

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    def __submit_by_name(self, fname, *args, **kwargs):
        return self._submit(getattr(self, fname), *args, **kwargs)

    def _first_submit(self, fn, *args, **kwargs):
        self._executor = futures.ThreadPoolExecutor(max_workers=1)
        self._submit = self._notfirst_submit
        return self._notfirst_submit(fn, *args, **kwargs)

    def _notfirst_submit(self, fn, *args, **kwargs):
        self.__unfinished_tasks += 1
        fut = self._executor.submit(fn, *args, **kwargs)
        fut.add_done_callback(self._decrease_unfinished_tasks)
        return fut

    _submit = _first_submit

    def _decrease_unfinished_tasks(self, *args):
        self.__unfinished_tasks -= 1

    unfinished_tasks = property(lambda self: self.__unfinished_tasks)

    def log(self, level, msg, *args, **kwargs):
        """Log with the integer severity 'level'
        on the logger corresponding to this instrument.

        :param level: severity level for this event.
        :param msg: message to be logged (can contain PEP3101 formatting codes)
        """
        if kwargs:
            kwargs.update(self.log_extra)
            logger.log(level, msg, *args, extra=kwargs)
        else:
            logger.log(level, msg, *args, extra=self.log_extra)

    def log_info(self, msg, *args, **kwargs):
        """Log with the severity 'INFO'
        on the logger corresponding to this instrument.

        :param msg: message to be logged (can contain PEP3101 formatting codes)
        """
        self.log(logging.INFO, msg, *args, **kwargs)

    def log_debug(self, msg, *args, **kwargs):
        """Log with the severity 'DEBUG'
        on the logger corresponding to this instrument.

        :param msg: message to be logged (can contain PEP3101 formatting codes)
        """

        self.log(logging.DEBUG, msg, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        """Log with the severity 'ERROR'
        on the logger corresponding to this instrument.

        :param msg: message to be logged (can contain PEP3101 formatting codes)
        """

        self.log(logging.ERROR, msg, *args, **kwargs)

    def log_warning(self, msg, *args, **kwargs):
        """Log with the severity 'WARNING'
        on the logger corresponding to this instrument.

        :param msg: message to be logged (can contain PEP3101 formatting codes)
        """

        self.log(logging.WARNING, msg, *args, **kwargs)

    def log_critical(self, msg, *args, **kwargs):
        """Log with the severity 'CRITICAL'
        on the logger corresponding to this instrument.

        :param msg: message to be logged (can contain PEP3101 formatting codes)
        """

        self.log(logging.CRITICAL, msg, *args, **kwargs)

    def __str__(self):
        classname = self.__class__.__name__
        return "{} {}".format(classname, self.name)

    def __repr__(self):
        classname = self.__class__.__name__
        return "<{}('{}')>".format(classname, self.name)

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, *args):
        self.finalize()

    @Action()
    def initialize(self):
        pass

    @Action()
    def finalize(self):
        pass

    def update(self, newstate=None, *, force=False, **kwargs):
        """Update driver.

        :param newstate: a dictionary containing the new driver state.
        :type newstate: dict.
        :param force: apply change even when the cache says it is not necessary.
        :param force: boolean.

        :raises: ValueError if called with an empty dictionary.
        """

        newstate = _merge_dicts(newstate, kwargs)
        if not newstate:
            raise ValueError("update() called with an empty dictionary")

        for key, value in newstate.items():
            self._lantz_features[key].set(self, value, force)

    def update_async(self, newstate=None, *, force=False, callback=None, **kwargs):
        """Asynchronous update driver.

        :param newstate: driver state.
        :type newstate: dict.
        :param force: apply change even when the cache says it is not necessary.
        :type force: boolean.
        :param callback: Called when the update finishes.
        :type callback: callable.

        :return type: concurrent.future

        :raises: ValueError if called with an empty dictionary.
        """
        newstate = _merge_dicts(newstate, kwargs)
        if not newstate:
            raise ValueError("update() called with an empty dictionary")

        fut = self._submit(self.update, newstate, force=force)
        if not callback is None:
            fut.add_done_callback(callback)
        return fut

    def refresh(self, keys=None):
        """Refresh cache by reading values from the instrument.

        :param keys: a string or list of strings with the properties to refresh.
                     Default None, meaning all properties.
                     If keys is a string, returns the value.
                     If keys is a list/tuple, returns a tuple.
                     If keys is a dict, returns a dict.
        :type keys: str or list or tuple or dict
        """
        if keys:
            if isinstance(keys, (list, tuple)):
                return tuple(getattr(self, key) for key in keys)
            elif isinstance(keys, dict):
                return {key: getattr(self, key) for key in keys.keys()}
            elif isinstance(keys, str):
                return getattr(self, keys)
            else:
                raise ValueError('keys must be a (str, list, tuple or dict)')
        return {key: getattr(self, key) for key in self._lantz_features}

    def refresh_async(self, keys=None, *, callback=None):
        """Asynchronous refresh cache by reading values from the instrument.

        :param keys: a string or list of strings with the properties to refresh
                     Default None, meaning all properties.
                     If keys is a string, returns the value.
                     If keys is a list, returns a dictionary.
        :type keys: str or list or tuple or dict

        :return type: concurrent.future.


        """
        fut = self._submit(self.refresh, keys=keys)
        if not callback is None:
            fut.add_done_callback(callback)
        return fut

    def recall(self, keys=None):
        """Return the last value seen for a feat or a collection of feats.

        :param keys: a string or list of strings with the properties to refresh.
                     Default None all properties.
                     If keys is a string, returns the value.
                     If keys is a list, returns a dictionary.
        :type keys: str, list, tuple, dict.
        """

        if keys:
            if isinstance(keys, (list, tuple, set)):
                return {key: self._lantz_features[key].get_cache(self) for key in keys}
            return self._lantz_features[keys].get_cache(self)
        return {key: value.get_cache(self) for key, value in self._lantz_features.keys()}

    @property
    def feats(self):
        return Proxy(self, self._lantz_features, FeatProxy)

    @property
    def actions(self):
        return Proxy(self, self._lantz_actions, ActionProxy)


class TextualMixin(object):
    """Mixin class for classes that communicate with instruments
    exchanging text messages.

    Ideally, transport classes should provide receive methods
    that support:
    1. query the number of available bytes
    2. read chunks of bytes (with and without timeout)
    3. read until certain character is found (with and without timeout)

    Most transport layers support 1 and 2 but not all support 3 (or only
    for a defined set of characters) and TextualMixin provides fallback
    a method.
    """

    #: Encoding to transform string to bytes and back as defined in
    #: http://docs.python.org/py3k/library/codecs.html#standard-encodings
    ENCODING = 'ascii'
    #: Termination characters for receiving data, if not given RECV_CHUNK
    #: number of bytes will be read.
    RECV_TERMINATION = ''
    #: Termination characters for sending data
    SEND_TERMINATION = ''
    #: Timeout in seconds of the complete read operation.
    TIMEOUT = 1
    #: Parsers
    PARSERS = {}
    #: Size in bytes of the receive chunk (-1 means all bytes in buffer)
    RECV_CHUNK = 1

    #: String containing the part of the message after RECV_TERMINATION
    #: Used in software based finding of termination character when
    #: RECV_CHUNK > 1
    _received = ''

    def raw_recv(self, size):
        """Receive raw bytes from the instrument. No encoding or termination
        character should be applied.

        This method must be implemented by base classes.

        :param size: number of bytes to receive.
        :return: received bytes, eom
        :rtype: bytes, bool
        """
        raise NotImplemented

    def raw_send(self, data):
        """Send raw bytes to the instrument. No encoding or termination
        character should be applied.

        This method must be implemented by base classes.

        :param data: bytes to be sent to the instrument.
        :param data: bytes.
        """
        raise NotImplemented

    def send(self, command, termination=None, encoding=None):
        """Send command to the instrument.

        :param command: command to be sent to the instrument.
        :type command: string.

        :param termination: termination character to override class defined
                            default.
        :param encoding: encoding to transform string to bytes to override class
                         defined default.

        :return: number of bytes sent.

        """
        if termination is None:
            termination = self.SEND_TERMINATION
        if encoding is None:
            encoding = self.ENCODING

        message = bytes(command + termination, encoding)
        self.log_debug('Sending {}', message)
        return self.raw_send(message)

    def recv(self, termination=None, encoding=None, recv_chunk=None):
        """Receive string from instrument.

        :param termination: termination character (overrides class default)
        :type termination: str
        :param encoding: encoding to transform bytes to string (overrides class default)
        :param recv_chunk: number of bytes to receive (overrides class default)
        :return: string encoded from received bytes
        """

        termination = termination or self.RECV_TERMINATION
        encoding = encoding or self.ENCODING
        recv_chunk = recv_chunk or self.RECV_CHUNK

        if not termination:
            return str(self.raw_recv(recv_chunk), encoding)

        if self.TIMEOUT is None or self.TIMEOUT < 0:
            stop = float('+inf')
        else:
            stop = time.time() + self.TIMEOUT

        received = self._received
        eom = False
        while not (termination in received or eom):
            if time.time() > stop:
                raise LantzTimeoutError
            raw_received = self.raw_recv(recv_chunk)
            received += str(raw_received, encoding)

        self.log_debug('Received {!r} (len={})', received, len(received))

        received, self._received = received.split(termination, 1)

        return received

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Send query to the instrument and return the answer

        :param command: command to be sent to the instrument
        :type command: string

        :param send_args: (termination, encoding) to override class defaults
        :param recv_args: (termination, encoding) to override class defaults
        """

        self.send(command, *send_args)
        return self.recv(*recv_args)

    def parse_query(self, command, *,
                    send_args=(None, None), recv_args=(None, None),
                    format=None):
        """Send query to the instrument, parse the output using format
        and return the answer.

        .. seealso:: TextualMixin.query and stringparser
        """
        ans = self.query(command, send_args=send_args, recv_args=recv_args)
        if format:
            parser = self.PARSERS.setdefault(format, ParseProcessor(format))
            ans = parser(ans)
        return ans


def _solve_dependencies(dependencies, all_members=None):
    """Solve a dependency graph.

    :param dependencies: dependency dictionary. For each key, the value is
                         an iterable indicating its dependencies.
    :param all_members: If provided
    :return: list of sets, each containing independent task only dependent of the
             previous set in the list.

    """
    d = dict((key, set(value)) for key, value in dependencies.items())
    if all_members:
        d.update({key: set() for key in all_members if key not in d})
    r = []
    while d:
        # values not in keys (items without dep)
        t = set(i for v in d.values() for i in v) - set(d.keys())
        # and keys without value (items without dep)
        t.update(k for k, v in d.items() if not v)
        # can be done right away
        r.append(t)
        # and cleaned up
        d = dict(((k, v - t) for k, v in d.items() if v))

    return r


def initialize_many(drivers, register_finalizer=True,
                    on_initializing=None, on_initialized=None, on_exception=None,
                    concurrent=False, dependencies=None):
    """Initialize a group of drivers.

    :param drivers: an iterable of drivers.
    :param register_finalizer: register driver.finalize method to be called at python exit.
    :param on_initializing: a callable to be executed BEFORE initialization.
                            It takes the driver as the first argument.
    :param on_initialized: a callable to be executed AFTER initialization.
                           It takes the driver as the first argument.
    :param on_exception: a callable to be executed in case an exception occurs.
                         It takes the offending driver as the first argument and the
                         exception as the second one.
    :param concurrent: indicates that drivers with satisfied dependencies
                       should be initialized concurrently.
    :param dependencies: indicates which drivers depend on others to be initialized.
                         each key is a driver name, and the corresponding
                         value is an iterable with its dependencies.
    """

    if dependencies:
        names = {driver.name: driver for driver in drivers}

        groups = _solve_dependencies(dependencies, set(names.keys()))
        drivers = tuple(tuple(names[name] for name in group) for group in groups)
        for subset in drivers:
            initialize_many(subset, register_finalizer,
                            on_initializing, on_initialized, on_exception,
                            concurrent)
        return

    if concurrent:
        def _finalize(d):
            def _inner_finalize(f):
                atexit.register(d.finalize)
            return _inner_finalize

        def _done(d):
            def _inner(f):
                ex = f.exception()
                if ex:
                    if not on_exception:
                        raise ex
                    on_exception(d, ex)
                else:
                    if on_initialized:
                        on_initialized(d)
            return _inner

        futs = []
        for driver in drivers:
            if on_initializing:
                on_initializing(driver)
            fut = driver.initialize_async()
            if register_finalizer:
                fut.add_done_callback(_finalize(driver))
            fut.add_done_callback(_done(driver))
            futs.append(fut)

        futures.wait(futs)
    else:
        for driver in drivers:
            if on_initializing:
                on_initializing(driver)
            try:
                driver.initialize()
            except Exception as ex:
                if not on_exception:
                    raise ex
                on_exception(driver, ex)
            else:
                if on_initialized:
                    on_initialized(driver)

            if register_finalizer:
                atexit.register(driver.finalize)


def finalize_many(drivers,
                  on_finalizing=None, on_finalized=None, on_exception=None,
                  concurrent=False, dependencies=None):
    """Finalize a group of drivers.

    :param drivers: an iterable of drivers.
    :param on_finalizing: a callable to be executed BEFORE finalization.
                          It takes the driver as the first argument.
    :param on_finalized: a callable to be executed AFTER finalization.
                         It takes the driver as the first argument.
    :param on_exception: a callable to be executed in case an exception occurs.
                         It takes the offending driver as the first argument and the
                         exception as the second one.
    :param concurrent: indicates that drivers with satisfied dependencies
                       are finalized concurrently.
    :param dependencies: indicates which drivers depend on others to be initialized.
                         each key is a driver name, and the corresponding
                         value is an iterable with its dependencies.
                         The dependencies are used in reverse.
    """

    if dependencies:
        names = {driver.name: driver for driver in drivers}

        groups = _solve_dependencies(dependencies, set(names.keys()))
        drivers = tuple(tuple(names[name] for name in group) for group in groups)
        for subset in reversed(drivers):
            finalize_many(subset, on_finalizing, on_finalized, on_exception, concurrent)
        return

    if concurrent:
        def _done(d):
            def _inner(f):
                ex = f.exception()
                if ex:
                    if not on_exception:
                        raise ex
                    on_exception(d, ex)
                else:
                    if on_finalized:
                        on_finalized(d)
            return _inner

        futs = []
        for driver in drivers:
            if on_finalizing:
                on_finalizing(driver)
            fut = driver.finalize_async()
            fut.add_done_callback(_done(driver))
            futs.append(fut)

        futures.wait(futs)
    else:
        for driver in drivers:
            if on_finalizing:
                on_finalizing(driver)
            try:
                driver.finalize()
            except Exception as ex:
                if not on_exception:
                    raise ex
                on_exception(driver, ex)
            else:
                if on_finalized:
                    on_finalized(driver)
