.. _tutorial-using:

===================
Using lantz drivers
===================

In this tutorial, you will learn how to use Lantz drivers to control an instrument. Lantz is shipped with drivers for common laboratory instruments. Each instrument has different capabilities, and these reflect in the drivers being different. However, all Lantz drivers share a common structure and learning about it allows you to use them in a more efficient way.

Following a tutorial about using a driver to communicate with an instrument that you do not have is not much fun. That's why we have created a virtual version of this instrument. From the command line, run the following command::

    $ sim-fungen.py tcp

This will start an application (i.e. your instrument) that listens for incoming TCP packages (commands) on port 5678 from `localhost`. In the screen you will see the commands received and sent by the instrument.

Your program and the instrument will communicate by exchanging text commands via TCP. But having a Lantz driver already built for your particular instrument releases you for the burden of sending and receiving the messages. Let's start by finding the driver. Lantz drivers are organized inside packages, each package named after the manufacturer. So the `Coherent Argon Laser Innova` 300C driver is in `lantz.drivers.coherent` under the name `ArgonInnova300C`. We follow Python style guide (PEP8) to name packages and modules (lowercase) and classes (CamelCase).

Our simulated device is under the company `examples` and is named `LantzSignalGeneratorTCP`. Create a python script named `test_fungen.py` and type::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    inst = LantzSignalGeneratorTCP('localhost', 5678)
    inst.initialize()
    print(inst.idn)
    inst.finalize()

Let's look at the code line-by-line. First we import the class into our script::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

Then we create an instance of the class, setting the address to localhost and port to 5678::

    inst = LantzSignalGeneratorTCP('localhost', 5678)

This does not connects to the device. To do so, you call the `initialize` method::

    inst.initialize()

All Lantz drivers have an `initialize` method. Drivers that communicate through a port (e.g. a Serial port) will open the port in this call. Then we query the instrument for it's identification and we print it::

    print(inst.idn)

At the end, we call the `finalize` method to clean up all resources (e.g. close ports)::

    inst.finalize()

Just like the `initialize` method, all Lantz drivers have a `finalize`. Save the python script and run it by::

    $ python test_fungen.py

and you will get the following output::

    FunctionGenerator Serial #12345

In the window where `sim-fungen.py` is running you will see the message exchange. You normally don't see this in real instruments. Having a simulated instrument allow us to peek into it and understand what is going on: when we called `inst.idn`, the driver sent message (`?IDN`) to the instrument and it answered back (`FunctionGenerator Serial #12345`). Notice that end of line characters were stripped by the driver.

 To find out which other properties and methods are available checkout the documentation. A nice feature of Lantz (thanks to sphinx) is that useful documentation is generated from the driver itself. `idn` is a `Feat` of the driver. Think of a `Feat` as a pimped property. It works just like python properties but it wraps its call with some utilities (more on this later). `idn` is a read-only and as the documentation states it gets the identification information from the device. As `idn` is read-only, the following code will raise an exception::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    inst = LantzSignalGeneratorTCP('localhost', 5678)
    inst.initialize()
    inst.idn = 'A new identification' # <- This will fail as idn is read-only
    inst.finalize()

The problem is that finalize will never be called possibly leaving resources open. You need to wrap your possible failing code into a try-except-finally structure::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    inst = LantzSignalGeneratorTCP('localhost', 5678)
    inst.initialize()
    try:
        inst.idn = 'A new identification' # <- This will fail as idn is read-only
    except Exception as e:
        pass
    finally:
        inst.finalize()

All lantz drivers are also context managers and there fore you can write this in a much more compact way::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        inst.idn = 'A new identification' # <- This will fail as idn is read-only

The with statement will create an instance, assign it to `inst` and call `initialize`. The `finalize` will be called independently if there is an exception or not.


Lantz Feat in depth
-------------------

Let's query all parameters and print them state::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        print('idn: {}'.format(inst.idn))
        print('frequency: {}'.format(inst.frequency))
        print('amplitude: {}'.format(inst.amplitude))
        print('offset: {}'.format(inst.offset))
        print('output_enabled: {}'.format(inst.output_enabled))
        print('waveform: {}'.format(inst.waveform))
        for channel in range(1, 9):
            print('dout[{}]: {}'.format(channel, inst.dout[channel]))
        for channel in range(1, 9):
            print('din[{}]: {}'.format(channel, inst.din[channel]))


If you run the program you will get something like::

    idn: FunctionGenerator Serial #12345
    frequency: 1000.0 hertz
    amplitude: 0.0 volt
    offset: 0.0 volt
    output_enabled: False
    waveform: sine
    dout[1]: False
    dout[2]: False
    dout[3]: False
    dout[4]: False
    dout[5]: False
    dout[6]: False
    dout[7]: False
    dout[8]: False
    din[1]: False
    din[2]: False
    din[3]: False
    din[4]: False
    din[5]: False
    din[6]: False
    din[7]: False
    din[8]: False


Multiple queries
----------------

You can actually make it simpler. All lantz feats of a given instrument are registered within the driver. You can call the `refresh` method to get them all at once::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        state = inst.refresh()
        for key, value in state.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    print('{}[{}]: {}'.format(key, k, v))
            else:
                print('{}: {}'.format(key, value))
