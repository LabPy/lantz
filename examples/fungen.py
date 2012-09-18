# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import argparse

    from lantz.drivers.examples import (LantzSignalGeneratorTCP, LantzSignalGeneratorSerial,
                                        LantzSignalGeneratorSerialVisa)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    subparser = subparsers.add_parser('serial')
    subparser.add_argument('-p', '--port', type=str, default='1',
                            help='Serial port')
    subparser.add_argument('-i', '--interactive', action='store_true',
                           help='Start interactive GUI')
    subparser.set_defaults(func=LantzSignalGeneratorSerial)

    subparser = subparsers.add_parser('serial-visa')
    subparser.add_argument('-r', '--resource_name', type=str, default='1',
                           help='Serial port')
    subparser.add_argument('-i', '--interactive', action='store_true',
                       help='Start interactive GUI')
    subparser.set_defaults(func=LantzSignalGeneratorSerialVisa)


    subparser = subparsers.add_parser('tcp')
    subparser.add_argument('-H', '--host', type=str, default='localhost',
                           help='TCP hostname')
    subparser.add_argument('-p', '--port', type=int, default=5678,
                            help='TCP port')
    subparser.add_argument('-i', '--interactive', action='store_true',
                           help='Start interactive GUI')
    subparser.set_defaults(func=LantzSignalGeneratorTCP)

    args = parser.parse_args()

    import lantz.log
    lantz.log.log_to_screen(lantz.log.DEBUG)
    lantz.log.log_to_socket(lantz.log.DEBUG)

    from lantz import Q_

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')
    Hz = Q_(1, 'Hz')

    print(args)
    with args.func(**dict(args._get_kwargs())) as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            print('The identification of this instrument is : ' + inst.idn)
            print(inst.amplitude)
            inst.amplitude = 3 * volt
            inst.offset = 200 * milivolt
            inst.frequency = 20 * Hz
            inst.output_enabled = True
            inst.waveform = 'sine'
            inst.refresh()
            inst.dout[1] = True
            print(inst.dout[1])
            print(inst.din[2])
            inst.calibrate()
