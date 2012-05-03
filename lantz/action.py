# -*- coding: utf-8 -*-
"""
    lantz.action
    ~~~~~~~~~~~~

    Implements the Action class to wrap driver bound methods with Lantz's
    data handling, logging, timing.

    :copyright: (c) 2011 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time
import functools

from .processors import (Processor, ToQuantityProcessor, FromQuantityProcessor,
                         MapProcessor, ReverseMapProcessor)


class Action(object):
    """Wraps a Driver method with Lantz. Can be used as a decorator.

    Processors can registered for each arguments to modify their values before
    they are passed to the body of the method. Two standard processors are
    defined: `map` and `units` and others can be given as callables in the
    `procs` parameter.

    If a method contains multiple arguments, use a tuple. None can be used as
    `do not change`.

    :param func: driver method to be wrapped.
    :param map: A dictionary to map key to values.
                If a list/tuple instead of a dict is given, the value is not
                changed but only tested to belong to the container.
    :param units: `Quantity` or string that can be interpreted as units.
    :param procs: Other callables to be applied to input arguments.

    """

    def __init__(self, func=None, *, map=None, units=None, range=None, procs=None):
        self.map = map
        self.units = units
        self.range = range
        self.processors = procs
        self.func = None
        if func:
            self.__call__(func)

    def decorate(self, func, instance):
        def decorated_function(*args, **kwargs):
            out = func(instance, *args, **kwargs)
            return out
        return functools.update_wrapper(decorated_function, func)

    def __call__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
        return self

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        rv = instance.__dict__.get(self.func.__name__)
        if rv is None:
            rv = self.decorate(self.func, instance)
            instance.__dict__[self.func.__name__] = rv
        return rv

    def call(self, *args, **kwargs):
        name = self.name

        # This part calls to the underlying function wrapping
        # and timing, logging and error handling
        with instance._lock:
            instance.log_info('Calling {0} with ({}, {}))'.format(name, args, kwargs))

            try:
                t_value = self.pre_action(*args, **kwargs)
            except Exception as e:
                self.log_error('Error while calling {}'.format(e))
                raise e

            try:
                tic = time.time()
                out = self.func(self, *t_value)
            except Exception as e:
                self.log_error('Error while calling {}'.format(e))
                raise e

            instance.timing.add(name, time.time() - tic)

            instance.log_info('{} returned {}'.format(name, out))

    def pre_action(self, value):
        for processor in self.action_processors:
            value = processor(value)
        return value

    def rebuild(self):
        self.action_processors = []
        if self.map:
            self.processors.append(MapProcessor(self.map))
        if self.units:
            self.action_processors.append(FromQuantityProcessor(self.units))
        if self.processors:
            for proc in self.processors:
                self.action_processors.append(Processor(proc))
