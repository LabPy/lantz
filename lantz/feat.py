# -*- coding: utf-8 -*-
"""
    lantz.feat
    ~~~~~~~~~~

    Implements Feat and DictFeat property-like classes with data handling,
    logging, timing, cache and notification.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time
import copy
from weakref import WeakKeyDictionary

from . import Q_
from .processors import (Processor, ToQuantityProcessor, FromQuantityProcessor,
                         MapProcessor, ReverseMapProcessor, RangeProcessor)


class _NamedObject(object):
    """A class to construct named sentinels.
    """

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return id(self)

    def __deepcopy__(self, memo):
        return self

MISSING = _NamedObject('MISSING')


class Signal(object):
    """PyQt like signal
    """

    def __init__(self):
        self.slots = []

    def connect(self, slot, type=0):
        self.slots.append(slot)

    def disconnect(self, slot=None):
        if slot is None:
            self.slots = []

        self.slots.remove(slot)

    def emit(self, *args):
        for slot in self.slots:
            slot(*args)


def _dget(adict, instance=MISSING, key=MISSING):

    try:
        adict = adict[instance]
    except KeyError:
        adict = adict[MISSING]
    try:
        return adict[key]
    except KeyError:
        return adict[MISSING]

def _dset(adict, value, instance=MISSING, key=MISSING):
    if instance not in adict:
        adict[instance] = copy.deepcopy(adict[MISSING])

    if key not in adict[instance]:
        adict[instance][key] = copy.deepcopy(adict[instance][MISSING])

    if isinstance(adict[instance][key], dict):
        adict[instance][key].update(value)
    else:
        adict[instance][key] = value


class Feat(object):
    """Pimped Python property for interfacing with instruments. Can be used as
    a decorator.

    Processors can registered for each arguments to modify their values before
    they are passed to the body of the method. Two standard processors are
    defined: `values` and `units` and others can be given as callables in the
    `procs` parameter.

    If a method contains multiple arguments, use a tuple. None can be used as
    `do not change`.

    :param fget: getter function.
    :param fset: setter function.
    :param doc: docstring, if missing fget or fset docstring will be used.

    :param values: A dictionary to map key to values.
                   A set to restrict the values.
                   If a list/tuple instead of a dict is given, the value is not
                   changed but only tested to belong to the container.
    :param units: `Quantity` or string that can be interpreted as units.
    :param procs: Other callables to be applied to input arguments.

    """


    def __init__(self, fget=MISSING, fset=None, doc=None, *,
                 values=None, units=None, limits=None, procs=None,
                 read_once=False):
        self.fget = fget
        self.fset = fset
        self.__doc__ = doc
        self.name = '?'

        #: instance: value
        self.value = WeakKeyDictionary()

        #: instance: key: value
        self.modifiers = WeakKeyDictionary()
        self.get_processors = WeakKeyDictionary()
        self.set_processors = WeakKeyDictionary()

        if fget is not MISSING and fget.__doc__ and not self.__doc__:
            self.__doc__ = fget.__doc__
        if fset and fset.__doc__ and not self.__doc__:
            self.__doc__ = fset.__doc__

        self.modifiers[MISSING] = {MISSING: {'values': values,
                                             'units': units,
                                             'limits': limits,
                                             'processors': procs}}
        self.get_processors[MISSING] = {MISSING: ()}
        self.set_processors[MISSING] = {MISSING: ()}

        self.read_once = read_once

        self.rebuild(build_doc=True, store=True)

    def rebuild(self, instance=MISSING, key=MISSING, build_doc=False, modifiers=None, store=False):
        if not modifiers:
            modifiers = _dget(self.modifiers, instance, key)

        values = modifiers['values']
        units = modifiers['units']
        limits = modifiers['limits']
        processors = modifiers['processors']

        get_processors = []
        set_processors = []
        if values:
            get_processors.append(ReverseMapProcessor(values))
            set_processors.append(MapProcessor(values))
        if units:
            get_processors.insert(0, ToQuantityProcessor(units))
            set_processors.append(FromQuantityProcessor(units))
        if limits:
            if isinstance(limits[0], (list, tuple)):
                set_processors.append(RangeProcessor(limits))
            else:
                set_processors.append(RangeProcessor((limits, )))
        if processors:
            for getp, setp in processors:
                if getp is not None:
                    get_processors.insert(0, Processor(getp))
                if setp is not None:
                    set_processors.append(Processor(setp))

        if build_doc:
            _dochelper(self)

        if store:
            _dset(self.get_processors, get_processors, instance, key)
            _dset(self.set_processors, set_processors, instance, key)

        return get_processors, set_processors

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

    def post_get(self, value, instance=None, key=MISSING):
        for processor in _dget(self.get_processors, instance, key):
            value = processor(value)
        return value

    def pre_set(self, value, instance=None, key=MISSING):
        for processor in _dget(self.set_processors, instance, key):
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
            instance.log_info('Getting {}', name)

            try:
                tic = time.time()
                if key is MISSING:
                    value = self.fget(instance)
                else:
                    value = self.fget(instance, key)
            except Exception as e:
                instance.log_error('While getting {}: {}', name, e)
                raise e

            instance.timing.add('get_' + name, time.time() - tic)

            instance.log_debug('(raw) Got {} for {}', value, name)
            try:
                value = self.post_get(value, instance, key)
            except Exception as e:
                instance.log_error('While post-processing {} for {}: {}', value, name, e)
                raise e

            instance.log_info('Got {} for {}', value, name, lantz_feat=(name, str(value)))

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
                instance.log_info('No need to set {} = {} (current={}, force={})', name, value, current_value, force)
                return

            instance.log_info('Setting {} = {} (current={}, force={})', name, value, current_value, force)

            try:
                t_value = self.pre_set(value, instance, key)
            except Exception as e:
                instance.log_error('While pre-processing {} for {}: {}', value, name, e)
                raise e
            instance.log_debug('(raw) Setting {} = {}', name, t_value)

            try:
                tic = time.time()
                if key is MISSING:
                    self.fset(instance, t_value)
                else:
                    self.fset(instance, key, t_value)
            except Exception as e:
                instance.log_error('While setting {} to {}. {}', name, value, e)
                raise e

            instance.timing.add('set_' + name, time.time() - tic)

            instance.log_info('{} was set to {}', name, value, lantz_feat=(name, str(value)))

            self.set_cache(instance, value, key)

    def __get__(self, instance, owner=None):
        return self.get(instance)

    def __set__(self, instance, value):
        self.set(instance, value)

    def __delete__(self, instance):
        raise AttributeError('{} is a permanent feat of {}'.format(self.name, instance.__class__.__name__))

    def get_cache(self, instance, key=MISSING):
        try:
            return self.value[instance]
        except KeyError:
            return MISSING

    def set_cache(self, instance, value, key=MISSING):
        old_value = self.get_cache(instance, key)

        if value == old_value:
            return

        if isinstance(value, Q_):
            value = copy.copy(value)

        self.value[instance] = value

        getattr(instance, self.name + '_changed').emit(value, old_value)


class DictFeat(Feat):
    """Pimped Python property with getitem access for interfacing with
    instruments. Can be used as a decorator.

    Takes the same parameters as `Feat`, plus:

    :param keys: List/tuple restricts the keys to the specified ones.

    """

    def __init__(self, fget=MISSING, fset=None, doc=None, *,
                 keys=None, **kwargs):
        super().__init__(fget, fset, doc, **kwargs)
        self.modifiers[MISSING][MISSING]['keys'] = keys


    def getitem(self, instance, key):
        keys = _dget(self.modifiers, instance, key)['keys']
        if keys and not key in keys:
            raise KeyError('{} is not valid key for {} {}'.format(key, self.name,
                                                                    keys))
        if isinstance(keys, dict):
            key = keys[key]

        return self.get(instance, instance.__class__, key)

    def setitem(self, instance, key, value, force=False):
        keys = _dget(self.modifiers, instance, key)['keys']
        if keys and not key in keys:
            raise KeyError('{} is not valid key for {} {}'.format(key, self.name,
                                                                    keys))
        if isinstance(keys, dict):
            key = keys[key]

        self.set(instance, value, force, key)

    def __get__(self, instance, owner=None):
        if not instance:
            return self
        return _DictFeatAccesor(instance, self)

    def __set__(self, instance, value):
        if not isinstance(value, dict):
            raise AttributeError('This is a DictFeat and cannot be set in this way. '
                                 'You probably want to do something like:'
                                 'obj.prop[index] = value or obj.prop = dict')

        for key, value in value.items():
            self.setitem(instance, key, value)

    def __delete__(self, instance):
        raise AttributeError('{} is a permanent attribute from {}', self.name, instance.__class__.__name__)

    def get_cache(self, instance, key=MISSING):
        keys = _dget(self.modifiers, instance, key)['keys']
        if instance not in self.value:
            self.value[instance] = dict()
        if isinstance(keys, dict):
            keys = keys.values()
        if keys and key not in keys:
            raise KeyError('{} is not valid key for {} {}'.format(key, self.name,
                                                                  keys))
        if key is MISSING:
            return self.value[instance]
        else:
            return self.value[instance].get(key, MISSING)

    def set_cache(self, instance, value, key=MISSING):
        old_value = self.get_cache(instance, key)

        if value == old_value:
            return

        if key is MISSING:
            assert isinstance(value, dict)
            self.value[instance] = value
        else:
            self.value[instance][key] = value

        getattr(instance, self.name + '_changed').emit(value, old_value, {'key': key})


def _dochelper(feat):
    if not hasattr(feat, '__original_doc__'):
        feat.__original_doc__ = feat.__doc__ or ''

    doc = ''
    predoc = ''

    modifiers = feat.modifiers[MISSING][MISSING]

    if isinstance(feat, DictFeat):
        predoc = ':keys: {}\n\n'.format(modifiers.get('keys', None) or 'ANY')


    if modifiers['values']:
        doc += ':values: {}\n'.format(modifiers['values'])
    if modifiers['units']:
        doc += ':units: {}\n'.format(modifiers['units'])
    if modifiers['limits']:
        doc += ':limits: {}\n'.format(modifiers['limits'])
    if modifiers['processors']:
        docpg = []
        docps = []
        for getp, setp in modifiers['processors']:
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


class FeatProxy(object):
    """Proxy object for Feat that allows to
    store instance specific modifiers.
    """

    def __init__(self, instance, feat, key=MISSING):
        super().__setattr__('instance', instance)
        super().__setattr__('feat', feat)
        super().__setattr__('key', key)

    def __getattr__(self, item):
        modifiers = _dget(self.feat.modifiers, self.instance, self.key)

        if item not in modifiers:
            return getattr(self.feat, item)

        return modifiers[item]

    def __setattr__(self, item, value):
        _modifiers = _dget(self.feat.modifiers, MISSING, MISSING)

        if item not in _modifiers:
            raise AttributeError()

        _dset(self.feat.modifiers, {item: value}, self.instance, self.key)

        self.feat.rebuild(self.instance, self.key, build_doc=False, store=True)

    def __getitem__(self, key):
        if not isinstance(self.feat, DictFeat):
            raise TypeError
        return self.__class__(self.instance, self.feat, key)


class _DictFeatAccesor(object):
    """Helper class to provide indexed access to DictFeat.
    """

    def __init__(self, instance, dictfeat):
        self.df = dictfeat
        self.instance = instance

    def __getitem__(self, key):
        return DictFeat.getitem(self.df, self.instance, key)

    def __setitem__(self, key, value):
        DictFeat.setitem(self.df, self.instance, key, value)

    def __repr__(self):
        return repr(self.df.value[self.instance])
