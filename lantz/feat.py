# -*- coding: utf-8 -*-
"""
    lantz.feat
    ~~~~~~~~~~

    Implements Feat and DictFeat property-like classes with data handling,
    logging, timing, cache and notification.

    :copyright: (c) 2011 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time

from .processors import (Processor, ToQuantityProcessor, FromQuantityProcessor,
                         MapProcessor, ReverseMapProcessor, RangeProcessor)

MISSING = object()

class Feat(object):
    """Pimped Python property for interfacing with instruments. Can be used as
    a decorator.

    Processors can registered for each arguments to modify their values before
    they are passed to the body of the method. Two standard processors are
    defined: `map` and `units` and others can be given as callables in the
    `procs` parameter.

    If a method contains multiple arguments, use a tuple. None can be used as
    `do not change`.

    :param fget: getter function.
    :param fset: setter function.
    :param doc: docstring, if missing fget or fset docstring will be used.

    :param map: A dictionary to map key to values.
                If a list/tuple instead of a dict is given, the value is not
                changed but only tested to belong to the container.
    :param units: `Quantity` or string that can be interpreted as units.
    :param procs: Other callables to be applied to input arguments.

    """

    def __init__(self, fget=MISSING, fset=None, doc=None, *,
                 map=None, units=None, range=None, procs=None,
                 read_once=False):
        self.fget = fget
        self.fset = fset
        self.__doc__ = doc
        self.name = '?'

        if fget is not MISSING and fget.__doc__ and not self.__doc__:
            self.__doc__ = fget.__doc__
        if fset and fset.__doc__ and not self.__doc__:
            self.__doc__ = fset.__doc__

        self.map = map
        self.units = units
        self.range = range
        self.processors = procs
        self.read_once = read_once

    def rebuild(self):
        self.get_processors = []
        self.set_processors = []
        if self.map:
            self.get_processors.append(ReverseMapProcessor(self.map))
            self.set_processors.append(MapProcessor(self.map))
        if self.units:
            self.get_processors.insert(0, ToQuantityProcessor(self.units))
            self.set_processors.append(FromQuantityProcessor(self.units))
        if self.range:
            if isinstance(self.range[0], (list, tuple)):
                self.set_processors.append(RangeProcessor(self.range))
            else:
                self.set_processors.append(RangeProcessor((self.range, )))
        if self.processors:
            for getp, setp in self.processors:
                if getp is not None:
                    self.get_processors.insert(0, Processor(getp))
                if setp is not None:
                    self.set_processors.append(Processor(setp))

        _dochelper(self)

    def __call__(self, func):
        if self.fget is MISSING:
            return self.getter(func)

        return self.setter(func)

    def getter(self, func):
        if func.__doc__ and not self.__doc__:
            self.__doc__ = func.__doc__
        self.fget = func
        return self

    def setter(self, func):
        if func.__doc__ and not self.__doc__:
            self.__doc__ = func.__doc__
        self.fset = func
        return self

    def post_getter(self, func):
        self.post_get = func
        return self

    def post_setter(self, func):
        self.pre_set = func
        return self

    def post_get(self, value):
        for processor in self.get_processors:
            value = processor(value)
        return value

    def pre_set(self, value):
        for processor in self.set_processors:
            value = processor(value)
        return value

    def get(self, instance, owner=None, key=MISSING):
        if instance is None:
            return self

        name = self.name + ('' if key is MISSING else '[{!r}]'.format(key))
        if self.fget is None or self.fget is MISSING:
            raise AttributeError('{} is a write-only feature'.format(name))

        current = self.get_cache(instance, key)
        if self.read_once and current is not MISSING:
            return current

        # This part calls to the underlying get function wrapping
        # and timing, caching, logging and error handling
        with instance._lock:
            instance.log_info('Getting {}'.format(name))

            try:
                tic = time.time()
                if key is MISSING:
                    value = self.fget(instance)
                else:
                    value = self.fget(instance, key)
            except Exception as e:
                instance.log_error('While getting {}: {}'.format(name, e))
                raise e

            instance.timing.add('get_' + name, time.time() - tic)

            instance.log_debug('(raw) Got {} for {}'.format(value, name))
            try:
                value = self.post_get(value)
            except Exception as e:
                instance.log_error('While post-processing {} for {}: {}'.format(value, name, e))
                raise e

            instance.log_info('Got {} for {}'.format(value, name), lantz_feat=(name, str(value)))

            self.set_cache(instance, value, key)

        return value

    def set(self, instance, value, force=False, key=MISSING):
        name = self.name + ('' if key is MISSING else '[{!r}]'.format(key))

        if self.fset is None:
            raise AttributeError('{} is a read-only feature'.format(name))

        # This part calls to the underlying get function wrapping
        # and timing, caching, logging and error handling
        with instance._lock:
            current_value = self.get_cache(instance, key)
            if not force and value == current_value:
                instance.log_info('No need to set {0} = {1} (current={2}, force={3})'.format(name, value, current_value, force))
                return

            instance.log_info('Setting {0} = {1} (current={2}, force={3})'.format(name, value, current_value, force))

            try:
                t_value = self.pre_set(value)
            except Exception as e:
                instance.log_error('While pre-processing {} for {}: {}'.format(value, name, e))
                raise e
            instance.log_debug('(raw) Setting {} = {}'.format(name, t_value))

            try:
                tic = time.time()
                if key is MISSING:
                    self.fset(instance, t_value)
                else:
                    self.fset(instance, key, t_value)
            except Exception as e:
                instance.log_error('While setting {} to {}. {}'.format(name, value, e))
                raise e

            instance.timing.add('set_' + name, time.time() - tic)

            instance.log_info('{} was set to {}'.format(name, value), lantz_feat=(name, str(value)))

            self.set_cache(instance, value, key)

    def __get__(self, instance, owner=None):
        return self.get(instance)

    def __set__(self, instance, value):
        self.set(instance, value)

    def __delete__(self, instance):
        raise AttributeError('{} is a permanent feat of {}'.format(self.name, instance.__class__.__name__))

    def get_cache(self, instance, key):
        return instance.__dict__[self.name]

    def set_cache(self, instance, value, key):
        if value == instance.__dict__[self.name]:
            return
        instance.__dict__[self.name] = value
        for callback in instance.on_changed[self.name]:
            callback(value)


class DictFeat(Feat):
    """Pimped Python property with getitem access for interfacing with
    instruments. Can be used as a decorator.

    Takes the same parameters as `Feat`, plus:

    :param valid_keys: List/tuple restricts the keys to the specified ones.

    """

    def __init__(self, fget=MISSING, fset=None, doc=None, *,
                 valid_keys=None, **kwargs):
        self.instance = None
        self.valid_keys = valid_keys
        if self.valid_keys:
            self._internal = {key: MISSING for key in self.valid_keys}
        else:
            self._internal = {}

        super().__init__(fget, fset, doc, **kwargs)

    def getitem(self, key):
        if self.valid_keys and not key in self.valid_keys:
            raise KeyError('{} is not valid key for {} {}'.format(key, self.name,
                                                                    self.valid_keys))
        if isinstance(self.valid_keys, dict):
            key = self.valid_keys[key]

        return self.get(self.instance, self.instance.__class__, key)

    def setitem(self, key, value, force=False):
        if self.valid_keys and not key in self.valid_keys:
            raise KeyError('{} is not valid key for {} {}'.format(key, self.name,
                                                                    self.valid_keys))
        if isinstance(self.valid_keys, dict):
            key = self.valid_keys[key]

        self.set(self.instance, value, force, key)

    def __getitem__(self, key):
        return self.getitem(key)

    def __setitem__(self, key, value):
        self.setitem(key, value)

    def __get__(self, instance, owner=None):
        if not instance:
            return self
        return instance._lantz_features[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise AttributeError('This is a dictfeature and cannot be set in this way. '
                                 'You probably want to do something like:'
                                 'obj.prop[index] = value or obj.prop = dict')

        for key, value in value.items():
            self.setitem(key, value)

    def __delete__(self, instance):
        raise AttributeError('{} is a permanent attribute from {}'.format(self.name, instance.__class__.__name__))

    def __repr__(self):
        return repr(self._internal)

    def get_cache(self, instance, key):
        if not self.valid_keys and not key in self._internal:
            return None
        return self._internal.get(key, MISSING)

    def set_cache(self, instance, value, key):
        self._internal[key] = value
        for callback in instance.on_changed[self.name]:
            callback(value)
        for callback in instance.on_changed[(self.name, key)]:
            callback(value)


def _dochelper(feat):
    if not hasattr(feat, '__original_doc__'):
        feat.__original_doc__ = feat.__doc__ or ''

    doc = ''
    predoc = ''

    if isinstance(feat, DictFeat):
        predoc = ':valid keys: {}\n\n'.format(feat.valid_keys or 'ANY')


    if feat.map:
        doc += ':map: {}\n'.format(feat.map)
    if feat.units:
        doc += ':units: {}\n'.format(feat.units)
    if feat.range:
        doc += ':range: {}\n'.format(feat.range)
    if feat.processors:
        docpg = []
        docps = []
        for getp, setp in feat.processors:
            if getp is not None:
                docpg.insert(0, '  - {}'.format(getp))
            if setp is not None:
                docps.append('  - {}'.format(setp))
            if docpg:
                doc += ':get procs: {}'.format('\n'.join(docpg))
            if docps:
                doc += ':set procs: {}'.format('\n'.join(docps))

    if predoc:
        predoc = '\n\n{}'.format(predoc)
    if doc:
        doc = '\n\n{}'.format(doc)

    feat.__doc__ = predoc + feat.__original_doc__ + doc

