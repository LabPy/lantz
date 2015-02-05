# -*- coding: utf-8 -*-
"""
    lantz.drivers.rigol
    ~~~~~~~~~~~~~~~~~~~

    :company: Rigol.
    :description: Acquisition devices
    :website: http://www.rigolna.com/

    ----

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from .ds1052e import DS1052e

__all__ = ['DS1052e']
