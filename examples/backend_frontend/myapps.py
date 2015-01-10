# -*- coding: utf-8 -*-
"""
    lantz.ui.qapp
    ~~~~~~~~~~~~

    Example backend and frontend for 2 different applications.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time

import numpy as np

# This is a plotting library that we are using. You could also use Matplotlib.
import pyqtgraph as pg

from lantz import Q_

# Import Qt modules from lantz (pyside and pyqt compatible)
from lantz.utils.qt import QtGui, QtCore

# These classes simplify application development
from lantz.ui.app import Frontend, Backend, InstrumentSlot


class AmplitudeScanner(Backend):
    """A simple application that requires a function generator and an
    oscilloscope.
    """

    # Enumerate drivers required by the backend marking them with InstrumentSlot
    fungen = InstrumentSlot
    osci = InstrumentSlot

    def scan_amplitude(self, amplitudes):
        """For each amplitude:
        - scan the amplitude of the function generator.
        - sleeps .3 seconds.
        - measures the trace of the oscilloscope.
        - yields amplitude, data for each amplitude.

        :param amplitudes: iterable of amplitudes.
        """
        for amplitude in amplitudes:
            self.fungen.amplitude = amplitude
            time.sleep(.3)
            data = self.osci.measure()
            yield amplitude, data

    def _scan_amplitude(self, amplitudes):
        """Because scan_amplitude is a generator, this helper functions is used
        to iterate over all the items.
        """
        return list(self.scan_amplitude(amplitudes))

    def default_scan(self):
        """A linear scan from 1 to 19 Volts.
        """
        return list(self.scan_amplitude(Q_(list(range(1, 20)), 'volt')))


class AmplitudeScannerUi(Frontend):
    """A frontend for the AmplitudeScanner backend.

    Provides controls to select the scan range and to start and stop de scanning.
    """

    # a declarative way to indicate the user interface file to use.
    # The file must be located next to the python file where this class
    # is defined.
    gui = 'amplitude_scanner.ui'

    # connect widgets to instruments using connect_setup automatically.
    auto_connect = True

    # amplitudes
    request_start = QtCore.Signal(object)

    def _scan(self):
        start, stop, steps = (getattr(self.widget, name).value()
                              for name in ('start', 'stop', 'steps'))
        amplitudes = Q_(np.linspace(start, stop, steps), 'volt')
        self.request_start.emit(amplitudes)

    def connect_backend(self):

        # This method is called after gui has been loaded (referenced in self.widget)
        # and the backend is connected to the frontend (referenced in self.backend).
        # In this case, we use it to connect the scan button, to the scan method
        # and the request_start signal to the _scan_amplitude
        self.widget.scan_amplitudes.clicked.connect(self._scan)
        self.request_start.connect(self.backend._scan_amplitude)


class AmplitudeScannerShutter(Backend):
    """A complex application that requires a function generator, an
    oscilloscope and a shutter.

    We could subclass AmplitudeScanner, but we have chosen to embed it instead.
    """

    # Enumerate drivers required by the backend marking them with InstrumentSlot
    osci = InstrumentSlot
    fungen = InstrumentSlot
    shutter = InstrumentSlot

    # Embedded apps (Notice we embed the backend, not the Frontend)
    scanner = AmplitudeScanner

    # This signal will be emited when new data is available.
    new_data = QtCore.Signal(object, object)

    def scan_amplitude(self, amplitudes):
        """Open the shutter an then for each amplitude:
        - scan the amplitude of the function generator.
        - sleeps .3 seconds.
        - measures the trace of the oscilloscope.
        - yields amplitude, data for each amplitude.

        Finally, close the shutter.

        :param amplitudes: iterable of amplitudes.
        """
        self.shutter.opened = True

        # We use the embedded app to perform the actual operation.
        # Notice that we have not explicitly instantiated the AmplitudeScanner
        # nor provided the instruments. Lantz has done this in the back
        # connecting InstrumentsSlots by name.
        # i.e. self.osci is self.scanner.osci
        for amplitude, data in self.scanner.scan_amplitude(amplitudes):
            self.new_data.emit(amplitude, data)
            yield amplitude, data

        self.shutter.opened = False

    def _scan_amplitude(self, amplitudes):
        """Because scan_amplitude is a generator, this helper functions is used
        to iterate over all the items.
        """
        return list(self.scan_amplitude(amplitudes))

    def default_scan(self):
        """A linear scan from 1 to 19 Volts.
        """
        return list(self.scan_amplitude(Q_(list(range(1, 20)), 'volt')))


class AmplitudeScannerShutterUi(Frontend):
    """A frontend for the AmplitudeScannerShutter backend.

    Provides controls to select the scan range and to start and stop the scanning.
    """

    # a declarative way to indicate the user interface file to use.
    # The file must be located next to the python file where this class
    # is defined.
    gui = 'scanner_shutter.ui'

    # connect widgets to instruments using connect_setup automatically.
    auto_connect = True

    def setupUi(self):

        # This method is called after gui has been loaded (referenced in self.widget)
        # to customize gui building. In this case, we are adding a plot widget.
        self.pw = pg.PlotWidget()
        self.curve = self.pw.plot(pen='y')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.pw)
        self.widget.plotParent.setLayout(layout)
        self.scannerUi = AmplitudeScannerUi()

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.scannerUi.widget)
        self.widget.scanner_widget.setLayout(layout)

    def connect_backend(self):

        # This method is called after gui has been loaded (referenced in self.widget)
        # and the backend is connected to the frontend (referenced in self.backend).
        # In this case, we use it to connect the scan button, to the default_scan
        # method in the backend, and the signal to the plot function.
        self.scannerUi.widget.scan_amplitudes.clicked.connect(self.scannerUi._scan)
        self.scannerUi.request_start.connect(self.backend._scan_amplitude)
        self.backend.new_data.connect(self.plot)

    def plot(self, x, y):
        self.curve.setData(y)
