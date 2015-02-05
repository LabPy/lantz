# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.usb
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Implements base classes for drivers that communicate with instruments
    via usb using PyUSB

    See the following link for more information about USB.

    http://www.beyondlogic.org/usbnutshell/usb5.shtml

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from collections import namedtuple, OrderedDict
from fnmatch import fnmatch

import usb
from usb.util import (get_string as usb_get_string,
                      find_descriptor as usb_find_desc)

from lantz import Driver
from lantz.errors import LantzTimeoutError, InstrumentError


ClassCodes = {
    0x00: ('Device', 'Use class information in the Interface Descriptors'),
    0x01: ('Interface', 'Audio'),
    0x02: ('Both', 'Communications and CDC Control'),
    0x03: ('Interface', 'HID (Human Interface Device)'),
    0x05: ('Interface', 'Physical'),
    0x06: ('Interface', 'Image'),
    0x07: ('Interface', 'Printer'),
    0x08: ('Interface', 'Mass Storage'),
    0x09: ('Device', 'Hub'),
    0x0A: ('Interface', 'CDC-Data'),
    0x0B: ('Interface', 'Smart Card'),
    0x0D: ('Interface', 'Content Security'),
    0x0E: ('Interface', 'Video'),
    0x0F: ('Interface', 'Personal Healthcare'),
    0x10: ('Interface', 'Audio/Video Devices'),
    0xDC: ('Both', 'Diagnostic Device'),
    0xE0: ('Interface', 'Wireless Controller'),
    0xEF: ('Both', 'Miscellaneous'),
    0xFE: ('Interface', 'Application Specific'),
    0xFF: ('Both', 'Vendor Specific')
}

# None is 0xxx
AllCodes = {
    (0x00, 0x00, 0x00): 'Use class code info from Interface Descriptors',
    (0x01, None, None): 'Audio device',
    (0x02, None, None): 'Communication device class',
    (0x03, None, None): 'HID device class',
    (0x05, None, None): 'Physical device class',
    (0x06, 0x01, 0x01): 'Still Imaging device',
    (0x07, None, None): 'Printer device',
    (0x08, None, None): 'Mass Storage device',
    (0x09, 0x00, 0x00): 'Full speed Hub',
    (0x09, 0x00, 0x01): 'Hi-speed hub with single TT',
    (0x09, 0x00, 0x02): 'Hi-speed hub with multiple TTs',
    (0x0A, None, None): 'CDC data device',
    (0x0B, None, None): 'Smart Card device',
    (0x0D, 0x00, 0x00): 'Content Security device',
    (0x0E, None, None): 'Video device',
    (0x0F, None, None): 'Personal Healthcare device',
    (0x10, 0x01, 0x00): 'Control Interface',
    (0x10, 0x02, 0x00): 'Data Video Streaming Interface',
    (0x10, 0x03, 0x00): 'VData Audio Streaming Interface',
    (0xDC, 0x01, 0x01): 'USB2 Compliance Device',
    (0xE0, 0x01, 0x01): 'Bluetooth Programming Interface.',
    (0xE0, 0x01, 0x02): 'UWB Radio Control Interface.',
    (0xE0, 0x01, 0x03): 'Remote NDIS',
    (0xE0, 0x01, 0x04): 'Bluetooth AMP Controller.',
    (0xE0, 0x2, 0x01): 'Host Wire Adapter Control/Data interface.',
    (0xE0, 0x2, 0x02): 'Device Wire Adapter Control/Data interface.',
    (0xE0, 0x2, 0x03): 'Device Wire Adapter Isochronous interface.',
    (0xEF, 0x01, 0x01): 'Active Sync device.',
    (0xEF, 0x01, 0x02): 'Palm Sync. This class code can be used in either '
                        'Device or Interface Descriptors.',
    (0xEF, 0x02, 0x01): 'Interface Association Descriptor.',
    (0xEF, 0x02, 0x02): 'Wire Adapter Multifunction Peripheral programming interface.',
    (0xEF, 0x03, 0x01): 'Cable Based Association Framework.',
    (0xEF, 0x04, 0x01): 'RNDIS over Ethernet. Connecting a host to the Internet via '
                        'Ethernet mobile device. The device appears to the host as an'
                        'Ethernet gateway device. This class code may only be used in '
                        'Interface Descriptors.',
    (0xEF, 0x04, 0x02): 'RNDIS over WiFi. Connecting a host to the Internet via WiFi '
                        'enabled mobile device.  The device represents itself to the host'
                        'as an 802.11 compliant network device. This class code may only'
                        'be used in Interface Descriptors.',
    (0xEF, 0x04, 0x03): 'RNDIS over WiMAX. Connecting a host to the Internet via WiMAX '
                        'enabled mobile device.  The device is represented to the host '
                        'as an 802.16 network device. This class code may only be used '
                        'in Interface Descriptors.',
    (0xEF, 0x04, 0x04): 'RNDIS over WWAN. Connecting a host to the Internet via a device '
                        'using mobile broadband, i.e. WWAN (GSM/CDMA). This class code may '
                        'only be used in Interface Descriptors.',
    (0xEF, 0x04, 0x05): 'RNDIS for Raw IPv4. Connecting a host to the Internet using raw '
                        'IPv4 via non-Ethernet mobile device.  Devices that provide raw '
                        'IPv4, not in an Ethernet packet, may use this form to in lieu of '
                        'other stock types. '
                        'This class code may only be used in Interface Descriptors.',
    (0xEF, 0x04, 0x06): 'RNDIS for Raw IPv6. Connecting a host to the Internet using raw '
                        'IPv6 via non-Ethernet mobile device.  Devices that provide raw '
                        'IPv6, not in an Ethernet packet, may use this form to in lieu of '
                        'other stock types. '
                        'This class code may only be used in Interface Descriptors.',
    (0xEF, 0x04, 0x07): 'RNDIS for GPRS. Connecting a host to the Internet over GPRS mobile '
                        'device using the device‚Äôs cellular radio.',
    (0xEF, 0x05, 0x00): 'USB3 Vision Control Interface',
    (0xEF, 0x05, 0x01): 'USB3 Vision Event Interface',
    (0xEF, 0x05, 0x02): 'USB3 Vision Streaming Interface',
    (0xFE, 0x01, 0x01): 'Device Firmware Upgrade.',
    (0xFE, 0x02, 0x00): 'IRDA Bridge device.',
    (0xFE, 0x03, 0x00): 'USB Test and Measurement Device.',
    (0xFE, 0x03, 0x01): 'USB Test and Measurement Device conforming to the USBTMC USB488 Subclass',
    (0xFF, None, None): 'Vendor specific'
}


