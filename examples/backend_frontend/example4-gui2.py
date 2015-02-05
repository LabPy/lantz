# -*- coding: utf-8 -*-
"""
    lantz.action
    ~~~~~~~~~~~~

    This example shows how to use a Frontend (with an embedded Frontend)
     (and apps WITHOUT graphical user interface).

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

# From lantz, you import a helper function.
from lantz.ui.app import start_gui_app

# From your project you import:

# the drivers you need (In this case just simulated dummy drivers).
from lantz.drivers.examples.dummydrivers import DummyOsci, DummyFunGen, DummyShutter

# and the application backend.
# This particular backend has a function to scan the amplitude
# of a function generator while measuring the oscilloscope trace and a shutter.
from myapps import AmplitudeScannerShutter, AmplitudeScannerShutterUi

# Drivers are instantiated in the usual way.
fungen = DummyFunGen('COM1')
osci = DummyOsci('COM2')
shutter = DummyShutter('COM3')

# The application is called with keyword arguments to assign
# instantiated drivers to each InstrumentSlot
app = AmplitudeScannerShutter(fungen=fungen, osci=osci, shutter=shutter)

# Your start the application using the helper function.
# As arguments, you provide a Backend INSTANCE and a Frontend CLASS.
start_gui_app(app, AmplitudeScannerShutterUi)
