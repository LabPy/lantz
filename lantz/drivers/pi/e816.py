# -*- coding: utf-8 -*-
"""
    lantz.driver.pi.e816
    ~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control a Piezo Controller


    Implementation notes
    --------------------

    The e816 has can be controlled via USB or Serial port. Additionally,
    PI provides a library (dll for windows and so for linux) that wraps
    serial and USB communication.

    Library: according to the manual, you can get or set multiple axis
    together (for example set positions for axis A, B and C).
    However, this does not seem to possible in the underlying serial/usb
    communication and the library seems to do it sequentially.

    As there is no real speed gain  we have decided to remove this
    possibility from the current implementation of the Lantz driver.

    USB: Not implemented yet
    Serial: Not implemented yet.


    Sources::

        - PZ116E User Manual / E-816 Computer Interface and Command Interpreter
        - PZ120E Software Manual / E-816 Windows GCS DLL

    :copyright: © 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import ctypes as ct
from time import sleep

from lantz import Action, Feat, DictFeat
from lantz.foreign import LibraryDriver, RetStr, RetTuple
from lantz.errors import InstrumentError

_ERRORS = {2 : "2",
           1 : "1",
           0 : "Success",
           -1 : "COM_ERROR",}

_PARAMS = {1 : "VAD gain",
           2 : "VAD offset",
           3 : "PAD gain",
           4 : "PAD offset",
           5 : "DA gain",
           6 : "DA offset",
           7 : "KSen",
           8 : "OSen",
           9 : "Kpzt",
           10 : "Opzt"}


class E816Library(LibraryDriver):
    """E-816 Computer Interface and Command Interpreter Submodule for Piezo Controllers.

    (firmware version 3.20 and newer)
    """

    LIBRARY_NAME = 'E816_DLL.dll', 'libpi_e816'

    def __init__(self, port=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #: This holds the list of valid axes that will be populated by other functions.
        #: Do not replace with other list as DictFeat have ref to it.
        self.axes = []

        self.ild = None
        self.port = port

    def _return_handler(self, func_name, ret_value):
        if ret_value < 0:
            raise InstrumentError('{} ({})'.format(ret_value, _ERRORS[ret_value]))
        return ret_value


    @Action()
    def enumerateUSB(self):
        """Enumerate USB devices.
        """
        devfilter = ct.c_char_p("")
        numdev, devices = self.lib.E816_EnumerateUSB(*RetStr(1024), devfilter=devfilter)
        return devices.split('\n')

    @Feat(read_once=True)
    def idn(self):
        """Identification
        """
        ret, idn = self.lib.E816_qIDN(self.ild, *RetStr(64))
        return idn

    @Feat()
    def remote(self):
        if not self.idl:
            return False
        ret = self.lib.E816_IsConnected(self.ild)
        return bool(ret)

    @Feat()
    def remote(self, value):
        """Set the equipment to remote computer control.
        """
        if value:
            self.idl = ct.c_int()
            try:
                if isinstance(self.port, int):
                    self._connectRS232(self.port)
                else:
                    self._connectUSB(self.port)
            except:
                self.idl = None
                raise
        else:
            ans = self.lib.E816_CloseConnection(self.ild)
            self.idl = None

    def _connectUSB(self, port):
        """Connect to USB devices.
        """
        self.idl = ct.c_int()
        port = ct.c_char(port)
        self.ild = self.lib.E816_ConnectUSB(port)

    def _connectRS232(self, port):
        """Connect to RS-232 devices.
        """
        baud = ct.c_long(115200)
        self.ild = self.lib.E816_ConnectRS232(port, baud)

    def _disconnect(self):
        """Initialise Library.
        """
        error = self.lib.E816_CloseConnection(self.ild)

    @Feat()
    def connected_axes(self):
        """Connected axes
        """
        ret, axes = self.lib.E816_qSAI(self.ild, *RetStr(32))
        return tuple(axes)

    @DictFeat(units='um')
    def target_position(self, axis):
        """Target position
        """
        ret, position = self.lib.E816_qMOV(self.ild, axis, RetTuple('d', len(axis)))
        return position[0]

    @target_position.setter
    def target_position(self, axis, value):
        """
        """
        value = (ct.c_double * len(axis))(value)
        ret = self.lib.E816_MOV(self.ild, axis, value)

    @DictFeat(units='um')
    def position(self, axis):
        """Position
        """
        ret, position = self.lib.E816_qPOS(self.ild, axis, RetTuple('d', len(axis)))
        return position[0]

    @Action()
    def move_relative(self, axis, value):
        """Move axes to relative position.
        """
        value = (ct.c_double * len(axis))(value)
        self.lib.E816_MVR(self.ild, axis, value)

    @DictFeat(units='volt')
    def qvol(self, axis):
        """Piezo voltage
        """
        ret, voltage = self.lib.E816_qVOL(self.ild, axis, RetTuple('d', len(axis)))
        return voltage[0]

    @DictFeat(units='volt')
    def target_voltage(self, axis):
        """Targeted voltage.
        """
        ret, voltage = self.lib.E816_qSVA(self.ild, axis, RetTuple('d', len(axis)))
        return voltage[0]

    @target_voltage.setter
    def target_voltage(self, axis, value):
        value = (ct.c_double * len(axis))(value)
        ret = self.lib.E816_SVA(self.ild, axis, value)

    def svr(self, ax, value):
        """Set the given axes to relative piezo voltage."""
        axes = ct.c_char_p(str(ax))
        valuearr = (ct.c_double * 1)(value)
        error = self.lib.E816_SVR(self.ild, axes, valuearr)
        print("SVR -> %s" %  _ERRORS[error])
        print("SVR = %d" % value)

    @DictFeat()
    def arrived(self, axis):
        """Check if the given axis has reached target position.
        """
        ret, arrived = self.lib.E816_qONT(self.ild, axis, RetTuple('?', len(axis)))
        return arrived[0]

    @DictFeat()
    def servo_enabled(self, axis):
        """Servo-control state.
        You can choose between a  open-loop (servo disabled) or closed-loop (servo enabled) operation.
        """
        ret, state = self.lib.E816_qSVO(self.ild, axis, RetTuple('?', len(axis)))
        return state[0]

    @servo_enabled.setter
    def servo_enabled(self, axis, state):
        """Sets servo-control ON or OFF.
        """
        state = (ct.c_bool * 1)(state)
        error = self.lib.E816_SVO(self.ild, axis, state)

    @Feat()
    def error(self):
        """Get Error.
        """
        error_code = self.lib.E816_GetError(self.ild)
        return error_code, self.translate_error(error_code)

    @Action()
    def translate_error(self, error_code):
        """Translate error code to error message.
        """
        ret, msg = self.lib.E816_TranslateError(error_code, *RetStr(128))
        return msg

    @DictFeat()
    def axis_parameters(self, axis):
        """Axis parameters.
        """
        sz = len(_PARAMS)
        axis *= sz
        params = (ct.c_int() * sz)(*_PARAMS.values())
        ret, values = self.lib.E816_qSPA(self.ild, axis, params, RetTuple('d', sz))
        return {key: value for key, value in zip(_PARAMS.keys(), values)}


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
    with E816Library(args.port, baudrate=9600) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            from time import sleep

            ports = inst.enumerateUSB()
            inst.port = ports[0]
            inst.remote = True
            print(inst.isconnected())
            print(inst.idn())

            axes = inst.connected_axes

            for axis in axes:
                print(inst.axis_parameters[axis])
                inst.servo_enabled[axis] = True
                print(inst.servo_enabled[axis])
                inst.targeted_position[axis] = 1
                while not inst.arrived[axis]:
                    sleep(1)

                print(inst.position[axis])

                inst.move_relative[axis] = 1
                while not inst.arrived[axis]:
                    sleep(1)

                print(inst.position[axis])

            inst.error()

            inst.remote = False









