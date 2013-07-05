
import ctypes
import unittest

from array import array

from lantz.foreign import LibraryDriver, RetStr, RetTuple, RetValue, TYPES

class Array(array):

    @property
    def _as_parameter_(self):
        return self.buffer_info()[0]

    def array_len(self):
        return self.buffer_info()

class MyDriver(LibraryDriver):

    LIBRARY_NAME = 'simplelib.dylib'

class MyWrongDriver(LibraryDriver):

    LIBRARY_NAME = 'no_simplelib.dylib'

class ForeignTest(unittest.TestCase):

    def setUp(self):
        self.driver = MyDriver()

    def test_raise(self):
        self.assertRaises(OSError, MyWrongDriver, ())

    def test_simple_return(self):
        a = self.driver.lib.returni10()
        self.assertEqual(a, 10)
        self.assertEqual(type(a), int)

        a = self.driver.lib.sumi13(5)
        self.assertEqual(a, 18)
        self.assertEqual(type(a), int)

    def test_return_string(self):
        value = ctypes.create_string_buffer(b"Hello", 20)
        value = (ctypes.c_char * 20)()
        ret = self.driver.lib.write_in_charp(value, len(value))
        value = value.value.decode('ascii')
        self.assertEqual((ret, value, type(value)), (1, '28G11AC10T32', str))

        ret, value = self.driver.lib.write_in_charp(RetStr(20), 20)
        self.assertEqual((ret, value, type(value)), (1, '28G11AC10T32', str))

        ret, value = self.driver.lib.write_in_charp(*RetStr(20))
        self.assertEqual((ret, value, type(value)), (1, '28G11AC10T32', str))

    def test_atoi(self):
        value = ctypes.create_string_buffer(b'23',20)
        ret = self.driver.lib.use_atoi(value)
        self.assertEqual(ret, 23)

        ret = self.driver.lib.use_atoi('23')
        self.assertEqual(ret, 23)

    def test_return_array(self):
        value = (ctypes.c_double * 3)()
        ret = self.driver.lib.double_array_param(value)
        value = tuple(value[:])
        self.assertEqual((ret, value, type(value)), (1, (1, 2, 3), tuple))

        ret, value = self.driver.lib.double_array_param(RetTuple('d', 3))
        self.assertEqual((ret, value, type(value)), (1, (1, 2, 3), tuple))

        value = (ctypes.c_double * 10)()
        ret = self.driver.lib.double_array_length_param(value, 10)
        value = tuple(value[:])
        self.assertEqual((ret, value, type(value)), (1, tuple(range(10)), tuple))

        ret, value = self.driver.lib.double_array_length_param(*RetTuple('d', 10))
        self.assertEqual((ret, value, type(value)), (1, tuple(range(10)), tuple))

        l = 10
        arr = tuple(range(l))
        total = float(sum(arr))
        self.driver.lib.internal.sum_double_array_length.restype = ctypes.c_double

        value = (ctypes.c_double * l)(*arr)
        ret = self.driver.lib.sum_double_array_length(value, l)
        self.assertEqual((ret, type(ret)), (total, type(total)))

        value = Array('d', arr)
        ret = self.driver.lib.sum_double_array_length(*value.buffer_info())
        self.assertEqual((ret, type(ret)), (total, type(total)))

        ret = self.driver.lib.sum_double_array_length(value, l)
        self.assertEqual((ret, type(ret)), (total, type(total)))

        ret = self.driver.lib.sum_double_array_length(*value.array_len())
        self.assertEqual((ret, type(ret)), (total, type(total)))

    def test_return_value(self):
        value = ctypes.c_double()
        ret = self.driver.lib.double_param(ctypes.byref(value))
        value = value.value
        self.assertEqual((ret, value, type(value)), (1, 7., float))

        ret, value = self.driver.lib.double_param(RetValue('d'))
        self.assertEqual((ret, value, type(value)), (1, 7., float))


