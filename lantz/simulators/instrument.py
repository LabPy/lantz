# -*- coding: utf-8 -*-
"""
    lantz.simulators.instrument
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    An simple framework to wrap a simulated instrument into
    a Serial or TCP receiver.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import logging
import socket
import socketserver
try:
    from lantz.serial import SerialDriver
except ImportError:
    pass

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S')

class SimError(Exception):
    pass


class SerialServer(SerialDriver):

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    ENCODING = 'ascii'

    TIMEOUT = None

    def __init__(self, port, instrument):
        self.instrument = instrument
        super().__init__(port=port)

    def serve_forever(self):
        self.initialize()
        try:
            while True:
                data = self.recv()
                logging.debug('%s -> inst: %s', self.serial.portstr, data)
                out = self.instrument.handle(data)
                self.send(out)
                logging.debug('%s <- inst: %s', self.serial.portstr, out)
        except Exception as e:
            logging.info(str(e))
        finally:
            pass

    def shutdown(self):
        self.finalize()


def create_TCPInstrumentHandler(instrument):
    class TCPHandler(socketserver.StreamRequestHandler):

        TERMINATION = '\n'
        ENCODING = 'ascii'

        def __init__(self, *args, **kwargs):
            self.instrument = instrument
            super().__init__(*args, **kwargs)

        def handle(self):
            try:
                while True:
                    data = self.rfile.readline()
                    logging.debug('%s -> inst: %s', self.client_address[0], data)
                    data = str(data, self.ENCODING)
                    out = self.instrument.handle(data)
                    out = bytes(out + self.TERMINATION, self.ENCODING)
                    self.wfile.write(out)
                    logging.debug('%s <- inst: %s', self.client_address[0], out)
            except socket.error as e:
                if e.errno == 32: # Broken pipe
                    logging.info('Client disconnected')
            finally:
                self.finish()

    return TCPHandler


class InstrumentHandler(object):

    CONVERSION = {float: '{:.4f}',
                  int: '{:d}',
                  str: '{}'}

    def handle(self, data):
        out = self.dispatch(data)
        out = self.CONVERSION[type(out)].format(out)
        return out

    def dispatch(self, data):
        data = data.strip()
        dict_key = None
        try:
            sig, value = data[0], data[1:].split()
            prop = value[0].lower()
            try:
                current = getattr(self, prop)
            except AttributeError:
                raise SimError
            if isinstance(current, dict):
                dict_key = getattr(self, prop + '_key_convert')(value[1])
            elif callable(current):
                try:
                    current = current(*value[1:])
                    if current is None:
                        return 'OK'
                except Exception as ex:
                    logging.exception('While calling %s with %s: %s', current, value, ex)
                    return 'ERROR'

            if sig == '?':
                if dict_key is not None:
                    return current[dict_key]
                return current
            elif sig == '!':
                if dict_key is not None:
                    cls = type(current[dict_key])
                    current[dict_key] = cls(value[2])
                else:
                    cls = type(current)
                    setattr(self, prop, cls(value[1]))
                return 'OK'
            return 'ERROR'
        except (SimError, IndexError) as e:
            return 'ERROR'
        except Exception as e:
            logging.exception('Exception {}'.format(e))
            raise Exception

def main_serial(instrument, args):
    return SerialServer(args.port, instrument)


def main_tcp(instrument, args):
    logging.info('Listening to %s:%s', args.host, args.port)
    Handler = create_TCPInstrumentHandler(instrument)
    server = socketserver.TCPServer((args.host, args.port), Handler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return server
