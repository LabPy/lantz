# -*- coding: utf-8 -*-
"""
    lantz.action
    ~~~~~~~~~~~~

    Implements the Action class to wrap driver bound methods with Lantz's
    data handling, logging, timing.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time
import copy
import inspect
import functools

from weakref import WeakKeyDictionary

from .processors import (Processor, FromQuantityProcessor,
                         MapProcessor, RangeProcessor)

from .feat import MISSING


def _dget(adict, instance=MISSING):
    """Helper function to get an element by key
    from a dictionary defaulting to key=MISSING
    """

    try:
        return adict[instance]
    except KeyError:
        return adict[MISSING]

def _dset(adict, value, instance=MISSING):
    """Helper function to set an element by key
    copying taken the value from MISSING.
    """
    if instance not in adict:
        adict[instance] = copy.deepcopy(adict[MISSING])

    if isinstance(adict[instance], dict):
        adict[instance].update(value)
    else:
        adict[instance] = value


class Action(object):
    """Wraps a Driver method with Lantz. Can be used as a decorator.

    Processors can registered for each arguments to modify their values before
    they are passed to the body of the method. Two standard processors are
    defined: `values` and `units` and others can be given as callables in the
    `procs` parameter.

    If a method contains multiple arguments, use a tuple. None can be used as
    `do not change`.

    :param func: driver method to be wrapped.
    :param values: A dictionary to values key to values.
                If a list/tuple instead of a dict is given, the value is not
                changed but only tested to belong to the container.
    :param units: `Quantity` or string that can be interpreted as units.
    :param procs: Other callables to be applied to input arguments.

    """

    def __init__(self, func = None, *, values=None, units=None, limits=None, procs=None):

        #: instance: key: value
        self.modifiers = WeakKeyDictionary()

        self.action_processors = {MISSING: ()}
        self.modifiers[MISSING] = {'values': values,
                                   'units': units,
                                   'limits': limits,
                                   'processors': procs}
        self.func = func
        self.args = None

    def __call__(self, func):
        self.func = func
        self.args = inspect.getfullargspec(func).args
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.rebuild(store=True)
        return self

    def __get__(self, instance, owner=None):
        func = functools.partial(self.call, instance)
        func.__wrapped__ = self.func
        return func

    @property
    def name(self):
        return self.__name__

    def call(self, instance, *args, **kwargs):
        name = self.__name__

        # This part calls to the underlying function wrapping
        # and timing, logging and error handling
        with instance._lock:
            instance.log_info('Calling {} with ({}, {}))', name, args, kwargs)

            try:
                values = inspect.getcallargs(self.func, *(instance, ) + args, **kwargs)
                fargs = self.args
                values = tuple(values[farg] for farg in fargs)[1:]
                if len(values) == 1:
                    t_values = (self.pre_action(values[0], instance), )
                else:
                    t_values = self.pre_action(values, instance)
            except Exception as e:
                instance.log_error('While pre-processing ({}, {}) for {}: {}', args, kwargs, name, e)
                raise e
            instance.log_debug('(raw) Setting {} = {}', name, t_values)

            try:
                tic = time.time()
                out = self.func(instance, *t_values)
            except Exception as e:
                instance.log_error('While calling {} with {}. {}', name, t_values, e)
                raise e

            instance.timing.add(name, time.time() - tic)

            instance.log_info('{} returned {}', name, out)

        return out

    def pre_action(self, value, instance=None):
        procs = _dget(self.action_processors, instance)
        for processor in procs:
            value = processor(value)
        return value

    def rebuild(self, instance=MISSING, build_doc=False, modifiers=None, store=False):
        if not modifiers:
            modifiers = _dget(self.modifiers, instance)

        procs = []
        largs = len(self.args) - 1
        name = self.name

        values = modifiers['values']
        units = modifiers['units']
        limits = modifiers['limits']
        processors = modifiers['processors']

        if values:
            proc = MapProcessor(values)
            lproc = len(proc) if isinstance(proc, Processor) else 1
            if lproc != largs:
                raise ValueError("In {}: the number of elements in 'values' ({}) "
                                 "must match the number of arguments ({})".format(name, lproc, largs))
            procs.append(proc)

        if units:
            proc = FromQuantityProcessor(units)
            lproc = len(proc) if isinstance(proc, Processor) else 1
            if lproc != largs:
                raise ValueError("In {}: the number of elements in 'units' ({}) "
                                 "must match the number of arguments ({})".format(name, lproc, largs))
            procs.append(proc)

        if limits:
            if isinstance(limits[0], (list, tuple)):
                proc = RangeProcessor(limits)
            else:
                proc = RangeProcessor((limits, ))

            lproc = len(proc) if isinstance(proc, Processor) else 1
            if lproc != largs:
                raise ValueError("In {}: the number of elements in 'limits' ({}) "
                                 "must match the number of arguments ({})".format(name, lproc, largs))

            procs.append(proc)

        if processors:
            for processor in processors:
                proc = Processor(processor)
                lproc = len(proc) if isinstance(proc, Processor) else 1
                if lproc != largs:
                    raise ValueError("In {}: the number of elements in 'processor' ({}) "
                                     "must match the number of arguments ({})".format(name, len(proc), largs))
                procs.append(proc)

        if store:
            _dset(self.action_processors, procs, instance)

        return procs


class ActionProxy(object):
    """Proxy object for Actions that allows to
    store instance specific modifiers.
    """

    def __init__(self, instance, action):
        super().__setattr__('instance', instance)
        super().__setattr__('action', action)

    def __getattr__(self, item):
        modifiers = _dget(self.action.modifiers, self.instance)

        if item not in modifiers:
            raise AttributeError()

        return modifiers[item]

    def __setattr__(self, item, value):
        _modifiers = _dget(self.action.modifiers, MISSING)

        if item not in _modifiers:
            raise AttributeError()

        _dset(self.action.modifiers, {item: value}, self.instance)

        self.action.rebuild(self.instance, build_doc=False, store=True)

