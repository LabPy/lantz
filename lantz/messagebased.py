# -*- coding: utf-8 -*-
"""
    lantz.messagebased
    ~~~~~~~~~~~~~~~~~~

    Implementes base class for message based drivers using PyVISA under the hood.

    :copyright: 2013 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from collections import ChainMap
import types

import visa

from .errors import NotSupportedError
from .driver import Driver
from .log import LOGGER
from .processors import ParseProcessor


#: Cache of parsing functions.
#: :type: dict[str, ParseProcessor]
_PARSERS_CACHE = {}

#: PyVISA Resource Manager used in Lantz
#: :type: visa.ResourceManager
_resource_manager = None


def get_resource_manager():
    """Return the PyVISA Resource Manager, creating an instance if necessary.

    :rtype: visa.ResourceManager
    """
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = visa.ResourceManager()
    return _resource_manager


class MessageBasedDriver(Driver):
    """Base class for message based drivers using PyVISA as underlying library.

    Notice that PyVISA can communicate using different backends. For example:
    - @ni: Using NI-VISA for communication. Backend bundled with PyVISA.
    - @py: Using PySerial, PyUSB and linux-gpib for communication. Available with PyVISA-py package.
    - @sim: Simulated devices. Available with PyVISA-sim package.
    """

    #: Default arguments passed to the Resource constructor on initialize.
    #: It should be specified in two layers, the first indicating the
    #: interface type and the second the corresponding arguments.
    #: The key COMMON is used to indicate keywords for all interfaces.
    #: For example::
    #:
    #:       {'ASRL':     {'read_termination': '\n',
    #:                     'baud_rate': 9600},
    #:        'USB':      {'read_termination': \r'},
    #:        'COMMON':   {'write_termination': '\n'}
    #:       }
    #:
    #: :type: dict[str, dict[str, str]]
    DEFAULTS_KWARGS = None

    #: Stores a reference to a PyVISA ResourceManager.
    #: :type: visa.ResourceManager
    __resource_manager = None

    @classmethod
    def _get_defaults_kwargs(cls, instrument_type, resource_type, **user_kwargs):
        """Compute the default keyword arguments combining:
            - user provided keyword arguments.
            - (instrument_type, resource_type) keyword arguments.
            - instrument_type keyword arguments.
            - resource_type keyword arguments.
            - common keyword arguments.

        (the first ones have precedence)

        :param instrument_type: ASRL, USB, TCPIP, GPIB
        :type instrument_type: str
        :param resource_type: INSTR, SOCKET, RAW
        :type resource_type: str

        :rtype: dict
        """

        if cls.DEFAULTS_KWARGS:

            maps = [user_kwargs] if user_kwargs else []

            for key in ((instrument_type, resource_type), instrument_type, resource_type, 'COMMON'):
                if key not in cls.DEFAULTS_KWARGS:
                    continue
                value = cls.DEFAULTS_KWARGS[key]
                if value is None:
                    raise NotSupportedError('An %s instrument is not supported by the driver %s',
                                            key, cls.__name__)
                if value:
                    maps.append(value)

            return dict(ChainMap(*maps))
        else:
            return user_kwargs

    @classmethod
    def _from_usb(cls, resource_type='INSTR', serial_number=None, manufacturer_id=None, model_code=None, name=None, board=0, **kwargs):
        """Return a Driver with an underlying USB resource.

        A connected USBTMC instrument with the specified serial_number, manufacturer_id,
        and model_code is returned. If any of these is missing, the first USBTMC driver
        matching any of the provided values is returned.

        Override this method to specify the manufacturer id and/or the model code::

            class RigolDS1052E(MessageBasedDriver):

                @classmethod
                def from_usbtmc(self, serial_number=None, name=None, **kwargs):

                    return super().from_usbtmc(serial_number, '0x1AB1', '0x0588', name, **kwargs)


        :param serial_number: The serial number of the instrument.
        :param manufacturer_id: The unique identification number of the manufacturer.
        :param model_code: The unique identification number of the product.
        :param name: Unique name given within Lantz to the instrument for logging purposes.
                     Defaults to one generated based on the class name if not provided.
        :param board: USB Board to use
        :param kwargs: keyword arguments passed to the Resource constructor on initialize.

        :rtype: MessageBasedDriver
        """

        if serial_number is None or manufacturer_id is None or model_code is None:
            query = 'USB%d::%s::%s::%s::%s' % (board, manufacturer_id or '?*', model_code or '?*', serial_number or '?*', resource_type)
            try:
                resources = get_resource_manager().list_resources(query)
            except:
                resources = []

            if len(resources) != 1:
                msg = ' USBTMC devices found for %s' % query
                if not len(resources):
                    raise ValueError('No' + msg)
                elif len(resources) > 1:
                    LOGGER.debug(str(len(resources)) + msg + '. Picking the first.')

            resource_name = resources[0]
        else:
            resource_name = 'USB%d::%s::%s::%s::%s' % (board, manufacturer_id, model_code, serial_number, resource_type)

        return cls(resource_name, name)

    @classmethod
    def from_usbtmc(cls, serial_number=None, manufacturer_id=None, model_code=None, name=None, board=0, **kwargs):
        """Return a Driver with an underlying USB Instrument resource.

        A connected USBTMC instrument with the specified serial_number, manufacturer_id,
        and model_code is returned. If any of these is missing, the first USBTMC driver
        matching any of the provided values is returned.

        Override this method to specify the manufacturer id and/or the model code::

            class RigolDS1052E(MessageBasedDriver):

                @classmethod
                def from_usbtmc(self, serial_number=None, name=None, **kwargs):

                    return super().from_usbtmc(serial_number, '0x1AB1', '0x0588', name, **kwargs)


        :param serial_number: The serial number of the instrument.
        :param manufacturer_id: The unique identification number of the manufacturer.
        :param model_code: The unique identification number of the product.
        :param name: Unique name given within Lantz to the instrument for logging purposes.
                     Defaults to one generated based on the class name if not provided.
        :param board: USB Board to use
        :param kwargs: keyword arguments passed to the Resource constructor on initialize.

        :rtype: MessageBasedDriver
        """

        return cls._from_usb('INSTR', serial_number, manufacturer_id, model_code, name, board, **kwargs)


    @classmethod
    def from_usbtmc_raw(cls, serial_number=None, manufacturer_id=None, model_code=None, name=None, board=0, **kwargs):
        """Return a Driver with an underlying USB RAW resource.

        :param serial_number: The serial number of the instrument.
        :param manufacturer_id: The unique identification number of the manufacturer.
        :param model_code: The unique identification number of the product.
        :param name: Unique name given within Lantz to the instrument for logging purposes.
                     Defaults to one generated based on the class name if not provided.
        :param board: USB Board to use
        :param kwargs: keyword arguments passed to the Resource constructor on initialize.

        :rtype: MessageBasedDriver
        """

        return cls._from_usb('RAW', serial_number, manufacturer_id, model_code, name, board, **kwargs)

    @classmethod
    def from_serial_port(cls, port, name=None, **kwargs):
        """Return a Driver with an underlying ASRL (Serial) Instrument resource.

        :param port: The serial port to which the instrument is connected.
        :param name: Unique name given within Lantz to the instrument for logging purposes.
                     Defaults to one generated based on the class name if not provided.
        :param kwargs: keyword arguments passed to the Resource constructor on initialize.

        :rtype: MessageBasedDriver
        """
        resource_name = 'ASRL%s::INSTR' % port
        return cls(resource_name, name, **kwargs)

    @classmethod
    def from_hostname(cls, hostname, name=None, **kwargs):
        """Return a Driver with an underlying TCP Instrument resource.

        :param port: The ip address or hostname of the instrument.
        :param name: Unique name given within Lantz to the instrument for logging purposes.
                     Defaults to one generated based on the class name if not provided.
        :param kwargs: keyword arguments passed to the Resource constructor on initialize.

        :rtype: MessageBasedDriver
        """
        resource_name = 'TCPIP::%s::INSTR' % hostname
        return cls(resource_name, name, **kwargs)

    @classmethod
    def from_hostname_socket(cls, hostname, name=None, **kwargs):
        """Return a Driver with an underlying TCP Socket resource.

        :param port: The ip address or hostname of the instrument.
        :param name: Unique name given within Lantz to the instrument for logging purposes.
                     Defaults to one generated based on the class name if not provided.
        :param kwargs: keyword arguments passed to the Resource constructor on initialize.

        :rtype: MessageBasedDriver
        """
        resource_name = 'TCPIP::%s::INSTR' % hostname
        return cls(resource_name, name, **kwargs)

    @classmethod
    def from_gpib_address(cls, address, name=None, **kwargs):
        """Return a Driver with an underlying GPIB Instrument resource.

        :param address: The gpib address of the instrument.
        :param name: Unique name given within Lantz to the instrument for logging purposes.
                     Defaults to one generated based on the class name if not provided.
        :param kwargs: keyword arguments passed to the Resource constructor on initialize.

        :rtype: MessageBasedDriver
        """
        resource_name = 'GPIB::%s::INSTR' % address
        return cls(resource_name, name, **kwargs)

    def __init__(self, resource_name, name=None, **kwargs):
        """
        :param resource_name: The resource name
        :type resource_name: str
        :params name: easy to remember identifier given to the instance for logging
                      purposes.
        :param kwargs: keyword arguments passed to the resource during initialization.
        """

        try:
            resource_info = get_resource_manager().resource_info(resource_name)
        except visa.VisaIOError:
            raise ValueError('The resource name is invalid')

        super().__init__(name=name)

        # This is to avoid accidental modifications of the class value by an instance.
        self.DEFAULTS_KWARGS = types.MappingProxyType(self.DEFAULTS_KWARGS or {})

        #: The resource name
        #: :type: str
        self.resource_name = resource_name

        #: keyword arguments passed to the resource during initialization.
        #: :type: dict
        self.resource_kwargs = self._get_defaults_kwargs(resource_info.interface_type.name.upper(),
                                                         resource_info.resource_class,
                                                         **kwargs)

        # The resource will be created when the driver is initialized.
        #: :type: pyvisa.resources.MessageBasedResource
        self.resource = None

        self.log_debug('Using MessageBasedDriver for {}', self.resource_name)

    def initialize(self):
        super().initialize()
        self.log_debug('Opening resource {}', self.resource_name)
        self.log_debug('Setting {}', list(self.resource_kwargs.items()))
        self.resource = get_resource_manager().open_resource(self.resource_name, **self.resource_kwargs)

    def finalize(self):
        self.log_debug('Closing resource {}', self.resource_name)
        self.resource.close()
        super().finalize()

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        """Send query to the instrument and return the answer

        :param command: command to be sent to the instrument
        :type command: string

        :param send_args: (termination, encoding) to override class defaults
        :param recv_args: (termination, encoding) to override class defaults
        """

        self.write(command, *send_args)
        return self.read(*recv_args)

    def parse_query(self, command, *,
                    send_args=(None, None), recv_args=(None, None),
                    format=None):
        """Send query to the instrument, parse the output using format
        and return the answer.

        .. seealso:: TextualMixin.query and stringparser
        """
        ans = self.query(command, send_args=send_args, recv_args=recv_args)
        if format:
            parser = _PARSERS_CACHE.setdefault(format, ParseProcessor(format))
            ans = parser(ans)
        return ans

    def write(self, command, termination=None, encoding=None):
        """Send command to the instrument.

        :param command: command to be sent to the instrument.
        :type command: string.

        :param termination: termination character to override class defined
                            default.
        :param encoding: encoding to transform string to bytes to override class
                         defined default.

        :return: number of bytes sent.

        """
        self.log_debug('Writing {!r}', command)
        return self.resource.write(command, termination, encoding)

    def read(self, termination=None, encoding=None):
        """Receive string from instrument.

        :param termination: termination character (overrides class default)
        :type termination: str
        :param encoding: encoding to transform bytes to string (overrides class default)
        :return: string encoded from received bytes
        """
        ret =  self.resource.read(termination, encoding)
        self.log_debug('Read {!r}', ret)
        return ret
