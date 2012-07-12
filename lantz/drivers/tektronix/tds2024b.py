# -*- coding: utf-8 -*-
"""
    lantz.drivers.tektronix.tds2024b
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an oscilloscope.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from numpy import array, arange

from lantz.feat import Feat
from lantz.action import Action
from lantz.visa import VisaDriver

class TDS2024(VisaDriver):
    """Tektronix TDS2024 200 MHz 4 Channel Digital Real-Time Oscilloscope
    """

    def __init__(self, port):
        super().__init__(port)
        timeout=10

    @Action()
    def autoconf(self):
        """Autoconfig oscilloscope.
        """
        self.send(':AUTOS EXEC')

    def initialize(self):
        """initiate.
        """
        self.send(':ACQ:STATE ON')
        return "Init"

    @Feat()
    def idn(self):
        """IDN.
        """
        return self.query('ID?')

    @Feat()
    def trigger(self):
        """Trigger state.
        """
        return self.query(':TRIG:STATE?')

    @trigger.setter
    def trigger(self, mode):
        """Set trigger state.
        """
        self.query('TRIG:MAIN:MODE {}'.format(mode))

    @Action()
    def triggerlevel(self):
        """Set trigger level to 50% of the minimum adn maximum
        values of the signal.
        """
        self.send('TRIG:MAIn SATLevel')

    @Action()
    def forcetrigger(self):
        """Force trigger event.
        """
        self.send('TRIG FORCe')

    @Action()
    def datasource(self, chn):
        """Selects channel.
        """
        self.send(':DATA:SOURCE CH{}'.format(chn))

    @Action()
    def acqparams(self):
        """ X/Y Increment Origin and Offset.
        """
        commands = 'XZE?;XIN?;YZE?;YMU?;YOFF?'
        #params = self.query(":WFMPRE:XZE?;XIN?;YZE?;YMU?;YOFF?;")
        params = self.query(':WFMPRE:{}'.format(commands))
        params = {k: float(v) for k, v in zip(commands.split(';'), commands.split(';'))}
        return params

    @Action()
    def dataencoding(self):
        """Set data encoding.
        """
        self.send(':DAT:ENC RPB;WID 2;')
        return "Set data encoding"

    @Action()
    def curv(self):
        """Get data.

            Returns:
            xdata, data as list
        """
        self.dataencoding()
        self.send('CURV?')
        answer = self.recv()
        numdigs = int(answer[1])
        bytecount = int(answer[2:2+numdigs])
        data = answer[2+numdigs:]
        length = bytecount / 2
        data = struct.unpack("{}H".format(length), data[0:2*length])
        params = self.acqparams()
        data = array(list(map(float, data)))
        yoff = params['YOFF?']
        ymu = params['YMU?']
        yze = params['YZE?']
        xin = params['XIN?']
        xze = params['XZE?']
        ydata = ( data - yoff) * ymu + yze
        xdata = arange(len(data)) * xin + xze
        return list(xdata), list(data)

    def _measure(self, type, source):
        self.send('MEASUrement:IMMed:TYPe {}'.format(type))
        self.send('MEASUrement:IMMed:SOUrce1 CH{}'.format(source))
        self.send('MEASUrement:IMMed:VALue?')
        return self.recv()

    @Action()
    def measure_frequency(self, channel):
        """Get immediate measurement result.
        """
        return self._measure('FREQuency', channel)

    @Action()
    def measure_min(self, channel):
        """Get immediate measurement result.
        """
        return self._measure('MINImum', channel)

    @Action()
    def measure_max(self, chn):
        """Get immediate measurement result.
        """
        return self._measure('MAXImum', channel)

    @Action()
    def measure_mean(self, chn):
        """Get immediate measurement result.
        """
        return self._measure('MEAN', channel)


if __name__ == '__main__':
    import argparse
    import csv

    parser = argparse.ArgumentParser(description='Measure using TDS2024 and dump to screen')
    parser.add_argument('-p', '--port', default='USB0::0x0699::0x036A::C048617',
                        help='USB port')
    parser.add_argument('-v', '--view', action='store_true', default=False,
                        help='View ')
    parser.add_argument('Channels', metavar='channels', type=int, nargs='*',
                        help='Channels to use')
    parser.add_argument('--output', type=argparse.FileType('wb', 0), default='-')

    args = parser.parse_args()

    osc = TDS2024(args.port)
    osc.initialize()
    print(osc.idn)
    print(osc.trigger)
    osc.forcetrigger()
    osc.triggerlevel()
    osc.trigger = "AUTO"
    print(osc.trigger)
    #osc.autoconf()
    params = osc.acqparams()

    if args.view:
        import matplotlib.pyplot as plt
        import numpy as np

    with args.output as fp:
        writer = csv.writer(fp)
        writer.write_row(('Channel', 'Freq', 'Max', 'Min', 'Mean'))
        for channel in args.channels or range(1, 4):
            osc.datasource(channel)
            writer.write_row(([osc.measure_frequency(channel),
                               osc.measure_max(channel),
                               osc.measure_min(channel),
                               osc.measure_mean(channel)]))

            if args.view:
                x, y = osc.curv()
                x = np.array(x)
                x = x - x.min()
                y = np.array(y)
                plt.plot(x, y)

    if args.view:
        plt.show()
