# -*- coding: utf-8 -*-
"""
    lantz.ui.loop
    ~~~~~~~~~~~~~

    A Loop backend and frontend.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time
import math
from enum import IntEnum

from lantz.utils.qt import QtCore, QtGui
from lantz.ui.app import Frontend, Backend, start_gui_app


class StopMode(IntEnum):
    Continuous = 0
    Duration = 1
    Iterations = 2
    IterationsTimeOut = 3


class Loop(Backend):
    """The Loop backend allows you to execute task periodically.

    Usage:

        from lantz.ui.blocks import Loop, LoopUi

        def measure(counter, iterations, overrun):
            print(counter, iterations, overrun)
            data = osci.measure()
            print(data)

        app = Loop()

        app.body = measure

        start_gui_app(app, LoopUi)

    """

    #: Signal emitted before starting a new iteration
    #: Parameters: loop counter, iterations, overrun
    iteration = QtCore.Signal(int, int, bool)

    #: Signal emitted when the loop finished.
    #: The parameter is used to inform if the loop was canceled.
    loop_done = QtCore.Signal(bool)

    #: The function to be called. It requires three parameters.
    #:   counter - the iteration number
    #:   iterations - total number of iterations
    #:   overrun - a boolean indicating if the time required for the operation
    #:            is longer than the interval.
    #: :type: (int, int, bool) -> None
    body = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active = False
        self._internal_func = None

    def stop(self):
        """Request the scanning to be stop.
        Will stop when the current iteration is finished.
        """
        self._active = False

    def start(self, body, interval=0, iterations=0, timeout=0):
        """Request the scanning to be started.

        :param body: function to be called at each iteration.
                     If None, the class body will be used.
        :param interval: interval between starts of the iteration.
                         If the body takes too long, the iteration will
                         be as fast as possible and the overrun flag will be True
        :param iterations: number of iterations
        :param timeout: total time in seconds that the scanning will take.
                        If overdue, the scanning will be stopped.
                        If 0, there is no timeout.
        """
        self._active = True
        body = body or self.body

        def internal(counter, overrun=False, schedule=QtCore.QTimer.singleShot):
            if not self._active:
                self.loop_done.emit(True)
                return

            st = time.time()
            self.iteration.emit(counter, iterations, overrun)
            body(counter, iterations, overrun)

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


class LoopUi(Frontend):
    """The Loop frontend provides a GUI for the Rich Backend
    """

    gui = 'loop.ui'

    auto_connect = False

    #: Signal emitted when a start is requested.
    #: The parameters are None, interval, iterations, duration
    request_start = QtCore.Signal(object, object, object, object)

    #: Signal emitted when a stop is requested.
    request_stop = QtCore.Signal()

    def connect_backend(self):
        super().connect_backend()

        self.widget.start_stop.clicked.connect(self.on_start_stop_clicked)
        self.widget.mode.currentIndexChanged.connect(self.on_mode_changed)
        self.widget.iterations.valueChanged.connect(self.recalculate)
        self.widget.duration.valueChanged.connect(self.recalculate)
        self.widget.interval.valueChanged.connect(self.recalculate)
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

        mode = self.widget.mode.currentIndex()
        interval, iterations, duration = [getattr(self.widget, name).value()
                                          for name in 'interval iterations duration'.split()]
        if mode == StopMode.Continuous:
            self.request_start.emit(None, interval, 0, 0)
        elif mode == StopMode.Iterations:
            self.request_start.emit(None, interval, iterations, 0)
        elif mode == StopMode.Duration:
            self.request_start.emit(None, interval, 0, duration)
        elif mode == StopMode.IterationsTimeOut:
            self.request_start.emit(None, interval, iterations, duration)

    def recalculate(self, *args):
        mode = self.widget.mode.currentIndex()
        if mode == StopMode.Duration:
            iterations = self.widget.duration.value() / self.widget.interval.value()
            self.widget.iterations.setValue(math.ceil(iterations))
        elif mode == StopMode.Iterations:
            self.widget.duration.setValue(self.widget.iterations.value() * self.widget.interval.value())

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
        if new_index == StopMode.Continuous:
            self.widget.duration.setEnabled(False)
            self.widget.iterations.setEnabled(False)
        elif new_index == StopMode.Duration:
            self.widget.duration.setEnabled(True)
            self.widget.iterations.setEnabled(True)
            self.widget.duration.setReadOnly(False)
            self.widget.iterations.setReadOnly(True)
        elif new_index == StopMode.Iterations:
            self.widget.duration.setEnabled(True)
            self.widget.iterations.setEnabled(True)
            self.widget.duration.setReadOnly(True)
            self.widget.iterations.setReadOnly(False)
        elif new_index == StopMode.IterationsTimeOut:
            self.widget.duration.setEnabled(True)
            self.widget.iterations.setEnabled(True)
            self.widget.duration.setReadOnly(False)
            self.widget.iterations.setReadOnly(False)
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
    app = Loop()
    app.body = func
    start_gui_app(app, LoopUi)
