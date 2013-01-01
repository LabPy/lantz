"""
    lantz.log
    ~~~~~~~~~

    Implements logging support for Lantz.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import types

import pickle

import select
import socket
import struct
import logging
import threading

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from logging.handlers import SocketHandler, DEFAULT_TCP_LOGGING_PORT, DEFAULT_UDP_LOGGING_PORT

from socketserver import (ThreadingUDPServer, DatagramRequestHandler,
                          ThreadingTCPServer, StreamRequestHandler)


from stringparser import Parser

class _LogRecord(logging.LogRecord):

    def getMessage(self):
        """
        Return the message for this LogRecord.

        Return the message for this LogRecord after merging any user-supplied
        arguments with the message.
        """
        msg = str(self.msg)
        if self.args:
            msg = msg.format(*self.args)
        return msg


def _makeRecord(name, level, fn, lno, msg, args, exc_info,
                func=None, extra=None, sinfo=None):
    """
    A factory method which can be overridden in subclasses to create
    specialized LogRecords.
    """
    rv = _LogRecord(name, level, fn, lno, msg, args, exc_info, func,
                    sinfo)
    if extra is not None:
        for key in extra:
            if (key in ["message", "asctime"]) or (key in rv.__dict__):
                raise KeyError("Attempt to overwrite %r in LogRecord" % key)
            rv.__dict__[key] = extra[key]
    return rv


def get_logger(name, add_NullHandler=True, patch_makeRecord=True):
    """Return a logger with the specified name, creating if necessary.

    if patch_makeRecord, the logger makeRecord will be replaced with a PEP3101 compatible version.
    """
    logger = logging.getLogger(name)
    if add_NullHandler:
        logger.addHandler(logging.NullHandler())
    if patch_makeRecord:
        logger.makeRecord = _makeRecord
    return logger

LOGGER = get_logger('lantz')

try:
    from colorama import Fore, Back, Style, init as colorama_init
    colorama_init()
    colorama = True
    DEFAULT_FMT = Style.NORMAL + '{asctime} <color>{levelname:8s}</color>' + Style.RESET_ALL + ' {message}'
except Exception as e:
    LOGGER.info('Log will not be colorized. Could not import colorama: {}', e)
    colorama = False
    DEFAULT_FMT = '{asctime} {levelname:8s} {message}'


class ColorizingFormatter(logging.Formatter):
    """Color capable logging formatter.

    Use <color> </color> to enclose text to colorize.
    """


    SPLIT_COLOR = Parser('{0:s}<color>{1:s}</color>{2:s}')

    SCHEME = {'bw': {logging.DEBUG: '',
                     logging.INFO: '',
                     logging.WARNING: '',
                     logging.ERROR: '',
                     logging.CRITICAL: ''}
             }

    @classmethod
    def add_color_schemes(cls):
        cls.format = cls.color_format
        cls.SCHEME.update(bright={DEBUG: Style.NORMAL,
                                  INFO: Style.NORMAL,
                                  WARNING: Style.BRIGHT,
                                  ERROR: Style.BRIGHT,
                                  CRITICAL: Style.BRIGHT},
                          simple={DEBUG: Fore.BLUE + Style.BRIGHT,
                                  INFO: Back.WHITE + Fore.BLACK,
                                  WARNING: Fore.YELLOW + Style.BRIGHT,
                                  ERROR: Fore.RED + Style.BRIGHT,
                                  CRITICAL: Back.RED + Fore.WHITE + Style.BRIGHT},
                          whitebg={DEBUG: Fore.BLUE + Style.BRIGHT,
                                   INFO: Back.WHITE + Fore.BLACK,
                                   WARNING: Fore.YELLOW + Style.BRIGHT,
                                   ERROR: Fore.RED + Style.BRIGHT,
                                   CRITICAL: Back.RED + Fore.WHITE + Style.BRIGHT},
                          blackbg={DEBUG: Fore.BLUE + Style.BRIGHT,
                                   INFO: Fore.GREEN,
                                   WARNING: Fore.YELLOW + Style.BRIGHT,
                                   ERROR: Fore.RED + Style.BRIGHT,
                                   CRITICAL: Back.RED + Fore.WHITE + Style.BRIGHT}
                          )

    def __init__(self, fmt=DEFAULT_FMT, datefmt='%H:%M:%S', style='%', scheme='bw'):
        super().__init__(fmt, datefmt, style)
        self.scheme = scheme

    @property
    def scheme(self):
        return self.scheme

    @scheme.setter
    def scheme(self, value):
        if isinstance(value, str):
            self._scheme = self.SCHEME[value]
        else:
            self._scheme = value

    def colorize(self, message, record):
        """Colorize message based on record level
        """
        if record.levelno in self._scheme:
            color = self._scheme[record.levelno]
            return color + message + Style.RESET_ALL

        return message

    def color_format(self, record):
        """Format record into string, colorizing the text enclosed
        within <color></color>
        """
        message = super().format(record)
        parts = message.split('\n', 1)
        if '<color>' in parts[0] and '</color>' in parts[0]:
            bef, dur, aft = self.SPLIT_COLOR(parts[0])
            parts[0] = bef + self.colorize(dur, record) + aft
        message = '\n'.join(parts)
        return message


if colorama:
    ColorizingFormatter.add_color_schemes()


class BaseServer(object):
    """Mixin for common server functionality
    """

    allow_reuse_address = True

    def __init__(self, handler, timeout):
        self._record_handler = handler
        self._stop = threading.Event()
        self.timeout = timeout

    def handle_record(self, record):
        self._record_handler(record)

    def serve_until_stopped(self):
        while not self._stop.isSet():
            rd, wr, ex = self.select()
            if rd:
                self.handle_request()
        self.server_close()

    def select(self):
        return select.select([self.socket.fileno()], [], [], self.timeout)

    def stop(self):
        self._stop.set()


class LogRecordStreamHandler(StreamRequestHandler):
    """ Handler for a streaming logging request. It basically logs the record
    using whatever logging policy is configured locally.
    """

    def handle(self):
        """Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            try:
                chunk = self.connection.recv(4)
                if len(chunk) < 4:
                    break
                slen = struct.unpack(">L", chunk)[0]
                chunk = self.connection.recv(slen)
                while len(chunk) < slen:
                    chunk = chunk + self.connection.recv(slen - len(chunk))
                obj = pickle.loads(chunk)
                record = _LogRecord(None, None, "", 0, "", (), None, None)
                record.__dict__.update(obj)
                self.server.handle_record(record)
            except socket.error as e:
                if not isinstance(e.args, tuple):
                    raise e
                else:
                    if e.args[0] != logging.RESET_ERROR:
                        raise e
                    break


