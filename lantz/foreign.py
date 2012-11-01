# -*- coding: utf-8 -*-
"""
    lantz.foreign
    ~~~~~~~~~~~~~

    Implements classes and methods to interface to foreign functions.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os
import ctypes
import inspect
from ctypes.util import find_library
from itertools import chain

from lantz import Driver


class Wrapper(object):

    def __init__(self, name, wrapped, wrapper):
        self.name = name
        self.wrapped = wrapped
        self.wrapper = wrapper

    def __call__(self, *args):
        return self.wrapper(self.name, self.wrapped, *args)

    @property
    def argtypes(self):
        return self.wrapped.argtypes

    @argtypes.setter
    def argtypes(self, value):
        self.wrapped.argtypes = value

    @property
    def restype(self):
        return self.wrapped.restype

    @restype.setter
    def restype(self, value):
        self.wrapped.restype = value


class Library(object):
    """Library wrapper

    :param library: ctypes library
    :param wrapper: callable that takes two arguments the name of the function
                    and the function itself. It should return a callable.
    """

    def __init__(self, library, prefix='', wrapper=None):
        if isinstance(library, str):
            self.library_name = library

            if os.name == 'nt':
                library = ctypes.WinDLL(library)
            else:
                library = ctypes.CDLL(library)

        self.wrapper = wrapper
        self.prefix = prefix
        self.internal = library

    def __get_func(self, name):
        if self.prefix:
            try:
                return getattr(self.internal, self.prefix + name)
            except Exception:
                pass

        try:
            return getattr(self.internal, name)
        except Exception:
            if self.prefix:
                raise AttributeError('Could not find ({}){} in {}'.format(self.prefix, name, self.internal))
            raise AttributeError('Could not find {} in {}'.format(name, self.internal))

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)

        func = self.__get_func(name)

        if self.wrapper:
            func = Wrapper(name, func, self.wrapper)

        setattr(self, name, func)
        return func


TYPES = {'c': ctypes.c_char,
         'b': ctypes.c_byte,
         'B': ctypes.c_ubyte,
         '?': ctypes.c_bool,
         'h': ctypes.c_short,
         'H': ctypes.c_ushort,
         'i': ctypes.c_int,
         'I': ctypes.c_uint,
         'l': ctypes.c_long,
         'L': ctypes.c_ulong,
         'q': ctypes.c_longlong,
         'Q': ctypes.c_ulonglong,
         'f': ctypes.c_float,
         'd': ctypes.c_double,
         'u32': ctypes.c_uint32,
         'i32': ctypes.c_int32,
         'f32': ctypes.c_float,
         'f64': ctypes.c_double}


class RetStr(object):

    def __init__(self, length, encoding='ascii'):
        self.length = length
        self.buffer = ctypes.create_string_buffer(b'', length)
        self.encoding = encoding

    def __iter__(self):
        yield self
        yield self.length

    @property
    def value(self):
        if self.encoding:
            return self.buffer.value.decode(self.encoding)
        else:
            return self.buffer.value


class RetValue(object):

    def __init__(self, type):
        try:
            self.buffer = (TYPES[type] * 1)()
        except KeyError:
            raise KeyError('The type {} is not defined ()'.format(type, TYPES.keys()))

    def __iter__(self):
        yield self

    @property
    def value(self):
        return self.buffer[0]


class RetTuple(object):

    def __init__(self, type, length=1):
        try:
            self.buffer = (TYPES[type] * length)()
        except KeyError:
            raise KeyError('The type {} is not defined ()'.format(type, TYPES.keys()))
        self.length = length

    def __iter__(self):
        yield self
        yield self.length

    @property
    def value(self):
        return tuple(self.buffer[:])


class LibraryDriver(Driver):
    """Base class for drivers that communicate with instruments
    calling a library (dll or others)

    To use this class you must override LIBRARY_NAME
    """

    #: Name of the library
    LIBRARY_NAME = ''
    LIBRARY_PREFIX = ''

    def __init__(self, *args, **kwargs):
        library_name = kwargs.pop('library_name', None)
        super().__init__(*args, **kwargs)

        folder = os.path.dirname(inspect.getfile(self.__class__))
        for name in chain(iter_lib(library_name, folder), iter_lib(self.LIBRARY_NAME, folder)):
            if name is None:
                continue
            self.log_debug('Trying to open library: {}'.format(name))
            try:
                self.lib = Library(name, self.LIBRARY_PREFIX, self._wrapper)
                break
            except OSError:
                pass
        else:
            raise OSError('While instantiating {}: library not found'.format(self.__class__.__name__))

        self.log_info('LibraryDriver created with {}', name)
        self._add_types()


    def _add_types(self):
        pass

    def _return_handler(self, func_name, ret_value):
        return ret_value

    def _preprocess_args(self, name, *args):
        new_args = []
        collect = []
        for arg in args:
            if isinstance(arg, (RetStr, RetTuple, RetValue)):
                collect.append(arg)
                new_args.append(arg.buffer)
            elif isinstance(arg, str):
                new_args.append(bytes(arg, 'ascii'))
            else:
                new_args.append(arg)

        return new_args, collect

    def _wrapper(self, name, func, *args):
        new_args, collect = self._preprocess_args(name, *args)

        try:
            ret = func(*new_args)
        except Exception as e:
            raise Exception('While calling {} with {} (was {}): {}'.format(name, new_args, args, e))

        ret = self._return_handler(name, ret)

        return self._postprocess(name, ret, collect)

    def _postprocess(self, name, ret, collect):
        if collect:
            values = [item.value for item in collect]
            values.insert(0, ret)
            self.log_debug('Function call {} returned {}. Collected: {}', name, ret, collect)
            return tuple(values)

        self.log_debug('Function call {} returned {}.', name, ret)
        return ret


def iter_lib(library_name, folder=''):
    if not library_name:
        raise StopIteration
    if isinstance(library_name, str):
        if folder:
            yield os.path.join(folder, library_name)
        yield library_name
        yield find_library(library_name.split('.')[0])
    else:
        for name in library_name:
            if folder:
                yield os.path.join(folder, name)
        for name in library_name:
            yield name
            yield find_library(name.split('.')[0])
