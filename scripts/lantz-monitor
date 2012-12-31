#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
    lantz-monitor
    ~~~~~~~~~~~~~

    Text based tool to monitor Lantz messages logged to a socket.


    :copyright: 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import pickle
import logging
import itertools
from io import StringIO
from fnmatch import fnmatch

from collections import OrderedDict, defaultdict

import colorama
from colorama import Fore, Back, Style

from lantz.stringparser import Parser
from lantz.log import ColorizingFormatter, SocketListener

try:
    from msvcrt import getch
except ImportError:
    import sys, tty, termios
    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

COLS = 80


def restyle(text, new):
    """Replace style with a new one.

    :param text: the styled text.
    :param new: the new style, a value from colorame.Style.
    """
    for style in (Style.DIM, Style.BRIGHT, Style.NORMAL):
        text = text.replace(style, new)
    return text


def pos(row, column):
    """Move cursor to a given row and column.
    """
    return '\x1b[%d;%dH' % (row, column)


def clear():
    """Clear screen.
    """
    return '\x1b[2J'

RETITLE = logging.LogRecord('', 0, '', '', '', '', '', '')
REDRAW = logging.LogRecord('', 0, '', '', '', '', '', '')


def level_name(level):
    """For a level defined in the logging module, return its name
    """
    if level == logging.DEBUG:
        return 'DEBUG'
    elif level == logging.INFO:
        return 'INFO'
    elif level == logging.WARNING:
        return 'WARNING'
    elif level == logging.CRITICAL:
        return 'CRITICAL'
    elif level == logging.ERROR:
        return 'ERROR'
    return str(level)


class MessageListFormatter(ColorizingFormatter):
    """Log formatter for Message List View.

    :param queues: The list of queues with sorted logging messages. Each queue
                   corresponds to one instrument.
    """

    FMT = Style.NORMAL + '%(asctime)s <color>%(levelname)-8s</color>' + Style.RESET_ALL + ' %(message)s'

    FIRST_ROW = 2
    ROWS = 24

    def __init__(self, queues, *args, **kwargs):
        super().__init__(fmt=self.FMT, datefmt='%H:%M:%S', *args, **kwargs)
        self.queues = queues
        self.redraw = True
        self._title = ''
        self._current = ''
        self.last_records = []

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        self.redraw = True

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.redraw = True

    SEL = Style.BRIGHT + Back.RED + Fore.WHITE

    def format(self, record):
        if record is RETITLE:
            return pos(0, 0) + self.title

        if not record is REDRAW:
            self.last_records.append(record)
            if len(self.last_records) > self.ROWS:
                self.last_records = self.last_records[-self.ROWS:]

        buf = StringIO()
        self.redraw = False
        buf.write(clear())
        buf.write(pos(0, 0))
        buf.write(self.title)
        for row, saved_record in zip(range(self.ROWS), self.last_records):
            buf.write(pos(row + self.FIRST_ROW, 0))
            queue = saved_record.lantz_driver, saved_record.lantz_name
            if queue == self._current:
                buf.write(self.SEL + ' ' + Style.RESET_ALL)
            else:
                buf.write(' ')
            buf.write(queue[1].ljust(30))

            buf.write(super().format(saved_record))

        return buf.getvalue()


