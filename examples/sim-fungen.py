
import time
import logging

try:
    from lantz.serial import SerialDriver
except ImportError:
    pass

import socket
import socketserver

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S')

class SimError(Exception):
    pass


class SerialServer(SerialDriver):

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    ENCODING = 'ascii'

    TIMEOUT = None

    def __init__(self, port, instrument_class):
        self.instrument = instrument_class()
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


def create_TCPInstrumentHandler(instrument_class):

    class TCPHandler(socketserver.StreamRequestHandler):

        TERMINATION = '\n'
        ENCODING = 'ascii'

        def __init__(self, *args, **kwargs):
            self.instrument = instrument_class()
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
                    current(*value[1:])
                except Exception as ex:
                    logging.exception('While calling %s with %s: %s', current, value, ex)
                    return 'ERROR'
                return 'OK'
            else:
                dict_key = None

            if sig == '?':
                if dict_key:
                    return current[dict_key]
                return current
            elif sig == '!':
                if dict_key:
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


class SimFunctionGenerator(InstrumentHandler):

    def __init__(self):
        super().__init__()
        self._amp = 0.0
        self.fre = 1000.0
        self.off = 0.0
        self._wvf = 0
        self.out = 0
        self.dou = {ch:0 for ch in range(1, 9)}
        self.din = {ch:0 for ch in range(1, 9)}

        self.din_key_convert = int
        self.dou_key_convert = int

    @property
    def idn(self):
        return 'FunctionGenerator Serial #12345'

    @property
    def wvf(self):
        return self._wvf

    @wvf.setter
    def wvf(self, value):
        if value < 0 or value > 3:
            raise SimError
        self._wvf = value

    @property
    def amp(self):
        return self._amp

    @amp.setter
    def amp(self, value):
        if value > 10 or value < 0:
            raise SimError
        self._amp = value

    def cal(self):
        logging.info('Calibrating ...')
        time.sleep(.1)

    def tes(self, level, repetitions):
        level = int(level)
        repetitions = int(repetitions)
        for rep in range(repetitions):
            logging.info('Testing level %s. (%s/%s)', level, rep + 1, repetitions)


def main_serial(args):
    return SerialServer(args.port, SimFunctionGenerator)


def main_tcp(args):
    logging.info('Listening to %s:%s', args.host, args.port)
    Handler = create_TCPInstrumentHandler(SimFunctionGenerator)
    server = socketserver.TCPServer((args.host, args.port), Handler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return server


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser('serial')
    subparser.add_argument('-p', '--port', type=str, default='1',
                            help='Serial port')
    subparser.set_defaults(func=main_serial)

    subparser = subparsers.add_parser('tcp')
    subparser.add_argument('-H', '--host', type=str, default='localhost',
                           help='TCP hostname')
    subparser.add_argument('-p', '--port', type=int, default=5678,
                            help='TCP port')
    subparser.set_defaults(func=main_tcp)

    args = parser.parse_args()
    server = args.func(args)

    logging.info('interrupt the program with Ctrl-C')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Ending')
    finally:
        server.shutdown()


