# -*- coding: utf-8 -*-
"""
    lantz.simulators
    ~~~~~~~~~~~~~~~~

    Instrument simulators for testing.

    :copyright: 2015 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

#: Dict connecting simulator name with main callable.
SIMULATORS = {}

from . import fungen, experiment, voltmeter


def main(args=None):
    """Run simulators.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Run Lantz simulators.')
    parser.add_argument('simulator', choices=list(SIMULATORS.keys()))
    args, pending = parser.parse_known_args(args)
    print('Dispatching ' + args.simulator)
    SIMULATORS[args.simulator](pending)
