# -*- coding: utf-8 -*-
"""
    lantz
    ~~~~~

    An automation and instrumentation toolkit with a clean, well-designed and
    consistent interface.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import os
import subprocess
import pkg_resources

__version__ = "unknown"
try:  # try to grab the commit version of our package
    __version__ = (subprocess.check_output(["git", "describe"],
                                           stderr=subprocess.STDOUT,
                                           cwd=os.path.dirname(os.path.abspath(__file__)))).strip()
except:  # on any error just try to grab the version that is installed on the system
    try:
        __version__ = pkg_resources.get_distribution('lantz').version
    except:
        pass  # we seem to have a local copy without any repository control or installed without setuptools
              # so the reported version will be __unknown__

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
