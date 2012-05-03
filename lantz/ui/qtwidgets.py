import types

from . import Signal, Property, Slot

from PyQt4.QtCore import QRect, QVariant, Qt, QSize
from PyQt4.QtGui import (QWidget, QLabel, QPlainTextEdit, QPushButton, QDialog,
                         QDoubleSpinBox, QHBoxLayout, QFormLayout, QComboBox,
                         QVBoxLayout, QLayout, QDialogButtonBox, QLineEdit,
                         QSpinBox, QCheckBox, QFont, QGridLayout,
                         QApplication)

from .. import Q_, Driver
from ..feat import MISSING


def get_widget(feat):
    """Return a widget to represent a lantz feature.

    :param feat: a lantz feature, the result of inst._lantz_feat[feat_name].
    """

    if feat.map:
        if isinstance(feat.map, dict):
            tmp = set(feat.map.keys())
        else:
            tmp = set(feat.map)

        if tmp == {True, False}:
            return QCheckBox
        return QComboBox

    if feat.units or feat.range:
        return QDoubleSpinBox

    return QLineEdit


def request_new_units(current_units):
    """Ask for new units using a dialog box and return them.

    :param current: current units or magnitude.
    :type current: Q_

    """
    new_units = UnitInputDialog.get_units(current_units)
    if new_units is None:
        return None

    try:
        return Q_(1, new_units)
    except LookupError:
        # cannot parse units
        return None


def add_keyPressEvent_handler(widget):
    """Add to a QWidget instance proper handling of 'u' for unit changing
    and 'r' for refreshing.

    :param widget: QWidget instance.
    """

    widget._original_keyPressEvent = widget.keyPressEvent

    def keyPressEvent(self, event):
        """When 'u' is pressed, request new units.
        When 'r' is pressed, get new value from the driver.
        """
        widget._original_keyPressEvent(event)

        if self._lantz_units and event.text() == 'u':
            self.change_units(request_new_units(self.value()))

        if event.text() == 'r':
            # This should also trigger a widget update if necessary.
            getattr(self._target, self._feat_name)

    widget.keyPressEvent = types.MethodType(keyPressEvent, widget)


def add_magnitude_handler(widget):
    """Add to a QWidget proper handling of units.

    :param widget: QDoubleSpinBox instance.
    """
    if not widget._lantz_units:
        widget.setValue = types.MethodType(_setValue, widget)
        return

    def change_units(self, new_units):
        """Update displayed suffix and stored units.
        """
        if new_units is None:
            return
        try:
            rescaled = self.value().rescale(new_units)
        except ValueError:
            # incompatible units
            return None
        else:
            self._lantz_units = new_units
            self.setSuffix(' ' + str(new_units.units))
            self.setValue(rescaled)

    def value(self):
        """Get widget value and scale by units.
        """
        return self._original_getter() * self._lantz_units

    def setValue(self, value):
        """Set widget value scaled by units.
        """
        if value is MISSING:
            font = QFont()
            font.setItalic(True)
            self.setFont(font)
            return
        self._original_setter(value.rescale(self._lantz_units).magnitude)

    widget.change_units = types.MethodType(change_units, widget)
    widget.value = types.MethodType(value, widget)
    widget.setValue = types.MethodType(setValue, widget)

    widget.setSuffix(' ' + str(widget._lantz_units.units))


def _setValue(self, value):

    if value is MISSING:
        return
    self._original_setter(value)


# Pimpers

def pimp_QDoubleSpinBox(widget):

    widget._original_getter = widget.value
    widget._original_setter = widget.setValue
    widget._original_changed = widget.valueChanged

    add_magnitude_handler(widget)

    try:
        rng = widget._lantz_range
        if len(rng) == 1:
            widget.setRange(0, rng[0])
        else:
            widget.setRange(rng[0], rng[1])
            if len(rng) == 3:
                widget.setSingleStep(rng[2])
    except (IndexError, TypeError) as e:
        widget.setRange(float('-inf'), float('inf'))

def pimp_QComboBox(widget):

    widget._original_getter = widget.currentIndex
    widget._original_setter = widget.setCurrentIndex
    widget._original_changed = widget.currentIndexChanged

    widget.addItems(widget._lantz_map)

    def value(self):
        return self.currentText()

    def setValue(self, value):
        if value is MISSING:
            font = QFont()
            font.setItalic(True)
            self.setFont(font)
            return
        self.setCurrentIndex(self._lantz_map.index(value))

    def setReadOnly(self, value):
        widget.setEnabled(not value)

    widget.value = types.MethodType(value, widget)
    widget.setValue = types.MethodType(setValue, widget)
    widget.setReadOnly = types.MethodType(setReadOnly, widget)


