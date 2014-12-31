# -*- coding: utf-8 -*-
"""
    lantz.utils.qt_loaders
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains factory functions that attempt
    to return Qt submodules from the various python Qt bindings.

    It also protects against double-importing Qt with different
    bindings, which is unstable and likely to crash

    This is used primarily by qt and qt_for_kernel, and shouldn't
    be accessed directly from the outside

    Copied with modifications from the IPython Project.
    http://ipython.scipy.org/

    :copyright: IPython
    :license: BSD, see the IPython Project for more details.
"""

import sys
from functools import partial

from distutils.version import LooseVersion

# Available APIs.
QT_API_PYQT = 'pyqt'
QT_API_PYQTv1 = 'pyqtv1'
QT_API_PYQT_DEFAULT = 'pyqtdefault' # don't set SIP explicitly
QT_API_PYSIDE = 'pyside'
QT_MOCK = 'mock'


def check_version(version, minimum_version):
    """check version string version >= minimum_version

    :param version: Version of the package.
    :param minimum_version: Minimum version required.

    If dev/prerelease tags result in TypeError for string-number comparison,
    it is assumed that the dependency is satisfied.
    Users on dev branches are responsible for keeping their own packages up to date.
    """
    try:
        return LooseVersion(version) >= LooseVersion(minimum_version)
    except TypeError:
        return True



class ImportDenier(object):
    """Import Hook that will guard against bad Qt imports
    once Lantz commits to a specific binding
    """

    def __init__(self):
        self.__forbidden = None

    def forbid(self, module_name):
        sys.modules.pop(module_name, None)
        self.__forbidden = module_name

    def find_module(self, mod_name, pth):
        if pth:
            return
        if mod_name == self.__forbidden:
            return self

    def load_module(self, mod_name):
        raise ImportError("""
    Importing %s disabled by Lantz, which has
    already imported an Incompatible QT Binding: %s
    """ % (mod_name, loaded_api()))

ID = ImportDenier()
sys.meta_path.append(ID)


def commit_api(api):
    """Commit to a particular API, and trigger ImportErrors on subsequent
       dangerous imports"""

    if api == QT_API_PYSIDE:
        ID.forbid('PyQt4')
    else:
        ID.forbid('PySide')


def loaded_api():
    """Return which API is loaded, if any

    If this returns anything besides None,
    importing any other Qt binding is unsafe.

    Returns
    -------
    None, 'pyside', 'pyqt', or 'pyqtv1'
    """
    if 'PyQt4.QtCore' in sys.modules:
        if qtapi_version() == 2:
            return QT_API_PYQT
        else:
            return QT_API_PYQTv1
    elif 'PySide.QtCore' in sys.modules:
        return QT_API_PYSIDE
    return None


def has_binding(api):
    """Safely check for PyQt4 or PySide, without importing
       submodules

       Parameters
       ----------
       api : str [ 'pyqtv1' | 'pyqt' | 'pyside' | 'pyqtdefault']
            Which module to check for

       Returns
       -------
       True if the relevant module appears to be importable
    """
    # we can't import an incomplete pyside and pyqt4
    # this will cause a crash in sip (#1431)
    # check for complete presence before importing

    if api == QT_MOCK:
        return True

    module_name = {QT_API_PYSIDE: 'PySide',
                   QT_API_PYQT: 'PyQt4',
                   QT_API_PYQTv1: 'PyQt4',
                   QT_API_PYQT_DEFAULT: 'PyQt4'}
    module_name = module_name[api]

    import importlib
    try:
        #importing top level PyQt4/PySide module is ok...
        #...importing submodules is not
        mod = importlib.import_module(module_name + '.QtCore')
        mod = importlib.import_module(module_name + '.QtGui')
        mod = importlib.import_module(module_name + '.QtSvg')

        #we can also safely check PySide version
        if api == QT_API_PYSIDE:
            return check_version(mod.__version__, '1.0.3')
        else:
            return True
    except ImportError:
        return False


def qtapi_version():
    """Return which QString API has been set, if any

    Returns
    -------
    The QString API version (1 or 2), or None if not set
    """
    try:
        import sip
    except ImportError:
        return
    try:
        return sip.getapi('QString')
    except ValueError:
        return


def can_import(api):
    """Safely query whether an API is importable, without importing it"""
    if not has_binding(api):
        return False

    current = loaded_api()
    if api == QT_API_PYQT_DEFAULT:
        return current in [QT_API_PYQT, QT_API_PYQTv1, None]
    else:
        return current in [api, None]


def import_pyqt4(version=2):
    """
    Import PyQt4

    :param version: 1, 2, or None. Which QString/QVariant API to use.
                    Set to None to use the system default

    ImportErrors raised within this function are non-recoverable
    """
    # The new-style string API (version=2) automatically
    # converts QStrings to Unicode Python strings. Also, automatically unpacks
    # QVariants to their underlying objects.
    import sip

    if version is not None:
        sip.setapi('QString', version)
        sip.setapi('QVariant', version)

    from PyQt4 import QtGui, QtCore, QtSvg

    if not check_version(QtCore.PYQT_VERSION_STR, '4.7'):
        raise ImportError("Lantz requires PyQt4 >= 4.7, found %s" %
                          QtCore.PYQT_VERSION_STR)

    # Alias PyQt-specific functions for PySide compatibility.
    QtCore.Signal = QtCore.pyqtSignal
    QtCore.Slot = QtCore.pyqtSlot

    from PyQt4.uic import loadUi
    QtGui.loadUi = loadUi

    # query for the API version (in case version == None)
    version = sip.getapi('QString')
    api = QT_API_PYQTv1 if version == 1 else QT_API_PYQT
    return QtCore, QtGui, QtSvg, api


