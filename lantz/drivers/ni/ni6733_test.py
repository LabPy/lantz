import ctypes as ct

nidaq = ct.windll.nicaiu 

_ChanForAllLines = 1
_GroupByChannel = 0
_DAQmx_Val_Hz = ct.c_long(10373)
_DAQmx_Val_High = ct.c_long(10192)
_DAQmx_Val_Low = ct.c_long(10214)
_DAQmx_Val_Seconds = ct.c_long(10364)
_Val_FinitSamps = 10178

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
timeout = ct.c_double(50)

CHK(nidaq.DAQmxCreateTask("", ct.byref(hndl)) )

initDelay = ct.c_double(0) # in seconds
lowTime = ct.c_double(0.0001)
highTime = ct.c_double(0.0001)

CHK(nidaq.DAQmxCreateCOPulseChanTime(hndl, "Dev2/ctr0", "",
                                        _DAQmx_Val_Seconds,
                                        _DAQmx_Val_High,
                                        initDelay,
                                        lowTime,
                                        highTime) )

CHK(nidaq.DAQmxStartTask(hndl))
CHK(nidaq.DAQmxWaitUntilTaskDone(hndl, timeout))

CHK(nidaq.DAQmxStopTask(hndl))
CHK(nidaq.DAQmxClearTask(hndl))
