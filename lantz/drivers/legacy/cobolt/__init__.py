# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.cobolt
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :company: Cobolt.
    :description: DPSS lasers, diode laser modules, fiber pigtailed lasers.
    :website: http://www.cobolt.se/

    ----

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from .cobolt0601 import Cobolt0601

__all__ = ['Cobolt0601']
