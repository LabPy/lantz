# -*- coding: utf-8 -*-
"""
    lantz.drivers.aeroflex.a2023a
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers for an signal generator.


    Sources::

        - Aeroflex 2023a Manual.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Feat, Action
from lantz.serial import SerialDriver
from lantz.processors import ParseProcessor

class A2023a(SerialDriver):
    """Aeroflex Test Solutions 2023A 9 kHz to 1.2 GHz Signal Generator.
    """

    RECV_TERMINATION = 256
    SEND_TERMINATION = '\n'

    @Feat(read_once=True)
    def idn(self):
        """Instrument identification.
        """
        return self.parse_query('*IDN?',
                                format='{manufacturer:s},{model:s},{serialno:s},{softno:s}')

    @Feat(read_once=True)
    def fitted_options(self):
        """Fitted options.
        """
        return self.query('*OPT?').split(',')

    @Action()
    def reset(self):
        """Set the instrument functions to the factory default power up state.
        """
        self.send('*RST')

    @Action()
    def self_test(self):
        """Is the interface and processor are operating?
        """
        return self.query('*TST?') == '0'

    @Action()
    def wait(self):
        """Inhibit execution of an overlapped command until the execution of
        the preceding operation has been completed.
        """
        self.send('*WAI')

    @Action()
    def trigger(self):
        """Equivalent to Group Execute Trigger.
        """
        self.send('*TRG')

    @Feat()
    def status_byte(self):
        """Status byte, a number between 0-255.
        """
        return int(self.query('*STB?'))

    @Feat()
    def service_request_enabled(self):
        """Service request enable register.
        """
        return int(self.query('*SRE?'))

    @service_request_enabled.setter
    def service_request_enabled(self, value):
        return self.query('*SRE {0:d}', value)

    @Feat()
    def event_status_reg(self):
        """Standard event enable register.
        """
        return int(self.query('*ESR?'))

    @event_status_reg.setter
    def event_status_reg(self, value):
        self.query('*ESR {0:d}', value)

    @Feat()
    def event_status_enabled(self):
        """Standard event enable register.
        """
        return int(self.query('*ESR?'))

    @event_status_enabled.setter
    def event_status_enabled(self, value):
        self.query('*ESR {0:d}', value)

    @Action()
    def clear_status(self):
        self.send('*CLS')

    @Feat(units='Hz')
    def frequency(self):
        """Carrier frequency.
        """
        return self.parse_query('CFRQ?',
                                format=':CFRQ:VALUE {0:f};{_}')

    @frequency.setter
    def frequency(self, value):
        self.send('CFRQ:VALUE {0:f}HZ'.format(value))


    @Feat(units='V')
    def amplitude(self):
        """RF amplitude.
        """
        return self.parse_query('RFLV?',
                                format=':RFLV:UNITS {_};TYPE {_};VALUE {0:f};INC {_};<status>')

    @amplitude.setter
    def amplitude(self, value):
        self.query('RFLV:VALUE {0:f}V', value)


    @Feat(units='V')
    def offset(self):
        """Offset amplitude.
        """
        return self.query('RFLV:OFFS?',
                          format=':RFLV:OFFS:VALUE {0:f};{_}')

    @offset.setter
    def offset(self, value):
        self.query('RFLV:OFFS:VALUE {0:f}'.format(value))

    @Feat(values={True: 'ENABLED', False: 'DISABLED'})
    def output_enabled(self):
        """Enable or disable the RF output
        """
        return self.query('OUTPUT?')

    @output_enabled.setter
    def output_enabled(self, value):
        self.query('OUTPUT:{}'.format(value))

    @Feat(units='deg')
    def phase(self):
        """Phase offset
        """
        return self.parse_query('CFRQ?',
                                format=':CFRQ:VALUE {:f}; INC {_};MODE {_}')

    @phase.setter
    def phase(self, value):
        """Adjust phase offset of carrier in degrees.
        """
        self.send('CFRQ:PHASE {}'.format(value))

    @Feat(values={'INT', 'EXT10DIR', 'EXTIND', 'EXT10IND', 'INT10OUT'})
    def frequency_standard(self):
        """Get internal or external frequency standard.
        """
        return self.query('FSTD?')

    @frequency_standard.setter
    def frequency_standard(self, value):
        self.query('FSTD {}'.format(value))

    @Feat()
    def rflimit(self):
        """Set RF output level max.
        """
        return self.query('*RFLV:LIMIT?')

    @rflimit.setter
    def rflimit(self, value):
        self.query('RFLV:LIMIT {}'.format(value))

    @Feat(values={True: 'ENABLED', False: 'DISABLED'})
    def rflimit_enabled(self):
        return self.query('*RFLV:LIMIT?')

    @rflimit_enabled.setter
    def rflimit_enabled(self, value):
        self.query('RFLV:LIMIT:{}'.format(value))

    def remote(self, value):
        if value:
            self.send('^A')
        else:
            self.send('^D')

    @Action(units='ms')
    def expose(self, exposure_time=1):
        self.send('EXPOSE {}'.format(exposure_time))

    @Feat(values={True: 'on', False: 'off'})
    def time(self):
        self.send()
        return self.recv()

    @time.setter
    def time(self, value):
        self.send("vlal ".format(value))

    def local_lockout(self, value):
        if value:
            self.send('^R')
        else:
            self.send('^P')

    def software_handshake(self, value):
        if value:
            self.send('^Q')
        else:
            self.send('^S')


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
    with A2023a(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            print(inst.idn)
            inst.fstd = "EXT10DIR"
            print(inst.fstd)
            print(inst.freq)
            inst.freq = 41.006
            print(inst.rflevel)
            inst.rflevel = -13
            inst.phase=0
            print(inst.phase)
            inst.phase=30
            print(inst.phase)
            inst.phase=60
            print(inst.phase)

