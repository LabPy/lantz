# -*- coding: utf-8 -*-
"""
    lantz.driver
    ~~~~~~~~~~~~

    Implements the Driver base class.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import time
import copy
import logging
import threading

from abc import abstractmethod
from functools import partial, wraps
from concurrent import futures
from collections import defaultdict, namedtuple

from .feat import Feat, DictFeat, MISSING, FeatProxy, Signal
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


class _DriverType(type):
    """Base metaclass for all drivers.
    """

    def __init__(cls, classname, bases, class_dict):
        super().__init__(classname, bases, class_dict)
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

        for key, action in actions.items():
            async_action = repartial_submit(key)
            async_action.__doc__ = '(Async) ' + action.__doc__ if action.__doc__ else ''
            setattr(cls, key + '_async', async_action)

        if hasattr(cls, '_lantz_features'):
            feats.update(cls._lantz_features)
        cls._lantz_features = feats

        if hasattr(cls, '_lantz_actions'):
            actions.update(cls._lantz_actions)
        cls._lantz_actions = actions

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


class Driver(metaclass=_DriverType):
    """Base class for all drivers.

    :params name: easy to remember identifier given to the instance for logging
                  purposes
    """

    def __new__(cls, *args, **kwargs):
        name = kwargs.pop('name', None)
        new_meth = super(Driver, cls).__new__
        if new_meth is object.__new__:
            inst = new_meth(cls)
        else:
            inst = new_meth(cls, *args, **kwargs)

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
            setattr(inst, feat_name + '_changed', Signal())

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

    def initialize(self):
        pass

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
    exchanging messages.

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

    @abstractmethod
    def raw_recv(self, size):
        """Receive raw bytes to the instrument. No encoding or termination
        character should be applied.

        This method must be implemented by base classes.

        :param size: number of bytes to receive.
        :return: received bytes.
        :rtype: bytes.
        """
        raise NotImplemented

    @abstractmethod
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
        while not termination in received:
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
