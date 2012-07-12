#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    lantz-scan
    ~~~~~~~~~~

    Serial port scanner.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import serial

def scan(ports=None, verbose=False):
    """Scan for available ports.

    :param ports: an iterable of device names or port number numbers.
                  if None, ports 0 to 9 is given.
    :param verbose: print status.
    :return: return a list of tuples (identification, name)
    """

    if not ports:
        ports = range(10)

    if verbose:
        _print = print
    else:
        def _print(*args, **kwargs):
            pass

    for port in ports:
        try:
            _print('Trying {} ... '.format(port), end='')
            s = serial.Serial(port)
            yield port, s.portstr
            s.close()
            _print('success (port string: {}'.format(s.portstr))
        except serial.SerialException:
            _print('failed!')
            pass

if __name__=='__main__':
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Tries to open serial ports and print the valid ones.')
    parser.add_argument('ports', metavar='ports', type=str, nargs='*', default=None,
                        help='Ports to open. Ranges (e.g. 0-3, meaning 0, 1, 2, 3 are also possible.')
    args = parser.parse_args()

    if args.ports:
        try:
            ports = set()
            for port in args.ports:
                if '-' in port:
                    fr, to = port.split('-')
                    ports.update(range(int(fr), int(to)+1))
                else:
                    try:
                        ports.add(int(port))
                    except ValueError:
                        ports.add(port)
        except Exception as e:
            print('Could no parse input {}: {}'.format(port, e))
            sys.exit(1)
    else:
        ports = list(range(0, 10))

    print("Testing ports ...")

    number = len(tuple(scan(ports, verbose=True)))

    print('{} ports found'.format(number + 1))
