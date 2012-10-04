#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lantz.drivers.ni.daqmx import System

def bulleted_list(title, elements, indent=2, bullet='-', details=False):
    elements = tuple(elements)
    sp = ' ' * indent
    print('{}{} {}: {}'.format(sp, bullet, title, len(elements)))
    if details:
        sp += ' '
        for element in elements:
            print(' {}{} {}'.format(sp, bullet, element))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print debug information')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List details')

    args = parser.parse_args()

    if args.debug:
        import lantz.log
        lantz.log.log_to_screen(lantz.log.DEBUG)

    inst = System()
    print('DAQmx Version: {}.{}'.format(inst.version[0], inst.version[1]))

    print('')
    print('System Devices: {}'.format(len(inst.devices)))
    for key, value in inst.devices.items():
        print('-- {} --'.format(key))
        print(' - Is Simulated: {}'.format(value.is_simulated))
        print(' - Product Type: {}'.format(value.product_type))
        print(' - Product Number: {}'.format(value.product_number))
        print(' - Product Type: {}'.format(value.product_type))
        print(' - Serial Number: {}'.format(value.serial_number))
        print(' - Bus Info: {}'.format(value.bus_info))
        bulleted_list('AI Channels', value.analog_input_channels, details=args.list)
        bulleted_list('AI Channels', value.analog_input_channels, details=args.list)
        bulleted_list('AO Channels', value.analog_output_channels, details=args.list)
        bulleted_list('DI Lines', value.digital_input_lines, details=args.list)
        bulleted_list('DO Lines', value.digital_output_lines, details=args.list)
        bulleted_list('DI Ports', value.digital_input_ports, details=args.list)
        bulleted_list('DI Ports', value.digital_output_ports, details=args.list)
        bulleted_list('CI Ports', value.counter_input_channels, details=args.list)
        bulleted_list('CO Ports', value.counter_output_channels, details=args.list)
    print('')
    print('System Tasks: {}'.format(len(inst.tasks)))
    for key, value in inst.tasks.items():
        print('-- {} --'.format(key))
        print(' - Type: {}'.format(value.io_type))
        print(' - Task Complete: {}'.format(value.is_done))
        bulleted_list('Devices', value.devices.keys(), details=args.list)
        bulleted_list('Channels', value.channels.keys(), details=args.list)
    print('')
    print('System Channels: {}'.format(len(inst.channels)))
