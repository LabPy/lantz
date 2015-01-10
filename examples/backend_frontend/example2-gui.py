# -*- coding: utf-8 -*-
"""
    example2-gui
    ~~~~~~~~~~~~

    This example shows how to use a Backend and a Frontend
    (an app WITH graphical user interface).

    The program uses a predefined application that scans the amplitude of a function
    generator and for each amplitude measures the trace in an oscilloscope
    (just random data in this simulated example).

    The User interface has two widgets connected to feats of the function generator
    (amplitude and frequency) and a few controls to control the scan.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

# From lantz, you import a helper function.
from lantz.ui.app import start_gui_app

# From your project you import:

# the drivers you need (In this case just simulated dummy drivers).
from lantz.drivers.examples.dummydrivers import DummyOsci, DummyFunGen

# and the application backend and front end
# This particular backend has a function to scan the amplitude
# of a function generator while measuring the oscilloscope trace.
from myapps import AmplitudeScanner, AmplitudeScannerUi

# Drivers are instantiated in the usual way.
fungen = DummyFunGen('COM1')
osci = DummyOsci('COM2')

# The backend is instantiated with keyword arguments to assign
# instantiated drivers to each InstrumentSlot (see scanner.py)
app = AmplitudeScanner(fungen=fungen, osci=osci)

# Your start the application using the helper function.
# As arguments, you provide a Backend INSTANCE and a Frontend CLASS.
start_gui_app(app, AmplitudeScannerUi)

