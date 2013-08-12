

from lantz import Feat
from lantz.drivers.usbtmc import USBTMCDriver


class TDS1002b(USBTMCDriver):

    def __init__(self, serial_number=None, **kwargs):
        super().__init__(1689, 867, serial_number, **kwargs)

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')
