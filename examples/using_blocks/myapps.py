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

from lantz.ui.blocks import Loop, LoopUi

# These classes simplify application development
from lantz.ui.app import Frontend, Backend, InstrumentSlot


class LoopOsciMeasure(Backend):
    """An application that measures from an Osci in a loop.
    """

    # Enumerate drivers required by the backend marking them with InstrumentSlot
    osci = InstrumentSlot

    # Embedded apps (Notice we embed the backend, not the Frontend)
    loop = Loop

    # This signal will be emitted when new data is available.
    new_data = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop.body = self.measure

    def measure(self, counter, iterations, overrun):
        data = self.osci.measure()
        self.new_data.emit(data)


class LoopPlot(Frontend):
    """A frontend that has a loop UI and a plot. (Works form many things!)
    """

    # a declarative way to indicate the user interface file to use.
    # The file must be located next to the python file where this class
    # is defined.
    gui = 'loop_plot.ui'

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

        self.loopUi = LoopUi()
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.loopUi.widget)
        self.widget.loopParent.setLayout(layout)

    def connect_backend(self):

        # This method is called after gui has been loaded (referenced in self.widget)
        # and the backend is connected to the frontend (referenced in self.backend).
        # In this case, we use it to connect the scan button, to the default_scan
        # method in the backend, and the signal to the plot function.
        self.loopUi.backend = self.backend.loop
        self.backend.new_data.connect(self.plot)

    def plot(self, y):
        self.curve.setData(y)
