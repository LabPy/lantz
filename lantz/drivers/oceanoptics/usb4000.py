# -*- coding: utf-8 -*-
"""
    lantz.drivers.oceanoptics.usb4000
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Driver for spectrograph.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""


import struct
import numpy as np

from pyvisa.errors import VisaIOError

from lantz import Feat, DictFeat
from lantz.drivers.legacy.usb import USBDriver, usb_find_desc

__all__ = ['USB4000']

commands = {
    0x01: ('init', 'initialize USB4000'), 
    0x02: ('set_i', 'set integration time in uS'), 
    0x03: ('set_strobe', 'set strobe enable status'), 
    0x05: ('ask', 'query information'), 
    0x06: ('write', 'write information'), 
    0x09: ('get_spectra', 'request spectra'),
    0x0A: ('set_trigger', 'set trigger mode'),
    0x0B: ('num_plugins', 'query number of plug-in accessories present'),
    0x0C: ('plugin_ids', 'query plug-in identifiers'),
    0x0D: ('detect_plugins', 'detect plug-ins'),
    0x60: ('read_i2c', 'general I2C read'),
    0x61: ('write_i2c', 'general I2C write'),
    0x62: ('spi_io', 'general spi I/O'),
    0x68: ('read_psoc', 'PSOC read'),
    0x69: ('write_psoc', 'PSOC write'),
    0x6A: ('write_reg', 'write register information'),
    0x6B: ('read_reg', 'read register information'),
    0x6C: ('read_temp', 'read PCB temperature'),
    0x6D: ('read_calib', 'read irradiance calibration factors'),
    0x6E: ('write_calib', 'write irradiance calibration factors'),
    0xFE: ('ask_2', 'query information')
}

config_regs = {
    0: 'serial_number',
    1: '0_order_wavelength_coeff',
    2: '1_order_wavelength_coeff',
    3: '2_order_wavelength_coeff',
    4: '3_order_wavelength_coeff',
    5: 'stray_light_constant',
    6: '0_order_nonlinear_coeff',
    7: '1_order_nonlinear_coeff',
    8: '2_order_nonlinear_coeff',
    9: '3_order_nonlinear_coeff',
    10: '4_order_nonlinear_coeff',
    11: '5_order_nonlinear_coeff',
    12: '6_order_nonlinear_coeff',
    13: '7_order_nonlinear_coeff',
    14: 'polynomial_order',
    15: 'bench_configuration',
    16: 'USB4000_config',
    17: 'autonull',
    18: 'baud_rate'
}   


class USB4000(USBDriver):
    """Ocean Optics spectrometer
    """

    def __init__(self, serial_number=None, **kwargs):
        super().__init__(vendor=0x2457, product=0x1022, serial_number=serial_number, **kwargs)

        self._spec_hi = usb_find_desc(self.usb_inf, bEndpointAddress=0x82)
        self._spec_lo = usb_find_desc(self.usb_inf, bEndpointAddress=0x86)

        # initialize spectrometer
        self.initialize()

    def initialize(self):
        """Ends the initialization command to the USB4000 spectrometer
            
        This command initializes certain parameters on the USB4000 and sets internal variables
        based on the USB communication speed. This command is called at object instantiation.
        """
        self.usb_send_ep.write(struct.pack('<B', 0x01))

    integration_time = Feat(units='microsecond', limits=(10, 65535000))

    @integration_time.setter
    def integration_time(self, dt):
        """Sets the integration time to use by the spectrometer in microseconds

        This command sets the integration time that the USB4000 uses when acquiring spectra. The
        value is passed as a 32 bit integer and has a valid range between 10 and 65,535,000 us. 
        """

        cmd = struct.pack('<BI', 0x02, dt)
        self.usb_send_ep.write(cmd)

    @DictFeat(keys=tuple(range(32)))
    def query_config(self, position):
        """returns the value stored in register `reg` of the spectrometer
        """
        cmd = struct.pack('<2B', 0x05, position)
        self.usb_send_ep.write(cmd)
        resp = bytearray(self.usb_recv_ep.read(64, timeout=1000))

        # Check that proper echo is returned
        assert resp[0:2] == bytearray([0x05, position]) 

        config.update({config_regs[x] : resp[2:].decode('ascii', errors='ignore').strip('\x00')})
            
        return config
            
    def reset(self):
        self.usb.reset()

    @Feat(units='degree_celsius')
    def pcb_temperature(self):
        cmd = struct.pack('<B', 0x6C)
        self.usb_send_ep.write(cmd)        
        resp = bytearray(self.usb_recv_ep.read(3, timeout=1000))
        
        # Check that proper echo is returned
        assert resp[0:1] == bytearray([0x08]) 
        
        t = struct.unpack('<h', resp[1:3])[0]
        return t * 0.003906
    
    @Feat(read_once=True)
    def firmware_version(self):
        cmd = struct.pack('<2B', 0x6B, 0x04)
        self.usb_send_ep.write(cmd)
        
        resp = bytearray(self.usb_recv_ep.read(3, timeout=200))
        log.debug('got {:s}'.format(repr(resp)))
        
        assert resp[0:1] == bytearray([0x04]) # Check that proper echo is returned
        
        vers = struct.unpack('>H', resp[1:3])[0]
        log.info('firmware is {:d}'.format(vers))
        return vers

    trigger = Feat(values={'Freerun': 0, 'Software': 1, 'ExternalSync': 2, 'ExternalHard': 3})

    @trigger.setter
    def trigger(self, mode):
        cmd = struct.pack('<BH', 0x0A, mode)
        self.usb_send_ep.write(cmd)

    def request_spectra(self):
        cmd = struct.pack('<B', 0x09)
        self.log_debug('Requesting spectra')
        self.usb_send_ep.write(cmd)
        
        data = np.zeros(shape=(3840,), dtype='<u2')
        
        try:
            data_lo = self._spec_lo.read(512*4, timeout=100)
            data_hi = self._spec_hi.read(512*11, timeout=100)

            data_sync = self._spec_hi.read(1, timeout=100)

            assert struct.unpack('<B', data_sync)[0] == 0x69

            data[:1024], data[1024:] = np.frombuffer(data_lo, dtype='<u2'), \
                                       np.frombuffer(data_hi, dtype='<u2')
        except AssertionError:
            self.log_error('Not synchronized')
        except VisaIOError:
            self.log_error('Timeout on usb')
        finally:
            self.log_debug('Obtained spectra')

        return data

    def get_status(self):
        cmd = struct.pack('<B', 0xFE)
        self.usb_send_ep.write(cmd)
        resp = bytearray(self.usb_recv_ep.read(16, timeout=1000))

        stat = {
            'num_pixels': struct.unpack('<H', resp[0:2])[0],
            'integration_time': struct.unpack('<I', resp[2:6])[0],
            'lamp_enable': bool(struct.unpack('<B', resp[6:7])[0]),
            'trigger_mode': struct.unpack('<B', resp[7:8])[0],
            'acq_status': struct.unpack('<B', resp[8:9])[0],
            'packets_in_spectra': struct.unpack('<B', resp[9:10])[0],
            'power_down': bool(struct.unpack('<B', resp[10:11])[0]),
            'packet_count': struct.unpack('<B', resp[11:12])[0],
            'usb_speed': struct.unpack('<B', resp[14:15])[0]
        }
        
        return stat