class LantzUSBTimeoutError(usb.core.USBError, LantzTimeoutError):
    pass


def ep_attributes(ep):
    c = ep.bmAttributes
    attrs = []
    tp = c &usb.ENDPOINT_TYPE_MASK
    if tp == usb.ENDPOINT_TYPE_CONTROL:
        attrs.append('Control')
    elif tp == usb.ENDPOINT_TYPE_ISOCHRONOUS:
        attrs.append('Isochronous')
    elif tp == usb.ENDPOINT_TYPE_BULK:
        attrs.append('Bulk')
    elif tp == usb.ENDPOINT_TYPE_INTERRUPT:
        attrs.append('Interrupt')
        
    sync = (c & 12) >> 2
    if sync == 0:
        attrs.append('No sync')
    elif sync == 1:
        attrs.append('Async')
    elif sync == 2:
        attrs.append('Adaptive')
    elif sync == 3:
        attrs.append('Sync')
    usage = (c & 48) >> 4
    if usage == 0:
        attrs.append('Data endpoint')
    elif usage == 1:
        attrs.append('Feedback endpoint')
    elif usage ==2:
        attrs.append('Subordinate Feedback endpoint')
    elif usage == 3:
        attrs.append('Reserved')

    return ', '.join(attrs)


def list_devices():
    devs = find_devices()
    print('{} devices found'.format(len(devs)))
    for ndx, dev in enumerate(devs):
        print('Device #{}'.format(ndx))
        c, s, p = dev.bDeviceClass, dev.bDeviceSubClass, dev.bDeviceProtocol
        a, b = ClassCodes.get(c, ('Unknown', 'Unknown'))
        nfo = DeviceInfo.from_device(dev)
        print('- Class: {}, {} ({})'.format(a, b, c))
        print('- Subclass and protocol: {} ({} {})'.format(AllCodes.get((c, s, p), 'Unknown'), s, p))
        print('- Manufacturer: {} ({})'.format(nfo.manufacturer, dev.idVendor))
        print('- Product: {} ({})'.format(nfo.product, dev.idProduct))
        print('- Serial Number: {}'.format(nfo.serial_number))
        print('- Number of configurations: {}'.format(dev.bNumConfigurations))
        try:
            for cfg in dev:
                print('- Configurations #{}'.format(cfg.bConfigurationValue))
                for intf in cfg:
                    print('-- Interface: {}'.format(intf.bInterfaceNumber))
                    print('-- Alternate: {}'.format(intf.bAlternateSetting))
                    print('-- Endpoints:')
                    for ep in intf:
                        if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                            inout = 'out'
                        else:
                            inout = 'in'
                        print('--- {} ({})'.format(ep.bEndpointAddress, inout))
                        print('--- Max Packet Size: {}'.format(ep.wMaxPacketSize))
                        print('--- Polling interval: {}'.format(ep.bInterval))
                        print('--- Attributes: {}'.format(ep_attributes(ep)))
        except Exception as e:
            print('- Exception: {}'.format(e))
        print('-------')


