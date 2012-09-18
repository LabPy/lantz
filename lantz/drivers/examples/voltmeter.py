# -*- coding: utf-8 -*-
"""
    lantz.drivers.examples.voltmeter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the Simple Voltmeter described in the Lantz tutorial.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat, DictFeat, Q_, Action
from lantz.network import TCPDriver
from lantz.errors import InstrumentError

class LantzVoltmeterTCP(TCPDriver):
    """Lantz Signal Generator
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        answer = super().query(command, send_args=send_args, recv_args=recv_args)
        if answer == 'ERROR':
            raise InstrumentError
        return answer

    @Feat()
    def idn(self):
        return self.query('?IDN')

    @DictFeat(units='V', keys=(0, 1))
    def voltage(self, key):
        """Measure the voltage.
        """
        return float(self.query('?MEAS {}'.format(key)))

    @DictFeat(values={0.1: '0', 1: '1', 10: '2', 100: '3', 1000: '4'}, keys=(0, 1))
    def range(self, key):
        return self.query('?RANGE {}'.format(key))

    @range
    def range(self, key, value):
        self.query('!RANGE {} {}'.format(key, value))

    @Action()
    def auto_range(self, key):
        """Autoselect a range.
        """
        self.query('!ARANGE {}'.format(key))

    @Action()
    def calibrate(self):
        """Calibrate.
        """
        self.query('!CAL')

    @Action()
    def self_test(self):
        """Self test
        """
        self.query('!TES')
