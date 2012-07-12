# -*- coding: utf-8 -*-
"""
    lantz.drivers.coherent.innova
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers for Innova 300 Series gas lasers.


    Implementation Notes
    --------------------

    There are currently 3 drivers implemented Innova300C, ArgonInnova300C
    and KryptonInnova300C. The last two only add to the first the
    corresponding wavelength selection.

    Sources::

        - Innova 300C Manual

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.

"""

from ... import Q_, Feat, DictFeat, Action
from ...serial import SerialDriver
from ...errors import InvalidCommand


def make_feat(command, **kwargs):

    def get(self):
        return self.query('PRINT {}'.format(command))

    def set(self, value):
        return self.query('{}={}'.format(command, value))

    if kwargs.pop('readonly', None):
        return Feat(fget=get, **kwargs)
    elif kwargs.pop('writeonly', None):
        return Feat(fset=set, **kwargs)

    return Feat(get, set, **kwargs)


class Innova300C(SerialDriver):
    """Innova300 C Series.
    """

    ENCODING = 'ascii'

    SEND_TERMINATION = '\r\n'
    RECV_TERMINATION = '\r\n'


    def __init__(self, port=1, baudrate=1200, **kwargs):
        super().__init__(port, baudrate, bytesize=8, parity='None',
                         stopbits=1, **kwargs)

    def initialize(self):
        super().initialize()
        self.echo_enabled = False

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Send query to the laser and return the answer, after handling
        possible errors.

        :param command: command to be sent to the instrument
        :type command: string

        :param send_args: (termination, encoding) to override class defaults
        :param recv_args: (termination, encoding) to override class defaults
        """
        ans = super().query(command, send_args=send_args, recv_args=recv_args)
        # TODO: Echo handling
        if ans == 'Out of Range':
            raise ValueError()
        elif ans.startswith('Syntax Error'):
            raise InvalidCommand()
        elif ans == 'Laser must be off':
            raise Exception('Laser must be off')

        return ans


    # General information and communication

    idn = make_feat('ID',
                    readonly=True,
                    doc='Laser identification, should be I300.',
                    read_once=True)

    software_rev = make_feat('SOFTWARE',
                             readonly=True,
                             doc='Software revision level in the power supply.',
                             read_once=True)

    head_software_rev = make_feat('HEAD SOFTWARE',
                                  readonly=True,
                                  doc='Software revision level in the laser head board.',
                                  read_once=True)

    echo_enabled = make_feat('ECHO',
                             writeonly=True,
                             doc='Echo mode of the serial interface.',
                             values={True: 1, False: 0})

    baudrate = Feat(values={110, 300, 1200, 2400, 4800, 9600, 19200})

    @baudrate.setter
    def baudrate(self, value):
        """RS-232/422 baud rate, the serial connection will be reset after.
        """
        self.query('BAUDRATE={}'.format(value))
        #TODO: RESET Connection


    # Interface

    analog_relative = make_feat('ANALOG MODE',
                                doc='Analog Interface input mode.',
                                values={True: 1, False: 0})

    analog_enabled = make_feat('ANALOGINT',
                               doc='Analog Interface input state.',
                               values={True: 1, False: 0})

    current_range = make_feat('CURRENT RANGE',
                              doc='Current corresponding to 5 Volts at the input'\
                                  ' or output lines of the Analog Interface.',
                              units='A',
                              limits=(10, 100, 1))

    control_pin_high = make_feat('CONTROL',
                                 readonly=True,
                                 doc='State of the input pin 10 of the Analog Interface.',
                                 values={True: 1, False: 0})

    output_pin_high = make_feat('STATUS',
                                doc='State of the output pin 24 and 25 of the Analog Interface.',
                                values={(False, False): 0, (True, False): 1,
                                     (False, True): 2, (True, True): 3})

    # Diagnostics

    @Feat()
    def faults(self):
        """List of all active faults.
        """
        return self.query('PRINT FAULT').split('&')

    autofill_delta = make_feat('AUTOFILL DELTA',
                               readonly=True,
                               doc='Tube voltage minus the autofill setting.',
                               units='V')

    autofill_needed = make_feat('AUTOFILL STATUS',
                                readonly=True,
                                doc='Is the autofill needed (wheter fill is enabled or not)',
                                values={True: 1, False: 0})

    remaining_time = make_feat('HRSTILSHUTDOWN',
                               readonly=True,
                               doc='Number of hours remaining before the laser '\
                                   'will shut down automatically.',
                               units='hour')

    cathode_current = make_feat('CATHODE CURRENT',
                                readonly=True,
                                doc='Laser cathode current (AC).',
                                units='A')

    cathode_voltage = make_feat('CATHODE VOLTAGE',
                                readonly=True,
                                doc='Laser cathode voltage (AC).',
                                units='V')

    time_to_start = make_feat('START',
                              readonly=True,
                              doc='Timer countdown during the start delay cycle.',
                              units='second')

    @Feat()
    def is_in_start_delay(self):
        """Laser is in start delay (tube not ionized)
        """
        return self.query('LASER') == '1'


    tube_time = make_feat('HOURS',
                          readonly=True,
                          doc='Number of operating hours on the plasma tube.',
                          units='hour')

    tube_voltage = make_feat('TUBE VOLTAGE',
                             readonly=True,
                             doc='Laser tube voltage.',
                             units='V')

    water_flow = make_feat('FLOW',
                           readonly=True,
                           doc='Water flow.',
                           units='gallons/minute')

    water_resistivity = make_feat('WATER RESISTIVITY',
                                  readonly=True,
                                  doc='Resistivity of the incoming water to the power supply.',
                                  units='kohm*cm')

    water_temperature = make_feat('WATER TEMPERATURE',
                                  doc='Temperature of the incoming water to the power supply.')


    # Other

    autofill_mode = make_feat('AUTOFILL',
                              doc='Autofill mode.',
                              values={'disabled': 0, 'enabled': 1,
                                   'enabled until next autofill': 2})

    laser_enabled = make_feat('LASER',
                              doc='Energize the power supply.',
                              values={True: 2, False: 0})

    magnet_current = make_feat('MAGNET CURRENT',
                               readonly=True,
                               doc='Laser magnet current.',
                               units='A')

    operating_mode = make_feat('MODE',
                               readonly=True,
                               doc='Laser operating mode.',
                               values={'current regulation': 0,
                                    'reduced bandwidth light regulation': 1,
                                    'standard light regulation': 2,
                                    'current regulation, light regulation out of range': 3})

    # Etalon

    etalon_mode = make_feat('EMODE',
                            doc='Etalon mode.',
                            values={'manual': 0, 'modetrack': 1, 'modetune': 2})

    etalon_temperature = make_feat('ETALON',
                                   readonly=True,
                                   doc='Etalon temperature.',
                                   units='degC')

    @Feat(units='degC', limits=(51.5, 54, 0.001))
    def etalon_temperature_setpoint(self):
        """Setpoint for the etalon temperature.
        """
        return self.query('PRINT SET ETALON')

    @etalon_temperature_setpoint.setter
    def etalon_temperature_setpoint(self, value):
        self.query('ETALON={}'.format(value))


    # Magnetic field

    magnetic_field_high = make_feat('FIELD',
                                    doc='Magnetic field.',
                                    values={True: 1, False: 0})

    @Feat(values={True: 1, False: 0})
    def magnetic_field_setpoint_high(self):
        """Setpoint for magnetic field setting.
        """
        return self.query('PRINT SET FIELD')

    @magnetic_field_setpoint_high.setter
    def magnetic_field_setpoint_high(self, value):
        self.query('FIELD={}'.format(value))


    # Light and current regulation

    powertrack_mode_enabled = make_feat('PT',
                                        doc='PowerTrack.',
                                        values={True: 1, False: 0})

    @DictFeat(keys=('A', 'B'), limits=(0, 255))
    def powertrack_position(self, key):
        """Relative position of the PowerTrack solenoids.
        """
        return self.query('PRINT PTDAC{}'.format(key))

    @powertrack_position.setter
    def powertrack_position(self, key, value):
        self.query('PTDAC{}={}'.format(key, value))

    @Action()
    def recalibrate_powertrack(self):
        """Recalibrate PowerTrack. This will only execute if PowerTrack is on
        and light regulation is off
        """
        self.query('PT=2')

    @Action()
    def center_powertrack(self):
        """Center PowerTrack and turn it off.
        """
        self.query('PT=3')

    current = make_feat('CURRENT',
                        readonly=True,
                        doc='Current regulation mode.',
                        units='A')

    @Feat(units='A', limits=(0, 50, 0.01))
    def current_setpoint(self):
        """Current setpoint when using the current regulation mode.
        """
        return self.query('PRINT SET CURRENT')

    @current_setpoint.setter
    def current_setpoint(self, value):
        self.query('CURRENT={}'.format(value))


    power = make_feat('LIGHT 3',
                      readonly=True,
                      doc='Current power output.',
                      units='A')

    @Feat(units='W', limits=(0, 50, 0.0001))
    def power_setpoint(self):
        """Setpoint for the light regulation.
        """
        return self.query('PRINT SET LIGHT')

    @power_setpoint.setter
    def power_setpoint(self, value):
        self.query('LIGHT={}'.format(value))


    auto_light_cal_enabled = make_feat('AUTOLTCAL',
                                       doc='Automatic light regulation calibration flag.',
                                       values={True: 1, False: 0})

    current_change_limit = make_feat('PCTCHGTILRECAL',
                                     doc='Percent tube change before an automatic '\
                                         'light regulation recalibration becomes '\
                                         'necessary.',
                                     units='', #TODO: %
                                     limits=(5, 100, 1))


class ArgonInnova300C(Innova300C):
    """Argon Innova 300C.
    """

    wavelength = make_feat('WAVELENGTH',
                           doc='Wavelength for the internal power meter calibration',
                           values={351, 364, 454, 457, 465, 472, 476, 488, 496, 501,
                                 514, 528, 1090, 'MLVS', 'MLUV', 'MLDUV'})


class KryptonInnova300C(Innova300C):
    """Krypton Innova 300C.
    """
    wavelength = make_feat('WAVELENGTH',
                           doc='Wavelength for the internal power meter calibration',
                           values={476, 482, 520, 530, 568, 647, 676, 752, 'MLVS',
                                 'MLUV', 'MLVI', 'MLBG', 'MLRD', 'MLIR'})

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
    with Innova300C(args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            print(inst.idn)
            print(inst.software_rev)
            print(inst.head_software_rev)
