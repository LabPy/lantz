# -*- coding: utf-8 -*-
"""
    lantz.drivers.aa.aotf
    ~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers for an AOTF Controller


    Implementation Notes
    --------------------

    There are currently two (disconnected) ways of setting the power for each
    line: powerdb and power.

    Sources::

        - MDSnC Manual

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

#TODO: Implement calibrated power.

from lantz import Feat, DictFeat
from lantz.serial import SerialDriver

class MDSnC(SerialDriver):
    """MDSnC synthesizer for AOTF.nC
    """

    CHANNELS = list(range(8))

    @Feat(None, values={True: 1, False: 0})
    def main_enabled(self, value):
        """Enable the
        """
        self.send("I{}".format(value))

    @DictFeat(None, keys=CHANNELS)
    def enabled(self, channel, value):
        """Enable single channels.
        """
        self.send("L{}O{}".format(channel, value))

    @DictFeat(None, keys=CHANNELS)
    def frequency(self, channel, value):
        """RF frequency for a given channel.
        """
        self.send("L{}F{}".format(channel, value))

    @DictFeat(None, keys=CHANNELS)
    def powerdb(self, channel, value):
        """Power for a given channel (in db).
        """
        self.send("L{}D{}".format(channel, value))

    @DictFeat(None, keys=CHANNELS, limits=(0, 1023, 1))
    def power(self, channel, value):
        """Power for a given channel (in digital units).
        """
        self.send("L{}P{:04d}".format(channel, value))


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
    with MDSnC(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            from time import sleep
            print("init")
            freq = 130
            inst.power(4,10)
            sleep(0.2)
            inst.enabled(4,1)
            sleep(1.2)
            inst.enabled(4,0)
            sleep(1.2)
            inst.enabled(4,1)


