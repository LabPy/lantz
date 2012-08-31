# -*- coding: utf-8 -*-
"""
    lantz.drivers.aeroflex.daqe
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers for Full-Featured E Series Multifunctional DAQ
    12 or 16-bit, up to 1.25 MS/s, up to 64 Analog Inputs


    Sources::

        - ???

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
# http://pylibnidaqmx.googlecode.com/svn/trunk/nidaqmx/libnidaqmx.py
from lantz import Feat, Action
from lantz.errors import InstrumentError
from lantz.foreign import LibraryDriver, RetValue, RetStr

import ctypes

default_buf_size = 3000


class NI6052E(LibraryDriver):

    LIBRARY_NAME = 'nicaiu'



class System(LibraryDriver):
    """
    Exposes NI-DACmx system properties to Python.

    Attributes
    ----------
    major_version
    minor_version
    version
    devices
    tasks
    global_channels
    """

    LIBRARY_NAME = 'nicaiu'
    
    def _return_handler(self, func_name, ret_value):
        if ret_value < 0:
            msg = 'Cannot obtain error message'
            if not func_name == 'DAQmxGetExtendedErrorInfo':
                err, msg = self.lib.DAQmxGetExtendedErrorInfo(*RetStr(default_buf_size * 100))
                if err < 0:
                    msg = 'Cannot obtain error message'
            raise InstrumentError('In {}: {} ({})'.format(func_name, msg, ret_value))
        return ret_value
    
    @Feat(read_once=True)
    def version(self):
        """Version of installed NI-DAQ library. 
        """
        err, major  = self.lib.DAQmxGetSysNIDAQMajorVersion(RetValue('I'))
        err, minor  = self.lib.DAQmxGetSysNIDAQMinorVersion(RetValue('I'))
        return major, minor

    @Feat()
    def device_names(self):
        """Indicates the names of all devices installed in the system.
        """
        err, buf = self.lib.DAQmxGetSysDevNames(*RetStr(default_buf_size))
        names = tuple(n.strip() for n in buf.split(',') if n.strip())
        return names

    @Feat()
    def tasks(self):
        """
        Indicates an array that contains the names of all tasks saved
        on the system.
        """
        buf_size = default_buf_size
        buf = ctypes.create_string_buffer('\000' * buf_size)
        CALL ('GetSysTasks', ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    @Feat()
    def global_channels(self):
        """
        Indicates an array that contains the names of all global
        channels saved on the system.
        """
        buf_size = default_buf_size
        buf = ctypes.create_string_buffer('\000' * buf_size)
        CALL ('GetSysGlobalChans', ctypes.byref (buf), buf_size)
        names = [n.strip() for n in buf.value.split(',') if n.strip()]
        return names

    
if __name__ == '__main__':
    
    import lantz.log

    lantz.log.log_to_screen(lantz.log.DEBUG)
    
    inst = System()
    print(inst.version)
    print(inst.device_names)