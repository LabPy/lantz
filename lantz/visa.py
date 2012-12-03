# -*- coding: utf-8 -*-
"""
    lantz.visa
    ~~~~~~~~~~

    Implements base classes for drivers that communicate with instruments using visalib.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from . import Driver
from .driver import TextualMixin
from .errors import LantzTimeoutError

from .visalib import Constants, ResourceManager


class LantzVisaTimeoutError(LantzTimeoutError):
    pass

BYTESIZE = {5: 5, 6: 6,
            7: 7, 8: 8}

PARITY = {'none': Constants.ASRL_PAR_NONE, 'even': Constants.ASRL_PAR_EVEN,
          'odd': Constants.ASRL_PAR_ODD, 'mark': Constants.ASRL_PAR_MARK,
          'space': Constants.ASRL_PAR_SPACE}

STOPBITS = {1: Constants.ASRL_STOP_ONE, 1.5: Constants.ASRL_STOP_ONE5,
            2: Constants.ASRL_STOP_TWO}


class VisaDriver(object):

    def __new__(cls, resource_name, *args, **kwargs):
        library_path = kwargs.get('library_path', None)
        manager = ResourceManager(library_path)
        name = manager.resource_info(resource_name).resource_name
        if name.startswith('GPIB'):
            return GPIBVisaDriver(resource_name, *args, **kwargs)
        elif name.startswith('ASRL'):
            return SerialVisaDriver(resource_name, *args, **kwargs)
        elif name.startswith('TCPIP'):
            return TCPVisaDriver(resource_name, *args, **kwargs)
        elif name.startswith('USB'):
            return USBVisaDriver(resource_name, *args, **kwargs)
        else:
            raise ValueError('Unknown resource type: {}'.format(name))


class MessageVisaDriver(TextualMixin, Driver):
    """Base class for drivers that communicate with instruments
    via serial or parallel port using pyserial

    :param resource_name: name or alias of the resource to open.

    """

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'
    ENCODING = 'ascii'

    RECV_CHUNK = -1

    def __init__(self, resource_name, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vi = None
        self._init_attributes = {}

        library_path = kwargs.get('library_path', None)
        self.resource_manager = ResourceManager(library_path)

        self.visa = self.resource_manager.visa

        self.resource_name = resource_name
        self.log_debug('Created Instrument {}', self.resource_name)

    def raw_send(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument
        :param data: bytes
        """

        try:
            self.visa.write(self.vi, data)
        except Exception as e:
            raise Exception(str(e))

    def initialize(self):
        """Open port
        """
        if not self.is_open():
            self.log_debug('Opening {}', self.resource_name)
            self.vi = self.resource_manager.open_resource(self.resource_name)
            for key, value in self._init_attributes.items():
                self.visa.set_attribute(self.vi, key, value)

            self.log_debug('The session for {} is {}', self.resource_name, self.vi)
        else:
            self.log_debug('{} is already open', self.resource_name)

    def finalize(self):
        """Close port
        """
        self.log_debug('Closing port {}', self.resource_name)
        self.visa.close(self.vi)
        self.vi = None

    def is_open(self):
        return self.vi is not None


class SerialVisaDriver(MessageVisaDriver):
    """Base class for drivers that communicate with instruments
    via serial port using visa.

    :param resource_name: the visa resource name or alias (e.g. 'ASRL1::INSTR')
    """

    #: communication parameters
    BAUDRATE = 9600
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    RECV_CHUNK = -1

    def __init__(self, resource_name, *args, **kwargs):
        super().__init__(resource_name, *args, **kwargs)

        kw = {}
        kw['ASRL_BAUD']= kwargs.get('baudrate', self.BAUDRATE)
        kw['ASRL_DATA_BITS'] = BYTESIZE[kw.get('bytesize', self.BYTESIZE)]
        kw['ASRL_PARITY'] = PARITY[kw.get('parity', self.PARITY)]
        kw['ASRL_STOP_BITS'] = STOPBITS[kw.get('stopbits', self.STOPBITS)]

        flow = Constants.ASRL_FLOW_NONE
        if kwargs.get('rtscts', getattr(self, 'RTSCTS')):
            flow |= Constants.ASRL_FLOW_RTS_CTS
        if kwargs.get('dsrdtr', getattr(self, 'DSRDTR')):
            flow |= Constants.ASRL_FLOW_DTR_DSR
        if kwargs.get('xonxoff', getattr(self, 'XONXOFF')):
            flow |= Constants.ASRL_FLOW_XON_XOFF

        kw['ASRL_FLOW_CNTRL'] = flow

        if self.RECV_TERMINATION and self.RECV_CHUNK > 1:
            kw['TERMCHAR'] = ord(self.RECV_TERMINATION)
            kw['ASRL_END_IN'] = Constants.ASRL_END_TERMCHAR
        else:
            kw['ASRL_END_IN'] = Constants.ASRL_END_NONE

        self._init_attributes.update(kw)


    def raw_recv(self, size):
        """Receive raw bytes to the instrument.

        :param size: number of bytes to receive
        :return: received bytes
        :return type: bytes

        If a timeout is set, it may return less bytes than requested.
        If size == -1, then the number of available bytes will be read.

        """

        if size == -1:
            size = self.visa.get_attribute(self.vi, 'ASRL_AVAIL_NUM')
            if not size:
                return bytes()

        if not size:
            size = 1

        data = self.visa.read(self.vi, size)

        return data


class GPIBVisaDriver(MessageVisaDriver):


    def raw_recv(self, size):
        """Receive raw bytes to the instrument.

        :param size: number of bytes to receive
        :return: received bytes
        :return type: bytes

        If a timeout is set, it may return less bytes than requested.
        If size == -1, then the number of available bytes will be read.

        """

        if not size:
            size = 1

        data = self.visa.read(self.vi, 1)

        return data

class TCPVisaDriver(MessageVisaDriver):
    pass


class USBVisaDriver(MessageVisaDriver):
    pass
