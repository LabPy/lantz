# -*- coding: utf-8 -*-
"""
    lantz.simulators.fungen
    ~~~~~~~~~~~~~~~~~~~~~~~

    A simulated function generator.
    See specification in the Lantz documentation.

    :copyright: 2015 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import time
import logging
import math

from . import SIMULATORS

from .instrument import SimError, InstrumentHandler, main_tcp, main_serial, main_generic

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S')


class SimFunctionGenerator(InstrumentHandler):

    def __init__(self):
        super().__init__()
        self._amp = 0.0
        self.fre = 1000.0
        self.off = 0.0
        self._wvf = 0
        self.out = 0
        self.dou = {ch:0 for ch in range(1, 9)}
        self.din = {ch:0 for ch in range(1, 9)}

        self.din_key_convert = int
        self.dou_key_convert = int
        self.start_time = time.time()  #This is for the 'experiment' example

    @property
    def idn(self):
        return 'FunctionGenerator Serial #12345'

    @property
    def wvf(self):
        return self._wvf

    @wvf.setter
    def wvf(self, value):
        if value < 0 or value > 3:
            raise SimError
        self._wvf = value

    @property
    def amp(self):
        return self._amp

    @amp.setter
    def amp(self, value):
        if value > 10 or value < 0:
            raise SimError
        self._amp = value

    def cal(self):
        logging.info('Calibrating ...')
        time.sleep(.1)

    def tes(self, level, repetitions):
        level = int(level)
        repetitions = int(repetitions)
        for rep in range(repetitions):
            logging.info('Testing level %s. (%s/%s)', level, rep + 1, repetitions)

    def generator_output(self):
        """This function generates the output, used in the 'experiment' example
        """
        if self.out == 1:
            dt = time.time() - self.start_time
            value = self._amp * math.sin(2 * math.pi * self.fre * dt) + self.off
        else:
            value = 0
        return value


def main(args=None):

    return main_generic(args, SimFunctionGenerator)


SIMULATORS['fungen'] = main

if __name__ == "__main__":
    main()