class DriverListFormatter(ColorizingFormatter):
    """Log formatter for Driver List View.

    :param queues: The list of queues with sorted logging messages. Each queue
                   corresponds to one instrument.
    """

    FMT = Style.NORMAL + '%(asctime)s <color>%(levelname)-8s</color>' + Style.NORMAL + ' %(message)s'

    FIRST_ROW = 2
    LOG_HEIGHT = 4

    def __init__(self, queues, *args, **kwargs):
        super().__init__(fmt=self.FMT, datefmt='%H:%M:%S', *args, **kwargs)
        self.queues = queues
        self.redraw = True
        self._title = ''
        self._current = ''

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        self.redraw = True

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.redraw = True

    def format(self, record):
        if record is RETITLE:
            return pos(0, 0) + self.title

        buf = StringIO()
        if self.redraw or record is REDRAW:
            self.redraw = False
            buf.write(clear())
            buf.write(pos(0, 0))
            buf.write(self.title)
            self._write_view(buf)
        else:
            self._write_record(record, buf)
        return buf.getvalue()

    def _write_view(self, buf):
        for num, (name, state) in enumerate(self.queues.items()):
            self._write_record_helper(num, name, state, buf)

    def _write_record(self, record, buf):
        queue = record.lantz_driver, record.lantz_name
        num = list(self.queues.keys()).index(queue)
        state = self.queues[queue]
        self._write_record_helper(num, queue, state, buf)

    def _write_record_helper(self, num, name, state, buf):
        row = num * self.LOG_HEIGHT + self.FIRST_ROW
        buf.write(pos(row, 0))

        if name == self._current:
            buf.write(Back.RED + Fore.WHITE + Style.BRIGHT)
            buf.write((' ' + '.'.join(name)).ljust(COLS))
        else:
            buf.write(Back.WHITE + Fore.BLACK)
            buf.write((' ' + '.'.join(name)).ljust(COLS))
        buf.write(Style.RESET_ALL)
        for subrow, saved_record in zip(range(1, self.LOG_HEIGHT), state.last_records):
            buf.write(pos(row + subrow, 0))
            buf.write('  ' + super().format(saved_record))


class DriverFormatter(ColorizingFormatter):
    """Log formatter for Driver View.

    :param queues: The list of queues with sorted logging messages. Each queue
                   corresponds to one instrument.
    """

    FIRST_ROW = 3
    COL_WIDTH = 40
    PROP_HEIGHT = 15
    LOG_HEIGHT = 4

    FMT = Style.NORMAL + '%(asctime)s <color>%(levelname)-8s</color>' + Style.NORMAL + ' %(message)s'

    def __init__(self, queues, *args, **kwargs):
        super().__init__(fmt=self.FMT, datefmt='%H:%M:%S', *args, **kwargs)
        self.queues = queues
        self.redraw = True
        self._title = ''
        self._current = ''

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        self.redraw = True

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.redraw = True

    def format(self, record):
        if record is RETITLE:
            return pos(0, 0) + self.title

        buf = StringIO()
        if self.redraw or record is REDRAW:
            self.REDRAW = False
            buf.write(clear())
            buf.write(pos(0, 0))
            buf.write(self.title)
            self._write_view(buf)
        else:
            self._write_record(record, buf)

        return buf.getvalue()

    def _write_view(self, buf):
        current = self._current
        buf.write(pos(2, 0))
        buf.write(Back.RED + Fore.WHITE + Style.BRIGHT)
        buf.write((' ' + '.'.join(current)).ljust(COLS))
        buf.write(pos(self.FIRST_ROW + self.PROP_HEIGHT, 0))
        buf.write(Style.RESET_ALL)
        buf.write(Back.WHITE + Fore.BLACK)
        buf.write((' Messages').ljust(COLS))
        buf.write(Style.RESET_ALL)
        if current not in self.queues:
            return
        state = self.queues[current]
        for num, (name, value) in enumerate(state.feats.items()):
            col = num // self.PROP_HEIGHT * self.COL_WIDTH
            row = num % self.PROP_HEIGHT + self.FIRST_ROW
            self._write_property(row, col, name, value, buf)

        self._write_log_helper(state, buf)

    def _write_log_helper(self, state, buf):
        row = self.FIRST_ROW + self.PROP_HEIGHT
        for subrow, saved_record in zip(range(1, self.PROP_HEIGHT), state.last_records):
            buf.write(pos(row + subrow, 0))
            buf.write('  ' + super().format(saved_record))

    def _write_record(self, record, buf):
        queue = record.lantz_driver, record.lantz_name
        state = self.queues[queue]
        if hasattr(record, 'lantz_feat'):
            if queue not in self.queues:
                return
            name, value = record.lantz_feat
            num = list(state.feats.keys()).index()
            col = num // self.PROP_HEIGHT * self.COL_WIDTH
            row = num % self.PROP_HEIGHT + self.FIRST_ROW
            self._write_property(row, col, name, value, buf)

        self._write_record_helper(0, '.'.join(queue), state, buf)

    def _write_property(self, row, col, name, value, buf):
        if name:
            buf.write(pos(row, col + 0))
            buf.write(name)
        buf.write(pos(row, col + 20))
        buf.write(value)


#: Parser for set messages.
SETTER = Parser('{0:s} was set to {1:s}')

#: Parser for get messages.
GETTER = Parser('Got {1:s} for {0:s}')


