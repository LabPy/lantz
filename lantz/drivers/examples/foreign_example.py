# -*- coding: utf-8 -*-
"""
    lantz.driver.example.foreign
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Foreign library example.

    :copyright: © 2011 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import ctypes as ct

from lantz import Feat, Action, DictFeat
from lantz.foreign import LibraryDriver
from lantz.errors import InstrumentError

class ForeignExample(LibraryDriver):

    LIBRARY_NAME = 'mylibrary.dll'

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    @Feat(units='V', range=(10,))
    def amplitude(self):
        """Amplitude.
        """
        return float(self.query('?AMP'))

    @amplitude.setter
    def amplitude(self, value):
        self.query('!AMP {:.1f}'.format(value))

    @DictFeat(map={True: '1', False: '0'}, valid_keys=list(range(1,9)))
    def dout(self, key):
        """Digital output state.
        """
        return self.query('?DOU {}'.format(key))

    @dout.setter
    def dout(self, key, value):
        self.query('!DOU {} {}'.format(key, value))

    @Action()
    def do_something(self):
        """Help for do_something
        """
        return self.lib.something()



if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)
    with ForeignExample() as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_form
            start_form(inst)
        else:
            # Add your test code here
            print('Non interactive mode')