def find_devices(vendor=None, product=None, serial_number=None, custom_match=None, **kwargs):
    """Find connected USB devices matching certain keywords.

    Wildcards can be used for vendor, product and serial_number.

    :param vendor: name or id of the vendor (manufacturer)
    :param product: name or id of the product
    :param serial_number: serial number.
    :param custom_match: callable returning True or False that takes a device as only input.
    :param kwargs: other properties to match. See usb.core.find
    :return:
    """
    kwargs = kwargs or {}
    attrs = {}
    if isinstance(vendor, str):
        attrs['manufacturer'] = vendor
    elif vendor is not None:
        kwargs['idVendor'] = vendor

    if isinstance(product, str):
        attrs['product'] = product
    elif product is not None:
        kwargs['idProduct'] = product

    if serial_number:
        attrs['serial_number'] = str(serial_number)

    if attrs:
        def cm(dev):
            if custom_match is not None and not custom_match(dev):
                return False
            info = DeviceInfo.from_device(dev)
            for attr, pattern in attrs.items():
                if not fnmatch(getattr(info, attr).lower(), pattern.lower()):
                    return False
            return True
    else:
        cm = custom_match

    return usb.core.find(find_all=True, custom_match=cm, **kwargs)


def find_interfaces(device, **kwargs):
    """
    :param device:
    :return:
    """
    interfaces = []
    try:
        for cfg in device:
            try:
                interfaces.extend(usb_find_desc(cfg, find_all=True, **kwargs))
            except:
                pass
    except:
        pass
    return interfaces


def find_endpoint(interface, direction, type):
    ep = usb_find_desc(interface, custom_match=
                                  lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == direction and
                                            usb.util.endpoint_type(e.bmAttributes) == type
         )
    return ep


class DeviceInfo(namedtuple('DeviceInfo', 'manufacturer product serial_number')):

    def __str__(self):
        return '{} {}. S/N {}'.format(self.manufacturer, self.product, self.serial_number)

    @classmethod
    def from_device(cls, device):
        ret = []
        for attr in ('iManufacturer', 'iProduct', 'iSerialNumber'):
            try:
                ret.append(usb_get_string(device, 255, getattr(device, attr)).strip())
            except Exception as e:
                ret.append('Unknown')
        return cls(*ret)


