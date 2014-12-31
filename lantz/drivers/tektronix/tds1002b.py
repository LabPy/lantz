# -*- coding: utf-8 -*-
"""
    lantz.drivers.tektronix.tds1012
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an oscilloscope.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat
from lantz.messagebased import MessageBasedDriver


class TDS1002b(MessageBasedDriver):

    @classmethod
    def usb_from_serial(cls, serial_number):
        # find resource and get resource name

        #super().__init__(1689, 867, serial_number, **kwargs)

        return cls(resource_name='bla')

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')
