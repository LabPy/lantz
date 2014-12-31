# -*- coding: utf-8 -*-
"""
    lantz.utils.qt
    ~~~~~~~~~~~~~~

    A Qt API selector that can be used to switch between PyQt and PySide.

    This uses the ETS 4.0 selection pattern of:
    PySide first, PyQt with API v2. second.

    Do not use this if you need PyQt with the old QString/QVariant API.

    Copied with modifications from the IPython Project.
    http://ipython.scipy.org/

    :copyright: IPython
    :license: BSD, see the IPython Project for more details.
"""

import os

from lantz.utils.qt_loaders import (load_qt, QT_API_PYSIDE, QT_API_PYQT, QT_MOCK)

QT_API = os.environ.get('QT_API', None)
if QT_API not in [QT_API_PYSIDE, QT_API_PYQT, QT_MOCK, None]:
    raise RuntimeError("Invalid Qt API %r, valid values are: %r, %r, %r" %
                       (QT_API, QT_API_PYSIDE, QT_API_PYQT, QT_MOCK))
if QT_API is None:
    api_opts = [QT_API_PYSIDE, QT_API_PYQT]
else:
    api_opts = [QT_API]

QtCore, QtGui, QtSvg, QT_API = load_qt(api_opts)


class SuperQObject(QtCore.QObject):
    """ Permits the use of super() in class hierarchies that contain QObject.

    Unlike QObject, SuperQObject does not accept a QObject parent. If it did,
    super could not be emulated properly (all other classes in the hierarchy
    would have to accept the parent argument--they don't, of course, because
    they don't inherit QObject.)

    This class is primarily useful for attaching signals to existing non-Qt
    classes. See QtKernelManager for an example.
    """

    def __new__(cls, *args, **kw):
        # We initialize QObject as early as possible. Without this, Qt complains
        # if SuperQObject is not the first class in the super class list.
        inst = QtCore.QObject.__new__(cls)
        QtCore.QObject.__init__(inst)
        return inst

    def __init__(self, *args, **kw):
        # Emulate super by calling the next method in the MRO, if there is one.
        mro = self.__class__.mro()
        for qt_class in QtCore.QObject.mro():
            mro.remove(qt_class)
        next_index = mro.index(SuperQObject) + 1
        if next_index < len(mro):
            init = mro[next_index].__init__
            if init is object.__init__:
                init(self)
            else:
                init(self, *args, **kw)


MetaQObject = type(QtCore.QObject)
