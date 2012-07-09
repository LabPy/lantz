# -*- coding: utf-8 -*-
"""
    lantz.drivers.mcc
    ~~~~~~~~~~~~~~~~~

    :company: Measurement Computing Corporation.
    :description: PC-based data acquisition hardware and software.
    :website: http://www.mccdaq.com/

    ---

    :copyright: © 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from .usb3103 import Usb3103

__all__ = ['Usb3103', ]
