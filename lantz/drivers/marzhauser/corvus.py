# -*- coding: utf-8 -*-
"""
    lantz.drivers.marzhauser
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :company: Märzhäuser Wetzlar GmbH.
    :description: Manufacturer of microscope stages.
    :website: http://www.marzhauser.com/

    ---

    :copyright: © 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


from lantz import Feat, DictFeat, Action
from lantz.serial import SerialDriver


class Corvus(SerialDriver):

    # host mode
    WRITE_TERMINATION = ' '
    READ_TERMINATION = '\r\n'

    @Feat(None, values={True: 0, False: 1}) #TODO: Check
    def remote(self, value):
        self.query('{0:d} mode'.format(value))

    @Feat(values={1, 2, })
    def dimensions(self):
        """Number of dimensions used.
        """
        return int(self.query('getdim'))
    
    @dimensions.setter
    def dimensions(self, value):
        return self.query('{0:d} setdim'.format(value))

    @DictFeat(keys=limits(4),
              values={'microstep':1, 'um': 2, 'mm': 3, 'cm': 3, 'm': 5, 'inch': 6,  'mil': 7})
    def units(self, axis):
        """Input and output units for each axis
        """
        return self.query('{0:d} getunit'.format(axos))

    @units.setter
    def units(self, axis, unit):
        return self.query('{0:d} {1:d} setunit'.format(axis, value))


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
    with CorvusSerial(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            #todo
            pass