def import_pyside():
    """
    Import PySide

    ImportErrors raised within this function are non-recoverable
    """
    from PySide import QtGui, QtCore, QtSvg

    from PySide.QtUiTools import QUiLoader

    class UiLoader(QUiLoader):
        """
        Subclass :class:`~PySide.QtUiTools.QUiLoader` to create the user interface
        in a base instance.

        Unlike :class:`~PySide.QtUiTools.QUiLoader` itself this class does not
        create a new instance of the top-level widget, but creates the user
        interface in an existing instance of the top-level class.

        This mimics the behaviour of :func:`PyQt4.uic.loadUi`.
        """

        def __init__(self, baseinstance):
            """
            Create a loader for the given ``baseinstance``.

            The user interface is created in ``baseinstance``, which must be an
            instance of the top-level class in the user interface to load, or a
            subclass thereof.

            ``parent`` is the parent object of this loader.
            """
            QUiLoader.__init__(self, baseinstance)
            self.baseinstance = baseinstance

        def createWidget(self, class_name, parent=None, name=''):
            if parent is None and self.baseinstance:
                # supposed to create the top-level widget, return the base instance
                # instead
                return self.baseinstance
            else:
                # create a new widget for child widgets
                widget = QUiLoader.createWidget(self, class_name, parent, name)
                if self.baseinstance:
                    # set an attribute for the new child widget on the base
                    # instance, just like PyQt4.uic.loadUi does.
                    setattr(self.baseinstance, name, widget)
                return widget


    def loadUi(uifile, baseinstance=None):
        """
        Dynamically load a user interface from the given ``uifile``.

        :param uifile: a string containing a file name of the UI file to load.
        :param baseinstance: If ``None``, the a new instance of the top-level widget
        will be created.  Otherwise, the user interface is created within the given
        ``baseinstance``.  In this case ``baseinstance`` must be an instance of the
        top-level widget class in the UI file to load, or a subclass thereof.  In
        other words, if you've created a ``QMainWindow`` interface in the designer,
        ``baseinstance`` must be a ``QMainWindow`` or a subclass thereof, too.  You
        cannot load a ``QMainWindow`` UI file with a plain
        :class:`~PySide.QtGui.QWidget` as ``baseinstance``.

        :method:`~PySide.QtCore.QMetaObject.connectSlotsByName()` is called on the
        created user interface, so you can implemented your slots according to its
        conventions in your widget class.

        Return ``baseinstance``, if ``baseinstance`` is not ``None``.  Otherwise
        return the newly created instance of the user interface.
        """
        loader = UiLoader(baseinstance)
        widget = loader.load(uifile)
        QtCore.QMetaObject.connectSlotsByName(widget)
        return widget

    QtGui.loadUi = loadUi

    return QtCore, QtGui, QtSvg, QT_API_PYSIDE


def import_qtmock():
    """
    Return Mock Modules
    """
    # The new-style string API (version=2) automatically
    # converts QStrings to Unicode Python strings. Also, automatically unpacks
    # QVariants to their underlying objects.

    from unittest.mock import MagicMock

    class Mock(MagicMock):

        @classmethod
        def __getattr__(cls, name):
            m = Mock()
            m.__name__ = name
            return m

        QObject = object

    QtGui, QtCore, QtSvg = Mock(), Mock(), Mock()

    return QtCore, QtGui, QtSvg, 'mock'


def load_qt(api_options):
    """
    Attempt to import Qt, given a preference list
    of permissible bindings

    It is safe to call this function multiple times.

    :param api_options: List of strings
        The order of APIs to try. Valid items are 'pyside',
        'pyqt', and 'pyqtv1'

    Returns
    -------

    A tuple of QtCore, QtGui, QtSvg, QT_API
    The first three are the Qt modules. The last is the
    string indicating which module was loaded.

    Raises
    ------
    ImportError, if it isn't possible to import any requested
    bindings (either becaues they aren't installed, or because
    an incompatible library has already been installed)
    """
    loaders = {QT_API_PYSIDE: import_pyside,
               QT_API_PYQT: import_pyqt4,
               QT_API_PYQTv1: partial(import_pyqt4, version=1),
               QT_API_PYQT_DEFAULT: partial(import_pyqt4, version=None),
               QT_MOCK: import_qtmock
               }

    for api in api_options:

        if api not in loaders:
            raise RuntimeError(
                "Invalid Qt API %r, valid values are: %r, %r, %r, %r, %r" %
                (api, QT_API_PYSIDE, QT_API_PYQT,
                 QT_API_PYQTv1, QT_API_PYQT_DEFAULT, QT_MOCK))

        if not can_import(api):
            continue

        #cannot safely recover from an ImportError during this
        result = loaders[api]()
        api = result[-1]  # changed if api = QT_API_PYQT_DEFAULT
        commit_api(api)
        return result
    else:
        raise ImportError("""
    Could not load requested Qt binding. Please ensure that
    PyQt4 >= 4.7 or PySide >= 1.0.3 is available,
    and only one is imported per session.

    Currently-imported Qt library:   %r
    PyQt4 installed:                 %s
    PySide >= 1.0.3 installed:       %s
    Tried to load:                   %r
    """ % (loaded_api(),
           has_binding(QT_API_PYQT),
           has_binding(QT_API_PYSIDE),
           api_options))
