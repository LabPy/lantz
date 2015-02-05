# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.textual
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements a Mixin class for message based instruments,

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import time
from lantz.errors import LantzTimeoutError
from lantz.processors import ParseProcessor


class TextualMixin(object):
    """Mixin class for classes that communicate with instruments
    exchanging text messages.

    Ideally, transport classes should provide receive methods
    that support:
    1. query the number of available bytes
    2. read chunks of bytes (with and without timeout)
    3. read until certain character is found (with and without timeout)

    Most transport layers support 1 and 2 but not all support 3 (or only
    for a defined set of characters) and TextualMixin provides fallback
    a method.
    """

    #: Encoding to transform string to bytes and back as defined in
    #: http://docs.python.org/py3k/library/codecs.html#standard-encodings
    ENCODING = 'ascii'
    #: Termination characters for receiving data, if not given RECV_CHUNK
    #: number of bytes will be read.
    RECV_TERMINATION = ''
    #: Termination characters for sending data
    SEND_TERMINATION = ''
    #: Timeout in seconds of the complete read operation.
    TIMEOUT = 1
    #: Parsers
    PARSERS = {}
    #: Size in bytes of the receive chunk (-1 means all bytes in buffer)
    RECV_CHUNK = 1

    #: String containing the part of the message after RECV_TERMINATION
    #: Used in software based finding of termination character when
    #: RECV_CHUNK > 1
    _received = ''

    def raw_recv(self, size):
        """Receive raw bytes from the instrument. No encoding or termination
        character should be applied.

        This method must be implemented by base classes.

        :param size: number of bytes to receive.
        :return: received bytes, eom
        :rtype: bytes, bool
        """
        raise NotImplemented

    def raw_send(self, data):
        """Send raw bytes to the instrument. No encoding or termination
        character should be applied.

        This method must be implemented by base classes.

        :param data: bytes to be sent to the instrument.
        :param data: bytes.
        """
        raise NotImplemented

    def send(self, command, termination=None, encoding=None):
        """Send command to the instrument.

        :param command: command to be sent to the instrument.
        :type command: string.

        :param termination: termination character to override class defined
                            default.
        :param encoding: encoding to transform string to bytes to override class
                         defined default.

        :return: number of bytes sent.

        """
        if termination is None:
            termination = self.SEND_TERMINATION
        if encoding is None:
            encoding = self.ENCODING

        message = bytes(command + termination, encoding)
        self.log_debug('Sending {}', message)
        return self.raw_send(message)

    def recv(self, termination=None, encoding=None, recv_chunk=None):
        """Receive string from instrument.

        :param termination: termination character (overrides class default)
        :type termination: str
        :param encoding: encoding to transform bytes to string (overrides class default)
        :param recv_chunk: number of bytes to receive (overrides class default)
        :return: string encoded from received bytes
        """

        termination = termination or self.RECV_TERMINATION
        encoding = encoding or self.ENCODING
        recv_chunk = recv_chunk or self.RECV_CHUNK

        if not termination:
            return str(self.raw_recv(recv_chunk), encoding)

        if self.TIMEOUT is None or self.TIMEOUT < 0:
            stop = float('+inf')
        else:
            stop = time.time() + self.TIMEOUT

        received = self._received
        eom = False
        while not (termination in received or eom):
            if time.time() > stop:
                raise LantzTimeoutError
            raw_received = self.raw_recv(recv_chunk)
            received += str(raw_received, encoding)

        self.log_debug('Received {!r} (len={})', received, len(received))

        received, self._received = received.split(termination, 1)

        return received

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Send query to the instrument and return the answer

        :param command: command to be sent to the instrument
        :type command: string

        :param send_args: (termination, encoding) to override class defaults
        :param recv_args: (termination, encoding) to override class defaults
        """

        self.send(command, *send_args)
        return self.recv(*recv_args)

    def parse_query(self, command, *,
                    send_args=(None, None), recv_args=(None, None),
                    format=None):
        """Send query to the instrument, parse the output using format
        and return the answer.

        .. seealso:: TextualMixin.query and stringparser
        """
        ans = self.query(command, send_args=send_args, recv_args=recv_args)
        if format:
            parser = self.PARSERS.setdefault(format, ParseProcessor(format))
            ans = parser(ans)
        return ans
