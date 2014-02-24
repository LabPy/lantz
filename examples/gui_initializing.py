# -*- coding: utf-8 -*-

import sys
import time
import random

from lantz.utils.qt import QtGui

from lantz import Driver
from lantz.ui.widgets import initialize_and_report


class FunGen3210(Driver):
    """This an fake driver that takes some random time to initialize.
    """

    def initialize(self):
        time.sleep(random.choice((2, 3, 4, 5)))
        print('initialize {}'.format(self))
        super().initialize()

    def finalize(self):
        print('finalize {}'.format(self))
        super().finalize()


class InitializeWindow(QtGui.QWidget):
    """This windows receives the list of drivers to initialize
    and their dependency.
    """

    def __init__(self, drivers=None, dependencies=None, parent=None):
        super(InitializeWindow, self).__init__(parent)

        factory = QtGui.QItemEditorFactory()
        QtGui.QItemEditorFactory.setDefaultFactory(factory)

        self.drivers = drivers
        self.dependencies = dependencies

        self.createGUI()

    def initialize(self):
        self.thread = initialize_and_report(self.widget, self.drivers,
                                            dependencies=self.dependencies,
                                            concurrent=True)

    def createGUI(self):

        # Demonstrate the supported widgets.
        # Uncomment to try others.
        self.widget = self._createGUITable()
        #self.widget = self._createGUILine()
        #self.widget = self._createGUIText()

        button = QtGui.QPushButton()
        button.setText('Initialize')
        button.setEnabled(True)
        button.clicked.connect(self.initialize)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(button)
        layout.addWidget(self.widget)
        self.setLayout(layout)

        self.setWindowTitle("Driver initialization")

    def _createGUIText(self):

        text = QtGui.QTextEdit()
        return text

    def _createGUILine(self):

        text = QtGui.QLineEdit()
        return text

    def _createGUITable(self):

        table = QtGui.QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Name", "Class", "Status"])
        table.verticalHeader().setVisible(False)
        table.resize(250, 50)
        table.resizeColumnToContents(0)
        return table



qapp = QtGui.QApplication(sys.argv)

dependencies = {'slave': ('master', )}

drivers = [FunGen3210(name='master'),
           FunGen3210(name='slave'),
           FunGen3210(name='sync')]

window = InitializeWindow(drivers=drivers, dependencies=dependencies)
window.show()

if sys.platform.startswith('darwin'):
    window.raise_()

sys.exit(qapp.exec_())


