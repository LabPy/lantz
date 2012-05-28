# -*- coding: utf-8 -*-
"""
    lantz.visa
    ~~~~~~~~~~

    Implements base classes for drivers that communicate with instruments using visalib.

    :copyright: (c) 2011 by Lantz Authors, see AUTHORS for more details.
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

PARITY = {'None': Constants.ASRL_PAR_NONE, 'Even': Constants.ASRL_PAR_EVEN,
          'Odd': Constants.ASRL_PAR_ODD, 'Mark': Constants.ASRL_PAR_MARK,
          'Space': Constants.ASRL_PAR_SPACE}

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

    def __init__(self, resource_name, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vi = None

        library_path = kwargs.get('library_path', None)
        self.resource_manager = ResourceManager(library_path)

        self.visa = self.resource_manager.visa

        #bytesize = BYTESIZE[bytesize]
        #parity = PARITY[parity]
        #stopbits = STOPBITS[stopbits]

        self.resource_name = resource_name
        self.log_debug('Created Instrument {}'.format(self.resource_name))

    def raw_send(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument
        :param data: bytes
        """

        try:
            self.visa.write(self.vi, data)
        except Exception as e:
            raise Exception(str(e))

    def raw_recv(self, size=-1):
        """Receive raw bytes to the instrument.

        :param size: number of bytes to receive
        :return: received bytes
        :return type: bytes

        If a timeout is set, it may return less bytes than requested.
        If size == -1, then the number of available bytes will be read.

        """
        size = 0 ###
        if size == -1:
            size = self.serial.inWaiting()

        if size == 0:
            size = 1
        #self.log_debug('waiting {}'.format(size))
        data = self.visa.read(self.vi, size)
        #self.log_debug(data)
        return data

    def initialize(self):
        """Open port
        """
        if not self.is_open():
            self.log_debug('Opening {}'.format(self.resource_name))
            self.vi = self.resource_manager.open_resource(self.resource_name) #, self.access_mode, self.open_timeout
            self.log_debug('The session for {} is {}'.format(self.resource_name, self.vi))
        else:
            self.log_debug('{} is already open'.format(self.resource_name))

    def finalize(self):
        """Close port
        """
        self.log_debug('Closing port {}'.format(self.resource_name))
        self.visa.close(self.vi)
        self.vi = None

    def is_open(self):
        return self.vi is not None


class SerialVisaDriver(MessageVisaDriver):
    pass


class GPIBVisaDriver(MessageVisaDriver):
    pass


class TCPVisaDriver(MessageVisaDriver):
    pass


class USBVisaDriver(MessageVisaDriver):
    pass
