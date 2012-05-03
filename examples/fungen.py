# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import argparse


    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=int, default=5678,
                        help='Serial port to connect to')

    args = parser.parse_args()

    import lantz.log
    lantz.log.log_to_socket(lantz.log.DEBUG)

    from lantz.drivers.examples import LantzSignalGenerator
    from lantz import Q_

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')
    Hz = Q_(1, 'Hz')

    with LantzSignalGenerator(host='localhost', port=args.port) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_form
            start_form(inst)
        else:
            print('The identification of this instrument is : ' + inst.idn)
            inst.amplitude = 3 * volt
            inst.offset = 200 * milivolt
            inst.frequency = 20 * Hz
            inst.output_enabled = True
            inst.waveform = 'sine'
            inst.refresh_async()
            inst.dout[1] = True
            print(inst.dout[1])
            print(inst.din[2])

