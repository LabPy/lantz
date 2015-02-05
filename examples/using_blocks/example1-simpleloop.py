# -*- coding: utf-8 -*-
"""
    example1-simpleloop
    ~~~~~~~~~~~~~~~~~~~

    This example shows how to use the loop block backend and frontend.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

# From lantz, you import a helper function.
from lantz.ui.app import start_gui_app

# and the loop block and its user interface
from lantz.ui.blocks import Loop, LoopUi

# the drivers you need (In this case just simulated dummy drivers).
from lantz.drivers.examples.dummydrivers import DummyOsci

# Drivers are instantiated in the usual way.
osci = DummyOsci('COM2')

# You create a function that will be called by the loop
# It requires three parameters
# counter - the iteration number
# iterations - total number of iterations
# overrun - a boolean indicating if the time required for the operation
#           is longer than the interval.
def measure(counter, iterations, overrun):
    print(counter, iterations, overrun)
    data = osci.measure()
    print(data)

# You instantiate the loop
app = Loop()

# and assign the function to the body of the loop
app.body = measure

# Finally you start the program
start_gui_app(app, LoopUi)

# This contains a very complete GUI for a loop you can easily create a customized version!

