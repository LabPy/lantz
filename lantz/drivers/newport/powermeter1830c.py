# -*- coding: utf-8 -*-
"""
    lantz.drivers.newport.powermeter1830c
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an Optical Power Meter.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
    
    Source: Instruction Manual (Newport)
"""

from pyvisa import constants

from lantz.feat import Feat
from lantz.action import Action
from lantz.messagebased import MessageBasedDriver


class PowerMeter1830c(MessageBasedDriver):
    """ Newport 1830c Power Meter
    """

    DEFAULTS = {'ASRL': {'write_termination': '\n',
                         'read_termination': '\n',
                         'baud_rate': 9600,
                         'bytesize': 8,
                         'parity': constants.Parity.none,
                         'stop_bits': constants.StopBits.one,
                         'encoding': 'ascii',
                         'timeout': 2000
                        }}


    @Feat(values={True: 1, False: 0})
    def attenuator(self):
        """ Attenuator. 
            1: Attenuator present
            0: Attenuator not present
        """
        return int(self.query('A?'))
    
    @attenuator.setter
    def attenuator(self, value):
        self.send('A{}'.format(value))
        
    @Feat(values={True: 1, False: 0})
    def beeper(self):
        """ Checks whether the audio output is on or off.
        """
        return int(self.query('B?'))
    
    @beeper.setter
    def beeper(self,value):
        self.send('B{}'.format(value))
        
    @Feat
    def data(self):
        """ Retrieves the value from the power meter.
        """        
        return float(self.query('D?'))
    
    @Feat(values={True: 1, False: 0})
    def echo(self):
        """ Returns echo mode. Only applied to RS232 communication
        """
        return int(self.query('E?'))
    
    @echo.setter
    def echo(self,value):
        self.send('E{}'.format(value))
        
    @Feat(values={'Slow': 1, 'Medium': 2, 'Fast': 3})
    def filter(self):
        """ How many measurements are averaged for the displayed reading.
            slow: 16 measurements
            medium: 4 measurements
            fast: 1 measurement. 
        """
        return int(self.query('F?'))
    
    @filter.setter
    def filter(self,value):
        self.send('F{}'.format(value))
        
    @Feat(values={True: 1, False: 0})
    def go(self):
        """ Enable or disable the power meter from taking new measurements. 
        """
        return int(self.query('G?'))
    
    @go.setter
    def go(self,value):
        self.send('G{}'.format(value))
        
    @Feat(values={'Off': 0, 'Medium': 1, 'High': 2})
    def keypad(self):
        """ Keypad/Display backlight intensity levels.
        """
        return int(self.query('K?'))
    
    @keypad.setter
    def keypad(self,value):
        self.send('K{}'.format(value))
        
    @Feat(values={True: 1, False: 0})
    def lockout(self):
        """ Enable/Disable the lockout. When the lockout is enabled, any front panel key presses would have no effect on system operation.
        """
        return int(self.query('L?'))
    
    @lockout.setter
    def lockout(self,value):
        self.send('L{}'.format(value))

    @Action()
    def autocalibration(self):
        """ Autocalibration of the power meter. This procedure disconnects the input signal. 
            It should be performed at least 60 minutes after warm-up.
        """
        self.send('O')
    
    @Feat(values=set(range(0,9)))
    def range(self):
        """ Set the signal range for the input signal. 
            0 means auto setting the range. 1 is the lowest signal range and 8 the highest.
        """
        return int(self.query('R?'))
    
    @range.setter
    def range(self,value):
        self.send('R{}'.format(value))
        
    @Action()
    def store_reference(self):
        """ Sets the current input signal power level as the power reference level. 
            Each time the S command is sent, the current input signal becomes the new reference level. 
        """
        self.send('S')
        
    @Feat(values={'Watts': 1, 'dB': 2, 'dBm': 3, 'REL': 4})
    def units(self):
        """ Sets and gets the units of the measurements. 
        """ 
        return int(self.query('U?'))
    
    @units.setter
    def units(self,value):
        self.send('U{}'.format(value))
        
    @Feat(limits=(1,10000,1))
    def wavelength(self):
        """ Sets and gets the wavelength of the input signal.
        """
        return int(self.query('W?'))
    
    @wavelength.setter
    def wavelength(self,value):
        self.send('W{}'.format(int(value)))
    
    @Feat(values={True: 1, False: 0})
    def zero(self):
        """ Turn the zero function on/off. Zero function is used for subtracting any background power levels in future measurements. 
        """
        return int(self.query('Z?'))
    
    @zero.setter
    def zero(self,value):
        self.send('Z{}'.format(value))
        
if __name__ == '__main__':
    import argparse
    import lantz.log
    
    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-p', '--port', type=str, default='1',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)
    
    with PowerMeter1830c.from_serial_port(args.port) as inst:
        
        inst.initialize() # Initialize the communication with the power meter
        
        inst.lockout = True # Blocks the front panel
        inst.keypad = 'Off' # Switches the keypad off
        inst.attenuator = True # The attenuator is on
        inst.wavelength = 633 # Sets the wavelength to 633nm
        inst.units = "Watts" # Sets the units to Watts
        inst.filter = 'Slow' # Averages 16 measurements
        
        if not inst.go:
            inst.go = True # If the instrument is not running, enables it
            
        inst.range = 0 # Auto-sets the range
        
        print('The measured power is {} Watts'.format(inst.data))
