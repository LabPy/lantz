# -*- coding: utf-8 -*-
"""
    lantz.simulators
    ~~~~~~~~~~~~~~~~

    Instrument simulators for testing.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

#: Dict connecting simulator name with main callable.
SIMULATORS = {}

from . import fungen, experiment, voltmeter
