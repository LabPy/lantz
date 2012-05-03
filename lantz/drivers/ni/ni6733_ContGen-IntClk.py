"""
This is an interpretation of the example program
C:\Program Files\National Instruments\NI-DAQ\Examples\DAQmx ANSI C\Analog Out\Generate Voltage\Cont Gen Volt Wfm-Int Clk\ContGen-IntClk.c
This routine will play an arbitrary-length waveform file.
This module depends on:
numpy
Adapted by Martin Bures [ mbures { @ } zoll { . } com ]
"""
# import system libraries
import ctypes
import numpy
import threading
# load any DLLs
nidaq = ctypes.windll.nicaiu # load the DLL
##############################
# Setup some typedefs and constants
# to correspond with values in
# C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\include\NIDAQmx.h
# the typedefs
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32
# the constants
DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_Volts = 10348
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_ContSamps = 10123
DAQmx_Val_GroupByChannel = 0
##############################
class WaveformThread( threading.Thread ):
    """
    This class performs the necessary initialization of the DAQ hardware and
    spawns a thread to handle playback of the signal.
    It takes as input arguments the waveform to play and the sample rate at which
    to play it.
    This will play an arbitrary-length waveform file.
    """
    def __init__( self, waveform, sampleRate ):
        self.running = True
        self.sampleRate = sampleRate
        self.periodLength = len( waveform )
        self.taskHandle = TaskHandle( 0 )
        self.data = numpy.zeros( ( self.periodLength, ), dtype=numpy.float64 )
        # convert waveform to a numpy array
        for i in range( self.periodLength ):
            self.data[ i ] = waveform[ i ]
        # setup the DAQ hardware
        self.CHK(nidaq.DAQmxCreateTask("",
                          ctypes.byref( self.taskHandle )))
        self.CHK(nidaq.DAQmxCreateAOVoltageChan( self.taskHandle,
                                   "Dev2/ao2",
                                   "",
                                   float64(-3.0),
                                   float64(3.0),
                                   DAQmx_Val_Volts,
                                   None))
        self.CHK(nidaq.DAQmxCfgSampClkTiming( self.taskHandle,
                                "",
                                float64(self.sampleRate),
                                DAQmx_Val_Rising,
                                #DAQmx_Val_FiniteSamps,
                                DAQmx_Val_ContSamps,
                                uInt64(self.periodLength)));
        self.CHK(nidaq.DAQmxWriteAnalogF64( self.taskHandle,
                              int32(self.periodLength),
                              0,
                              float64(-1),
                              DAQmx_Val_GroupByChannel,
                              self.data.ctypes.data,
                              None,
                              None))
        threading.Thread.__init__( self )

    def CHK( self, err ):
        """a simple error checking routine"""
        if err < 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
            raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))
        if err > 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
            raise RuntimeError('nidaq generated warning %d: %s'%(err,repr(buf.value)))

    def run( self ):
        counter = 0
        self.CHK(nidaq.DAQmxStartTask( self.taskHandle ))

    def stop( self ):
        self.running = False
        nidaq.DAQmxStopTask( self.taskHandle )
        nidaq.DAQmxClearTask( self.taskHandle )

if __name__ == '__main__':
    import time
    # generate a time signal 5 seconds long with 250Hz sample rate
    #t = numpy.arange( 0, 1, 1.0/1000.0 )
    samplesPerBuffer = 750
    cyclesPerBuffer = 15
    sampleRate = 50000.0
    f = 1000.0
    t = numpy.arange( 0, 1/f, 1/sampleRate)
    # generate sine wave
    #x = numpy.sin( t )
    x = numpy.sin( 2 * numpy.pi * f * t )
    mythread = WaveformThread( x, sampleRate)
    # start playing waveform
    mythread.start()
    # wait 5 seconds then stop
    time.sleep( 10 )
    mythread.stop()