class LoggingTCPServer(ThreadingTCPServer, BaseServer):
    """A simple-minded TCP socket-based logging receiver suitable for test
    purposes.
    """

    allow_reuse_address = True

    def __init__(self, addr, handler, timeout=1):
        ThreadingTCPServer.__init__(self, addr, LogRecordStreamHandler)
        BaseServer.__init__(self, handler, timeout)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


class LogRecordDatagramHandler(DatagramRequestHandler):
    """Handler for a datagram logging request. It basically logs the record
    using whatever logging policy is configured locally.
    """
    def handle(self):
        chunk = self.packet
        slen = struct.unpack(">L", chunk[:4])[0]
        chunk = chunk[4:]
        assert len(chunk) == slen
        obj = pickle.loads(chunk)
        record = _LogRecord(None, None, "", 0, "", (), None, None)
        record.__dict__.update(obj)
        self.server.handle_record(record)

    def finish(self):
        pass


class LoggingUDPServer(ThreadingUDPServer, BaseServer):
    """A simple-minded UDP datagram-based logging receiver suitable for test
    purposes.
    """

    def __init__(self, addr, handler, timeout=1):
        ThreadingUDPServer.__init__(self, addr, LogRecordDatagramHandler)
        BaseServer.__init__(self, handler, timeout)


class SocketListener(object):
    """Print incoming log recored to tcp and udp ports.
    """

    def __init__(self, tcphost, udphost):
        self.tcp_addr = get_address(tcphost)
        self.udp_addr = get_address(udphost, DEFAULT_UDP_LOGGING_PORT)
        self.start()

    def start(self):
        self._lock = threading.RLock()

        s = LoggingTCPServer(self.tcp_addr, self.on_record, 0.5)
        self.tcp_server = s
        self.tcp_thread = t = threading.Thread(target=s.serve_until_stopped)
        t.setDaemon(True)
        t.start()

        s = LoggingUDPServer(self.udp_addr, self.on_record, 0.5)
        self.udp_server = s
        self.udp_thread = t = threading.Thread(target=s.serve_until_stopped)
        t.setDaemon(True)
        t.start()

    def stop(self):
        self.tcp_server.stop()
        self.tcp_thread.join()
        self.udp_server.stop()
        self.udp_thread.join()

    def on_record(self, record):
        pass


def log_to_socket(level=logging.INFO, host='localhost',
                  port=DEFAULT_TCP_LOGGING_PORT):
    """Log all Lantz events to a socket with a specific host address and port.

    :param level: logging level for the lantz handler
    :param host: socket host (default 'localhost')
    :param port: socket port (default DEFAULT_TCP_LOGGING_PORT as defined in the
                 logging module)
    :return: lantz logger
    """
    handler = SocketHandler(host, port)
    handler.setLevel(level)
    LOGGER.addHandler(handler)
    if LOGGER.getEffectiveLevel() > level:
        LOGGER.setLevel(level)
    return LOGGER


def log_to_screen(level=logging.INFO, scheme='blackbg'):
    """Log all Lantz events to the screen with a colorized terminal

    :param level: logging level for the lantz handler
    :param scheme: color scheme. Valid values are 'bw', 'bright', 'simple', 'whitebg', 'blackg'
    :return: lantz logger
    """
    handler = logging.StreamHandler()
    handler.setLevel(level)
    if not colorama:
        scheme = 'bw'
    handler.setFormatter(ColorizingFormatter(scheme=scheme, style='{'))
    LOGGER.addHandler(handler)
    if LOGGER.getEffectiveLevel() > level:
        LOGGER.setLevel(level)
    return LOGGER


def get_address(value, default_port=DEFAULT_TCP_LOGGING_PORT):
    """Split host:port string into (host, port) tuple

    :param value: 'host:port' string
    :param default_port: port used if not given
    :return: (host, port)
    """
    value = value.strip()
    if ':' not in value[:-1]:
        result = value, default_port
    else:
        h, p = value.split(':')
        result = h, int(p)
    return result