class InstrumentState(object):
    """A class to build up the state of the instrument by parsing incoming
    log records. It also remember the last received log records.
    """

    #: Number of log records to remember.
    REMEMBER = 10

    def __init__(self):
        self.count = 0
        self.last_records = []
        self.feats = OrderedDict()

    def handle(self, record):
        self.count += 1
        self.last_records.append(record)
        if len(self.last_records) > self.REMEMBER:
            self.last_records = self.last_records[-self.REMEMBER:]
        if hasattr(record, 'lantz_feat'):
            self.feats[record.lantz_feat[0]] = record.lantz_feat[1]

class LantzMonitor(SocketListener):
    """Text UI to display log records incoming via tcp or udp.
    """

    def __init__(self, tcphost, udphost, level=logging.INFO,
                 filter_='lantz.*'):
        super().__init__(tcphost, udphost)

        self.queues = defaultdict(InstrumentState)
        self.filter = filter_ or '*'
        self._level = level
        self.formatters = [MessageListFormatter(self.queues),
                           DriverListFormatter(self.queues),
                           DriverFormatter(self.queues)]
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(self.formatters[0])
        self.retitle('Welcome, press h for help.')

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value
        self.retitle()

    def loop(self):
        view = 0
        queue = 0
        last_help = 0
        messages = itertools.cycle(('Change logging level: 1-5',
                                    'Change view: [ ]',
                                    'Select instrument: , .',
                                    'Quit: q',
                                    'Press h for help.'))
        while 1:
            command = getch()

            if command in ('1', '2', '3', '4', '5'):
                self.level = int(command) * 10

            elif command in ('[', ']'):
                view = (view + (-1 if command == '[' else 1)) % 3
                self.handler.setFormatter(self.formatters[view])
                self.handler.handle(REDRAW)

            elif command in (',', '.'):
                queue = (queue + (-1 if command == ',' else 1)) % len(self.queues)
                for formatter in self.formatters:
                    formatter.current = list(self.queues.keys())[queue]
                self.handler.handle(REDRAW)

            elif command in ('q', chr(3)):
                raise SystemExit

            elif command == 'h':
                self.retitle(next(messages))

            elif command in (chr(13), ):
                view = 2
                self.handler.setFormatter(self.formatters[view])
                self.handler.handle(REDRAW)

            else:
                self.retitle("Unknown command '{}' (ord {})".format(command, ord(command)))

    def retitle(self, message=''):
        title = '<> Lantz <> Queues: {:3d} <> Level: {:8s} <> {}'.format(len(self.queues),
                                                                    level_name(self._level),
                                                                    message)
        title = Back.BLUE + Fore.WHITE + title.ljust(COLS) + Style.RESET_ALL
        for formatter in self.formatters:
            formatter.title = title
        self.handler.handle(RETITLE)

    def on_record(self, record):
        if not fnmatch(record.name or '', self.filter):
            return
        if record.levelno < self.level:
            return
        with self._lock:
            queue = record.lantz_driver, record.lantz_name
            if queue not in self.queues:
                self.queues[queue] = InstrumentState()
                self.retitle()
            if len(self.queues) == 1:
                for formatter in self.formatters:
                    formatter.current = queue
            self.queues[queue].handle(record)
            self.handler.handle(record)


if __name__ == '__main__':
    colorama.init()

    import argparse

    parser = argparse.ArgumentParser(description='Text based tool to monitor Lantz messages logged to a socket..')
    parser.add_argument('-t', '--tcp', default='0.0.0.0', dest='tcphost',
                        help='Where to listen for TCP traffic (host[:port])')
    parser.add_argument('-u', '--udp', default='0.0.0.0', dest='udphost',
                        help='Where to listen for UDP traffic (host[:port])')
    parser.add_argument('--filter', default=None,
                        help='Filter to apply to incomming records')
    parser.add_argument('-l', '--level', choices=range(1, 6), default=2, type=int,
                        help='Logging level (debug, info, warn, error, critical')
    args = parser.parse_args()

    print(clear())
    monitor = LantzMonitor(args.tcphost, args.udphost,
                           args.level * 10, args.filter)

    try:
        monitor.loop()
    except (KeyboardInterrupt, SystemExit):
        monitor.stop()
    print(clear())
    print('Lantz Monitor stopped')
