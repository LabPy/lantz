# -*- coding: utf-8 -*-
"""
    lantz.drivers.olympus.ixbx
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    When talking about the z-axis of a microscope, use "near" and "far" instead of "up" and "down." "Nearer" always means the objective ends closer to the sample; "farther" means the objective ends farther away. On an inverted microscope, "near" is up and "far" is down; on an upright microscope it is exactly the reverse. Better to use "near" and "far" to avoid confusion.

    You can always get the current state of the system by sending the command you would use to change that state followed by ?. For example, to get the current objective position, send 1OB?. The microscope returns 1OB 3, say, if the current objective is position 3 on the nosepiece.

    The microscope only understands positive integers, no negative numbers, no floating point. All distances are sent as positive integers measured in hundredths of a micron. All voltages are sent as tenths of a volt. Where negative numbers are needed, such as to specify relative motion, an extra argument is used to tell the microscope the sign of the number.


    Sources::

        - Olympus IX-81 Chassis Commands `link <http://madhadron.com/?p=89>`_
        - Labview IX BX Series Driver `link <http://sine.ni.com/apps/utf8/niid_web_display.download_page?p_id_guid=0472CB8CEE4473B8E0440003BA7CCD71>`_
        - Lantz reverse engineering


    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.

"""

from lantz import Feat, Action, Q_
from lantz.errors import InstrumentError
from lantz.serial import SerialDriver

# Physical units used by the IX/BX microscopes
DECIVOLT = Q_(0.1, 'V')
ZSTEP = Q_(0.01, 'micrometer')

# Booleans mappings used by the IX/BX microscopes
ON_OFF = {True: 'ON', False: 'OFF'}
IN_OUT = {True: 'IN', False: 'OUT'}
CLOSED_OPEN = {True: 'IN', False: 'OUT'}
ONE_ZERO = {True: '1', False: '0'}
ONE_TWO = {True: '1', False: '2'}
FH_FRM = {True: 'FH', False: 'FRM'}
EPI_DIA = {True: 'EPI', False: 'DIA'}

INTSTR = (int, str)

def ofeat(command, doc, **kwargs):
    """Build Feat

    :param command: command root (without ?)
    :param doc: docstring to be applied to the feature
    """

    def _get(self):
        response = self.query(command + '?')
        return response

    def _set(self, value):
        self.query('{} {}'.format(command, value))

    return Feat(_get, _set, doc=doc, **kwargs)


