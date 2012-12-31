# -*- coding: utf-8 -*-
"""
    lantz.drivers.examples.fungen
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the Signal Generator described in the Lantz tutorial.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat, DictFeat, Q_, Action
from lantz.serial import SerialDriver
from lantz.network import TCPDriver
from lantz.errors import InstrumentError
from lantz.visa import SerialVisaDriver


class LantzSignalGenerator(object):
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

    @Feat(read_once=True)
    def idn(self):
        return self.query('?IDN')

    @Feat(units='V', limits=(10,))
    def amplitude(self):
        """Amplitude.
        """
        return float(self.query('?AMP'))

    @amplitude.setter
    def amplitude(self, value):
        self.query('!AMP {:.1f}'.format(value))

    @Feat(units='V', limits=(-5, 5, .01))
    def offset(self):
        """Offset.
        """
        return float(self.query('?OFF'))

    @offset.setter
    def offset(self, value):
        self.query('!OFF {:.1f}'.format(value))

    @Feat(units='Hz', limits=(1, 1e+5))
    def frequency(self):
        """Frequency.
        """
        return float(self.query('?FRE'))

    @frequency.setter
    def frequency(self, value):
        self.query('!FRE {:.2f}'.format(value))

    @Feat(values={True: 1, False: 0})
    def output_enabled(self):
        """Analog output enabled.
        """
        return int(self.query('?OUT'))

    @output_enabled.setter
    def output_enabled(self, value):
        self.query('!OUT {}'.format(value))

    @Feat(values={'sine': '0', 'square': '1', 'triangular': '2', 'ramp': '3'})
    def waveform(self):
        return self.query('?WVF')

    @waveform
    def waveform(self, value):
        self.query('!WVF {}'.format(value))

    @DictFeat(values={True: '1', False: '0'}, keys=list(range(1,9)))
    def dout(self, key):
        """Digital output state.
        """
        return self.query('?DOU {}'.format(key))

    @dout.setter
    def dout(self, key, value):
        self.query('!DOU {} {}'.format(key, value))

    @DictFeat(values={True: '1', False: '0'}, keys=list(range(1,9)))
    def din(self, key):
        """Digital input state.
        """
        return self.query('?DIN {}'.format(key))

    @Action()
    def calibrate(self):
        """Calibrate.
        """
        self.query('!CAL')

    @Action()
    def self_test(self, level=1, repetitions=3):
        """Reset to .
        """
        self.query('!TES {} {}'.format(level, repetitions))


class LantzSignalGeneratorTCP(LantzSignalGenerator, TCPDriver):
    pass


class LantzSignalGeneratorSerial(LantzSignalGenerator, SerialDriver):
    pass


class LantzSignalGeneratorSerialVisa(LantzSignalGenerator, SerialVisaDriver):
    pass


