# -*- coding: utf-8 -*-
"""
    lantz
    ~~~~~

    An automation and instrumentation toolkit with a clean, well-designed and
    consistent interface.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import pkg_resources

__version__ = pkg_resources.get_distribution('lantz').version

from pint import UnitRegistry
Q_ = UnitRegistry().Quantity

from .log import LOGGER
from .driver import Driver, Feat, DictFeat, Action, initialize_many, finalize_many

__all__ = ['Driver', 'Action', 'Feat', 'DictFeat', 'Q_']


def run_pyroma(data):
    import sys
    from zest.releaser.utils import ask
    if not ask("Run pyroma on the package before uploading?"):
        return
    try:
        from pyroma import run
        result = run(data['tagdir'])
        if result != 10:
            if not ask("Continue?"):
                sys.exit(1)
    except ImportError:
        if not ask("pyroma not available. Continue?"):
            sys.exit(1)
