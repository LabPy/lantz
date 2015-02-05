# -*- coding: utf-8 -*-
"""
    lantz
    ~~~~~

    An automation and instrumentation toolkit with a clean, well-designed and
    consistent interface.

    :copyright: 2015 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import pkg_resources

try:
    __version__ = pkg_resources.get_distribution('lantz').version
except:
    __version__ = "unknown"

from pint import UnitRegistry
ureg = UnitRegistry()
Q_ = ureg.Quantity

from .log import LOGGER
from .driver import Driver, Feat, DictFeat, Action, initialize_many, finalize_many

__all__ = ['Driver', 'Action', 'Feat', 'DictFeat', 'Q_']


def _run_pyroma(data):   # pragma: no cover
    """Run pyroma (used to perform checks before releasing a new version).
    """
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


def test():
    """Run all tests.

    :return: a :class:`unittest.TestResult` object
    """
    from .testsuite import run
    return run()
