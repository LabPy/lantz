# -*- coding: utf-8 -*-
"""
    lantz
    ~~~~~

    An automation and instrumentation toolkit with a clean, well-designed and
    consistent interface.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

__version__ = '0.1'

from pint import UnitRegistry
Q_ = UnitRegistry().Quantity

from .log import LOGGER
from .driver import Driver, Feat, DictFeat, Action



__all__ = ['Driver', 'Action', 'Feat', 'DictFeat', 'Q_']
