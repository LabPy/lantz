import ctypes as ct

class SinglePulse(object):

    def __init__(self):

        self.nidaq = ct.WinDLL("nicaiu.dll")
        self._DAQmx_Val_High = ct.c_long(10192)
        self._DAQmx_Val_Low = ct.c_long(10214)
        self._DAQmx_Val_Seconds = ct.c_long(10364)
        self._DAQmx_Val_ChanPerLine = ct.c_long(0) 

    def CHK(self, err):
        """a simple error checking routine
        TODO
        """
        if err < 0:
            buf_size = 100
            buf = ct.create_string_buffer('\000' * buf_size)
            self.nidaq.DAQmxGetErrorString(err,ct.byref(buf),buf_size)
            raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))
        if err > 0:
            buf_size = 100
            buf = ct.create_string_buffer('\000' * buf_size)
            self.nidaq.DAQmxGetErrorString(err,ct.byref(buf),buf_size)
            raise RuntimeError('nidaq generated warning %d: %s'%(err,repr(buf.value)))

    def run(self, lowtime, hightime):
        hndl = ct.c_ulong(0)
        initdelay = ct.c_double(0) # in seconds
        lowtime = ct.c_double(lowtime)
        hightime = ct.c_double(hightime)
        timeout = ct.c_double(50)
        self.CHK(self.nidaq.DAQmxCreateTask("", ct.byref(hndl)) )
        self.CHK(self.nidaq.DAQmxCreateCOPulseChanTime(hndl, "Dev2/ctr0", "",
                                                self._DAQmx_Val_Seconds,
                                                self._DAQmx_Val_High,
                                                initdelay,
                                                lowtime,
                                                hightime) )
        self.CHK(self.nidaq.DAQmxStartTask(hndl))
        self.CHK(self.nidaq.DAQmxWaitUntilTaskDone(hndl, timeout))
        self.CHK(self.nidaq.DAQmxStopTask(hndl))
        self.CHK(self.nidaq.DAQmxClearTask(hndl))

    def digiout(self, line, state):
        _ChanForAllLines = 1
        _GroupByChannel = 0

        error = ct.c_long(0)
        hndl = ct.c_ulong(0)
        values = (state,)
        data = (ct.c_ubyte*len(values))(*values)
        errBuff = ct.c_char_p(2048)

        self.CHK(self.nidaq.DAQmxCreateTask("", ct.byref(hndl)) )
        self.CHK(self.nidaq.DAQmxCreateDOChan(hndl, "Dev2/port0/line" +
                                    str(line), "", self._DAQmx_Val_ChanPerLine) )
        self.CHK(self.nidaq.DAQmxStartTask(hndl) )
        samples = ct.c_long(1)
        autostart = ct.c_bool(1)
        timeout = ct.c_double(10)
        self.CHK(self.nidaq.DAQmxWriteDigitalLines(hndl, samples, autostart, timeout, _GroupByChannel, 
                                        data, None, None) )
        #self.CHK(self.nidaq.DAQmxWaitUntilTaskDone(hndl, timeout))
        self.CHK(self.nidaq.DAQmxStopTask(hndl))
        self.CHK(self.nidaq.DAQmxClearTask(hndl))

