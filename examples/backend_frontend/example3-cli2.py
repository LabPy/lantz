# -*- coding: utf-8 -*-
"""
    lantz.action
    ~~~~~~~~~~~~

    This example shows how to use a Backend with an embedded Backend.
    (and apps WITHOUT graphical user interface).

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


from lantz import Q_

# From your project you import:

# the drivers you need (In this case just simulated dummy drivers).
from lantz.drivers.examples.dummydrivers import DummyOsci, DummyFunGen, DummyShutter

# and the application backend.
# This particular backend has a function to scan the amplitude
# of a function generator while measuring the oscilloscope trace and a shutter.
# Under the hood it uses AmplitudeScanner but opens the shutter before scanning
# and close it afterwards
from myapps import AmplitudeScannerShutter

# Drivers are instantiated in the usual way.
fungen = DummyFunGen('COM1')
osci = DummyOsci('COM2')
shutter = DummyShutter('COM3')

# The backend is instantiated with keyword arguments to assign
# instantiated drivers to each InstrumentSlot (see scanner.py)
# The context manager (with statement) is used to initialize
# and finalize the instruments.
with AmplitudeScannerShutter(fungen=fungen, osci=osci, shutter=shutter) as app:

    print('Scanning ...')
    # We call any of the functions defined by the App.
    data = list(app.scan_amplitude(Q_(range(1, 10), 'volt')))


print(data)

