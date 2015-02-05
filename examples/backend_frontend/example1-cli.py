# -*- coding: utf-8 -*-
"""
    example1-cli
    ~~~~~~~~~~~~

    This example shows how to use a Backend (and apps WITHOUT graphical user interface).

    The program uses a predefined application that scans the amplitude of a function
    generator and for each amplitude measures the trace in an oscilloscope
    (just random data in this simulated example).



    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


from lantz import Q_

# From your project you import:

# the drivers you need (In this case just simulated dummy drivers).
from lantz.drivers.examples.dummydrivers import DummyOsci, DummyFunGen

# and the application backend.
# This particular backend has a function to scan the amplitude
# of a function generator while measuring the oscilloscope trace.
from myapps import AmplitudeScanner

# Drivers are instantiated in the usual way.
fungen = DummyFunGen('COM1')
osci = DummyOsci('COM2')

# The backend is instantiated with keyword arguments to assign
# instantiated drivers to each InstrumentSlot (see scanner.py)
app = AmplitudeScanner(fungen=fungen, osci=osci)

# We initialize all devices
# (and perform any other initialization code required by the App)
app.initialize()

# We call any of the functions defined by the App.
print('Scanning ...')
for data in app.scan_amplitude(Q_(range(1, 10), 'volt')):
    print(data)

# We finalize all devices 
# (and perform any other finalize code required by the App)
app.finalize() 

"""
# Like in the drivers, you can use a context manager
# shown as a comment below:

with AmplitudeScanner(fungen=fungen, osci=osci) as app:
    data = list(app.scan_amplitude(Q_(range(1, 100), 'volt')))

print(data)
"""
