# -*- coding: utf-8 -*-
"""
    lantz.ui
    ~~~~~~~~

    Implements UI functionality for lantz using Qt.

    You can choose which python bindings to use by setting the
    environmental variable QTBINDINGS to PySide or PyQt4.
    If unset, PyQt4 is tried first, then PySide.

    :copyright: (c) 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os
import imp
import sys


class QtImporter(object):

    def __init__(self, qtbindings):
        if qtbindings not in ('PyQt4', 'PySide'):
            raise ValueError('Unknown Qt Bindings: {}'.format(package))

        self.qtbindings = qtbindings

    def find_module(self, fullname, path=None):
        if fullname.startswith('Qt') and path is None:
            fullname = self.qtbindings + fullname[2:]
            self.mod_data = imp.find_module(fullname)
            return self
        return None

    def load_module(self, fullname):
        return imp.load_module(fullname, *self.mod_data)


qtbindings = os.environ.get('QTBINDINGS', None)

if not qtbindings:
    try:
        import PyQt4
        del PyQt4
        qtbindings = 'PyQt4'
    except ImportError:
        try:
            import PySide
            del PySide
            qtbindings = 'PySide'
        except ImportError:
            raise ImportError('lantz.ui requires PyQt4 or PySide')

_hook = QtImporter(qtbindings)

def register_hook():
    enable = sys.version_info[0] >= 3
    if enable and _hook not in sys.meta_path:
        sys.meta_path.append(_hook)

def unregister_hook():
    if _hook in sys.meta_path:
        sys.meta_path.remove(_hook)

register_hook()

if qtbindings == 'PyQt4':
    import sip
    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)
    import Qt.QtCore as core
    core.Signal = core.pyqtSignal
    core.Slot = core.pyqtSlot
    core.Property = core.pyqtProperty
