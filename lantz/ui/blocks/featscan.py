# -*- coding: utf-8 -*-
"""
    lantz.ui.featscan
    ~~~~~~~~~~~~~~~~~

    A Feat Scan frontend and Backend. Builds upon Scan.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz.utils.qt import QtCore
from lantz.ui.widgets import WidgetMixin
from lantz.ui.app import start_gui_app, InstrumentSlot

from lantz.ui.blocks import Scan, ScanUi


class FeatScan(Scan):
    """A backend to scan a feat for a given instrument.
    """

    #: Signal emitted before starting a new iteration
    #: Parameters: loop counter, step value, overrun
    iteration = QtCore.Signal(int, int, bool)

    #: Signal emitted when the loop finished.
    #: The parameter is used to inform if the loop was canceled.
    loop_done = QtCore.Signal(bool)

    instrument = InstrumentSlot

    #: Name of the scanned feat
    #: :type: str

    def __init__(self, feat_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feat_name = feat_name

    def _pre_body(self, counter, new_value, overrun):
        setattr(self.instrument, self.feat_name, new_value)

    @property
    def feat_units(self):
        """Units of the scanned feat.
        """
        target = self.instrument
        feat_name = self.feat_name
        feat = target.feats[feat_name]
        return str(feat.units)


class FeatScanUi(ScanUi):
    """A Frontend displaying scan parameters with appropriate units.
    """

    def connect_backend(self):
        target = self.backend.instrument
        feat_name = self.backend.feat_name

        feat = target.feats[feat_name]

        def _pimp(widget):
            WidgetMixin.wrap(widget)
            widget.bind_feat(feat)

        for name in 'start stop step_size'.split():
            _pimp(getattr(self.widget, name))

        if feat.limits and len(feat.limits) == 3:
            self.widget.step_size.setMinimum(feat.limits[2])
        else:
            self.widget.step_size.setMinimum(0)
        super().connect_backend()


if __name__ == '__main__':
    from lantz.drivers.examples import LantzSignalGenerator

    with LantzSignalGenerator('TCPIP::localhost::5678::SOCKET') as inst:
        app = FeatScan('frequency', fungen=inst)
        start_gui_app(app, FeatScanUi)
