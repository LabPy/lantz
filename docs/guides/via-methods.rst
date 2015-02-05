.. _via-methods:

==========================================
Avoiding Resource Names: the *via* methods
==========================================

While resource names provide a comprehensive way to address devices in many cases you want a simpler and succint way to do it. :class::MessageBasedDriver provide special methods for each interface type. Under the hood, these methods build the resource name for you based on minimum information.


Via Serial
----------

For serial instruments, you just need to provide the serial port. Instead of doing::

    with MyDriver('ASRL1::INSTR') as instrument:

        print(instrument.idn)

you can do::

    with MyDriver.via_serial(1) as instrument:

        print(instrument.idn)

Just like with the standard constructor you can specify the name of the instrument (for logging purposes)::

    with MyDriver.via_serial(1, name='mydevice') as instrument:

        print(instrument.idn)


And you can also specify the initialization settings::

    with MyDriver.via_serial(1, name='mydevice', 'read_termination'='\n') as instrument:

        print(instrument.idn)

Names and setting are available for all constructor methods so we will ignore them from now on.


Via TCPIP
---------

For TCPIP instruments, you just need to provide the hostname (ip address) and port. Instead of doing::

    with MyDriver('TCPIP::localhost::5678::INSTR') as instrument:

        print(instrument.idn)

you can do::

    with MyDriver.via_tcpip('localhost', 5678) as instrument:

        print(instrument.idn)


The same is true for TCIP Sockets.

Instead of doing::

    with MyDriver('TCPIP::localhost::5678::SOCKET') as instrument:

        print(instrument.idn)

you can do::

    with MyDriver.via_tcpip_socket('localhost', 5678) as instrument:

        print(instrument.idn)


Via GPIB
--------

For TCPIP instruments, you just need to provide the gpib address::

    with MyDriver('GPIB::9::INSTR') as instrument:

        print(instrument.idn)

you can do::

    with MyDriver.via_gpib(9) as instrument:

        print(instrument.idn)


Via USB
-------

For USB instruments the thing becomes really useful. USB devices *announce* themselves to the computer indicating the manufacturer id, model code and serial number. Many classes have hardcoded the manufacturer id and model code (or codes) of the instruments they can control.

So instead of doing::

    with MyDriver('USB0::0x1AB1::0x0588::DS1K00005888::INSTR') as instrument

        print(instrument.idn)

you can just do::

    with MyDriver.via_usb() as instrument:

        print(instrument.idn)

If you have multiple identical usb instuments connected, this will fail. In this case you need to specify the serial number of the instrument you want::

    with MyDriver.via_usb('DS1K00005888') as instrument:

        print(instrument.idn)


If you want to try if a driver can control another instrument you can override the model code and/or the manufacturer id::

    with MyDriver.via_usb(manufacturer_id='0x1AB2', model_code='0x0589') as instrument:

        print(instrument.idn)

You can also specify the serial code if you want. The rule is simple you need to specify it in a way that there is only one.

The same arguments are valid to create a USB SOCKET::

    with MyDriver.via_usb_socket() as instrument:

        print(instrument.idn)
