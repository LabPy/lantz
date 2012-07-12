# -*- coding: utf-8 -*-
"""
    lantz.drivers.kentech.hri
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the driver for Kentech High Repetition Rate Image Intensifier
    revisions 1 and 2.


    Implementation Notes
    --------------------

    The set of commands is cumbersome and inconsistent. Moreover, each revision
    introduces backward incompatible changes. The Lantz driver abstracts those
    differences.

    Sources::

        - LaVision PicoStar HR12
        - HRI Commands obtained from Kentech
        - HRI.cl from DaVis
        - Lantz reverse engineering team


    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.

"""

from lantz import Feat, Action
from lantz.serial import SerialDriver
from lantz.errors import InstrumentError

def between(s, before, after):
    ndx1 = s.index(before)
    ndx2 = s.index(after)
    return s[ndx1+len(before):ndx2]


class HRI(SerialDriver):
    """Kentech High Repetition Rate Image Intensifier.
    """

    SEND_TERMINATION = '\r'
    RECV_TERMINATION = '\n'
    ENCODING = 'ascii'

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Send query to the instrument and return the answer.
        Set remote mode if needed.
        """
        if command and not self.recall('remote'):
            self.log_info('Setting Remote.')
            self.remote = True
        return super().query(command, send_args=send_args, recv_args=recv_args)

    def query_expect(self, command, recv_termination=None, expected='ok'):
        ans = self.query(command, recv_args=(recv_termination, HRI.ENCODING))
        if expected and not expected in ans:
            raise InstrumentError("'{}' not in '{}'".format(expected, ans))
        return ans

    @Action()
    def clear(self):
        """Clear the buffer.
        """
        self.send('\r\r')

    @Feat(None, values={True, False})
    def remote(self, value):
        """Remote or local.
        """
        if value:
            #self.query_expect('', None, None)
            self.query_expect('\r', expected=None)
            self.recv()
        else:
            return self.query_expect('LOCAL', chr(0), None)

    @Feat(read_once=True)
    def revision(self):
        """Revision.
        """
        ans = self.query_expect('.REV', expected=None)
        print(ans)
        if 'UNDEFINED' in ans:
            ans = '1.0'
        else:
            ans = self.recv()
            ans = ans.split()[1]
            return ans

    @Feat(None, values={'ecl': 'ECLTRIG', 'ttl': 'TTLTRIG'})
    def trigger_logic(self, value):
        """Trigger logic.
        """
        self.query_expect(value)

    @Feat(None, values={'high': 'HITRIG', '50ohm': '50TRIG}'})
    def trigger_ttl_termination(self, value):
        """Trigger termination for TTL logic (for ECL is fixed to 50 ohm).
        """
        if self.recall('trigger_type') == 'ecl':
            raise InstrumentError('Level triggering only with ECL')
        self.query_expect(value)

    @Feat(None, values={'rising': '+VETRIG', 'falling': '-VETRIG}'})
    def trigger_edge(self, value):
        """Trigger on rising or falling edge.
        """
        self.query_expect(value)

    @Feat(None, values={'level': 'LVLTRIG', 'log': 'LOGTRIG}'})
    def trigger_ecl_mode(self, value):
        """Trigger mode for ECL logic.
        """
        if self.recall('trigger_type') == 'ttl':
            raise InstrumentError('Level triggering only with ECL')

        self.query_expect(value)

    @Feat(units='centivolt', limits=(-40, 40, 1))
    def trigger_ecl_level(self):
        """Trigger level for ECL logic, mode level.
        """
        if self.revision >= 2.0:
            ans = self.query_expect('THRESHV ?')
            ans = between(ans, 'THRESHV ?', 'ok')
            return float(ans.strip())
        else:
            ans = self.query_expect('THRESHV @ .')[8:]
            try:
                pos = ans.index('.')
            except ValueError:
                raise InstrumentError('Unsupported operation.')
            return float(ans[pos+2:pos+7])

    @trigger_ecl_level.setter
    def trigger_ecl_level(self, value):
        if self.revision >= 2.0:
            self.query_expect('{:d} !THRESH'.format(value))
        else:
            value = 40 * value + 2000.0
            self.query_expect('{:d} THRESH ! TRIG+RF>HW'.format(value))

    @Feat(units='volt', limits=(-50, 50))
    def clamp_voltage(self):
        """Most negative value of the gate pulse.
        """
        if self.revision >= 2.0:
            ans = self.query_expect('CLAMP ?')
            ans = between(ans, 'CLAMP ?', 'ok').strip()
            return float(ans)
        else:
            ans = self.query_expect('CLAMP @ .')
            try:
                pos = ans.index('.')
            except ValueError:
                raise InstrumentError('Unsupported operation.')
            return float(ans[pos+2:pos+7]) / 10.0

    @clamp_voltage.setter
    def clamp_voltage(self, value):
        average = self.recall('average_voltage')
        mn, mx = average - Q_(60, volt), average
        if mn < value < mx:
            raise ValueError('Invalid clamp voltage. Not in range {}-{}'.format(mn, mx))
        self.query_expect('{:d} CLAMP ! CLAMP>HW'.format(value * 10))

    @Feat(units='volt', limits=(-50, 50))
    def average_voltage(self):
        """Cathode potential bias with respect of MCP.
        """
        if self.revision >= 2.0:
            ans = self.query_expect('AVE ?')
            ans = between(ans, 'AVE ?', 'ok')
            return float(ans.strip()) / 10.
        else:
            ans = self.query_expect('THRESHV @ .')[8:]
            try:
                pos = ans.index('.')
            except ValueError:
                raise InstrumentError('Unsupported operation.')
            return float(ans[pos+2:pos+7]) / 10.

    @average_voltage.setter
    def average_voltage(self, value):
        self.query_expect('{:d} AVE ! AVE>HW'.format(value * 10))

    @Feat()
    def status(self):
        """Get status.
        """
        return self.query_expect(".STATUS", chr(0))

    @Feat(None, units='volt', limits=(0, 1700))
    def mcp(self, value):
        """MCP Voltage.
        """
        if self.revision >= '2.0':
            return self.query_expect('{} !MCP'.format(value))
        else:
            return self.query_expect('{} !MCPVOLTS'.format(value))

    @Feat(None, values={'inhibit': 0, 'rf': 21, 'ldc': 22, 'hdc': 23, 'dc': 24,
                     'user1': 25, 'user2': 26, 'user3': 27, 'user4': 28})
    def mode(self, mode):
        """Gain modulation mode.

        HRI Machine Modes and Mode Indices
        None     Mode
        0        INHIBIT
        2-10     COMB modes 200 ps to 1 ns inclusive (High rate operation)
        11-20    COMB modes 100 ps to 3 ns inclusive (Low rate (+GOI) operation)
        21       RF
        22       logic low duty cycle (LDC)
        23       logic high duty cycle
        24       DC
        25-28    user modes 1 to 4
        """
        #TODO: Modes [11-20] not available in rev < 2.0
        return self.query_expect("{} !MODE".format(mode))

    @Feat(None)
    def rfgain(self, value):
        """RF Gain.
        """
        return self.query("{} !RFGAIN".format(value))

    @Feat()
    def temperature(self):
        """Temperature.
        """
        if self.revision == 2.0:
            return self.query("@TEMP .")
        return 0

    @Feat(None, values={True, False})
    def enabled(self, value):
        """MCP Enabled
        """
        if self.revision < 2:
            if value:
                self.query_expect('+M')
            else:
                self.query_expect('-M')
        else:
            if value:
                self.mode = self.__dict__.get('_last_mode', 21)
            else:
                self._last_mode = self.recall('mode')
                self.mode = 0


if __name__ == '__main__':
    import argparse
    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='17',
                        help='Serial port to connect to')

    args = parser.parse_args()
    lantz.log.log_to_socket(lantz.log.DEBUG)
    with HRI(args.port, baudrate=9600) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            #inst.clear()
            inst.remote = True
            print(inst.revision)
            inst.mode = "inhibit"
            inst.mcp = 350
            inst.rfgain = 99
            #print(inst.status)
            inst.mode = "rf"
            #print(inst.status)
            inst.remote = False