class USBDriver(Driver):
    """Base class for drivers that communicate with instruments
    via usb port using pyUSB
    """

    #: Configuration number to be used. If None, the default will be used.
    CONFIGURATION = None
    #: Interface index it be used
    INTERFACE = (0, 0)
    #: Receive and Send endpoints to be used. If None the first IN (or OUT) BULK
    #: endpoint will be used.
    ENDPOINTS = (None, None)

    TIMEOUT = 1000

    find_devices = staticmethod(find_devices)

    def __init__(self, vendor=None, product=None, serial_number=None,
                 device_filters=None, timeout=None, **kwargs):
        super().__init__(**kwargs)

        device_filters = device_filters or {}
        devices = self.find_devices(vendor, product, serial_number, None, **device_filters)

        if not devices:
            raise InstrumentError('No device found.')
        elif len(devices) > 1:
            desc = '\n'.join(str(DeviceInfo.from_device(dev)) for dev in devices)
            raise InstrumentError('{} devices found:\n{}\n'
                                  'Please narrow the search criteria'.format(len(devices), desc))

        self.usb_dev, other = devices[0], devices[1:]
        nfo = DeviceInfo.from_device(self.usb_dev)
        self.log_debug('- Manufacturer: {} ({})'.format(nfo.manufacturer, self.usb_dev.idVendor))
        self.log_debug('- Product: {} ({})'.format(nfo.product, self.usb_dev.idProduct))
        self.log_debug('- Serial Number: {}'.format(nfo.serial_number))
        try:
            if self.usb_dev.is_kernel_driver_active(0):
                    self.usb_dev.detach_kernel_driver(0)
        except (usb.core.USBError, NotImplementedError) as e:
            self.log_warning(repr(e))

        try:
            self.usb_dev.set_configuration() #self.CONFIGURATION
            self.usb_dev.set_interface_altsetting()
        except usb.core.USBError as e:
            self.log_error("Could not set configuration")
            raise InstrumentError('failed to set configuration')

        self.usb_intf = self._find_interface(self.usb_dev, self.INTERFACE)
        self.log_debug('Interface: {}'.format(self.usb_intf.index))


        self.usb_recv_ep, self.usb_send_ep = self._find_endpoints(self.usb_intf, self.ENDPOINTS)

        self.log_debug('EP Address: recv={}, send={}'.format(self.usb_recv_ep.bEndpointAddress,
                                                             self.usb_send_ep.bEndpointAddress))

    def _find_interface(self, dev, setting):
        return self.usb_dev.get_active_configuration()[self.INTERFACE]

    def _find_endpoints(self, interface, setting):
        recv, send = setting
        if recv is None:
            recv = find_endpoint(interface, usb.ENDPOINT_IN, usb.ENDPOINT_TYPE_BULK)
        else:
            recv = usb_find_desc(interface, bEndpointAddress=recv)

        if send is None:
            send = find_endpoint(interface, usb.ENDPOINT_OUT, usb.ENDPOINT_TYPE_BULK)
        else:
            send = usb_find_desc(interface, bEndpointAddress=send)

        return recv, send

    def send(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument
        :type data: bytes
        """
        self.raw_send(data)

    def raw_send(self, data):
        """Send raw bytes to the instrument.

        :param data: bytes to be sent to the instrument
        :type data: bytes
        """

        try:
            return self.usb_send_ep.write(data)
        except usb.core.USBError as e:
            raise InstrumentError(str(e))

    def recv(self, size):
        return self.raw_recv(size)

    def raw_recv(self, size):
        """Receive raw bytes to the instrument.

        :param size: number of bytes to receive
        :return: received bytes
        :return type: bytes
        """

        if size <= 0:
            size = 1

        data = self.usb_recv_ep.read(size, self.TIMEOUT).tobytes()

        return data

    def finalize(self):
        """Close port
        """
        self.log_debug('Closing device {}', str(DeviceInfo.from_device(self.usb_dev)))
        return usb.util.dispose_resources(self.usb_dev)


def _patch_endpoint(ep, log_func=print):
    _read = ep.read
    _write = ep.write
    def new_read(*args, **kwargs):
        log_func('---')
        log_func('reading from {}'.format(ep.bEndpointAddress))
        log_func('args: {}'.format(args))
        log_func('kwargs: {}'.format(kwargs))
        ret =_read(*args, **kwargs)
        log_func('returned', ret)
        log_func('---')
        return ret
    def new_write(*args, **kwargs):
        log_func('---')
        log_func('writing to {}'.format(ep.bEndpointAddress))
        log_func('args: {}'.format(args))
        log_func('kwargs: {}'.format(kwargs))
        ret = _write(*args, **kwargs)
        log_func('returned', ret)
        log_func('---')
        return ret
    ep.read = new_read
    ep.write = new_write