def pimp_QCheckBox(widget):

    widget._original_getter = widget.isChecked
    widget._original_setter = widget.setChecked
    widget._original_changed = widget.stateChanged

    def setReadOnly(self, value):
        widget.setCheckable(not value)

    widget.setReadOnly = types.MethodType(setReadOnly, widget)

def pimp_QLineEdit(widget):
    """

    :param widget:
    :type widget: QLineEdit
    :return:
    """

    widget._original_getter = widget.text
    widget._original_setter = widget.setText
    widget._original_changed = widget.textChanged

def pimp_pass(widget):
    pass


PIMPER = {QSpinBox: pimp_QDoubleSpinBox,
          QDoubleSpinBox: pimp_QDoubleSpinBox,
          QComboBox: pimp_QComboBox,
          QCheckBox: pimp_QCheckBox,
          QLineEdit: pimp_QLineEdit}

from .qtlog import LogTable


def start_form(inst, *args):
    app = QApplication(list(args))
    main = Form(None, inst)
    main.setMinimumWidth(500)
    main.show()
    app.exec_()


class Form(QWidget):

    def __init__(self, parent, target):
        super().__init__(parent)
        self._target = target
        self._layout = QVBoxLayout()

        label = QLabel()
        label.setText(str(target))
        self._layout.addWidget(label)
        layout = QHBoxLayout()

        recall = QPushButton()
        recall.setText('Refresh')
        recall.clicked.connect(lambda x: target.refresh())

        update = QPushButton()
        update.setText('Update')
        update.clicked.connect(lambda x: target.update(self.widgets_as_dict()))

        auto = QCheckBox()
        auto.setText('Update on change')
        auto.setChecked(True)
        auto.stateChanged.connect(self.update_on_change)

        layout.addWidget(recall)
        layout.addWidget(update)
        layout.addWidget(auto)
        self._layout.addLayout(layout)

        layout = QGridLayout()
        self._layout.addLayout(layout)


        self.writable_widgets = []
        for row, feat_name in enumerate(sorted(target._lantz_features.keys())):
            try:
                featwidget = FeatWidget(target, feat_name)
                if featwidget.writable:
                    self.writable_widgets.append(featwidget)
                for col, widget in enumerate(featwidget.widgets):
                    layout.addWidget(widget, row, col)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                print('Could not create control for {}: {}'.format(feat_name, ex))

        self.setLayout(self._layout)

    def update_on_change(self, new_state):
        for widget in self.writable_widgets:
            widget._widget._update_on_change = new_state

    def widgets_as_dict(self):
        return {widget._feat_name: widget._widget.value() for widget in self.writable_widgets}



def pimp(widget):

    add_keyPressEvent_handler(widget)

    PIMPER[type(widget)](widget)

    if not hasattr(widget, 'value'):
        widget.value = widget._original_getter

    if not hasattr(widget, 'setValue'):
        widget.setValue = types.MethodType(_setValue, widget)

    if not hasattr(widget, 'valueChanged'):
        widget.valueChanged = widget._original_changed

    @Slot(QVariant)
    def on_widget_value_changed(self, value):
        """When the widget is changed by the user, update the driver with
        the new value.
        """
        if self._update_on_change:
            setattr(self._target, self._feat_name, self.value())

    def on_feat_value_changed(self, value):
        """When the driver value is changed, update the widget if necessary.
        """
        if self.value() == value:
            return
        self.setValue(value)

    def target(self):
        return self._target

    def setTarget(self, target):
        if self._target:
            self._target.del_on_changed(self._feat_name, self.on_feat_value_changed, self._feat_key)
        if target:
            self._target = target
            self._target.add_on_changed(self._feat_name, self.on_feat_value_changed, self._feat_key)
            widget.on_feat_value_changed(self._target.recall(self._feat_name))

    widget._update_on_change = False

    widget.target = types.MethodType(target, widget)
    widget.setTarget = types.MethodType(setTarget, widget)

    widget.on_widget_value_changed = types.MethodType(on_widget_value_changed, widget)
    widget.on_feat_value_changed = types.MethodType(on_feat_value_changed, widget)

    widget.valueChanged.connect(widget.on_widget_value_changed)


