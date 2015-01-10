# -*- coding: utf-8 -*-
"""
    lantz.ui.scan
    ~~~~~~~~~~~~~

    A Scan frontend and Backend. Requires scan.ui

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


import time
import math
from enum import IntEnum

from lantz.utils.qt import QtCore, QtGui
from lantz.ui.app import Frontend, Backend, start_gui_app


def _linspace_args(start, stop, step_size=None, length=None):
    """Return the step_size and length for a given linspace
    where step_size OR length is defined.
    """

    if step_size is None:
        if length is None:
            length = 10
        step_size = (stop - start) / (length + 1)
    else:
        if length is not None:
            raise ValueError('step_size and length cannot be both different from None')
        length = math.floor((stop - start) / step_size) + 1

    return step_size, length


def _linspace(start, stop, step_size=None, length=None):
    """Yield a linear spacing from start to stop
    with defined step_size OR length.
    """

    step_size, length = _linspace_args(start, stop, step_size, length)

    for i in range(length):
        yield start + i * step_size


class StepsMode(IntEnum):
    """Step calculation modes.
    """

    #: fixed step size.
    step_size = 0

    #: fixed step count.
    step_count = 1


class Scan(Backend):
    """A backend that iterates over an list of values,
    calling a `body` function in each step.
    """

    #: Signal emitted before starting a new iteration
    #: Parameters: loop counter, step value, overrun
    iteration = QtCore.Signal(int, int, bool)

    #: Signal emitted when the loop finished.
    #: The parameter is used to inform if the loop was canceled.
    loop_done = QtCore.Signal(bool)

    #: The function to be called. It requires three parameters.
    #:    counter - the iteration number.
    #:    current value - the current value of the scan.
    #:    overrun - a boolean indicating if the time required for the operation
    #:             is longer than the interval.
    #: :type: (int, int, bool) -> None
    body = None

    #: To be called before the body. Same signature as body
    _pre_body = None

    #: To be called after the body. Same signature as body
    _post_body = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active = False
        self._internal_func = None

    def stop(self):
        """Request the scanning to be stop.
        Will stop when the current iteration is finished.
        """
        self._active = False

    def start(self, body, interval=0, steps=(), timeout=0):
        """Request the scanning to be started.

        :param body: function to be called at each iteration.
                     If None, the class body will be used.
        :param interval: interval between starts of the iteration.
                         If the body takes too long, the iteration will
                         be as fast as possible and the overrun flag will be True
        :param steps: iterable
        :param timeout: total time in seconds that the scanning will take.
                        If overdue, the scanning will be stopped.
                        If 0, there is no timeout.
        """
        self._active = True
        body = body or self.body

        iterations = len(steps)

        def internal(counter, overrun=False, schedule=QtCore.QTimer.singleShot):
            if not self._active:
                self.loop_done.emit(True)
                return

            st = time.time()
            self.iteration.emit(counter, iterations, overrun)
            if self._pre_body is not None:
                self._pre_body(counter, steps[counter], overrun)
            if body is not None:
                body(counter, steps[counter], overrun)
            if self._post_body is not None:
                self._post_body(counter, steps[counter], overrun)

            if iterations and counter + 1 == iterations:
                self._active = False
                self.loop_done.emit(False)
                return
            elif not self._active:
                self.loop_done.emit(True)
                return

            sleep = interval - (time.time() - st)
            schedule(sleep * 1000 if sleep > 0 else 0,
                     lambda: self._internal_func(counter + 1, sleep < 0))

        self._internal_func = internal
        if timeout:
            QtCore.QTimer.singleShot(timeout * 1000, self.stop)
        QtCore.QTimer.singleShot(0, lambda: self._internal_func(0))


class ScanUi(Frontend):
    """A frontend to the Scan backend.

    Allows you to create linear sequence of steps between a start a stop,
    with selectable step size or number of steps.
    """

    gui = 'scan.ui'

    auto_connect = False

    #: Signal emitted when a start is requested.
    #: The parameters are None, interval, vector of steps
    request_start = QtCore.Signal(object, object, object)

    #: Signal emitted when a stop is requested.
    request_stop = QtCore.Signal()

    def connect_backend(self):
        super().connect_backend()

        self.widget.start_stop.clicked.connect(self.on_start_stop_clicked)
        self.widget.mode.currentIndexChanged.connect(self.on_mode_changed)

        self.widget.step_count.valueChanged.connect(self.recalculate)
        self.widget.start.valueChanged.connect(self.recalculate)
        self.widget.stop.valueChanged.connect(self.recalculate)
        self.widget.step_size.valueChanged.connect(self.recalculate)

        self.widget.progress_bar.setValue(0)

        self._ok_palette = QtGui.QPalette(self.widget.progress_bar.palette())
        self._overrun_palette = QtGui.QPalette(self.widget.progress_bar.palette())
        self._overrun_palette.setColor(QtGui.QPalette.Highlight,
                                       QtGui.QColor(QtCore.Qt.red))

        self.backend.iteration.connect(self.on_iteration)
        self.backend.loop_done.connect(self.on_loop_done)

        self.request_start.connect(self.backend.start)
        self.request_stop.connect(self.backend.stop)

    def on_start_stop_clicked(self, value=None):
        if self.backend._active:
            self.widget.start_stop.setText('...')
            self.widget.start_stop.setEnabled(False)
            self.request_stop.emit()
            return

        self.widget.start_stop.setText('Stop')
        self.widget.start_stop.setChecked(True)

        vals = [getattr(self.widget, name).value()
                for name in 'start stop step_size step_count wait'.split()]
        start, stop, step_size, step_count, interval = vals

        steps = list(_linspace(start, stop, step_size))

        self.request_start.emit(None, interval, steps)

    def recalculate(self, *args):
        mode = self.widget.mode.currentIndex()
        if mode == StepsMode.step_size:
            step_size, length = _linspace_args(self.widget.start.value(),
                                               self.widget.stop.value(),
                                               self.widget.step_size.value())
            self.widget.step_count.setValue(length)
        elif mode == StepsMode.step_count:
            step_size, length = _linspace_args(self.widget.start.value(),
                                               self.widget.stop.value(),
                                               length=self.widget.step_count.value())
            self.widget.step_size.setValue(step_size)

    def on_iteration(self, counter, iterations, overrun):
        pbar = self.widget.progress_bar

        if not counter:
            if iterations:
                pbar.setMaximum(iterations + 1)
            else:
                pbar.setMaximum(0)

        if iterations:
            pbar.setValue(counter + 1)

        if overrun:
            pbar.setPalette(self._overrun_palette)
        else:
            pbar.setPalette(self._ok_palette)

    def on_mode_changed(self, new_index):
        if new_index == StepsMode.step_size:
            self.widget.step_count.setEnabled(False)
            self.widget.step_size.setEnabled(True)
        elif new_index == StepsMode.step_count:
            self.widget.step_count.setEnabled(True)
            self.widget.step_size.setEnabled(False)

        self.recalculate()

    def on_loop_done(self, cancelled):
        self.widget.start_stop.setText('Start')
        self.widget.start_stop.setEnabled(True)
        self.widget.start_stop.setChecked(False)
        if self.widget.progress_bar.maximum():
            self.widget.progress_bar.setValue(self.widget.progress_bar.maximum())
        else:
            self.widget.progress_bar.setMaximum(1)


if __name__ == '__main__':
    def func(current, total, overrun):
        print('func', current, total, overrun)
    app = Scan()
    app.body = func
    start_gui_app(app, ScanUi)
