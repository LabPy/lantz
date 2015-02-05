# -*- coding: utf-8 -*-
"""
    lantz.ui.chart
    ~~~~~~~~~~~~~~

    A chart frontend.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Q_

# Import Qt modules from lantz (pyside and pyqt compatible)
from lantz.utils.qt import QtGui

# These classes simplify application development
from lantz.ui.app import Frontend


class ChartUi(Frontend):
    """A frontend with a x,y plot (powered by pyqtgraph)
    """

    # a declarative way to indicate the user interface file to use.
    # The file must be located next to the python file where this class
    # is defined.
    gui = 'placeholder.ui'

    # connect widgets to instruments using connect_setup automatically.
    auto_connect = True

    _axis = {'x': 'bottom',
             'y': 'left'}

    def __init__(self, xlabel='', xunits='', ylabel='', yunits='', *args, **kwargs):
        self._labels = {'x': xlabel, 'y': ylabel}
        self._units = {'x': xunits, 'y': yunits}

        self._x = []
        self._y = []

        super().__init__(*args, **kwargs)

    @property
    def xlabel(self):
        """x-axis label.
        """
        return self._labels['x']

    @xlabel.setter
    def xlabel(self, value):
        self._labels['x'] = value
        self._relabel('x')

    @property
    def ylabel(self):
        """y-axis label.
        """
        return self._labels['y']

    @ylabel.setter
    def ylabel(self, value):
        self._labels['y'] = value
        self._relabel('y')

    @property
    def xunits(self):
        """x-axis units as a string.
        """
        return self._units['x']

    @xunits.setter
    def xunits(self, value):
        self._units['x'] = value
        self._relabel('x')

    @property
    def yunits(self):
        """y-axis units as a string.
        """
        return self._units['y']

    @yunits.setter
    def yunits(self, value):
        self._units['y'] = value
        self._relabel('y')

    def _relabel(self, axis):
        """Builds the actual label using the label and units for a given axis.
        Also builds a quantity to be used to normalized the data.

        :param axis: 'x' or 'y'
        """
        label = self._labels[axis]
        units = self._units[axis]
        if label and units:
            label = '%s [%s]' % (label, units)
        elif units:
            label = '[%s]' % units

        self.pw.setLabel(self._axis[axis], label)

        if units:
            setattr(self, '_q' + axis, Q_(1, units))

    def setupUi(self):
        import pyqtgraph as pg

        pg.setConfigOptions(antialias=True)
        # This method is called after gui has been loaded (referenced in self.widget)
        # to customize gui building. In this case, we are adding a plot widget.
        self.pw = pg.PlotWidget()

        self.curve = self.pw.plot(pen='y')
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.pw)
        self.widget.placeholder.setLayout(layout)

    def plot(self, x, y):
        """Add a pair of points to the plot.
        """
        x = float(x / self._qx)
        y = float(y / self._qy)
        self._x.append(x)
        self._y.append(y)
        self.curve.setData(self._x, self._y)

    def clear(self, *args):
        """Clear the plot.
        """
        self._x.clear()
        self._y.clear()
