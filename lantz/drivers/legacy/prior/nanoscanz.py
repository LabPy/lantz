# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.prior.nanoscanz
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Action, Feat
from lantz.drivers.legacy.serial import SerialDriver
from lantz.errors import InstrumentError

class NanoScanZ(SerialDriver):
    """Driver for the NanoScanZ Nano Focusing Piezo Stage from Prior.
    """

    ENCODING = 'ascii'
    
    RECV_TERMINATION = '\r'
    SEND_TERMINATION = '\r'
    
    BAUDRATE = 9600
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    
    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Send query to the stage and return the answer, after handling
        possible errors.

        :param command: command to be sent to the instrument
        :type command: string

        :param send_args: (termination, encoding) to override class defaults
        :param recv_args: (termination, encoding) to override class defaults
        """
        ans = super().query(command, send_args=send_args, recv_args=recv_args)
        if ans[0] == 'E':
            code = ans[2]
            if code == '8':
                raise InstrumentError('Value out of range')
            elif code == '4':
                raise InstrumentError('Command parse error, ie wrong number  of parameters')
            elif code == '5':
                raise InstrumentError('Unknown command')
            elif code == '2':
                raise InstrumentError('Invalid checksum')

        return ans
    
    @Feat(values={9600,19200,38400})
    def baudrate(self):
        """Reports and sets the baud rate.
        NOTE: DO NOT change the baud rate of the Piezo controller when daisy chained to ProScan.
        """
        return self.query('BAUD')

    @baudrate.setter
    def baudrate(self, value):
        self.query('BAUD {}'.format(value))


    @Feat(values={True: '4', False: '00000'})
    def moving(self):
        """Returns the movement status, 0 stationary, 4 moving
        """
        return self.query('$')
    
    @Feat(read_once=True)
    def idn(self):
        """Identification of the device
        """
        return self.query('DATE') +' '+ self.query('SERIAL')
    
    @Feat(units = 'micrometer')
    def position(self):
        """Gets and sets current position.
        If the value is set to z = 0, the display changes to REL 0 (relative display mode). To return to ABS mode use inst.move_absolute(0) and then inst.position = 0. Thus, the stage will return to 0 micrometers and the display screen will switch to ABS mode.
        """
        return self.query('PZ')

    @position.setter
    def position(self, value):
        self.query('PZ {}'.format(value))
    
    @Action()
    def zero_position(self):
        """Move to zero including any position redefinitions done by the position Feat
        """
        self.query('M')
    
    
    @Action(units = 'micrometer', limits=(100,))
    def move_absolute(self, value):
        """Move to absolute position n, range (0,100).
        This is a "real" absolute position and is independent of any relative offset added by the position Feat.
        """
        self.query('V {}'.format())
    
    
    @Action()
    def move_relative(self, value):
        """ 
        Move the stage position relative to the current position by an amount determined by 'value'.
        If value is given in micrometer, thats the amount the stage is going to move, in microns.
        If value is given in steps, the stage will move a distance  value.magnitude * step. The step is defined by the step Feat
        """
        """
    try:
            u = value.units
            if value.magnitude > 0:
                self.query('U {}'.format(value.magnitude))
            if value.magnitude < 0:
                self.query('D {}'.format(-value.magnitude))
        except:
            if isinstance(value, int):
                if value > 0:
                    for x in range(0,value):
                        self.query('U')
                elif value < 0:
                    for x in range(0,value):
                        self.query('D')
            else:
                raise ValueError('Specify the translation distance in micrometer unit')               
        """
        try:
            if value.units == 'micrometer':
                if value.magnitude > 0:
                    self.query('U {}'.format(value.magnitude))
                elif value.magnitude < 0:
                    self.query('D {}'.format(-value.magnitude))
            elif value.units == 'steps':
                if value.magnitude > 0:
                    for x in range(0,value.magnitude):
                        self.query('U')
                elif value.magnitude < 0:
                    for x in range(0,-value.magnitude):
                        self.query('D')
        except:
            raise ValueError('Specify the translation distance in micrometers or steps') 
    

    @Feat(units='micrometer')
    def step(self):
        """Report and set the default step size, in microns
        """
        return self.query('C')

    @step.setter
    def step (self, value):
        self.query('C {}'.format(value))
    
    
    
    @Feat(read_once=True)
    def software_version(self):
        """Software version
        """  
        return self.query('VER')

class NanoScanZ_chained(NanoScanZ):
    """This is needed when the NanoScanZ controller is connected to a ProScanII controller through its RS-232-2 input
    """
    def write(self, command, termination=None, encoding=None):
        super().write('<' + command, termination=termination, encoding=encoding)

    def read(self, termination=None, encoding=None, recv_chunk=None):
        return super().read(termination=termination, encoding=encoding)[1:]


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Prior NanoScanZ')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_screen(lantz.log.DEBUG)
    with NanoScanZ(args.port) as inst:
        if args.interactive:
            from lantz.ui.app import start_test_app
            start_test_app(inst)
        else:
            from lantz import Q_
            # Add your test code here
            print('Non interactive mode')
            
            um = Q_(1, 'micrometer')
            
            print(inst.idn)
            print(inst.moving)
            print(inst.position)
            print(inst.step)
            inst.step = 1 * um
            print(inst.step)
