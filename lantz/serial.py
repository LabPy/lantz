# -*- coding: utf-8 -*-
"""
    lantz.serial
    ~~~~~~~~~~~~

    Implements base classes for drivers that communicate with instruments
    via serial or parallel port.

    :copyright: (c) 2011 by Lantz Authors, see AUTHORS for more details.
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

PARITY = {'None': serial.PARITY_NONE, 'Even': serial.PARITY_EVEN,
          'Odd': serial.PARITY_ODD, 'Mark': serial.PARITY_MARK,
          'Space': serial.PARITY_SPACE}

#:
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
    :param flow: Bitflag for flow control mode (0 = None, 1 = xonoff, 2 = rtscts, 3 = dsrdtr)
    :param timeout: value in seconds, None to wait for ever or 0 for non-blocking mode
    :param write_timeout: see timeout

    """

    RECV_TERMINATION = ''
    SEND_TERMINATION = ''
    ENCODING = 'ascii'

    def __init__(self, port=1, baudrate=9600, bytesize=8, parity='None',
                 stopbits=1, flow=0, timeout=None, write_timeout=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        bytesize = BYTESIZE[bytesize]
        parity = PARITY[parity]
        stopbits = STOPBITS[stopbits]
        self.timeout = timeout
        self.serial = serial.Serial(None, baudrate,
                                    stopbits, timeout,
                                    bool(flow & 1), bool(flow & 2),
                                    write_timeout, bool(flow & 3))
        self.serial.port = port

        self.log_debug('Created pyserial port {}'.format(self.serial))

    def raw_send(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument
        :param data: bytes
        """

        try:
            self.serial.write(data)
        except serial.SerialTimeoutException as e:
            raise LantzSerialTimeoutError(str(e))

    def raw_recv(self, size=-1):
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
            size = 1
        #self.log_debug('waiting {}'.format(size))
        data = self.serial.read(size)
        #self.log_debug(data)
        return data

    def initialize(self):
        """Open port
        """
        if not self.serial.isOpen():
            self.log_debug('Opening port {}'.format(self.serial.port))
            self.serial.open()
        else:
            self.log_debug('Port {} is already open'.format(self.serial.port))

    def finalize(self):
        """Close port
        """
        self.log_debug('Closing port {}'.format(self.serial.port))
        return self.serial.close()

    def is_open(self):
        return self.serial.isOpen()
