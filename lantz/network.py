# -*- coding: utf-8 -*-
"""
    lantz.network
    ~~~~~~~~~~~~~

    Implements a base class for drivers that communicate with instruments via TCP.

    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import socket

from . import Driver
from .driver import TextualMixin
from .errors import LantzTimeoutError


class LantzSocketTimeoutError(socket.timeout, LantzTimeoutError):
    pass


class TCPDriver(TextualMixin, Driver):
    """Base class for drivers that communicate with instruments via TCP.

    :param host: Address of the network resource
    :param port: Port number
    """

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    RECV_CHUNK = 1024

    def __init__(self, host='localhost', port=9997, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host_port = (host, port)

    def raw_send(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument.
        :param data: bytes.
        """
        try:
            self.socket.send(data)
        except socket.timeout as e:
            raise LantzSocketTimeoutError(str(e))

    def raw_recv(self, size):
        """Receive raw bytes to the instrument.

        :param size: number of bytes to receive.
        :return: received bytes.
        :return type: bytes.
        """
        try:
            return self.socket.recv(size)
        except socket.timeout as e:
            raise LantzSocketTimeoutError(str(e))

    def initialize(self):
        self.log_debug('Opening port {}', self.host_port)
        return self.socket.connect(self.host_port)

    def finalize(self):
        self.log_debug('Closing port {}', self.host_port)
        return self.socket.close()

    def is_open(self):
        return self.socket.isOpen()
