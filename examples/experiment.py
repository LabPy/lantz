# -*- coding: utf-8 -*-
from lantz.drivers.examples import LantzSignalGeneratorTCP
from lantz.drivers.examples import LantzVoltmeterTCP

import lantz.log
lantz.log.log_to_screen(lantz.log.DEBUG)
lantz.log.log_to_socket(lantz.log.DEBUG)

from lantz import Q_

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')

def simple_test():
    with LantzSignalGeneratorTCP(host='localhost', port=5678) as actuator:
        print('The identification of the actuator is : ' + actuator.idn)
        actuator.amplitude = 3 * volt
        actuator.offset = 200 * milivolt
        actuator.frequency = 20 * Hz
        actuator.output_enabled = True
        actuator.waveform = 'sine'
        actuator.refresh()
        actuator.dout[1] = True
        print(actuator.dout[1])
        print(actuator.din[2])
        actuator.calibrate()
        actuator.self_test(1, 3)

    with LantzVoltmeterTCP(host='localhost', port=5679) as sensor:
        print('The identification of the sensor is : ' + sensor.idn)
        sensor.range[0] = 10
        sensor.self_test()
        sensor.refresh()
        print(sensor.voltage[0])
        print(sensor.voltage[1])
        sensor.calibrate()
        sensor.auto_range(0)
        print(sensor.range[0])
        print(sensor.voltage[0])

def test_experiment():
    import time
    actuator = LantzSignalGeneratorTCP(host='localhost', port=5678)
    sensor = LantzVoltmeterTCP(host='localhost', port=5679)
    actuator.initialize()
    sensor.initialize()

    actuator.amplitude = 3 * volt
    actuator.offset = 500 * milivolt
    actuator.frequency = 1 * Hz
    actuator.output_enabled = True
    actuator.waveform = 'sine'
    sensor.range[0] = 10
    sensor.range[1] = 10

    data = []
    start_time = time.time()
    try:
        lantz.log.log_to_screen(lantz.log.ERROR)
        while time.time() - start_time < 10:
            datapoint = (time.time()-start_time,
                         sensor.voltage[0],
                         sensor.voltage[1])
            data.append(datapoint)
        print(data)
    except KeyboardInterrupt:
        print('Ending ')
    finally:
        actuator.finalize()
        sensor.finalize()


if __name__ == '__main__':
    simple_test()
    test_experiment()

