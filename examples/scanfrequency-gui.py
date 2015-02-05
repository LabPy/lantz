# -*- coding: utf-8 -*-
"""
    scanfrequency
    ~~~~~~~~~~~~~

    This example shows how to program a GUI using Qt and lantz drivers, but
    without the backend-frontend classes that simplifies app development.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import sys

from lantz import Q_

# Import from lantz a function to connect drivers to UI
from lantz.ui.widgets import connect_driver

# Import lantz.ui register an import hook that will replace calls to Qt by PyQt4 or PySide ...
# and here we just use Qt and will work with both bindings!
from lantz.utils.qt import QtGui, QtCore

# These imports are from your own project
from lantz.drivers.examples import LantzSignalGeneratorTCP

# And we reuse the code from the command line application.
from scanfrequency import scan_frequency

qapp = QtGui.QApplication(sys.argv)

# Load the UI from the QtDesigner file. You can also use pyuic4 to generate a class.
main = QtGui.loadUi('scanfrequency.ui')

Hz = Q_(1, 'Hz')
sec = Q_(1, 'sec')

with LantzSignalGeneratorTCP('localhost', 5678) as inst:

    # Connect the main panel widgets to the instruments Feats,
    # matching by name
    connect_driver(main, inst, prefix='fungen')

    # Obtain a reference to the widgets controlling the scan parameters
    start = main.findChild((QtGui.QWidget, ), 'start')
    stop = main.findChild((QtGui.QWidget, ), 'stop')
    step = main.findChild((QtGui.QWidget, ), 'step')
    wait = main.findChild((QtGui.QWidget, ), 'wait')
    scan = main.findChild((QtGui.QWidget, ), 'scan')
    progress = main.findChild((QtGui.QWidget, ), 'progress')

    def update_progress_bar(new, old):
        fraction = (new.magnitude - start.value()) / (stop.value() - start.value())
        progress.setValue(fraction * 100)

    inst.frequency_changed.connect(update_progress_bar)

    # <--------- New code--------->
    # Define a function to read the values from the widget and call scan_frequency
    class Scanner(QtCore.QObject):

        def scan(self):
            # Call the scan frequency
            scan_frequency(inst, start.value() * Hz, stop.value() * Hz,
                           step.value() * Hz, wait.value() * sec)
            # When it finishes, set the progress to 100%
            progress.setValue(100)

    thread = QtCore.QThread()
    scanner = Scanner()
    scanner.moveToThread(thread)
    thread.start()

    # Connect the clicked signal of the scan button to the function
    scan.clicked.connect(scanner.scan)

    qapp.aboutToQuit.connect(thread.quit)
    # <--------- End of new code --------->

    main.show()
    exit(qapp.exec_())
