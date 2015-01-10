# -*- coding: utf-8 -*-
"""
    
        

	    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
	    :license: BSD, see LICENSE for more details.
"""


from lantz import Feat, Action, DictFeat
from lantz import Driver
from lantz.errors import InstrumentError

from _internal import u12 as _u12

class U12(Driver):
    """
        Driver for the Labjack U12 data acquisition device.
	http://labjack.com/support/u12/users-guide
        For details about the commands, refer to the users guide.
    """
    def __init__(self, board_id):
        self._internal = _u12.U12(board_id) 

    def initialize(self):
        super().initialize()
        self._internal.open()

    def finalize(self):
        self._internal.close()

     
    # ANALOG INPUT METHODS
    '''
    The LabJack U12 has 8 screw terminals for analog input signals (AI0-7). These can be configured individually and on-the-fly as 8 single-
    ended channels, 4 differential channels, or combinations in between. Each input has a 12-bit resolution and an input bias current of
    ±90 μA.
    '''

    ''' 
    EAnalogIn is a simplified (E is for easy) function that returns a single reading from 1 analog input channel. Execution time is up to
    20 ms.
    '''
    @DictFeat(units='volts', keys=list(range(0,8)))
    def analog_in(self, key):
        return self._internal.eAnalogIn(channel=key)['voltage']

    @DictFeat(units='volts', keys=list(range(0,4)))
    def analog_dif_in(self, key, gain = 1):
        '''
        Differential channels can make use of the low noise precision PGA to provide gains up to 20. In differential mode, the voltage of each AI with respect to ground must be between +20 and -10 volts, but the range of voltage difference between the 2 AI is a function of gain (G) as follows:
        G=1     ±20 volts
        G=2     ±10 volts
        G=4     ±5 volts
        G=5     ±4 volts
        G=8     ±2.5 volts
        G=10    ±2 volts
        G=16    ±1.25 volts
        G=20    ±1 volt
        The reason the range is ±20 volts at G=1 is that, for example, AI0 could be +10 volts and AI1 could be -10 volts giving a difference of +20 volts, or AI0 could be -10 volts and AI1 could be +10 volts giving a difference of -20 volts. The PGA (programmable gain amplifier, available on differential channels only) amplifies the AI voltage before it is digitized by the A/D converter. The high level drivers then divide the reading by the gain and return the actual measured voltage.
        '''
        gain_list = [1,2,4,5,8,10,16,20]
        gain_value = gain
        if gain_value not in gain_list:
            raise InstrumentError('Gain value not permitted, check driver code or Labjack user guide')
        else:
            return self._internal.eAnalogIn(channel = key + 8, gain = gain_value)['voltage']
    
    # ANALOG OUTPUT METHOD
    analog_out = DictFeat(units = 'volts', keys=list(range(0,2)))
    @analog_out.setter                       
    def analog_out(self, key, value):
        '''
        Easy function. This is a simplified version of AOUpdate. Sets the voltage of both analog outputs.
        Execution time for this function is 20 milliseconds or less (typically 16 milliseconds in Windows).
        If either passed voltage is less than zero, the DLL uses the last set voltage. This provides a way to update 1 output without changing the other. 
        '''
        if key == 0:                                                                                                                       
            self._internal.eAnalogOut(analogOut0 = value, analogOut1 = -1)                                                                   
        else:
            if key == 1:
                self._internal.eAnalogOut(analogOut0 = -1, analogOut1 = value)
        return                                                                                                                                                                                      

    # DIGITAL INPUT/OUTPUT METHOD
    @DictFeat(values={True: 1, False: 0}, keys=list(range(0,16)))
    def digital_in_out(self, key):
        '''
        Easy function. This is a simplified version of DigitalIO that reads the state of one digital input. Also configures the requested pin to input and leaves it that way.
        Execution time for this function is 20 milliseconds or less (typically 16 milliseconds in Windows).
        channel – Line to read. 0-3 for IO or 0-15 for D.
        '''
        return self._internal.eDigitalIn(key)['state']  
    
    @digital_in_out.setter
    def digital_in_out(self, key, value):
        '''
        Easy function. This is a simplified version of DigitalIO that sets/clears the state of one digital output. Also configures the requested pin to output and leaves it that way.
        Execution time for this function is 20 milliseconds or less (typically 16 milliseconds in Windows).
        channel – Line to read. 0-3 for IO or 0-15 for D.
        '''
        if key > 3:
            self._internal.eDigitalOut(channel=key, writeD = 1, state = value)
        else:
            self._internal.eDigitalOut(channel=key, writeD = 0, state = value)
