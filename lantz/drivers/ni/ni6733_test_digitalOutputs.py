import ctypes as ct


nidaq = ct.windll.nicaiu 

#int32 = ctypes.c_long
#uInt32 = ctypes.c_ulong
#uInt64 = ctypes.c_ulonglong
#float64 = ctypes.c_double
#TaskHandle = uInt32

#DAQmx_Val_Cfg_Default = int32(-1)
#DAQmx_Val_Volts = 10348
#DAQmx_Val_Rising = 10280
#DAQmx_Val_FiniteSamps = 10178
#DAQmx_Val_ContSamps = 10123
#DAQmx_Val_GroupByChannel = 0

#DAQmx_Val_ChanPerLine = 0
_ChanForAllLines = 1
_GroupByChannel = 0

def CHK(err):
    """a simple error checking routine"""
    if err < 0:
        buf_size = 100
        buf = ct.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err,ct.byref(buf),buf_size)
        raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))
    if err > 0:
        buf_size = 100
        buf = ct.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err,ct.byref(buf),buf_size)
        raise RuntimeError('nidaq generated warning %d: %s'%(err,repr(buf.value)))

error = ct.c_long(0)
hndl = ct.c_ulong(0)
values = (0, 0, 0 , 0, 0, 0, 0, 0)
data = (ct.c_ubyte*8)(*values)
errBuff = ct.c_char_p(2048)

CHK(nidaq.DAQmxCreateTask("", ct.byref(hndl)) )
CHK(nidaq.DAQmxCreateDOChan(hndl, "Dev2/port0/line0:7", "", _ChanForAllLines) )
CHK(nidaq.DAQmxStartTask(hndl) )
samples = ct.c_long(1)
autostart = ct.c_bool(1)
timeout = ct.c_double(10)
CHK(nidaq.DAQmxWriteDigitalLines(hndl, samples, autostart, timeout, _GroupByChannel, 
                                data, None, None) )
