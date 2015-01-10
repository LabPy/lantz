# -*- coding: utf-8 -*-
"""
    lantz.drivers.legacy.usbtmc
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements a USBDriver based class to control USBTMC instruments

    Loosely based on PyUSBTMC:python module to handle USB-TMC(Test and Measurement class)　devices.
    by Noboru Yamamot, Accl. Lab, KEK, JAPAN

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import enum
import time
import struct
from collections import namedtuple

import usb
from lantz.drivers.legacy.textual import TextualMixin
from lantz.errors import InstrumentError
from lantz.drivers.legacy.usb import find_devices, find_interfaces, find_endpoint, USBDriver


class MSGID(enum.IntEnum):
    """From USB-TMC table2
    """
    DEV_DEP_MSG_OUT = 1
    REQUEST_DEV_DEP_MSG_IN = 2
    DEV_DEP_MSG_IN = 2
    VENDOR_SPECIFIC_OUT = 126
    REQUEST_VENDOR_SPECIFIC_IN = 127
    VENDOR_SPECIFIC_IN = 127
    TRIGGER = 128 # for USB488


class REQUEST(enum.IntEnum):
    INITIATE_ABORT_BULK_OUT = 1
    CHECK_ABORT_BULK_OUT_STATUS = 2
    INITIATE_ABORT_BULK_IN = 3
    CHECK_ABORT_BULK_IN_STATUS = 4
    INITIATE_CLEAR = 5
    CHECK_CLEAR_STATUS = 6
    GET_CAPABILITIES = 7
    INDICATOR_PULSE = 64


def find_tmc_devices(vendor=None, product=None, serial_number=None, custom_match=None, **kwargs):
    """Find connected USBTMC devices. See lantz.usb.find_devices for more info.
    """
    def is_usbtmc(dev):
        if custom_match and not custom_match(dev):
            return False
        return bool(find_interfaces(dev, bInterfaceClass=0xfe, bInterfaceSubClass=3))

    return find_devices(vendor, product, serial_number, is_usbtmc, **kwargs)


class BulkOutMessage(object):
    """The Host uses the Bulk-OUT endpoint to send USBTMC command messages to the device.
    """

    @staticmethod
    def build_array(btag, eom, chunk):
        size = len(chunk)
        return struct.pack('BBBx', MSGID.DEV_DEP_MSG_OUT, btag, ~btag & 0xFF) + \
               struct.pack("<LBxxx", size, eom) + \
               chunk + \
               b'\0' * ((4 - size) % 4)


class BulkInMessage(namedtuple('BulkInMessage', 'msgid btag btaginverse '
                                                'transfer_size transfer_attributes data')):
    """The Host uses the Bulk-IN endpoint to read USBTMC response messages from the device.
    The Host must first send a USBTMC command message that expects a response before
    attempting to read a USBTMC response message.
    """

    @classmethod
    def from_bytes(cls, data):
        msgid, btag, btaginverse = struct.unpack_from('BBBx', data)
        assert msgid == MSGID.DEV_DEP_MSG_IN

        transfer_size, transfer_attributes = struct.unpack_from('<LBxxx', data, 4)

        data = data[12:]
        return cls(msgid, btag, btaginverse, transfer_size, transfer_attributes, data)


    @staticmethod
    def build_array(btag, transfer_size, term_char=None):
        """

        :param transfer_size:
        :param btag:
        :param term_char:
        :return:
        """

        if term_char is None:
            transfer_attributes = 0
            term_char = 0
        else:
            transfer_attributes = 2

        return struct.pack('BBBx', MSGID.REQUEST_DEV_DEP_MSG_IN, btag, ~btag & 0xFF) + \
               struct.pack("<LBBxx", transfer_size, transfer_attributes, term_char)


class USBTMCDriver(USBDriver, TextualMixin):

    SEND_TERMINATION = ''
    RECV_TERMINATION = '\n'

    RECV_CHUNK = 1024 ** 2

    find_devices = staticmethod(find_tmc_devices)

    def __init__(self, vendor=None, product=None, serial_number=None, **kwargs):
        super().__init__(vendor, product, serial_number, **kwargs)
        self.usb_intr_in = find_endpoint(self.usb_intf, usb.ENDPOINT_IN, usb.ENDPOINT_TYPE_INTERRUPT)
        self.log_debug('EP Address: intr={}'.format(self.usb_intr_in.bEndpointAddress))

        self.usb_dev.reset()

        time.sleep(0.01)

        self._get_capabilities()
    
        self._btag = 0

        if not (self.usb_recv_ep and self.usb_send_ep):
            raise InstrumentError("TMC device must have both Bulk-In and Bulk-out endpoints.")

    def _get_capabilities(self):
        cap = self.usb_dev.ctrl_transfer(
                   usb.util.build_request_type(usb.util.CTRL_IN,
                                               usb.util.CTRL_TYPE_CLASS,
                                               usb.util.CTRL_RECIPIENT_INTERFACE),
                   REQUEST.GET_CAPABILITIES,
                   0x0000,
                   self.usb_intf.index,
                   0x0018,
                   timeout=self.TIMEOUT)

    def _find_interface(self, dev, setting):
        interfaces = find_interfaces(dev, bInterfaceClass=0xFE, bInterfaceSubClass=3)
        if not interfaces:
            raise InstrumentError('USB TMC interface not found.')
        elif len(interfaces) > 1:
            self.log_warning('More than one interface found, selecting first.')

        return interfaces[0]

    def send(self, command, termination=None, encoding=None):
        if termination is None:
            termination = self.SEND_TERMINATION
        if encoding is None:
            encoding = self.ENCODING

        message = bytes(command + termination, encoding)
        self.log_debug('Sending {}', message)

        begin, end, size = 0, 0, len(message)
        bytes_sent = 0
        while not end > size:
            begin, end = end, begin + self.RECV_CHUNK

            self._btag = (self._btag % 255) + 1

            data = BulkOutMessage.build_array(self._btag, end > size, message[begin:end])

            bytes_sent += self.raw_send(data)

        return bytes_sent

    send.__doc__ = TextualMixin.send.__doc__

    def recv(self, termination=None, encoding=None, recv_chunk=None):

        termination = termination or self.RECV_TERMINATION
        encoding = encoding or self.ENCODING
        recv_chunk = recv_chunk or self.RECV_CHUNK

        eom = False

        received = self._received

        while not (termination in received or eom):
            self._btag = (self._btag % 255) + 1

            req = BulkInMessage.build_array(self._btag, recv_chunk, None)

            self.raw_send(req)

            resp = self.raw_recv(recv_chunk)

            response = BulkInMessage.from_bytes(resp)

            received += str(response.data, encoding)
            eom = response.transfer_attributes & 1

        self.log_debug('Received {!r} (len={})', received, len(received))

        received, self._received = received.split(termination, 1)

        return received

    recv.__doc__ = TextualMixin.recv.__doc__

