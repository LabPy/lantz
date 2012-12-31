.. _tutorial-using:


Using lantz drivers
===================

In this part of the tutorial, you will learn how to use Lantz drivers to control an instrument. Lantz is shipped with drivers for common laboratory instruments. Each instrument has different capabilities, and these reflect in the drivers being different. However, all Lantz drivers share a common structure and learning about it allows you to use them in a more efficient way.

Following a tutorial about using a driver to communicate with an instrument that you do not have is not much fun. That's why we have created a virtual version of this instrument. From the command line, run the following command::

    $ lantz-sim fungen tcp

.. note::
   If you are using Windows, it is likely that `lantz-sim` script is not be in
   the path. You will have to change directory to `C:\\Python32\\Scripts` or
   something similar.

This will start an application (i.e. your instrument) that listens for incoming TCP packages (commands) on port 5678 from `localhost`. In the screen you will see the commands received and sent by the instrument.

Your program and the instrument will communicate by exchanging text commands via TCP. But having a Lantz driver already built for your particular instrument releases you for the burden of sending and receiving the messages. Let's start by finding the driver. Lantz drivers are organized inside packages, each package named after the manufacturer. So the `Coherent Argon Laser Innova` 300C driver is in `lantz.drivers.coherent` under the name `ArgonInnova300C`. We follow Python style guide (PEP8) to name packages and modules (lowercase) and classes (CamelCase).

Make a new folder for your project and create inside a python script named `test_fungen.py`. Copy the following code inside the file::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    inst = LantzSignalGeneratorTCP('localhost', 5678)
    inst.initialize()
    print(inst.idn)
    inst.finalize()

Let's look at the code line-by-line. First we import the class into our script::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

The driver for our simulated device is under the company `examples` and is named `LantzSignalGeneratorTCP`.
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

.. note:: If you have different versions of python installed, remember to use
          the one in which you have installed Lantz. You might need to use
          `python3` instead of `python`.

and you will get the following output::

    FunctionGenerator Serial #12345

In the window where `sim-fungen.py` is running you will see the message exchange. You normally don't see this in real instruments. Having a simulated instrument allow us to peek into it and understand what is going on: when we called `inst.idn`, the driver sent message (`?IDN`) to the instrument and it answered back (`FunctionGenerator Serial #12345`). Notice that end of line characters were stripped by the driver.

To find out which other properties and methods are available checkout the documentation. A nice feature of Lantz (thanks to sphinx) is that useful documentation is generated from the driver itself. `idn` is a `Feat` of the driver. Think of a `Feat` as a pimped property. It works just like python properties but it wraps its call with some utilities (more on this later). `idn` is a read-only and as the documentation states it gets the identification information from the device.

Safely releasing resources
--------------------------

As `idn` is read-only, the following code will raise an exception::

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
        print(e)
    finally:
        inst.finalize()

All lantz drivers are also context managers and there fore you can write this in a much more compact way::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        # inst.initialize is called as soon as you enter this block
        inst.idn = 'A new identification' # <- This will fail as idn is read-only
        # inst.finalize is called as soon as you leave this block,
        # even if an error occurs

The with statement will create an instance, assign it to `inst` and call `initialize`. The `finalize` will be called independently if there is an exception or not.

Logging
-------

Lantz uses internally the python logging module :py:class:`logging.Logger`.
At any point in your code you can obtain the root Lantz logger::

    from lantz import LOGGER

But additionally, Lantz has some convenience functions to display the log
output in a nice format::

    from lantz.log import log_to_screen, DEBUG, INFO, CRITICAL

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    # This directs the lantz logger to the console.
    log_to_screen(DEBUG)

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        print(inst.idn)
        print(inst.waveform)

Run this script to see the generated log information (it should be colorized
in your screen)::

    16:25:03 INFO     Created LantzSignalGeneratorTCP0
    16:25:03 DEBUG    Opening port ('localhost', 5678)
    16:25:03 INFO     Getting idn
    16:25:03 DEBUG    Sending b'?IDN\n'
    16:25:03 DEBUG    Received 'FunctionGenerator Serial #12345\n' (len=32)
    16:25:03 DEBUG    (raw) Got FunctionGenerator Serial #12345 for idn
    16:25:03 INFO     Got FunctionGenerator Serial #12345 for idn
    FunctionGenerator Serial #12345
    16:25:03 INFO     Getting waveform
    16:25:03 DEBUG    Sending b'?WVF\n'
    16:25:03 DEBUG    Received '0\n' (len=2)
    16:25:03 DEBUG    (raw) Got 0 for waveform
    16:25:03 INFO     Got sine for waveform
    sine
    16:25:03 DEBUG    Closing port ('localhost', 5678)

The first line shows the creation of the driver instance. As no name was
provided, Lantz assigns one (`LantzSignalGeneratorTCP0`). Line 2 shows that
the port was opened (in the implicit call to initialize in the `with` statement).
We then request the `idn` (line 3), which is done by sending the command via
the TCP port (line 4). 32 bytes are received from the instrument (line 5)
which are stripped from the en of line (line 4) and processed (line 6, in this
case there is no processing done).

Then the same structure repeats for `waveform`, and important difference is that
the driver receives `0` from the instrument and this is translated to the
more user friendly `sine`.

Finally, the port is closed (in the implicit call to finalize when leaving
the `with` block).

The lines without the time are the result of the print function.

Change `INFO` to `DEBUG` or to `CRITICAL` and run it again to see the different
levels of information you can get.

