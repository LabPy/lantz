# -*- coding: utf-8 -*-
"""
    scanfrequency
    ~~~~~~~~~~~~~

    This example shows how to program a CLI using a lantz drivers, but
    without the backend-frontend classes that simplifies app development.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time


def scan_frequency(inst, start, stop, step, wait):
    """Scan frequency in an instrument.

    :param start: Start frequency.
    :type start: Quantity
    :param stop: Stop frequency.
    :type stop: Quantity
    :param step: Step frequency.
    :type step: Quantity
    :param wait: Waiting time.
    :type wait: Quantity

    """
    in_secs = wait.to('seconds').magnitude
    current = start
    while current < stop:
        inst.frequency = current
        time.sleep(in_secs)
        current += step


if __name__ == '__main__':
    import argparse

    from lantz import Q_

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    parser = argparse.ArgumentParser()

    parser.add_argument('start', type=float,
                        help='Start frequency [Hz]')
    parser.add_argument('stop', type=float,
                        help='Stop frequency [Hz]')
    parser.add_argument('step', type=float,
                        help='Step frequency [Hz]')
    parser.add_argument('wait', type=float,
                        help='Waiting time at each step [s]')

    args = parser.parse_args()

    Hz = Q_(1, 'Hz')
    sec = Q_(1, 'sec')

    def print_change(new, old):
        print('Changed from {} to {}'.format(old, new))

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        print(inst.idn)

        inst.frequency_changed.connect(print_change)

        scan_frequency(inst, args.start * Hz, args.stop * Hz,
                       args.step * Hz, args.wait * sec)
