# -*- coding: utf-8 -*-
"""
    example2-plot
    ~~~~~~~~~~~~~

    This example shows how to use the loop block (backend and frontend)
    inside another gui.

    The gui incorporates a plot.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

# From lantz, you import a helper function.
from lantz.ui.app import start_gui_app

# the drivers you need (In this case just simulated dummy drivers).
from lantz.drivers.examples.dummydrivers import DummyOsci

from myapps import LoopOsciMeasure, LoopPlot

# Drivers are instantiated in the usual way.
osci = DummyOsci('COM2')

# You instantiate the backend
app = LoopOsciMeasure(osci=osci)

# Finally you start the program
start_gui_app(app, LoopPlot)

# Notice that the LoopPlot GUI is not tied to the LoopOsciMeasure backend.
# It just requires a backend that has a measure method and that emits a new_data signal!

