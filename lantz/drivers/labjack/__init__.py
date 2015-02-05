# -*- coding: utf-8 -*-
"""
    lantz.drivers.labjack
    ~~~~~~~~~~~~~~~~~~~~~

    :company: LabJack
    :description: LabJacks are USB/Ethernet based measurement and automation
                  devices which provide analog inputs/outputs, digital inputs/outputs, and more.

    :website: http://www.labjack.com/

    ----

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from .u12 import U12

__all__ = ['U12']

