# -*- coding: utf-8 -*-
"""
    lantz
    ~~~~~

    An automation and instrumentation toolkit with a clean, well-designed and
    consistent interface.

    :copyright: (c) 2011 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

__version__ = 'pre'

from .pint import UnitRegistry
Q_ = UnitRegistry().Quantity

from .driver import Driver, Feat, DictFeat, Action



__all__ = ['Driver', 'Action', 'Feat', 'DictFeat', 'Q_']
