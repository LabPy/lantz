# -*- coding: utf-8 -*-
"""
    lantz.foreign
    ~~~~~~~~~~~~~

    Implements classes and methods to interface to foreign functions.

    :copyright: (c) 2011 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import ctypes
from ctypes.util import find_library
from itertools import chain

from lantz import Driver

class Library(object):
    """Library wrapper

    :param library: ctypes library
    :param wrapper: callable that takes two arguments the name of the function
                    and the function itself. It should return a callable.
    """

    def __init__(self, library, wrapper):
        if isinstance(library, str):
            if library.lower().endswith('.dll'):
                library = ctypes.WinDLL(library)
            else:
                library = ctypes.CDLL(library)

        self.internal = library
        self.wrapper = wrapper

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        func = self.wrapper(name, getattr(self.internal, name))
        setattr(self, name, func)
        return func


class RetStr():

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

class RetTuple():

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
             'd': ctypes.c_double}

    def __init__(self, type, length):
        try:
            self.buffer = (self.TYPES[type] * length)()
        except KeyError:
            raise KeyError('The type {} is not defined ()'.format(type, self.TYPES.keys()))
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

    #:Name of the library
    LIBRARY_NAME = ''

    def __libs(self, library_name):
        if not library_name:
            raise StopIteration
        if isinstance(library_name, str):
            yield library_name
            yield find_library(library_name.split('.')[0])
        else:
            for name in library_name:
                yield name
                yield find_library(name.split('.')[0])

    def __init__(self, *args, **kwargs):
        library_name = kwargs.pop('library_name', None)
        super().__init__(*args, **kwargs)

        for name in chain(self.__libs(library_name),
                          self.__libs(self.LIBRARY_NAME)):
            try:
                self.lib = Library(name, self._wrapper)
                break
            except OSError:
                pass
        else:
            raise Exception('library not found')

        self.log_info('LibraryDriver created with {}'.format(name))


    def _return_handler(self, func_name, ret_value):
        return ret_value

    def _wrapper(self, name, func):
        def _inner(*args):
            new_args = []
            collect = []
            for arg in args:
                if isinstance(arg, (RetStr, RetTuple)):
                    collect.append(arg)
                    new_args.append(arg.buffer)
                elif isinstance(arg, str):
                    new_args.append(bytes(arg, 'ascii'))
                else:
                    new_args.append(arg)

            ret = self._return_handler(name, func(*new_args))

            if collect:
                values = [item.value for item in collect]
                values.insert(0, ret)
                self.log_debug('Function call {} returned {}. Collected: {}'.format(name, ret, collect))
                return tuple(values)

            self.log_debug('Function call {} returned {}.'.format(name, ret))
            return ret

        return _inner



