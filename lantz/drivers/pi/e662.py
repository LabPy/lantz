# -*- coding: utf-8 -*-
"""
    lantz.driver.pi.e662
    ~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control a Piezo Controller


    Sources::

        - PZ 73E User Manual / E-662 LVPZT Position Servo Controller

    :copyright: © 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat, Action, DictFeat
from lantz.serial import SerialDriver


class E662(SerialDriver):
    """LVPZT Position Servo Controller
    """

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    def __init__(self, port=8, timeout=1, **kwargs):
        super().__init__(port=port, baudrate=9600,
                         bytesize=8, stopbits=1,
                         timeout=timeout, flow=2, **kwargs)

    def _return_handler(self, func_name, ret_value):
        if ret_value < 0:
            raise InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value

    @Feat(values={True: 'REM', False: 'LOC'})
    def remote(self):
        """Computer control mode
        """
        return self.query('SYST:DEV:CONT?')

    def remote(self, value):
        return self.send('SYST:DEV:CONT {}'.format(value))

    @Feat()
    def idn(self):
        """Instrument identification
        """
        return self.query('*IDN?')

    @Feat(units='volt')
    def voltage(self):
        """Piezo voltage
        """
        return float(self.query('VOLT?'))

    @voltage.setter
    def voltage(self, value):
        self.send('VOLT {:f}'.format(value))

    @Feat(units='um')
    def position(self):
        """Piezo voltage
        """
        return float(self.query('POS?'))

    @position.setter
    def position(self, value):
        self.send('POS {:f}'.format(value))

    @Feat()
    def error(self):
        self.query('SYST:ERR?').split(',')

    @Feat(units='volt')
    def min_voltage(self):
        self.query('VOLT:LIM:LOW?')

    def min_voltage(self, value):
        self.send('VOLT:LIM:LOW {:f}'.format(value))

    @Feat(units='volt')
    def max_voltage(self):
        self.query('VOLT:LIM:HIGH?')

    def max_voltage(self, value):
        self.send('VOLT:LIM:HIGH {:f}'.format(value))


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test PI E-662')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)
    with E662(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            from time import sleep
            inst.remote = True
            print(inst.idn())
            inst.voltage = 1
            sleep(1)
            print(inst.voltage)
            inst.position = 30
            sleep(1)
            print(inst.position)
            print(inst.error)

            inst.remote = False

