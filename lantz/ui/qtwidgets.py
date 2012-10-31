# -*- coding: utf-8 -*-
"""
    lantz.ui.qtwidgets
    ~~~~~~~~~~~~~~~~~~

    Implements UI widgets based on Qt widgets. To achieve functionality,
    instances of QtWidgets are patched.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import sys
import json
import inspect
import logging

try:
    from docutils import core as doc_core
except ImportError:
    class doc_core(object):

        @staticmethod
        def publish_parts(rst, *args, **kwargs):
            return rst

from Qt.QtCore import QVariant, Qt, QSize, Slot, Signal, Property
from Qt.QtGui import (QApplication, QDialog, QWidget, QFont, QSizePolicy,
                      QColor, QPalette, QToolTip, QMessageBox,
                      QLabel, QPushButton, QDialogButtonBox,
                      QLayout, QHBoxLayout, QVBoxLayout, QFormLayout, QFrame,
                      QTabWidget,
                      QLineEdit, QSpinBox, QDoubleSpinBox, QLCDNumber,
                      QDial, QProgressBar, QSlider, QScrollBar,
                      QComboBox, QCheckBox)

from .. import Q_, Driver
from ..feat import MISSING, DictFeat
from ..log import get_logger

QToolTip.setFont(QFont('SansSerif', 10))

logger = get_logger('lantz.ui', False)


def _rst_to_html(rst):
    """Convert rst docstring to HTML.
    """
    parts = doc_core.publish_parts(rst, writer_name="html")
    return parts['body']


def _params_doc(rst):
    """Extract
    """
    if not rst:
        return ''
    docs = {}
    rst = ' '.join(rst.splitlines())
    key = None
    for line in rst.split(':'):
        line = line.strip()
        if key:
            docs[key] = line.strip()
            key = None
        else:
            for prefix in ('param', 'parameter', 'arg', 'argument', 'key', 'keyword'):
                if line.startswith(prefix):
                    key = line[len(prefix):].strip()
                    break

    return docs


def register_wrapper(cls):
    """Register a class as lantz wrapper for QWidget subclasses.

    The class must contain a field (_WRAPPERS) with a tuple of the
    QWidget subclasses that it wraps.
    """
    for wrapped in cls._WRAPPED:
        if wrapped in cls._WRAPPERS:
            logger.warn('{} is already registered to {}.'.format(wrapped, cls._WRAPPERS[wrapped]))
        cls._WRAPPERS[wrapped] = type(wrapped.__class__.__name__ + 'Wrapped',
                                      (cls, wrapped), {})

    return cls


@register_wrapper
class WidgetMixin(object):
    """Mixin class to provide extra functionality to QWidget derived controls.

    Derived class must override _WRAPPED to indicate with which classes it
    can be mixed.

    To wrap an existing widget object use::

    >>> widget = QComboBox()
    >>> WidgetMixin.wrap(widget)

    If you want lantz to provide an appropriate wrapped widget for a given feat::

    >>> widget = WidgetMixin.from_feat(feat)

    In any case, after wrapping a widget you need to bind it to a feat::

    >>> feat = driver.feats[feat_name]
    >>> widget.bind_feat(feat)

    Finally, you need to

    >>> widget.lantz_target = driver

    """

    _WRAPPED = (QWidget, )

    #: Dictionary linking Widget types with the function to patch them
    _WRAPPERS = {}

    def keyPressEvent(self, event):
        """When 'u' is pressed, request new units.
        When 'r' is pressed, get new value from the driver.
        """
        super().keyPressEvent(event)

        if event.text() == 'r':
            # This should also trigger a widget update if necessary.
            self.value_from_feat()

    def value(self):
        """Get widget value.
        """
        return super().value()

    def setValue(self, value):
        """Set widget value.
        """
        if value is MISSING:
            return
        super().setValue(value)

    def setReadOnly(self, value):
        """Set read only s
        """
        super().setReadOnly(value)

    def value_from_feat(self):
        """Update the widget value with the current Feat value of the driver.
        """
        if self._feat is None or self._lantz_target is None:
            return

        self._feat.get(self._lantz_target, key=self._feat_key)

    def value_to_feat(self):
        """Update the Feat value of the driver with the widget value.
        """
        if self._feat is None or self._lantz_target is None:
            return

        self._feat.set(self._lantz_target, value=self.value(), key=self._feat_key)

    @property
    def readable(self):
        """If the Feat associated with the widget can be read (get).
        """
        if self._feat is None:
            return False
        return self._feat.fget not in (None, MISSING)

    @property
    def writable(self):
        """If the Feat associated with the widget can be written (set).
        """
        if self._feat is None:
            return False
        return self._feat.fset is not None

    @Slot(QVariant)
    def on_widget_value_changed(self, value, old_value=MISSING, other=MISSING):
        """When the widget is changed by the user, update the driver with
        the new value.
        """
        if self._update_on_change:
            self.value_to_feat()

    def on_feat_value_changed(self, value, old_value=MISSING, other=MISSING):
        """When the driver value is changed, update the widget if necessary.
        """
        if self.value() != value:
           self.setValue(value)

    @property
    def feat_key(self):
        """Key associated with the DictFeat.
        """
        return self._feat_key

    @feat_key.setter
    def feat_key(self, value):
        if self._lantz_target:
            getattr(self._lantz_target, self._feat.name + '_changed').disconnect(self.on_feat_value_changed)
            self._lantz_target.del_on_changed(self._feat.name, self.on_feat_value_changed, self._feat_key)
        self._feat_key = value
        if self._lantz_target:
            getattr(self._lantz_target, self._feat.name + '_changed').connect(self.on_feat_value_changed)
            #self._lantz_target.add_on_changed(self._feat.name, self.on_feat_value_changed, self._feat_key)
        self.value_from_feat()

    @property
    def lantz_target(self):
        """Driver connected to the widget.
        """
        return self._lantz_target

    @lantz_target.setter
    def lantz_target(self, target):
        if self._lantz_target:
            getattr(self._lantz_target, self._feat.name + '_changed').disconnect(self.on_feat_value_changed)
            #self._lantz_target.del_on_changed(self._feat.name, self.on_feat_value_changed, self._feat_key)
            self.valueChanged.disconnect()
        if target:
            self._lantz_target = target
            getattr(self._lantz_target, self._feat.name + '_changed').connect(self.on_feat_value_changed)
            #self._lantz_target.add_on_changed(self._feat.name, self.on_feat_value_changed, self._feat_key)
            #if feat_key is MISSING:
            #    self.on_feat_value_changed(self._lantz_target.recall(self._feat.name))
            #else:
            #    self.on_feat_value_changed(self._lantz_target.recall(self._feat.name)[self._feat_key])
            self.value_from_feat()
            self.valueChanged.connect(self.on_widget_value_changed)

    def bind_feat(self, feat):
        self._feat = feat
        try:
            keys = feat.keys
        except:
            keys = None

        if keys:
            self._feat_key = keys[0]
        else:
            self._feat_key = MISSING
        self.setReadOnly(not self.writable)

    @classmethod
    def _wrap(cls, widget):
        ChildrenWidgets.patch(widget)
        widget._lantz_target = None
        widget._feat = None
        widget._update_on_change = True
        widget.__class__ =  cls
        widget._lantz_wrapped = True

    @classmethod
    def wrap(cls, widget):
        if hasattr(widget, '_lantz_wrapped'):
            return
        cls._WRAPPERS.get(type(widget), cls)._wrap(widget)


    @classmethod
    def from_feat(cls, feat, parent=None):
        """Return a widget appropriate to represent a lantz feature.

        :param feat: a lantz feature proxy, the result of inst.feats[feat_name].
        :param parent: parent widget.
        """

        if feat.values:
            if isinstance(feat.values, dict):
                tmp = set(feat.values.keys())
            else:
                tmp = set(feat.values)

            if tmp == {True, False}:
                widget = QCheckBox
            else:
                widget = QComboBox
        elif not feat.units is None or feat.limits:
            widget = QDoubleSpinBox
        else:
            widget= QLineEdit

        widget = widget(parent)
        cls.wrap(widget)

        return widget


class FeatWidget(object):
    """Widget to show a Feat.

    :param parent: parent widget.
    :param target: driver object to connect.
    :param feat: Feat to connect.
    """

    def __new__(cls, parent, target, feat):
        widget = WidgetMixin.from_feat(feat, parent)
        widget.bind_feat(feat)
        widget.lanz_target = target
        return widget


class DictFeatWidget(QWidget):
    """Widget to show a DictFeat.

    :param parent: parent widget.
    :param target: driver object to connect.
    :param feat: DictFeat to connect.
    """

    def __init__(self, parent, target, feat):
        super().__init__(parent)
        self._feat = feat

        layout = QHBoxLayout(self)

        if feat.keys:
            wid = QComboBox()
            if isinstance(feat.keys, dict):
                self._keys = list(feat.keys.keys())
            else:
                self._keys = list(feat.keys)

            wid.addItems([str(key) for key in self._keys])
            wid.currentIndexChanged.connect(self._combobox_changed)
        else:
            wid = QLineEdit()
            wid.textChanged.connect(self._lineedit_changed)

        layout.addWidget(wid)
        self._key_widget = wid

        wid = WidgetMixin.from_feat(feat)
        wid.bind_feat(feat)
        wid.feat_key = self._keys[0]
        wid.lantz_target = target
        layout.addWidget(wid)
        self._value_widget = wid

    @Slot(QVariant)
    def _combobox_changed(self, value, old_value=MISSING, other=MISSING):
        self._value_widget.feat_key = self._keys[self._key_widget.currentIndex()]

    @Slot(QVariant)
    def _lineedit_changed(self, value, old_value=MISSING, other=MISSING):
        self._value_widget.feat_key = self._key_widget.text()

    def value(self):
        """Get widget value.
        """
        return self._value_widget.value()

    def setValue(self, value):
        """Set widget value.
        """
        if value is MISSING:
            return
        self._value_widget.setValue(value)

    def setReadOnly(self, value):
        """Set read only s
        """
        self._value_widget.setReadOnly(value)

    @property
    def lantz_target(self):
        """Driver connected to this widget.
        """
        return self._value_widget._lantz_target

    @lantz_target.setter
    def lantz_target(self, driver):
        self._value_widget._lantz_target = driver

    @property
    def readable(self):
        """If the Feat associated with the widget can be read (get).
        """
        return self._value_widget.readable

    @property
    def writable(self):
        """If the Feat associated with the widget can be written (set).
        """
        return self._value_widget.writable

    def value_from_feat(self):
        return self._value_widget.value_from_feat()


class LabeledFeatWidget(QWidget):
    """Widget containing a label, a control, and a get a set button.

    :param parent: parent widget.
    :param target: driver object to connect.
    :param feat: Feat to connect.
    """

    def __init__(self, parent, target, feat):
        super().__init__(parent)
        layout = QHBoxLayout(self)

        self._label = QLabel()
        self._label.setText(feat.name)
        self._label.setFixedWidth(120)
        self._label.setToolTip(_rst_to_html(feat.__doc__))
        layout.addWidget(self._label)

        if isinstance(feat, DictFeat):
            self._widget = DictFeatWidget(parent, target, feat)
        else:
            self._widget = WidgetMixin.from_feat(feat)
            self._widget.bind_feat(feat)
            self._widget.lantz_target = target

        layout.addWidget(self._widget)

        self._get = QPushButton()
        self._get.setText('get')
        self._get.setEnabled(self._widget.readable)
        self._get.setFixedWidth(60)
        layout.addWidget(self._get)

        self._set = QPushButton()
        self._set.setText('set')
        self._set.setEnabled(self._widget.writable)
        self._set.setFixedWidth(60)
        layout.addWidget(self._set)

        self._get.clicked.connect(self.on_get_clicked)
        self._set.clicked.connect(self.on_set_clicked)
        self._widget._update_on_change = self._widget.writable

        self.widgets = (self._label, self._widget, self._get, self._set)

    @property
    def label_width(self):
        """Width of the label
        """
        return self._label.width

    @label_width.setter
    def label_width(self, value):
        self._label.setFixedWidth(value)

    @property
    def lantz_target(self):
        """Driver connected to this widget.
        """
        return self._widget._lantz_target

    @lantz_target.setter
    def lantz_target(self, driver):
        self._widget._lantz_target = driver

    @Slot()
    def on_get_clicked(self):
        self._widget.value_from_feat()

    @Slot()
    def on_set_clicked(self):
        font = QFont()
        font.setItalic(False)
        self._widget.setFont(font)
        self._widget.value_to_feat()

    @property
    def readable(self):
        """If the Feat associated with the widget can be read (get).
        """
        return self._widget.readable

    @property
    def writable(self):
        """If the Feat associated with the widget can be written (set).
        """
        return self._widget.writable


class DriverTestWidget(QWidget):
    """Widget that is automatically filled to control all Feats of a given driver.

    :param parent: parent widget.
    :param target: driver object to map.
    """

    def __init__(self, parent, target):
        super().__init__(parent)
        self._lantz_target = target

        layout = QVBoxLayout(self)

        label = QLabel()
        label.setText(str(target))
        layout.addWidget(label)

        recall = QPushButton()
        recall.setText('Refresh')
        recall.clicked.connect(lambda x: target.refresh())

        update = QPushButton()
        update.setText('Update')
        update.clicked.connect(lambda x: target.update(self.widgets_values_as_dict()))

        auto = QCheckBox()
        auto.setText('Update on change')
        auto.setChecked(True)
        auto.stateChanged.connect(self.update_on_change)

        hlayout = QHBoxLayout()
        hlayout.addWidget(recall)
        hlayout.addWidget(update)
        hlayout.addWidget(auto)

        layout.addLayout(hlayout)

        self.writable_widgets = []
        self.widgets = []

        # Feat
        for feat_name, feat in sorted(target.feats.items()):
            try:
                feat_widget = LabeledFeatWidget(self, target, feat)

                self.widgets.append(feat_widget)
                if feat_widget.writable:
                    self.writable_widgets.append(feat_widget)

                layout.addWidget(feat_widget)
            except Exception as ex:
                logger.debug('Could not create control for {}: {}'.format(feat_name, ex))
                #import traceback
                #traceback.print_exc()

        # Actions
        line = QFrame(self)
        #self.line.setGeometry(QtCore.QRect(110, 80, 351, 31))
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)


        actions_label = QLabel(self)
        actions_label.setText('Actions:')
        actions_label.setFixedWidth(120)

        self.actions_combo = QComboBox(self)
        self.actions_combo.addItems(list(target.actions.keys()))

        actions_button = QPushButton(self)
        actions_button.setFixedWidth(60)
        actions_button.setText('Run')
        actions_button.clicked.connect(self.on_run_clicked)

        alayout = QHBoxLayout()
        alayout.addWidget(actions_label)
        alayout.addWidget(self.actions_combo)
        alayout.addWidget(actions_button)

        layout.addLayout(alayout)

    @Slot(QVariant)
    def on_run_clicked(self):
        ArgumentsInputDialog.run(getattr(self._lantz_target, self.actions_combo.currentText()), self)

    def update_on_change(self, new_state):
        """Set the 'update_on_change' flag to new_state in each writable widget
        within this widget. If True, the driver will be updated after each change.
        """

        for widget in self.writable_widgets:
            widget._widget._update_on_change = new_state

    def widgets_values_as_dict(self):
        """Return a dictionary mapping each writable feat name to the current
        value of the widget.
        """
        return {widget._feat.name: widget._widget.value()
                for widget in self.writable_widgets}

    @property
    def lantz_target(self):
        """Driver connected to this widget.
        """
        return self._lantz_target

    @lantz_target.setter
    def lantz_target(self, driver):
        self._lantz_target = driver
        for widget in self.widgets:
            widget.lantz_target = driver


class SetupTestWidget(QWidget):
    """Widget to control multiple drivers.

    :param parent: parent widget.
    :param targets: iterable of driver object to map.
    """

    def __init__(self, parent, targets):
        super().__init__(parent)

        layout = QHBoxLayout(self)

        tab_widget = QTabWidget(self)
        tab_widget.setTabsClosable(False)
        for target in targets:
            widget = DriverTestWidget(parent, target)
            tab_widget.addTab(widget, target.name)

        layout.addWidget(tab_widget)


def connect_feat(widget, target, feat_name=None, feat_key=MISSING):
    """Connect a feature from a given driver to a widget. Calling this
    function also patches the widget is necessary.

    If applied two times with the same widget, it will connect to the target
    provided in the second call. This behaviour can be useful to change the
    connection target without rebuilding the whole UI. Alternative, after
    connect has been called the first time, widget will have a property
    `lantz_target` that can be used to achieve the same thing.

    :param widget: widget instance.
    :param target: driver instance.
    :param feat_name: feature name. If None, connect using widget name.
    :param feat_key: For a DictFeat, this defines which key to show.
    """

    logger.debug('Connecting {} to {}, {}, {}'.format(widget, target, feat_name, feat_key))

    if not isinstance(target, Driver):
        raise TypeError('Connect target must be an instance of lantz.Driver, not {}'.format(target))

    if not feat_name:
        feat_name = widget.objectName()

    #: Reconnect
    if hasattr(widget, '_feat.name') and widget._feat.name == feat_name:
        widget.lantz_target = target
        return

    feat =  target.feats[feat_name]

    WidgetMixin.wrap(widget)
    widget.bind_feat(feat)
    widget.feat_key = feat_key

    widget.lantz_target = target


def connect_driver(parent, target, *, prefix='', sep='__'):
    """Connect all children widgets to their corresponding lantz feature
    matching by name. Non-matching names are ignored.

    :param parent: parent widget.
    :param target: the driver.
    :param prefix: prefix to be prepended to the lantz feature (default = '')
    :param sep: separator between prefix, name and suffix
    """

    logger.debug('Connecting {} to {}, {}, {}'.format(parent, target, prefix, sep))

    ChildrenWidgets.patch(parent)

    if prefix:
        prefix += sep

    for name, _, wid in parent.widgets:
        if prefix and name.startswith(prefix):
            name = name[len(prefix):]
        if sep in name:
            name, _ = name.split(sep, 1)
        if name in target.feats:
            connect_feat(wid, target, name)


def connect_setup(parent, targets, *, prefix=None, sep='__'):
    """Connect all children widget to their corresponding

    :param parent: parent widget.
    :param targets: iterable of drivers.
    :param prefix: prefix to be prepended to the lantz feature name
                   if None, the driver name will be used (default)
                   if it is a dict, the driver name will be used to obtain
                   he prefix.
    """

    logger.debug('Connecting {} to {}, {}, {}'.format(parent, targets, prefix, sep))

    ChildrenWidgets.patch(parent)
    for target in targets:
        name = target.name
        if isinstance(prefix, dict):
            name = prefix[name]
        connect_driver(parent, target, prefix=name, sep=sep)


def start_test_app(target, width=500, *args):
    """Start a single window test application with a form automatically
    generated for the driver.

    :param target: a driver object or a collection of drivers.
    :param width: to be used as minimum width of the window.
    :param args: arguments to be passed to QApplication.
    """
    app = QApplication(list(args))
    if isinstance(target, Driver):
        main = DriverTestWidget(None, target)
    else:
        main = SetupTestWidget(None, target)
    main.setMinimumWidth(width)
    main.setWindowTitle('Lantz Driver Test Panel')
    main.show()
    if sys.platform.startswith('darwin'):
        main.raise_()
    app.exec_()


class ChildrenWidgets(object):
    """Convenience class to iterate children.

    :param parent: parent widget.
    """

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, item):
        return self.parent.findChild((QWidget, ), item)

    def __iter__(self):
        pending = [self.parent, ]
        qualname = {self.parent: self.parent.objectName()}
        while pending:
            object = pending.pop()
            for child in object.children():
                if not isinstance(child, QWidget):
                    continue
                qualname[child] = qualname[object] + '.' + child.objectName()
                pending.append(child)
                yield child.objectName(), qualname[child], child

    @classmethod
    def patch(cls, parent):
        if not hasattr(parent, 'widgets'):
            parent.widgets = cls(parent)


def request_new_units(current_units):
    """Ask for new units using a dialog box and return them.

    :param current_units: current units or magnitude.
    :type current_units: Quantity

    """
    new_units = UnitInputDialog.get_units(current_units)
    if new_units is None:
        return None

    try:
        return Q_(1, new_units)
    except LookupError:
        # cannot parse units
        return None


@register_wrapper
class MagnitudeMixin(WidgetMixin):

    _WRAPPED = (QDoubleSpinBox, )

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if self._units and event.text() == 'u':
            self.change_units(request_new_units(self.value()))

    def bind_feat(self, feat):
        super().bind_feat(feat)

        #: self._units are the current units displayed by the widget.
        #: Respects units declared in the suffix

        if feat.units:
            suf = (self.suffix() if hasattr(self, 'suffix') else feat.units) or feat.units
            self._units = Q_(1, suf)
            self.change_units(self._units)
        else:
            self._units = None
            if feat.limits:
                self.change_limits(None)

    def change_units(self, new_units):
        """Update displayed suffix and stored units.
        """
        if new_units is None:
            return
        try:
            rescaled = self.value().to(new_units)
        except ValueError:
            # incompatible units
            return None
        else:
            if hasattr(self, 'setSuffix'):
               self.setSuffix(' ' + str(new_units.units))

            self.change_limits(new_units)
            self._units = new_units

            self.setValue(rescaled)

    def change_limits(self, new_units):
        """Change the limits (range) of the control taking the original values
        from the feat and scaling them to the new_units.
        """
        if not hasattr(self, 'setRange'):
            return

        rng = self._feat.limits or (float('-inf'), float('+inf'))
        if new_units:
            conv = lambda ndx: Q_(rng[ndx], self._feat.units).to(new_units).magnitude
        else:
            conv = lambda ndx: rng[ndx]

        if len(rng) == 1:
            self.setRange(0, conv(0))
        else:
            self.setRange(conv(0), conv(1))
            if len(rng) == 3:
                self.setSingleStep(conv(2))

    def value(self):
        """Get widget value and scale by units.
        """
        if self._units:
            return super().value() * self._units
        return super().value()

    def setValue(self, value):
        """Set widget value scaled by units.
        """
        if value is MISSING:
            font = QFont()
            font.setItalic(True)
            self.setFont(font)
        elif isinstance(value, Q_):
            super().setValue(value.to(self._units).magnitude)
        else:
            super().setValue(value)


@register_wrapper
class SliderMixin(MagnitudeMixin):

    _WRAPPED = (QSlider, QDial, QProgressBar, QScrollBar)

    def setReadOnly(self, value):
        super().setEnabled(not value)


@register_wrapper
class LCDNumberMixin(MagnitudeMixin):

    _WRAPPED = (QLCDNumber, )

    @classmethod
    def _wrap(cls, widget):
        super()._wrap(widget)
        #TODO: Create a real valueChanged Signal.
        widget.valueChanged = widget.overflow

    def setReadOnly(self, value):
        super().setEnabled(not value)

    def setValue(self, value):
        if value is MISSING:
            font = QFont()
            font.setItalic(True)
            self.setFont(font)
            return
        elif isinstance(value, Q_):
            super().display(value.to(self._units).magnitude)
        else:
            super().display(value)

    def value(self):
        return super().value()


@register_wrapper
class QComboBoxMixin(WidgetMixin):

    _WRAPPED = (QComboBox, )

    @classmethod
    def _wrap(cls, widget):
        super()._wrap(widget)
        widget.valueChanged = widget.currentIndexChanged

    def value(self):
        return self.currentText()

    def setValue(self, value):
        if value is MISSING:
            font = QFont()
            font.setItalic(True)
            self.setFont(font)
            return
        self.setCurrentIndex(self.__values.index(value))

    def setReadOnly(self, value):
        self.setEnabled(not value)

    def bind_feat(self, feat):
        super().bind_feat(feat)
        if isinstance(self._feat.values, dict):
            self.__values = list(self._feat.values.keys())
        else:
            self.__values = list(self.__values)
        self.clear()
        self.addItems([str(value) for value in self.__values])


@register_wrapper
class QCheckBoxMixin(WidgetMixin):

    _WRAPPED = (QCheckBox, )

    @classmethod
    def _wrap(cls, widget):
        super()._wrap(widget)
        widget.valueChanged = widget.stateChanged

    def setReadOnly(self, value):
        self.setCheckable(not value)

    def value(self):
        return self.isChecked()

    def setValue(self, value):
        if value is MISSING:
            return
        self.setChecked(value)


@register_wrapper
class QLineEditMixin(WidgetMixin):

    _WRAPPED = (QLineEdit, )

    @classmethod
    def _wrap(cls, widget):
        super()._wrap(widget)
        widget.valueChanged = widget.textChanged

    def value(self):
        return self.text()

    def setValue(self, value):
        if value is MISSING:
            return
        return self.setText(value)


class ArgumentsInputDialog(QDialog):

    def __init__(self, argspec, parent=None, window_title='Function arguments', doc=None):
        super().__init__(parent)

        vlayout = QVBoxLayout(self)

        layout = QFormLayout()

        widgets = []

        defaults = argspec.defaults if argspec.defaults else ()
        defaults = ('', ) * (len(argspec.args[1:]) - len(defaults)) + defaults

        self.arguments = {}
        for arg, default in zip(argspec.args[1:], defaults):
            wid = QLineEdit(self)
            wid.setObjectName(arg)
            wid.setText(json.dumps(default))
            self.arguments[arg] = default

            layout.addRow(arg, wid)
            widgets.append(wid)
            wid.textChanged.connect(self.on_widget_change(wid))
            if doc and arg in doc:
                wid.setToolTip(doc[arg])


        self.widgets = widgets

        buttonBox = QDialogButtonBox()
        buttonBox.setOrientation(Qt.Horizontal)
        buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        buttonBox.setEnabled(True)
        buttonBox.accepted.connect(self.accept)

        vlayout.addLayout(layout)

        label = QLabel()
        label.setText('Values are decoded from text using as JSON.')
        vlayout.addWidget(label)

        vlayout.addWidget(buttonBox)

        self.buttonBox = buttonBox
        self.valid = {wid.objectName(): True for wid in self.widgets}

        self.setWindowTitle(window_title)


    def on_widget_change(self, widget):
        name = widget.objectName()
        def validate(value):
            try:
                if value:
                    value = json.loads(value)
                else:
                    value = None
                palette = QPalette()
                palette.setColor(widget.backgroundRole(), QColor('white'))
                widget.setPalette(palette)
                self.arguments[name] = value
                self.valid[name] = True
            except:
                palette = QPalette()
                palette.setColor(widget.backgroundRole(), QColor(255, 102, 102))
                widget.setPalette(palette)
                self.valid[name] = False

            self.buttonBox.setEnabled(all(self.valid.values()))

        return validate

    def accept(self):
        super().accept()

    @staticmethod
    def run(func, parent=None):
        """Creates and display a UnitInputDialog and return new units.

        Return None if the user cancelled.

        """

        wrapped = getattr(func, '__wrapped__', func)
        name = wrapped.__name__
        doc = wrapped.__doc__
        argspec = inspect.getargspec(wrapped)

        arguments = {}
        if len(argspec.args) > 1:
            dialog = ArgumentsInputDialog(argspec, parent,
                                          window_title=name+ ' arguments',
                                          doc=_params_doc(doc))
            if not dialog.exec_():
                return None
            arguments = dialog.arguments

        try:
            func(**arguments)
        except Exception as e:
            logger.exception(e)
            QMessageBox.critical(parent, 'Lantz',
                                 'Instrument error while calling {}'.format(name),
                                 QMessageBox.Ok,
                                 QMessageBox.NoButton)


class UnitInputDialog(QDialog):
    """Dialog to select new units. Checks compatibility while typing
    and does not allow to continue if incompatible.

    Returns None if cancelled.

    :param units: current units.
    :param parent: parent widget.

    >>> new_units = UnitInputDialog.get_units('ms')
    """

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
        align = (Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)

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
        units = self.destination_units.text().strip()
        if not units:
            return
        try:
            new_units = Q_(1, units)
            factor = self.units.to(new_units).magnitude
        except LookupError or SyntaxError:
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
        """Creates and display a UnitInputDialog and return new units.

        Return None if the user cancelled.

        """
        dialog = UnitInputDialog(Q_(1, units.units))
        if dialog.exec_():
            return dialog.destination_units.text()
        return None
