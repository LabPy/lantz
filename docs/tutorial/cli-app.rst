.. _tutorial-cli-app:


A simple command line app
=========================

In this part of the tutorial you will build a simple command line application
to do a frequency scan.

Start the simulated instrument running the following command::

    $ lantz-sim fungen tcp


Open the folder in which you have created the driver (:ref:`tutorial-building`)
and create a python file named `scanfrequency.py`:


.. code-block:: python

    import time

    from lantz import Q_

    from mydriver import LantzSignalGenerator

    Hz = Q_(1, 'Hz')
    start = 1 * Hz
    stop = 10 * Hz
    step = 1 * Hz
    wait = .5

    with LantzSignalGenerator('TCPIP::localhost::5678::SOCKET') as inst:
        print(inst.idn)

        current = start

        # This loop scans the frequency
        while current < stop:
            inst.frequency = current
            print('Changed to {}'.format(current))
            time.sleep(wait)
            current += step

First we the `time` module, the quantities class and the driver that you created
in the previous tutorial. We could have used the driver included in Lantz, but
we will work as if the driver was not in Lantz and you have built it yourself
for your project. We create an instance of it using a context manager
(the `with` statement) to make sure that all resources will be properly closed
even if an error occurs. Finally, we just step through all the frequencies,
changing the instrument and waiting at each step.

Run it using::

    $ python scanfrequency.py

Using command line arguments
----------------------------

In our first implementation the scan range and the waiting time were fixed. We
will now add mandatory command line arguments to set the start and stop frequency
and optionally the step size and the waiting time. To do this, we will import
the `argparse` module and create a parser object::

    import time
    import argparse

    from lantz import Q_

    from mydriver import LantzSignalGenerator

    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=float,
                        help='Start frequency [Hz]')
    parser.add_argument('stop', type=float,
                        help='Stop frequency [Hz]')
    parser.add_argument('step', type=float,
                        help='Step frequency [Hz]')
    parser.add_argument('wait', type=float,
                        help='Waiting time at each step [s]')

    args = parser.parse_args()

    Hz = Q_(1, 'Hz')
    start = args.start * Hz
    stop = args.stop * Hz
    step = args.step * Hz
    wait = args.wait

    with LantzSignalGenerator('TCPIP::localhost::5678::SOCKET') as inst:
        print(inst.idn)

        current = start
        while current < stop:
            inst.frequency = current
            print('Changed to {}'.format(current))
            time.sleep(wait)
            current += step

A nice thing about Python argparse package is that you get the help::

    $ python scanfrequency.py

or in more detail::

    python scanfrequency.py -h

Try it again specifying the start, stop, step and waiting time::

    $ python scanfrequency.py 2 8 2 .1


.. rubric::
   Learn how in the next part of the tutorial: :ref:`tutorial-gui-app`.
