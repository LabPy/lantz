# -*- coding: utf-8 -*-
"""
    lantz.processors
    ~~~~~~~~~~~~~~~~

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import inspect
import logging
import warnings

from functools import wraps, partial

from . import Q_
from .log import LOGGER as _LOG
from stringparser import Parser


class DimensionalityWarning(Warning):
    pass


def _do_nothing(value):
    return value


def _getitem(a, b):
    """Return a[b] or if not found a[type(b)]
    """
    try:
        return a[b]
    except KeyError:
        return a[type(b)]

getitem = _getitem

def convert_to(units, on_dimensionless='warn', on_incompatible='raise',
               return_float=False):
    """Return a function that convert a Quantity to to another units.

    :param units: string or Quantity specifying the target units
    :param on_dimensionless: how to proceed when a dimensionless number
                             number is given.
                             'raise' to raise an exception,
                             'warn' to log a warning and proceed,
                             'ignore' to silently proceed
    :param on_incompatible: how to proceed when source and target units are
                            incompatible. Same options as `on_dimensionless`

    :raises: :class:`ValueError` if the incoming value cannot be
             properly converted

        >>> convert_to('mV')(Q_(1, 'V'))
        <Quantity(1000.0, 'millivolt')>
        >>> convert_to('mV', return_float=True)(Q_(1, 'V'))
        1000.0
    """
    if on_dimensionless not in ('ignore', 'warn', 'raise'):
        raise ValueError("{} is not a valid value for 'on_dimensionless'. "
                         "It should be either 'ignore', 'warn' or 'raise'".format(on_dimensionless))
    if on_incompatible not in ('ignore', 'warn', 'raise'):
        raise ValueError("{} is not a valid value for 'on_incompatible'. "
                         "It should be either 'ignore', 'warn' or 'raise'".format(on_dimensionless))

    if isinstance(units, str):
        units = Q_(1, units)
    elif not isinstance(units, Q_):
        raise ValueError("{} is not a valid value for 'units'. "
                         "It should be either str or Quantity")

    if return_float:
        def _inner(value):
            if isinstance(value, Q_):
                try:
                    return value.to(units).magnitude
                except ValueError as e:
                    if on_incompatible == 'raise':
                        raise ValueError(e)
                    elif on_incompatible == 'warn':
                        msg = 'Unable to convert {} to {}. Ignoring source units.'.format(value, units)
                        warnings.warn(msg, DimensionalityWarning)
                        _LOG.warn(msg)

                # on_incompatible == 'ignore'
                return value.magnitude
            else:
                if not units.dimensionless:
                    if on_dimensionless == 'raise':
                        raise ValueError('Unable to convert {} to {}'.format(value, units))
                    elif on_dimensionless == 'warn':
                        msg = 'Assuming units `{1.units}` for {0}'.format(value, units)
                        warnings.warn(msg, DimensionalityWarning)
                        _LOG.warn(msg)

                # on_incompatible == 'ignore'
                return float(value)
        return _inner
    else:
        def _inner(value):
            if isinstance(value, Q_):
                try:
                    return value.to(units)
                except ValueError as e:
                    if on_incompatible == 'raise':
                        raise ValueError(e)
                    elif on_incompatible == 'warn':
                        msg = 'Assuming units `{1.units}` for {0}'.format(value, units)
                        warnings.warn(msg, DimensionalityWarning)
                        _LOG.warn(msg)

                # on_incompatible == 'ignore'
                return float(value.magnitude) * units
            else:
                if not units.dimensionless:
                    if on_dimensionless == 'raise':
                        raise ValueError('Unable to convert {} to {}'.format(value, units))
                    elif on_dimensionless == 'warn':
                        msg = 'Assuming units `{1.units}` for {0}'.format(value, units)
                        warnings.warn(msg, DimensionalityWarning)
                        _LOG.warn(msg)

                # on_incompatible == 'ignore'
                return float(value) * units
        return _inner


class Processor(object):
    """Processor to convert the function parameters.

    A `callable` argument will be used to convert the corresponding
    function argument.

    For example, here `x` will be converted to float, before entering
    the function body::

        >>> conv = Processor(float)
        >>> conv
        <class 'float'>
        >>> conv('10')
        10.0

    The processor supports multiple argument conversion in a tuple::

        >>> conv = Processor((float, str))
        >>> type(conv)
        <class 'lantz.processors.Processor'>
        >>> conv(('10', 10))
        (10.0, '10')

    """

    def __new__(cls, processors):

        if isinstance(processors, (tuple, list)):
            if len(processors) > 1:
                inst = super().__new__(cls)
                inst.processors = tuple(cls._to_callable(processor)
                                        for processor in processors)
                return inst
            else:
                return cls._to_callable(processors[0])
        else:
            return cls._to_callable(processors)

    def __call__(self, values):
        return tuple(processor(value)
                     for processor, value in zip(self.processors, values))

    @classmethod
    def _to_callable(cls, obj):
        if callable(obj):
            return obj
        if obj is None:
            return _do_nothing
        return cls.to_callable(obj)

    @classmethod
    def to_callable(cls, obj):
        raise TypeError('Preprocessor argument must callable, not {}'.format(obj))

    def __len__(self):
        if isinstance(self.processors, tuple):
            return len(self.processors)
        return 1


class FromQuantityProcessor(Processor):
    """Processor to convert the units the function arguments.

    The syntax is equal to `Processor` except that strings are interpreted
    as units.

        >>> conv = FromQuantityProcessor('ms')
        >>> conv(Q_(1, 's'))
        1000.0

    """

    @classmethod
    def to_callable(cls, obj):
        if isinstance(obj, (str, Q_)):
            return convert_to(obj, return_float=True)
        raise TypeError('FromQuantityProcessor argument must be a string '
                        ' or a callable, not {}'.format(obj))


class ToQuantityProcessor(Processor):
    """Decorator to convert the units the function arguments.

    The syntax is equal to `Processor` except that strings are interpreted
    as units.

        >>> conv = ToQuantityProcessor('ms')
        >>> conv(Q_(1, 's'))
        <Quantity(1000.0, 'millisecond')>
        >>> conv(1)
        <Quantity(1.0, 'millisecond')>

    """

    @classmethod
    def to_callable(cls, obj):
        if isinstance(obj, (str, Q_)):
            return convert_to(obj, on_dimensionless='ignore')
        raise TypeError('ToQuantityProcessor argument must be a string '
                        ' or a callable, not {}'.format(obj))


class ParseProcessor(Processor):
    """Processor to convert/parse the function parameters.

    The syntax is equal to `Processor` except that strings are interpreted
    as a :class:Parser expression.

        >>> conv = ParseProcessor('spam {:s} eggs')
        >>> conv('spam ham eggs')
        'ham'

        >>> conv = ParseProcessor(('hi {:d}', 'bye {:s}'))
        >>> conv(('hi 42', 'bye Brian'))
        (42, 'Brian')

    """

    @classmethod
    def to_callable(cls, obj):
        if isinstance(obj, str):
            return Parser(obj)
        raise TypeError('parse_params argument must be a string or a callable, '
                        'not {}'.format(obj))


class MapProcessor(Processor):
    """Processor to map the function parameter values.

    The syntax is equal to `Processor` except that a dict is used as
    mapping table.

    Examples::

        >>> conv = MapProcessor({True: 42})
        >>> conv(True)
        42

    """

    @classmethod
    def to_callable(cls, obj):
        if isinstance(obj, dict):
            return get_mapping(obj)
        if isinstance(obj, set):
            return check_membership(obj)
        raise TypeError('MapProcessor argument must be a dict or a callable, '
                        'not {}'.format(obj))


class ReverseMapProcessor(Processor):
    """Processor to map the function parameter values.

    The syntax is equal to `Processor` except that a dict is used as
    mapping table.

    Examples::

        >>> conv = ReverseMapProcessor({True: 42})
        >>> conv(42)
        True
    """

    #: Shared cache of reversed dictionaries indexed by the id()
    __reversed_cache = {}

    @classmethod
    def to_callable(cls, obj):
        if isinstance(obj, dict):
            obj = cls.__reversed_cache.setdefault(id(obj),
                                                  {value: key for key, value
                                                   in obj.items()})
            return get_mapping(obj)
        if isinstance(obj, set):
            return check_membership(obj)
        raise TypeError('ReverseMapProcessor argument must be a dict or a callable, '
                        'not {}'.format(obj))


class RangeProcessor(Processor):
    """Processor to convert the units the function arguments.

    The syntax is equal to `Processor` except that iterables are interpreted
    as (low, high, step) specified ranges. Step is optional and max is included

        >>> conv = RangeProcessor(((1, 2, .5), ))
        >>> conv(1.7)
        1.5

    """

    @classmethod
    def to_callable(cls, obj):
        if not isinstance(obj, (list, tuple)):
            raise TypeError('RangeProcessor argument must be a tuple/list '
                            'or a callable, not {}'.format(obj))
        if not len(obj) in (1, 2, 3):
            raise TypeError('RangeProcessor argument must be a tuple/list '
                            'with 1, 2 or 3 elements ([low,] high[, step]) '
                            'not {}'.format(len(obj)))

        if len(obj) == 1:
            return check_range_and_coerce_step(0, *obj)
        return check_range_and_coerce_step(*obj)



def check_range_and_coerce_step(low, high, step=None):
    """

    :param low:
    :param high:
    :param step:
    :return:

        >>> checker = check_range_and_coerce_step(1, 10)
        >>> checker(1), checker(5), checker(10)
        (1, 5, 10)
        >>> checker(11)
        Traceback (most recent call last):
        ...
        ValueError: 11 not in range (1, 10)
        >>> checker = check_range_and_coerce_step(1, 10, 1)
        >>> checker(1), checker(5.4), checker(10)
        (1, 5, 10)

    """
    def _inner(value):
        if not (low <= value <= high):
            raise ValueError('{} not in range ({}, {})'.format(value, low, high))
        if step:
            value = round((value - low) / step) * step + low
        return value

    return _inner


def check_membership(container):
    """

    :param container:
    :return:

        >>> checker = check_membership((1, 2, 3))
        >>> checker(1)
        1
        >>> checker(0)
        Traceback (most recent call last):
        ...
        ValueError: 0 not in (1, 2, 3)

    """

    def _inner(value):
        if value not in container:
            raise ValueError('{!r} not in {}'.format(value, container))
        return value
    return _inner


def get_mapping(container):
    """
        >>> getter = get_mapping({'A': 42, 'B': 43})
        >>> getter('A')
        42
        >>> checker(0)
        Traceback (most recent call last):
        ...
        ValueError: 0 not in ('A', 'B')

    """

    def _inner(key):
        if key not in container:
            raise ValueError("{!r} not in {}".format(key, tuple(container.keys())))
        return container[key]
    return _inner
