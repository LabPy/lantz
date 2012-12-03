# -*- coding: utf-8 -*-
"""
    lantz.serial
    ~~~~~~~~~~~~

    Implements base classes for drivers that communicate with instruments
    via serial or parallel port.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import serial

from . import Driver
from .driver import TextualMixin
from .errors import LantzTimeoutError

from serial import SerialTimeoutException


class LantzSerialTimeoutError(SerialTimeoutException, LantzTimeoutError):
    pass


BYTESIZE = {5: serial.FIVEBITS, 6: serial.SIXBITS,
            7: serial.SEVENBITS, 8: serial.EIGHTBITS}

PARITY = {'none': serial.PARITY_NONE, 'even': serial.PARITY_EVEN,
          'odd': serial.PARITY_ODD, 'mark': serial.PARITY_MARK,
          'space': serial.PARITY_SPACE}

STOPBITS = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE,
            2: serial.STOPBITS_TWO}


class SerialDriver(TextualMixin, Driver):
    """Base class for drivers that communicate with instruments
    via serial or parallel port using pyserial

    :param port: Device name or port number
    :param baudrate: Baud rate such as 9600 or 115200
    :param bytesize: Number of data bits. Possible values = (5, 6, 7, 8)
    :param parity: Enable parity checking. Possible values = ('None', 'Even', 'Odd', 'Mark', 'Space')
    :param stopbits: Number of stop bits. Possible values = (1, 1.5, 2)
    :param xonoff: xonoff flow control enabled.
    :param rtscts: rtscts flow control enabled.
    :param dsrdtr: dsrdtr flow control enabled
    :param timeout: value in seconds, None or negative to wait for ever or 0 for non-blocking mode
    :param write_timeout: see timeout

    """

    RECV_TERMINATION = ''
    SEND_TERMINATION = ''
    ENCODING = 'ascii'

    #: -1 is mapped to get the number of bytes pending.
    RECV_CHUNK = -1

    #: communication parameters
    BAUDRATE = 9600
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    def __init__(self, port=1, timeout=1, write_timeout=1, **kwargs):
        super().__init__(**kwargs)
        self.TIMEOUT = timeout

        kw = {}
        for key in ('baudrate', 'bytesize', 'parity', 'stopbits',
                    'rtscts', 'dsrdtr', 'xonxoff'):
            kw[key] = kwargs.get(key, getattr(self, key.upper()))

        kw['bytesize'] = BYTESIZE[kw['bytesize']]
        kw['parity'] = PARITY[kw['parity']]
        kw['stopbits'] = STOPBITS[kw['stopbits']]

        self.serial = serial.Serial(None, timeout=timeout, writeTimeout=write_timeout, **kw)

        self.serial.port = port

        self.log_debug('Created pyserial port {}', self.serial.port)

    def raw_send(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument
        :param data: bytes
        """

        try:
            self.serial.write(data)
        except serial.SerialTimeoutException as e:
            raise LantzSerialTimeoutError(str(e))

    def raw_recv(self, size):
        """Receive raw bytes to the instrument.

        :param size: number of bytes to receive
        :return: received bytes
        :return type: bytes

        If a timeout is set, it may return less bytes than requested.
        If size == -1, then the number of available bytes will be read.

        """

        if size == -1:
            size = self.serial.inWaiting()
            if not size:
                return bytes()

        if not size:
            size = 1

        data = self.serial.read(size)

        return data

    def initialize(self):
        """Open port
        """
        if not self.serial.isOpen():
            self.log_debug('Opening port {}', self.serial.port)
            self.serial.open()
        else:
            self.log_debug('Port {} is already open', self.serial.port)

    def finalize(self):
        """Close port
        """
        self.log_debug('Closing port {}', self.serial.port)
        return self.serial.close()

    def is_open(self):
        return self.serial.isOpen()