You can change the name of the instrument when you instantiate it::

    from lantz.log import log_to_screen, DEBUG, INFO, CRITICAL

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    # This directs the lantz logger to the console.
    log_to_screen(DEBUG)

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        print(inst.idn)
        print(inst.waveform)


The cache
---------

As you have seen before, logging provides a look into the Lantz internals.
Let's duplicate some code::

    from lantz.log import log_to_screen, DEBUG

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    # This directs the lantz logger to the console.
    log_to_screen(DEBUG)

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        print(inst.idn)
        print(inst.idn)
        print(inst.waveform)
        print(inst.waveform)

If you see the log output::

    16:34:40 INFO     Created LantzSignalGeneratorTCP0
    16:34:40 DEBUG    Opening port ('localhost', 5678)
    16:34:40 INFO     Getting idn
    16:34:40 DEBUG    Sending b'?IDN\n'
    16:34:40 DEBUG    Received 'FunctionGenerator Serial #12345\n' (len=32)
    16:34:40 DEBUG    (raw) Got FunctionGenerator Serial #12345 for idn
    16:34:40 INFO     Got FunctionGenerator Serial #12345 for idn
    FunctionGenerator Serial #12345
    FunctionGenerator Serial #12345
    16:34:40 INFO     Getting waveform
    16:34:40 DEBUG    Sending b'?WVF\n'
    16:34:40 DEBUG    Received '0\n' (len=2)
    16:34:40 DEBUG    (raw) Got 0 for waveform
    16:34:40 INFO     Got sine for waveform
    sine
    16:34:40 INFO     Getting waveform
    16:34:40 DEBUG    Sending b'?WVF\n'
    16:34:40 DEBUG    Received '0\n' (len=2)
    16:34:40 DEBUG    (raw) Got 0 for waveform
    16:34:40 INFO     Got sine for waveform
    sine
    16:34:40 DEBUG    Closing port ('localhost', 5678)

`idn` is only requested once, but waveform twice as you except. The reason
is that `idn` is marked `read_once` in the driver as it does not change.
The value is cached, preventing unnecessary communication with the instrument.

The cache is specially useful with setters::

    from lantz.log import log_to_screen, DEBUG

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    # This directs the lantz logger to the console.
    log_to_screen(DEBUG)

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        inst.waveform = 'sine'
        inst.waveform = 'sine'

the log output::

    16:40:08 INFO     Created LantzSignalGeneratorTCP0
    16:40:08 DEBUG    Opening port ('localhost', 5678)
    16:40:08 INFO     Setting waveform = sine (current=MISSING, force=False)
    16:40:08 DEBUG    (raw) Setting waveform = 0
    16:40:08 DEBUG    Sending b'!WVF 0\n'
    16:40:08 DEBUG    Received 'OK\n' (len=3)
    16:40:08 INFO     waveform was set to sine
    16:40:08 INFO     No need to set waveform = sine (current=sine, force=False)
    16:40:08 DEBUG    Closing port ('localhost', 5678)

Lantz prevents setting the waveform to the same value, a useful feature to speed
up communication with instruments in programs build upon decoupled parts.

If you have a good reason to force the change of the value, you can do it with
the `update` method::

    from lantz.log import log_to_screen, DEBUG, INFO, CRITICAL

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    # This directs the lantz logger to the console.
    log_to_screen(DEBUG)

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        inst.waveform = 'sine'
        inst.update(waveform='sine', force=True)

the log output (notice `force=True`)::

    16:41:03 INFO     Created LantzSignalGeneratorTCP0
    16:41:03 DEBUG    Opening port ('localhost', 5678)
    16:41:03 INFO     Setting waveform = sine (current=MISSING, force=False)
    16:41:03 DEBUG    (raw) Setting waveform = 0
    16:41:03 DEBUG    Sending b'!WVF 0\n'
    16:41:03 DEBUG    Received 'OK\n' (len=3)
    16:41:03 INFO     waveform was set to sine
    16:41:03 INFO     Setting waveform = sine (current=sine, force=True)
    16:41:03 DEBUG    (raw) Setting waveform = 0
    16:41:03 DEBUG    Sending b'!WVF 0\n'
    16:41:03 DEBUG    Received 'OK\n' (len=3)
    16:41:03 INFO     waveform was set to sine
    16:41:03 DEBUG    Closing port ('localhost', 5678)


Cache related methods: update, refresh and recall
-------------------------------------------------

You have already seen the update method, a method to **set**::

    inst.waveform = 'sine'

is equivalent to::

    inst.update(waveform='sine')

and can also take a dict as an input::

    inst.update({'waveform': 'sine'})

You can also **set** many values at once::

    inst.update(waveform='sine', amplitude=value)

or equivalently::

    inst.update({'waveform': 'sine'}, 'amplitude': value})

but remember that internally these commands will be serialized as not all
instruments are capable of dealing with multiple commands.

As you have seen, the update method has a keyword parameter (`force`) that
will ignore the current value in the cache.

Lantz also has a method to **get**, named `refresh`::

    inst.waveform

is equivalent to::

    inst.refresh('waveform')

And also work with multiple names::

    inst.refresh(('frequency', 'amplitude'))

or::

    inst.refresh()

to get all values.

In some cases you need the value of some attribute of the instrument that
you have not changed since the last time you got/set. The `recall` method returns
the value stored in the cache::

    from lantz.log import log_to_screen, DEBUG

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    # This directs the lantz logger to the console.
    log_to_screen(DEBUG)

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        print(inst.waveform)
        print(inst.recall('waveform'))


.. rubric::
   You can use the the driver that you have created in you projects.
   Learn more in the next part of the tutorial: :ref:`tutorial-using-feats`.
