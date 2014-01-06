# -*- coding: utf-8 -*-
"""
    lantz.ui.app
    ~~~~~~~~~~~~

    Implements base class for graphical applications.

    :copyright: 2013 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os
import sys
import inspect

from ..log import get_logger
from ..driver import Driver, initialize_many, finalize_many
from ..ui.widgets import connect_setup, DriverTestWidget, SetupTestWidget
from ..utils.qt import QtCore, QtGui, SuperQObject, MetaQObject

logger = get_logger('lantz.ui.app', False)


class InstrumentSlot(object):

    def initialize(self):
        logger.warning('The Instrument slot {} has not been assigned '
                       'to an actual instrument', self._slot_name )

    def finalize(self):
        pass


class _AppType(MetaQObject):

    def create_instrument_property(cls, key):
        def getter(self):
            return self.instruments[key]
        def setter(self, instrument):
            instrument.name = key
            self.instruments[key] = instrument

        return property(getter, setter)

    def create_app_property(cls, key):
        def getter(self):
            return self.apps[key]
        def setter(self, app):
            self.apps[key] = app

        return property(getter, setter)


    def __init__(cls, classname, bases, class_dict):
        super().__init__(classname, bases, class_dict)

        cls.instruments = dict()
        cls.apps = dict()

        for key, value in class_dict.items():
            if isinstance(value, InstrumentSlot):
                cls.instruments[key] = value
                cls.instruments[key]._slot_name = key
                setattr(cls, key, cls.create_instrument_property(key))
                logger.debug('{}: creating instrument named {} of type {}'.format(cls, key, value))
            elif value is InstrumentSlot:
                value = value()
                cls.instruments[key] = value
                cls.instruments[key]._slot_name = key
                setattr(cls, key, cls.create_instrument_property(key))
                logger.debug('{} creating instrument named {} of type {}'.format(cls, key, value))
            elif hasattr(value, 'apps') and hasattr(value, 'instruments'):
                cls.apps[key] = value
                setattr(cls, key, cls.create_app_property(key))
                logger.debug('{}: creating app named {} of type {}'.format(cls, key, value))


class Frontend(QtGui.QMainWindow):

     # a declarative way to indicate the user interface file to use.
    gui = None

    # connect widgets to instruments using connect_setup
    auto_connect = True

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)

        self._backend = None

        if self.gui:
            filename = os.path.dirname(inspect.getfile(self.__class__))
            filename = os.path.join(filename, self.gui)
            logger.debug('{}: loading gui file {}'.format(self, filename))
            self.widget = QtGui.loadUi(filename)
            self.setCentralWidget(self.widget)

        self.setupUi()
        self.backend = backend

    def setupUi(self):
        pass

    def connect_backend(self):
        pass

    @property
    def backend(self):
        return self._backend

    @backend.setter
    def backend(self, backend):
        if self._backend:
            logger.debug('{}: disconnecting backend: {}'.format(self, backend))
            self.disconnect(backend)

        self._backend = backend

        if backend:
            logger.debug('{}: connecting backend: {}'.format(self, backend))
            if self.auto_connect:
                connect_setup(self.widget, backend.instruments.values())

            self.connect_backend()


class Backend(SuperQObject, metaclass=_AppType):

    apps = {}
    instruments = {}

    def __init__(self, parent=None, **instruments):
        super().__init__(parent)
        for name, app in self.apps.items():
            d = {key: inst for key, inst in instruments.items()
                 if key in app.instruments.keys()}
            logger.debug('{}: creating sub-backend named {} with {}'.format(self, name, app))
            setattr(self, name, app(parent=self, **d))

        for name, inst in instruments.items():
            logger.debug('{}: relating instrument named {} with {}'.format(self, name, inst))
            setattr(self, name, inst)
            inst.setParent(self)

        # TODO: Check for all instruments exists

    def initialize(self, register_finalizer=False):
        initialize_many(self.instruments.values(), register_finalizer=register_finalizer)

    def finalize(self):
        finalize_many(self.instruments.values())


    def __enter__(self):
        self.initialize(register_finalizer=False)
        return self

    def __exit__(self, *args):
        self.finalize()


def start_gui_app(backend, frontend_class, qapp_or_args=None):
    if isinstance(qapp_or_args, QtGui.QApplication):
        qapp = qapp_or_args
    else:
        qapp = QtGui.QApplication(qapp_or_args or [''])

    background_thread = QtCore.QThread()
    backend.moveToThread(background_thread)
    background_thread.start()

    frontend = frontend_class(backend=backend)
    frontend.show()

    qapp.aboutToQuit.connect(background_thread.quit)

    if sys.platform.startswith('darwin'):
        frontend.raise_()

    sys.exit(qapp.exec_())


def start_test_app(target, width=500, qapp_or_args=None):
    """Start a single window test application with a form automatically
    generated for the driver.

    :param target: a driver object or a collection of drivers.
    :param width: to be used as minimum width of the window.
    :param args: arguments to be passed to QApplication.
    """

    if isinstance(qapp_or_args, QtGui.QApplication):
        qapp = qapp_or_args
    else:
        qapp = QtGui.QApplication(qapp_or_args or [''])

    if isinstance(target, Driver):
        main = DriverTestWidget(None, target)
    else:
        main = SetupTestWidget(None, target)
    main.setMinimumWidth(width)
    main.setWindowTitle('Lantz Driver Test Panel')
    main.show()
    if sys.platform.startswith('darwin'):
        main.raise_()
    qapp.exec_()
