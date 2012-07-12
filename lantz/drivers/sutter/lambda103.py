# -*- coding: utf-8 -*-
"""
    lantz.drivers.sutter.lambda103
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control a filter wheel.

    Sources::

        - Sutter Instruments manual.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat, DictFeat, Action
from lantz.serial import SerialDriver

def logged(func):
    return func


class Lambda103(SerialDriver):
    """High performance, microprocessor-controlled multi-filter wheel system
    for imaging applications requiring up to 3 filter wheels.
    """

    RECV_TERMINATION = ''
    SEND_TERMINATION = ''

    def __init__(self, port=11, baudrate=9600, timeout=1, *args, **kwargs):
        super().__init__(port, baudrate, timeout, *args, **kwargs)

        self.speed = 1

    @Feat(None, values={True: chr(170), False: chr(172)})
    def open_A(self, value):
        """Open shutter A.
        """
        self.send(value)

    @logged
    def flush(self):
        """Flush.
        """
        self.serial.flushInput()
        self.serial.flushOutput()
        self.serial.flush()

    # TODO: WTF 2 values for the same wheel
    @DictFeat(None, keys={'A': 0, 'B': 1})
    def position(self, key, value):
        """Set filter wheel position and speed.

                w = 0 -> Filter wheels A and C
                w = 1 -> Fliter wheel B
        """
        command = chr( key * 128 + self.speed * 14 + value)
        self.send(command)

    @Action()
    def motorsON(self):
        """Power on all motors."""
        self.send(chr(206))
        return "Motors ON"
    
    @Action()
    def status(self):
        return "Status {}".format(self.query(chr(204)))

    @Feat(None, values={True: chr(238), False: chr(239)})
    def remote(self, value):
        """Set Local-Mode."""
        self.send(value)

    @Action()
    def reset(self):
        """Reset the controller."""
        self.send(chr(251))


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test PI E-662')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)
    with Lambda103(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            from time import sleep
            inst.remote = True

            inst.open_A = True
            sleep(5)
            inst.open_A = False

            sleep(1)
            for i in range(9):
                fw.position['A']= i
                sleep(1)

            sleep(1)
            inst.remote = False

            fw.open_A = False

