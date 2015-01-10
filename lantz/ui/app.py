# -*- coding: utf-8 -*-
"""
    lantz.ui.app
    ~~~~~~~~~~~~

    Implements base class for graphical applications.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import os
import sys
import inspect
import collections

from ..log import get_logger
from ..driver import Driver, initialize_many, finalize_many
from ..ui.widgets import connect_setup, DriverTestWidget, SetupTestWidget, connect_driver
from ..utils.qt import QtCore, QtGui, SuperQObject, MetaQObject

logger = get_logger('lantz.ui.app', False)


class InstrumentSlot(object):

    def __str__(self):
        return '<InstrumentSlot>'

    def initialize(self):
        logger.warning('The Instrument slot {} has not been assigned '
                       'to an actual instrument', self._slot_name )

    def finalize(self):
        pass


Front2Back = collections.namedtuple('Front2Back', 'frontend_class backend_name settings')


class _BackendType(MetaQObject):

    def create_instrument_property(cls, key):
        def getter(self):
            return self.instruments[key]
        def setter(self, instrument):
            instrument.name = key
            self.instruments[key] = instrument

        return property(getter, setter)

    def create_backend_property(cls, key):
        def getter(self):
            return self.backends[key]
        def setter(self, backend):
            self.backends[key] = backend

        return property(getter, setter)


    def __init__(cls, classname, bases, class_dict):
        super().__init__(classname, bases, class_dict)

        cls.instruments = dict()
        cls.backends = dict()

        for key, value in class_dict.items():
            if isinstance(value, InstrumentSlot):
                cls.instruments[key] = value
                cls.instruments[key]._slot_name = key
                setattr(cls, key, cls.create_instrument_property(key))
                logger.debug('{}, adding instrument named {} of type {}'.format(cls, key, value))
            elif value is InstrumentSlot:
                value = value()
                cls.instruments[key] = value
                cls.instruments[key]._slot_name = key
                setattr(cls, key, cls.create_instrument_property(key))
                logger.debug('In {}, adding instrument named {} of type {}'.format(cls, key, value))
            elif hasattr(value, 'backends') and hasattr(value, 'instruments'):
                cls.backends[key] = value
                setattr(cls, key, cls.create_backend_property(key))
                logger.debug('In {}, adding backend named {} of type {}'.format(cls, key, value))

    def __str__(cls):
        return cls.__name__


class _FrontendType(MetaQObject):

    def create_frontend_property(cls, key):
        def getter(self):
            return self.frontends[key]
        def setter(self, frontend):
            self.frontends[key] = frontend

        return property(getter, setter)


    def __init__(cls, classname, bases, class_dict):
        super().__init__(classname, bases, class_dict)

        cls.frontends = dict()

        for key, value in class_dict.items():
            if isinstance(value, Front2Back) or hasattr(value, 'frontends'):
                cls.frontends[key] = value
                setattr(cls, key, cls.create_frontend_property(key))
                logger.debug('{}, adding frontend named {} of type {}'.format(cls, key, value))

    def __str__(cls):
        return cls.__name__


class Frontend(QtGui.QMainWindow, metaclass=_FrontendType):

    frontends = {}

     # a declarative way to indicate the user interface file to use.
    gui = None

    # connect widgets to instruments using connect_setup
    auto_connect = True

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)

        self._backend = None

        if self.gui:
            for cls in self.__class__.__mro__:
                filename = os.path.dirname(inspect.getfile(cls))
                filename = os.path.join(filename, self.gui)
                if os.path.exists(filename):
                    logger.debug('{}: loading gui file {}'.format(self, filename))
                    self.widget = QtGui.loadUi(filename)
                    self.setCentralWidget(self.widget)
                    break
            else:
                raise ValueError('{}: loading gui file {}'.format(self, self.gui))

        for name, frontend in self.frontends.items():
            if isinstance(frontend, Front2Back):
                widget = frontend.frontend_class(backend=getattr(backend, frontend.backend_name))
            else:
                widget = frontend(backend=backend)
            widget.setParent(self)
            setattr(self, name, widget)

        self.setupUi()
        self.backend = backend

    def __str__(self):
        return self.__class__.__name__

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

    @classmethod
    def using(cls, backend_name=None, settings=None):
        return Front2Back(cls, backend_name, settings)


class Backend(SuperQObject, metaclass=_BackendType):

    backends = {}
    instruments = {}

    def __init__(self, parent=None, **instruments_and_backends):
        super().__init__(parent)

        for name, app in self.backends.items():
            if not name in instruments_and_backends:
                continue

            d = {key: inst for key, inst in instruments_and_backends.items()
                 if key in app.instruments.keys()}
            logger.debug('{}: creating sub-backend named {} with {}'.format(self, name, app))
            if name in instruments_and_backends:
                d.update(instruments_and_backends[name])
            setattr(self, name, app(parent=self, **d))

        for name in self.instruments.keys():
            if not name in instruments_and_backends:
                continue

            inst = instruments_and_backends[name]
            logger.debug('{}: relating instrument named {} with {}'.format(self, name, inst))
            setattr(self, name, inst)
            inst.setParent(self)

        # TODO: Check for all instruments exists

    def __str__(self):
        return self.__class__.__name__

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
    :param qapp_or_args: arguments to be passed to QApplication.
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


def start_gui(ui_filename, drivers, qapp_or_args=None):
    """Start a single window application with a form generated from
    a designer file.

    :param ui_filename: the full path of a file generated with QtDesigner.
    :param drivers: a driver object or a collection of drivers.
    :param qapp_or_args: arguments to be passed to QApplication.
    """

    if isinstance(qapp_or_args, QtGui.QApplication):
        qapp = qapp_or_args
    else:
        qapp = QtGui.QApplication(qapp_or_args or [''])

    main = QtGui.loadUi(ui_filename)

    if isinstance(drivers, Driver):
        connect_driver(main, drivers)
    else:
        connect_setup(main, drivers)

    main.show()
    if sys.platform.startswith('darwin'):
        main.raise_()
    qapp.exec_()
