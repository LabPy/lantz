# -*- coding: utf-8 -*-
"""
    lantz.drivers.tektronix.tds1012
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an oscilloscope.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat
from lantz.messagebased import MessageBasedDriver


class TDS1002b(MessageBasedDriver):

    MANUFACTURER_ID = '0x699'
    MODEL_CODE = '0x363'

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')
