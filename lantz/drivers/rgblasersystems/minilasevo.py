# -*- coding: utf-8 -*-
"""
    lantz.drivers.rgblasersystems.minilasevo
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Action, Feat, DictFeat
from lantz.serial import SerialDriver
from lantz.errors import InstrumentError

class MiniLasEvo(SerialDriver):
    """Driver for any RGB Lasersystems MiniLas Evo laser.
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\r\n'
    SEND_TERMINATION = '\r\n'

    BAUDRATE = 57600
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False


    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Send query to the laser and return the answer, after handling
        possible errors.

        :param command: command to be sent to the instrument
        :type command: string

        :param send_args: (termination, encoding) to override class defaults
        :param recv_args: (termination, encoding) to override class defaults
        """
        ans = super().query(command, send_args=send_args, recv_args=recv_args)
        # TODO: Echo handling
        code = ans[0]
        if code !=0:
            if code == '1':
                raise InstrumentError('Command invalid')
            elif code == '2':
                raise InstrumentError('Wrong number of parameters')
            elif code == '3':
                raise InstrumentError('Parameter value is out of range')
            elif code == '4':
                raise InstrumentError('Unlocking code is wrong')
            elif code == '5':
                raise InstrumentError('Device is locked for this command')
            elif code == '6':
                raise InstrumentError('This function is not supported')
            elif code == '7':
                raise InstrumentError('Timeout while reading command (60 s)')
            elif code == '8':
                raise InstrumentError('This value is currently not available')

        ans = ans[2:]
        # TODO: Code reporting?
        return ans

    @Feat(read_once=True)
    def idn(self):
        """Identification of the device
        """
        manufacturer = self.query('DM?')
        device = self.query('DT?')
        serial = self.query('DS?')
        ans = manufacturer + ', ' + device + ', serial number ' + serial
        return ans

    @Feat()
    def status(self):
        """Current device status
        """
        ans = self.query('S?')
        if ans == '0x10':
            ans = 'Temperature of laser head is ok'
        elif ans == '0x01':
            ans = 'Laser system is active, radiation can be emitted'
        elif ans == '0x02':
            ans = '(reserved)'
        elif ans == '0x04':
            ans = 'The interlock is open'
        elif ans == '0x08':
            ans = self.query('E?')
            if ans == '0x01':
                ans = 'Temperature of laser head is too high'
            elif ans == '0x02':
                ans = 'Temperature of laser head is too low'
            elif ans == '0x04':
                ans = 'Temperature-sensor connection is broken'
            elif ans == '0x08':
                ans = 'Temperature sensor cable is shortened'
            elif ans == '0x40':
                ans = 'Current for laser head is too high'
            elif ans == '0x80':
                ans = 'Internal error (laser system cannot be activated)'
        return ans

    @Feat()
    def operating_hours(self):
        """Total operating hours [hhhh:mm]
        """
        return self.query('R?')

    @Feat()
    def software_version(self):
        """Software version
        """
        return self.query('DO?')

    @Feat(read_once=True)
    def emission_wavelenght(self):
        """Emission wavelenght in nm
        """
        return self.query('DW?')

    @Feat()
    def available_features(self):
        """Available features (reserved for future use)
        """
        return self.query('DF?')

    @Feat()
    def control_mode(self):
        """Active current (power) control
        """
        ans = self.query('DC?')
        if ans == 'ACC':
            ans = 'Active current control'
        else:
            ans = 'Active power control'
        return ans

    # TEMPERATURE
    
    @Feat()
    def temperature(self):
        """Current temperature in ºC
        """
        return self.query('T?')

    @Feat(read_once=True)
    def temperature_min(self):
        """Lowest operating temperature in ºC
        """
        return self.query('LTN?')

    @Feat(read_once=True)
    def temperature_max(self):
        """Highest operating temperature in ºC
        """
        return self.query('LTP?')

    # ENABLED REQUEST
    
    @Feat(values={True: '1', False: '0'})
    def enabled(self):
        """Method for turning on the laser
        """
        return self.query('O?')

    @enabled.setter
    def enabled(self, value):
        self.query('O=' + value)

    # LASER POWER
    
    def initialize(self):
        super().initialize()
        self.feats.power.limits = (0, self.maximum_power.magnitude)

    @Feat(units='mW')
    def maximum_power(self):
        """Gets the maximum emission power of the laser
        """
        return float(self.query('LP?'))

    @Feat(units='mW')
    def power(self):
        """Gets and sets the emission power
        """
        return float(self.query('P?'))

    @power.setter
    def power(self, value):
        self.query('P={:.1f}'.format(value))

if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_screen(lantz.log.DEBUG)
    with MiniLasEvo(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
            """inst.power = 0
            inst.temperature
            print(inst.power)
            inst.power = 0
            print(inst.idn)
            """