def connect(widget, target, feat_name=None, feat_key=None):
    """Connect a feature from a given driver to a widget.

    If applied two times with the same widget, it will connect to the target
    provided in the second call. This behaviour can be useful to change the
    connection target without rebuilding the whole UI. Alternative, after
    connect has been called the first time, widget will have a member
    `setTarget` that can be used to achieve the same thing.

    :param widget: widget instance.
    :param target: driver instance.
    :param feat_name: feature name. If None, connect using widget name.
    :param feat_key: TBD
    """

    if not isinstance(target, Driver):
        raise TypeError('Connect target must be an instance of Lantz.Driver, not {}'.format(target))

    if not feat_name:
        feat_name = widget.name()

    if hasattr(widget, '_feat_name') and widget._feat_name == feat_name:
        widget.setTarget(target)
        return

    widget._target = None # Will be populated later
    widget._feat_name = feat_name
    widget._feat_key = feat_key

    feat =  target._lantz_features[feat_name]
    widget._lantz_units = feat.units
    if isinstance(widget._lantz_units, str):
        widget._lantz_units = Q_(1, widget._lantz_units)

    widget._lantz_map = feat.map
    if isinstance(widget._lantz_map, dict):
        widget._lantz_map = list(widget._lantz_map.keys())

    widget._lantz_range = feat.range

    pimp(widget)

    widget.setReadOnly(feat.fset is None)
    target.on_changed[feat_name].append(widget.on_feat_value_changed)
    widget.setTarget(target)



class FeatWidget(object):

    def __init__(self, target, feat_name):

        self._target = target
        self._feat_name = feat_name

        self._label = QLabel()
        self._label.setText(feat_name)

        self._widget = get_widget(target._lantz_features[feat_name])()
        connect(self._widget, target, feat_name)

        self._get = QPushButton()
        self._get.setText('get')
        self._get.setEnabled(self.readable)
        self._get.setFixedWidth(60)

        self._set = QPushButton()
        self._set.setText('set')
        self._set.setEnabled(self.writable)
        self._set.setFixedWidth(60)

        self._get.clicked.connect(self.on_get_clicked)
        self._set.clicked.connect(self.on_set_clicked)
        self._widget._update_on_change = self.writable

        self.widgets = (self._label, self._widget, self._get, self._set)

    @property
    def readable(self):
        return self.target._lantz_features[self._feat_name].fget not in (None, MISSING)

    @property
    def writable(self):
        return self._target._lantz_features[self._feat_name].fset is not None

    @property
    def label_width(self):
        return self._label.width

    @label_width.setter
    def label_width(self, value):
        self._label.width = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, driver):
        self._target = driver  #TODO: try weak ref

    @Slot()
    def on_get_clicked(self):
        getattr(self._target, self._feat_name)

    @Slot()
    def on_set_clicked(self):
        font = QFont()
        font.setItalic(False)
        self._widget.setFont(font)
        setattr(self._target, self._feat_name, self._widget.value())


class UnitInputDialog(QDialog):

    def __init__(self, units, parent=None):
        super().__init__(parent)
        self.setupUi(parent)
        self.units = units
        self.source_units.setText(str(units))

    def setupUi(self, parent):
        self.resize(275, 172)
        self.setWindowTitle('Convert units')
        self.layout = QVBoxLayout(parent)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        align = (Qt.AlignRight | Qt.AlignTrailing |
                 Qt.AlignVCenter)

        self.layout1 = QHBoxLayout()
        self.label1 = QLabel()
        self.label1.setMinimumSize(QSize(100, 0))
        self.label1.setText('Convert from:')
        self.label1.setAlignment(align)

        self.layout1.addWidget(self.label1)
        self.source_units = QLineEdit()
        self.source_units.setReadOnly(True)
        self.layout1.addWidget(self.source_units)

        self.layout.addLayout(self.layout1)

        self.layout2 = QHBoxLayout()
        self.label2 = QLabel()
        self.label2.setMinimumSize(QSize(100, 0))
        self.label2.setText('to:')
        self.label2.setAlignment(align)
        self.layout2.addWidget(self.label2)

        self.destination_units = QLineEdit()
        self.layout2.addWidget(self.destination_units)

        self.layout.addLayout(self.layout2)

        self.message = QLabel()
        self.message.setText('')
        self.message.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.message)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        self.layout.addWidget(self.buttonBox)
        self.buttonBox.setEnabled(False)

        self.buttonBox.accepted.connect(self.accept)
        self.destination_units.textChanged.connect(self.check)

        self.setLayout(self.layout)
        self.destination_units.setFocus()

    def check(self):
        try:
            new_units = Q_(1, self.destination_units.text())
            factor = self.units.rescale(new_units).magnitude
        except LookupError:
            self.message.setText('Cannot parse units')
            self.buttonBox.setEnabled(False)
        except ValueError:
            self.message.setText('Incompatible units')
            self.buttonBox.setEnabled(False)
        else:
            self.message.setText('factor {:f}'.format(factor))
            self.buttonBox.setEnabled(True)

    @staticmethod
    def get_units(units):
        dialog = UnitInputDialog(Q_(1, units.units))
        if dialog.exec_():
            return dialog.destination_units.text()
        return None

