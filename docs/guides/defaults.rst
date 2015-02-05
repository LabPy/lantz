.. _defaults_dictionary:

=======================
The DEFAULTS dictionary
=======================


Different instruments require different communication settings such as baud rate, end of a message characters, etc. The :attribute::`DEFAULTS` dictionary provides a way to customize resource initialization at the :class::MessageBasedDriver level, avoiding tedious customization in all instances.

It is easier to see it with an example. Let's start with simple case::

    class MyDriver(MessageBasedDriver):

        DEFAULTS = {
                      'COMMON':   {'write_termination': '\n'}
                    }

The 'COMMON' key is used to tells MessageBasedDriver that 'write_termination' should be set to '\n' for all type of interface types (USB, GPIB, etc).

But in certain cases, different resource types might require different settings::

        DEFAULTS = {
                      'ASRL':   {'write_termination': '\n',
                                 'read_termination': '\r',
                                 'baud_rate': 9600},

                      'USB':    {'write_termination': '\n',
                                 'read_termination': \n'}
                    }

This specifies a dictionary of settings for an ASRL (serial) resource and a different for USB. We might make this more concise::

        DEFAULTS = {
                      'ASRL':   {'read_termination': '\r',
                                 'baud_rate': 9600},

                      'USB':    {'read_termination': \n'},

                      'COMMON':   {'write_termination': '\n'}
                    }


When you require a USB resource, Lantz will combine the USB and COMMON settings.

The interface type is not the only thing that defines the resource. For example TCPIP device can be a INSTR or SOCKET. You can also specify this in a tuple::

        DEFAULTS = {
                      'INSTR':   {'read_termination': '\r'},

                      'SOCKET':    {'read_termination': \n'},

                      'COMMON':   {'write_termination': '\n'}
                    }

This will specify that 'read_termination' will be set '\r' to for al INSTR. If you want to specify only for TCPIP, use a tuple like this::

        DEFAULTS = {
                      ('TCPIP, 'INSTR'):   {'read_termination': '\r'},

                      'SOCKET':    {'read_termination': \n'},

                      'COMMON':   {'write_termination': '\n'}
                    }


Overriding on initialization
----------------------------

You can override the defaults when you instantiate the instrument by passing these values a command line arguments::

    inst = MyDriver('TCPIP::localhost::5678::INSTR', read_termination='\t')


Colliding values
----------------

When multiple values are given for the same setting (for example 'read_termination' is in USB And COMMON) and a USB resource is requested, the following order is used to define the precedence:

    - user provided keyword arguments.
    - settings for (instrument_type, resource_type).
    - settings for instrument_type: ASRL, USB, GPIB, TCPIP
    - settings for resource_type: SOCKET, INSTR, RAW
    - settings for COMMON

The rule is: more specific has precedence.


Valid settings
--------------

If you provide an invalid setting, you will get an Exception upon initalization. The valid settings are defined by `Attributes per resource in PyVISA`_

.. _Attributes per resource in PyVISA: http://pyvisa.readthedocs.org/en/master/api/resources.html
