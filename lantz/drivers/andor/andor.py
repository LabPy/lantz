# -*- coding: utf-8 -*-
"""
    lantz.drivers.andor.andor
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Low level driver wrapping atcore andor library.


    Sources::

        - Andor Manual

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import ctypes as ct

from lantz import Driver, Feat, Action
from lantz.errors import InstrumentError
from lantz.foreign import LibraryDriver

_ERRORS = {
    0: 'SUCCESS',
    1: 'AT_ERR_NOTINITIALISED',
    1: 'AT_HANDLE_SYSTEM', # TODO: Check twice the same key!
    2: 'AT_ERR_NOTIMPLEMENTED',
    3: 'AT_ERR_READONLY',
    4: 'AT_ERR_NOTREADABLE',
    5: 'AT_ERR_NOTWRITABLE',
    6: 'AT_ERR_OUTOFRANGE',
    7: 'AT_ERR_INDEXNOTAVAILABLE',
    8: 'AT_ERR_INDEXNOTIMPLEMENTED',
    9: 'AT_ERR_EXCEEDEDMAXSTRINGLENGTH',
    10: 'AT_ERR_CONNECTION',
    11: 'AT_ERR_NODATA',
    12: 'AT_ERR_INVALIDHANDLE',
    13: 'AT_ERR_TIMEDOUT',
    14: 'AT_ERR_BUFFERFULL',
    15: 'AT_ERR_INVALIDSIZE',
    16: 'AT_ERR_INVALIDALIGNMENT',
    17: 'AT_ERR_COMM',
    18: 'AT_ERR_STRINGNOTAVAILABLE',
    19: 'AT_ERR_STRINGNOTIMPLEMENTED',
    20: 'AT_ERR_NULL_FEATURE',
    21: 'AT_ERR_NULL_HANDLE',
    22: 'AT_ERR_NULL_IMPLEMENTED_VAR',
    23: 'AT_ERR_NULL_READABLE_VAR',
    24: 'AT_ERR_NULL_READONLY_VAR',
    25: 'AT_ERR_NULL_WRITABLE_VAR',
    26: 'AT_ERR_NULL_MINVALUE',
    27: 'AT_ERR_NULL_MAXVALUE',
    28: 'AT_ERR_NULL_VALUE',
    29: 'AT_ERR_NULL_STRING',
    30: 'AT_ERR_NULL_COUNT_VAR',
    31: 'AT_ERR_NULL_ISAVAILABLE_VAR',
    32: 'AT_ERR_NULL_MAXSTRINGLENGTH',
    33: 'AT_ERR_NULL_EVCALLBACK',
    34: 'AT_ERR_NULL_QUEUE_PTR',
    35: 'AT_ERR_NULL_WAIT_PTR',
    36: 'AT_ERR_NULL_PTRSIZE',
    37: 'AT_ERR_NOMEMORY',
    100: 'AT_ERR_HARDWARE_OVERFLOW',
    -1: 'AT_HANDLE_UNINITIALISED'
}

class Andor(LibraryDriver):

    LIBRARY_NAME = 'atcore.dll'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.AT_H = ct.c_int()
        self.AT_U8 = ct.c_ubyte()
        self.cameraIndex = ct.c_int(0)

    def _patch_functions(self):
        internal = self.lib.internal
        internal.AT_Command.argtypes = [ct.c_int, ct.c_wchar_p, ]

        internal.AT_GetInt.argtypes = [ct.c_int, ct.c_wchar_p, ct.addressof(ct.c_longlong)]
        internal.AT_SetInt.argtypes = [ct.c_int, ct.c_wchar_p, ct.c_longlong]

        internal.AT_GetFloat.argtypes = [ct.c_int, ct.c_wchar_p, ct.addressof(ct.c_double)]
        internal.AT_SetFloat.argtypes = [ct.c_int, ct.c_wchar_p, ct.c_double]

        internal.AT_GetBool.argtypes = [ct.c_int, ct.c_wchar_p, ct.addressof(ct.c_bool)]
        internal.AT_SetBool.argtypes = [ct.c_int, ct.c_wchar_p, ct.c_bool]

        internal.AT_GetEnumerated.argtypes = [ct.c_int, ct.c_wchar_p, ct.addressof(ct.c_int)]
        internal.AT_SetEnumerated.argtypes = [ct.c_int, ct.c_wchar_p, ct.c_int]

        internal.AT_SetEnumString.argtypes = [ct.c_int, ct.c_wchar_p, ct.c_wchar_p]

    def _return_handler(self, func_name, ret_value):
        if ret_value != 0:
            raise InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    def initialize(self):
        """Initialise Library.
        """
        self.lib.AT_InitialiseLibrary()
        self.open()

    def finalize(self):
        """Finalise Library. Concluding function.
        """
        self.close()
        self.lib.AT_FinaliseLibrary()

    @Action()
    def open(self):
        """Open camera self.AT_H.
        """
        camidx = ct.c_int(0)
        self.lib.AT_Open(camidx, ct.addressof(self.AT_H))
        return self.AT_H

    @Action()
    def close(self):
        """Close camera self.AT_H.
        """
        self.lib.AT_Close(self.AT_H)

    def is_implemented(self, strcommand):
        """Checks if command is implemented.
        """
        result = ct.c_bool()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_IsImplemented(self.AT_H, command, ct.addressof(result))
        return result.value

    def is_writable(self, strcommand):
        """Checks if command is writable.
        """
        result = ct.c_bool()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_IsWritable(self.AT_H, command, ct.addressof(result))
        return result.value

    def queuebuffer(self, bufptr, value):
        """Put buffer in queue.
        """
        value = ct.c_int(value)
        self.lib.AT_QueueBuffer(self.AT_H, ct.byref(bufptr), value)

    def waitbuffer(self, ptr, bufsize):
        """Wait for next buffer ready.
        """
        timeout = ct.c_int(20000)
        self.lib.AT_WaitBuffer(self.AT_H, ct.byref(ptr), ct.byref(bufsize), timeout)

    def command(self, strcommand):
        """Run command.
        """
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_Command(self.AT_H, command)

    def getint(self, strcommand):
        """Run command and get Int return value.
        """
        result = ct.c_longlong()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetInt(self.AT_H, command, ct.addressof(result))
        return result.value

    def setint(self, strcommand, value):
        """SetInt function.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_longlong(value)
        self.lib.AT_SetInt(self.AT_H, command, value)

    def getfloat(self, strcommand):
        """Run command and get Int return value.
        """
        result = ct.c_double()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetFloat(self.AT_H, command, ct.addressof(result))
        return result.value

    def setfloat(self, strcommand, value):
        """Set command with Float value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_double(value)
        self.lib.AT_SetFloat(self.AT_H, command, value)

    def getbool(self, strcommand):
        """Run command and get Bool return value.
        """
        result = ct.c_bool()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetBool(self.AT_H, command, ct.addressof(result))
        return result.value

    def setbool(self, strcommand, value):
        """Set command with Bool value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_bool(value)
        self.lib.AT_SetBool(self.AT_H, command, value)

    def getenumerated(self, strcommand):
        """Run command and set Enumerated return value.
        """
        result = ct.c_int()
        command = ct.c_wchar_p(strcommand)
        self.lib.AT_GetEnumerated(self.AT_H, command, ct.addressof(result))

    def setenumerated(self, strcommand, value):
        """Set command with Enumerated value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        value = ct.c_bool(value)
        self.lib.AT_SetEnumerated(self.AT_H, command, value) #TODO: IS THIS CORRECT

    def setenumstring(self, strcommand, item):
        """Set command with EnumeratedString value parameter.
        """
        command = ct.c_wchar_p(strcommand)
        item = ct.c_wchar_p(item)
        self.lib.AT_SetEnumString(self.AT_H, command, item)
        
    def flush(self):
        self.lib.AT_Flush(self.AT_H)

if __name__ == '__main__':
    import numpy as np
    import ctypes as ct
    from andor import Andor
    from matplotlib import pyplot as plt

    with Andor() as andor:
        andor.flush()
        width = andor.getint("SensorWidth")
        height = andor.getint("SensorHeight")
        length = width * height

        #andor.setenumerated("FanSpeed", 2)
        andor.getfloat("SensorTemperature")
        andor.setfloat("ExposureTime", 0.001)
        andor.setenumstring("PixelReadoutRate", "100 MHz")
        andor.setenumstring("PixelEncoding", "Mono32")
        #andor.setenumstring("PixelEncoding", "Mono16")

        imagesizebytes = andor.getint("ImageSizeBytes")

        userbuffer = ct.create_string_buffer(' ' * imagesizebytes)
        andor.queuebuffer(userbuffer, imagesizebytes)

        imsize = ct.c_int(1)
        ubuffer = ct.create_string_buffer(" " * 1)

        andor.command("AcquisitionStart")
        andor.waitbuffer(ubuffer, imsize)
        andor.command("AcquisitionStop")
        andor.flush()

        image = np.fromstring(userbuffer, dtype=np.uint32, count=length)
        #image = np.fromstring(userbuffer, dtype=np.uint16, count=length)
        image.shape = (height, width)

        im = plt.imshow(image, cmap = 'gray')
        plt.show()

        print(image.min(), image.max(), image.mean())

