
import ctypes

from lantz.foreign import LibraryDriver, RetStr, RetTuple

def _a():
    class MyDriver(LibraryDriver):

        LIBRARY_NAME = 'simplelib.dylib'

    P_ = ctypes.POINTER

    x = MyDriver()

    a = x.lib.returni10()
    print(a, type(a))

    b = x.lib.sumi13(5)
    print(b, type(b))

    x.lib.internal.returnf10.restype = ctypes.c_float
    a = x.lib.returnf10()
    print(a, type(a))

    x.lib.internal.returnd10.restype = ctypes.c_double
    a = x.lib.returnd10()
    print(a, type(a))

    here = ctypes.create_string_buffer(b"Hello", 20)
    print(type(here))
    here = (ctypes.c_char * 20)()
    print(type(here))
    a = x.lib.withCharp(here, len(here))
    print(a, here.value, type(here))

    a, ret = x.lib.withCharp(RetStr(20), 20)
    print(a, ret, type(ret))

    a, ret  = x.lib.withCharp(*RetStr(20))
    print(a, ret, type(ret))

    here = ctypes.create_string_buffer(b'23',20)
    a = x.lib.atoime(here)
    print(a, type(a))

    a = x.lib.atoime('23')
    print(a, type(a))

    p = (ctypes.c_double * 3)()
    a = x.lib.double_param(p)
    print(a, p, p[:], type(p))

    a = x.lib.double_param(RetTuple('d', 3))
    print(a, p, p[:], type(p))
