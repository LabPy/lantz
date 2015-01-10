# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.mpb.vfl
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Action, Feat
from lantz.drivers.legacy.serial import SerialDriver


class VFL(SerialDriver):
    """Driver for any VFL MPB Communications laser.
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\rD >'
    SEND_TERMINATION = '\r'

    BAUDRATE = 9600
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    @Feat(read_once=True)
    def idn(self):
        """Identification of the device
        """
        return self.query('GETMODEL')

    @Feat()
    def status(self):
        """Current device status
        """
        ans = self.query('shlaser')
        return ans.split('\r')

    # ENABLE LASER
    @Feat(values={True: '1', False: '0'})
    def enabled(self):
        """Method for turning on the laser
        """
        return self.query('GETLDENABLE')

    @enabled.setter
    def enabled(self, value):
        self.query('SETLDENABLE ' + value)

    # LASER'S CONTROL MODE AND SET POINT

    @Feat(values={'APC': '1', 'ACC': '0'})
    def ctl_mode(self):
        """To handle laser diode current (mA) in Active Current Control Mode
        """
        return self.query('GETPOWERENABLE')

    @ctl_mode.setter
    def ctl_mode(self, value):
        self.query('POWERENABLE {}'.format(value))

    @Feat(units='mA')
    def current_sp(self):
        """To handle laser diode current (mA) in Active Current Control Mode
        """
        return float(self.query('GETLDCUR 1'))

    @current_sp.setter
    def current_sp(self, value):
        self.query('SETLDCUR 1 {:.1f}'.format(value))

    @Feat(units='mW')
    def power_sp(self):
        """To handle output power set point (mW) in APC Mode
        """
        return float(self.query('GETPOWER 0'))

    @power_sp.setter
    def power_sp(self, value):
        self.query('SETPOWER 0 {:.0f}'.format(value))

    # LASER'S CURRENT STATUS

    @Feat(units='mW')
    def power(self):
        """To get the laser emission power (mW)
        """
        return float(self.query('POWER 0'))

    @Feat(units='mA')
    def ld_current(self):
        """To get the laser diode current (mA)
        """
        return float(self.query('LDCURRENT 1'))

    @Feat(units='degC')
    def ld_temp(self):
        """To get the laser diode temperature (ºC)
        """
        return float(self.query('LDTEMP 1'))

    @Feat(units='mA')
    def tec_current(self):
        """To get the thermoelectric cooler (TEC) current (mA)
        """
        return float(self.query('TECCURRENT 1'))

    @Feat(units='degC')
    def tec_temp(self):
        """To get the thermoelectric cooler (TEC) temperature (ºC)
        """
        return float(self.query('TECTEMP 1'))

    # SECOND HARMONIC GENERATOR METHODS

    @Feat(units='degC')
    def shg_temp_sp(self):
        """To handle the SHG temperature set point
        """
        return float(self.query('GETSHGTEMP'))

    @shg_temp_sp.setter
    def shg_temp_sp(self, value):
        self.query('GETSHGTEMP {:.2f}'.format(value))

    @Feat(units='degC')
    def shg_temp(self):
        """To get the SHG temperature
        """
        return float(self.query('SHGTEMP'))

    @Feat()
    def shg_tune_info(self):
        """Getting information about laser ready for SHG tuning
        """
        info = self.query('GETSHGTUNERDY').split()
        if info[0] == '0':
            ready = 'Laser not ready for SHG tuning. '
        else:
            ready = 'Laser ready for SHG tuning. '

        schedule = 'Next SHG tuning scheduled in {} '.format(info[1])
        schedule += 'hours of operation. '
        warm = 'Warm-up period expires in {} seconds.'.format(info[2])

        ans = ready + schedule + warm
        return ans

    @Feat()
    def shg_tuning(self):
        """Initiating SHG tuning
        """
        state = self.query('GETSHGTUNESTATE').split()
        tuning = error = ''

        if state[0] == '0':
            tuning = 'No SHG tuning performed since last reset. '
        elif state[0] == '3':
            tuning = 'SHG tuning in progress. '
        elif state[0] == '1':
            tuning = 'SHG tuning completed successfully. '
        elif state[0] == '2':
            tuning = 'SHG tuning aborted. '

        if state[1] == '0':
            error = 'No error detected.'
        elif state[1] == '1':
            error = 'Error: Laser not running in APC.'
        elif state[1] == '8':
            error = 'Error: Output Power not stabilized.'

        return tuning + error

    @Action()
    def tune_shg(self):
        self.query('SETSHGCMD 1')

    @Action()
    def tune_shg_stop(self):
        self.query('SETSHGCMD 2')

if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='COM3',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_screen(lantz.log.DEBUG)
    with VFL(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
            print(inst.idn)
            print(inst.shg_tuning)
