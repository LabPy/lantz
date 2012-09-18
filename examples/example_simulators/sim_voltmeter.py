# -*- coding: utf-8 -*-
import time
import logging

from sim_instrument import SimError, InstrumentHandler, main_tcp, main_serial

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S')


class SimVoltmeter(InstrumentHandler):

    def __init__(self, get_func1, get_func2):
        super().__init__()
        self._get_func = (get_func1, get_func2)
        self.vranges = (0.1, 1, 10, 100, 1000)
        self.range = {0: 4, 1: 4}
        self.range_key_convert = int

    @property
    def idn(self):
        return 'Simple DC Voltmeter #54321'

    def cal(self):
        logging.info('Calibrating ...')
        time.sleep(.1)

    def arange(self, ain):
        ain = int(ain)
        if ain not in (0, 1):
            raise SimError
        logging.info('Autoselecting range for input %d...', ain)
        value = self._get_func[ain]()
        for k in range(4, 0, -1):
            if self.vranges[k] > value or -self.vranges[k] < value:
                self.range[ain] = k
        logging.info('Selected range: %f V for input %d',
                            self.vranges[self.range[ain]], ain)

    def tes(self):
        logging.info('Testing...')

    def meas(self, ain):
        ain = int(ain)
        if ain not in (0, 1):
            raise SimError
        value = self._get_func[ain]()
        print(self.vranges)
        print(self.range)
        print(ain)
        max_val = self.vranges[self.range[ain]] * 1.2
        if value > max_val or value < -max_val:
            value = max_val
        return value


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
    subparser.add_argument('-p', '--port', type=int, default=5679,
                            help='TCP port')
    subparser.set_defaults(func=main_tcp)

    import random
    def measure():
        return random.random * 10 - 5

    instrument = SimVoltmeter(measure, measure)
    args = parser.parse_args()
    print(args)
    server = args.func(instrument, args)

    logging.info('interrupt the program with Ctrl-C')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Ending')
    finally:
        server.shutdown()
