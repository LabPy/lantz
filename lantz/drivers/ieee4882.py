# -*- coding: utf-8 -*-
"""
    lantz.drivers.ieee4882
    ~~~~~~~~~~~~~~~~~~~~~~~

    Implements a IEEE-488.2 commands.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from lantz import Action, Feat, Driver


class IEEE4882Driver(Driver):
    """Implements mandatory functions for a IEE488.2 device.

    You can use it as a mixin class.
    """

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
        """Performs a complete instrument self-test.

        If test fails, one or more error messages will provide additional information.
        When available, Use SYSTem:ERRor? to read error queue.
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

        Decimal sum of the bits in the register.
        Bit #6: Master Summary Status Bit (MSS)
                This bit is set, if one of the bits in STB becomes true
                and the corresponding bit in the SRE is enabled.
        Bit #5: Event Summary Bit (ESB)
                This bit is set, if one of the bits in ESR becomes true
                and the corresponding bit in the ESE is enabled.
        Bit #4: Message Available Bit (MAV)
                This bit is set, if there is a message in the output buffer available.
        """
        return int(self.query('*STB?'))

    @Feat()
    def service_request_enabled(self):
        """Service request enable register.

        Decimal sum of the bits in the register.
        """
        return int(self.query('*SRE?'))

    @service_request_enabled.setter
    def service_request_enabled(self, value):
        self.query('*SRE {0:d}'.format(value))

    event_status_reg = Feat()

    @event_status_reg.setter
    def event_status_reg(self):
        """Queries the event register for the Standard Event Register group.
        Register is read-only; bits not cleared when read.
        """
        return int(self.query('*ESR?'))

    @Feat()
    def event_status_enabled(self):
        """Enables bits in the enable register for the Standard Event Register group.
        The selected bits are then reported to bit 5 of the Status Byte Register.

        Decimal sum of the bits in the register.
        Bit #7: Enable ESB when Power on or restart
        Bit #5: Enable ESB when a Command Error occur
        Bit #3: Enable ESB when a Device Dependent Error occur
        Bit #0: Enable ESB when Operation complete

        Others are not used.
        """
        return int(self.query('*ESE?'))

    @event_status_enabled.setter
    def event_status_enabled(self, value):
        self.query('*ESE {0:d}', value)

    @Action()
    def clear_status(self):
        """Clears the event registers in all register groups.
         Also clears the error queue.
        """
        self.send('*CLS')

    @Action()
    def wait_operation_complete_bit(self):
        """Returns 1 to the output buffer after all pending commands complete.

        Other commands cannot be executed until this command completes.
        """
        return self.query('*OPC?')

    @Action()
    def set_operation_complete_bit(self):
        """Sets "Operation Complete" (bit 0) in the Standard Event register at
        the completion of the current operation.

        The purpose of this command is to synchronize your application with the instrument.
        Other commands may be executed before Operation Complete bit is set.
        """
        return self.query('*OPC')

    @Feat(values={True: 0, False: 1})
    def poweron_status_clear_enabled(self):
        """Enables or disables clearing of two specific registers at power on:
        - Standard Event enable register
        - Status Byte condition register
        - Questionable Data Register
        - Standard Operation Register
        """
        return self.query('*PSC?')

    @poweron_status_clear_enabled.setter
    def poweron_status_clear_enabled(self, value):
        self.query('*PSC {}'.format(value))

    @Action()
    def recall_state(self, location):
        """Recalls (*RCL) instrument state in specified non-volatile location.

        :param location: non-volatile storage location.
        """
        self.send('*RCL {}'.format(location))

    @Action()
    def save_state(self, location):
        """Saves instrument state in specified non-volatile location.

        Previously stored state in location is overwritten (no error is generated).
        :param location: non-volatile storage location.
        """
        self.send('*SAV'.format(location))
