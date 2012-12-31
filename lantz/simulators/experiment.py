# -*- coding: utf-8 -*-
"""
    lantz.simulators.experiment
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    An experiment connecting an actuator and a sensor.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

from threading import Thread, activeCount
from time import sleep
import logging
import queue

from . import fungen, voltmeter, instrument

class StudiedObject(object):
    def __init__(self, read_from_actuator):
        self.read = read_from_actuator
        self.memory = queue.Queue()
        self._present_value = 0

    def action(self):
        in_value = self.read()
        self.memory.put(in_value)
        if self.memory.empty() or self.memory.qsize()<10:
            self._present_value = 0
        else:
            self._present_value = 0.5*self.memory.get()

    def present_value(self):
        return self._present_value


class Namespace():
    def __init__(self, host, port):
        self.host = host
        self.port = port

def create_actuator_server(actuator):
    logging.info('Creating fungen server')
    args = Namespace('localhost', 5678)
    actuator_server = instrument.main_tcp(actuator, args)
    logging.info('Fungen: interrupt the program with Ctrl-C')
    try:
        actuator_server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Fungen: Ending')
    finally:
        actuator_server.shutdown()

def create_sensor_server(sensor):
    logging.info('Creating voltmeter server')
    args = Namespace('localhost', 5679)
    sensor_server = instrument.main_tcp(sensor, args)
    logging.info('Voltmeter: interrupt the program with Ctrl-C')
    try:
        sensor_server.serve_forever()
    except KeyboardInterrupt:
        logging.info('Voltmeter: Ending')
    finally:
        sensor_server.shutdown()

def serve_forever(obj):
    try:
        while activeCount() == 3:
            obj.action()
            sleep(0.1)
    except KeyboardInterrupt:
        logging.info('Experiment: Ending.')

def main():
    fg = fungen.SimFunctionGenerator()
    obj = StudiedObject(fg.generator_output)
    vm = voltmeter.SimVoltmeter(obj.present_value, fg.generator_output)
    fthread = Thread(target=create_actuator_server, args=(fg, ))
    vthread = Thread(target=create_sensor_server, args=(vm, ))
    fthread.daemon = True
    vthread.daemon = True
    fthread.start()
    vthread.start()

    sleep(1)
    serve_forever(obj)

if __name__ == "__main__":
    main()
