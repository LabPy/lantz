# -*- coding: utf-8 -*-
"""
    lantz.drivers.tektronix.afg3021b
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control a signal generator.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat

from lantz.messagebased import MessageBasedDriver



class AFG3021b(MessageBasedDriver):

    MANUFACTURER_ID = '0x0699'
    MODEL_CODE = '0x0346'

    @Feat()
    def idn(self):
        return inst.query('*IDN?')


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)

    with AFG3021b('USB0::0x0699::0x0346::C033250::INSTR') as inst:
        print(inst.idn)

    with AFG3021b.from_hostname('192.168.0.1') as inst:
        print(inst.idn)

    with AFG3021b.from_usbtmc(serial_number='C033250') as inst:
        print(inst.idn)
