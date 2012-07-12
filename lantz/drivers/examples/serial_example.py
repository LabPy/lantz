# -*- coding: utf-8 -*-
"""
    lantz.drivers.example.serial_template
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Serial example.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Action, Feat, DictFeat
from lantz.serial import SerialDriver

class SerialTemplate(SerialDriver):
    """Template for drivers connecting via serial port.
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    @Feat()
    def a_read_only_property(self):
        """Help for a a_read_only_property
        """
        return self.query('*IDN?')

    @Feat(units='V', limits=(10,))
    def a_read_write_property(self):
        """Help for a_read_write_property
        """
        return float(self.query('?AMP'))

    @a_read_write_property.setter
    def amplitude(self, value):
        self.query('!AMP {:.1f}'.format(value))

    @DictFeat(values={True: '1', False: '0'}, keys=list(range(1,9)))
    def a_read_write_dictionary_property(self, key):
        """Help for a_read_write_dictionary_property
        """
        return self.query('?DOU {}'.format(key))

    @a_read_write_dictionary_property.setter
    def a_read_write_dictionary_property(self, key, value):
        self.query('!DOU {} {}'.format(key, value))

    @Action()
    def do_something(self):
        """Help for do_something
        """
        return


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
    with SerialTemplate(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')


