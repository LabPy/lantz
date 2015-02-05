# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.cobolt.cobolt0601
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Action, Feat
from lantz.drivers.legacy.serial import SerialDriver


class Cobolt0601(SerialDriver):
    """Driver for any Cobolt 06-01 Series laser.
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\r'
    SEND_TERMINATION = '\r'

    BAUDRATE = 115200
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    @Feat(read_once=True)
    def idn(self):
        """Get serial number
        """
        ans = self.query('gsn?')[1:]
        wavel = ans[:3]
        sn = ans[3:]
        return 'Cobolt ' + wavel + 'nm 06-01 Series, serial number ' + sn

    def initialize(self):
        super().initialize()
        self.mode = 'APC'
        self.ctl_mode = self.mode

    # ENABLE LASER METHODS

    @Feat(values={True: '1', False: '0'})
    def ksw_enabled(self):
        """Handling Key Switch enable state
        """
        ans = self.query('@cobasky?')
        return ans[1:]

    @ksw_enabled.setter
    def ksw_enabled(self, value):
        self.query('@cobasky ' + value)

    @Feat(values={True: '1', False: '0'})
    def enabled(self):
        """Method for turning on the laser. Requires autostart disabled.
        """
        ans = self.query('l?')
        return ans[-1]

    @enabled.setter
    def enabled(self, value):
        self.query('l' + value)

    @Feat(values={True: '1', False: '0'})
    def autostart(self):
        """Autostart handling
        """
        ans = self.query('@cobas?')
        return ans[-1]

    @autostart.setter
    def autostart(self, value):
        self.query('@cobas ' + value)

    @Action()
    def restart(self):
        """Forces the laser on without checking if autostart is enabled.
        """
        self.query('@cob1')

    # LASER INFORMATION METHODS
    @Feat()
    def operating_hours(self):
        """Get Laser Head operating hours
        """
        return self.query('hrs?')[1:]

    @Feat(values={'Interlock open': '1', 'OK': '0'})
    def interlock(self):
        """Get interlock state
        """
        return self.query('ilk?')[1:]

    # LASER'S CONTROL MODE AND SET POINT

    @Feat(values={'APC', 'ACC'})
    def ctl_mode(self):
        """To handle laser control modes
        """
        return self.mode

    @ctl_mode.setter
    def ctl_mode(self, value):
        if value == 'ACC':
            self.query('ci')
            self.mode = 'ACC'
        elif value == 'APC':
            self.mode = 'APC'
            self.query('cp')

    @Feat(units='mA')
    def current_sp(self):
        """Get drive current
        """
        return float(self.query('i?'))

    @current_sp.setter
    def current_sp(self, value):
        self.query('slc {:.1f}'.format(value))

    @Feat(units='mW')
    def power_sp(self):
        """To handle output power set point (mW) in constant power mode
        """
        return 1000 * float(self.query('p?'))

    @power_sp.setter
    def power_sp(self, value):
        self.query('p {:.5f}'.format(value / 1000))

    # LASER'S CURRENT STATUS

    @Feat(units='mW')
    def power(self):
        """Read output power
        """
        return 1000 * float(self.query('pa?'))

    @Feat(values={'Temperature error': '1', 'No errors': '0',
                  'Interlock error': '3', 'Constant power time out': '4'})
    def status(self):
        """Get operating fault
        """
        return self.query('f?')[1:]

    @Action()
    def clear_fault(self):
        """Clear fault
        """
        self.query('cf')

    # MODULATION MODES
    @Action()
    def enter_mod_mode(self):
        """Enter modulation mode
        """
        self.query('em')

    @Feat(values={True: '1', False: '0'})
    def digital_mod(self):
        """digital modulation enable state
        """
        return self.query('gdmes?')[1:]

    @digital_mod.setter
    def digital_mod(self, value):
        self.query('gdmes ' + value)

    @Feat(values={True: '1', False: '0'})
    def analog_mod(self):
        """analog modulation enable state
        """
        return self.query('games?')[1:]

    @analog_mod.setter
    def analog_mod(self, value):
        self.query('sames ' + value)

    @Feat(values={True: '1', False: '0'})
    def analogli_mod(self):
        """analog modulation enable state
        """
        return self.query('galis?')[1:]

    @analogli_mod.setter
    def analogli_mod(self, value):
        self.query('salis ' + value)

    @Feat(values={'Waiting for key': '1', 'Off': '0', 'Continuous': '2',
                  'On/Off Modulation': '3', 'Modulation': '4', 'Fault': '5',
                  'Aborted': '6'})
    def mod_mode(self):
        """Returns the current operating mode
        """
        return self.query('gom?')[1:]

if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='COM4',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_screen(lantz.log.DEBUG)
    with Cobolt0601(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
            print(inst.idn)
            print(inst.shg_tuning)