class IXBX(SerialDriver):
    """ IX or BX Olympus microscope body.
    """

    RECV_TERMINATION = '\r\n'
    SEND_TERMINATION = '\r\n'


    def __init__(self, port=1, baudrate=19200, bytesize=8, parity='Even',
                 stopbits=1, flow=0, timeout=None, write_timeout=None,
                 *args, **kwargs):
        super().__init__(port, baudrate, bytesize, parity,
                         stopbits, flow, timeout, write_timeout,
                         *args, **kwargs)
        self.send('1LOG IN\n')
        self.send('2LOG IN')


    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Query the instrument and parse the response.

        :raises: InstrumentError
        """
        response = super().query(command, send_args=recv_args, recv_args=recv_args)
        command = command.strip()[0]
        if response in ('1x', '2x'):
            raise InstrumentError("Unknown command: '{}'".format(command))
        if not response.startswith(command):
            raise InstrumentError("Unknown response: '{}'".format(response))
        if response == 'X' or 'x':
            raise InstrumentError('Unable to set')
        elif not response == '+':
            raise InstrumentError("Unknown response: '{}'".format(response))
        return response


    @Feat(read_once=True)
    def idn(self):
        """Microscope identification
        """
        return parse_response(self.query('1UNIT?'))

    fluo_shutter = ofeat('1LED',
                        'External shutter for the fluorescent light source',
                         values=ONE_ZERO)

    lamp_epi_enabled = ofeat('1LMPSEL',
                             'Illumination source lamp.',
                             values=EPI_DIA)

    lamp_enabled = ofeat('1LMPSW',
                         'Turn the currently selected lamp onf and off',
                         values=ON_OFF)

    lamp_intensity = ofeat('1LMP',
                           'Transmitted light intensity',
                           procs=(INTSTR, ))

    def lamp_status(self):
        #LMPSTS OK, X
        pass

    objective = ofeat('1OB',
                      'Objective nosepiece position',
                      procs=(INTSTR, ))

    body_locked = ofeat('1LOG',
                        'Turn the currently selected lamp on and off',
                        values=ON_OFF)
    focus_locked = ofeat('2LOG',
                         'Turn the currently selected lamp on and off',
                         values=ON_OFF)

    @Feat(units=(ZSTEP, ZSTEP))
    def soft_limits(self):
        near = self.query('2NEARLMT?')
        far = self.query('2FARLMT?')
        return near, far

    @soft_limits.setter
    def soft_limits(self, near, far):
        self.query('2NEARLMT {:d}'.format(near))
        self.query('2FARLMT {:d}'.format(far))


    move_to_start_enabled = ofeat('INITRET',
                                  'Sets / cancels returning operation to the start '
                                  'position after initializing the origin.',
                                  values=ON_OFF)

    jog_enabled = ofeat('JOG', 'Jog enabled', values=ON_OFF)
    jog_sensitivity = ofeat('JOGSNS',' Jog sensitivity', procs=(INTSTR, ))
    jog_dial = ofeat('JOGSEL', 'Jog selection (Handle/BLA) ???', values=FH_FRM)
    jog_limit_enabled = ofeat('joglmt', 'Jog limit enabled', values=ON_OFF)

    @Feat()
    def movement_status(self):
        return self.query('ZDRV?')

    @Action(units=ZSTEP)
    def move_relative(self, distance):
        if distance == 0:
            return
        elif distance < 0:
            distance = -distance
            direction = 'N'
        else:
            direction = 'F'

        self.query('2MOV {:s} {:d}'.format(distance, direction))

    @Feat(units=ZSTEP)
    def z(self):
        """Position of the objective.
        """

        # OPTIMAL?? start accel, speed tenth of microns/s, end accel
        return int(self.query('2POS'))

    @z.setter
    def z(self, value):

        # OPTIMAL?? start accel, speed tenth of microns/s, end accel
        self.query('2MOV D {:d}'.format(value))

    def stop(self):
        """Stop any currently executing motion
        """

        # Stop any currently executing motion. Always responds with 2STOP +.
        # If there is a 2MOV command in progress,
        # it also aborts and returns an error condition with 2MOV !,E02133.
        self.query('2STOP')

    def init_origin(self):
        """Init origin
        """
        #INITORG
        pass


class IX2(IXBX):
    """ Olympus IX2 Body
    """

    bottom_port_closed = ofeat('1BPORT', 'Bottom port', values=CLOSED_OPEN)

    shutter1_closed = ofeat('SHUT1', 'Shutter', values=IN_OUT)
    shutter2_closed = ofeat('SHUT2', 'Shutter', values=IN_OUT)

    filter_wheel = ofeat('FW', 'Filter wheel position', procs=(INTSTR, ))
    condensor = ofeat('CD', 'Condensor position', procs=(INTSTR, ))
    mirror_unit = ofeat('MU', 'Mirror unit position', procs=(INTSTR, ))
    camera_port_enabled= ofeat('PRISM', 'Prism position', values=ONE_TWO)


class BX2A(IXBX):
    """ Olympus BX2A Body
    """

    shutter_closed = ofeat('SHUTTER', 'Shutter RFAA', values=IN_OUT)
    aperture_stop_diameter = ofeat('EAS', 'Aperture stop diameter (EPI AS RLAA)', procs=(INTSTR, ))
    aperture_stop_diameter = ofeat('DAS', 'Aperture stop diameter (DIA AS UCD)', procs=(INTSTR, ))
    condenser_top_lens_enabled = ofeat('CDTOP', 'Condenser top lens (UCD)', values=IN_OUT)
    turret = ofeat('TURRET', 'Turret position (UCD)', procs=(INTSTR, ))
    cube = ofeat('CUBE', 'Cube position (RFAA/RLAA)', procs=(INTSTR, ))
    configure_filterwheel = ofeat('FW', 'Configure filterwheel', procs=(INTSTR, ))

