.. _initializing-setup:

=============================
Initializing multiple drivers
=============================

Initializing and finalizing drivers correctly is an important aspect of any
instrumentation application. In particular, if resources are left open after
the program finishes it can lead to deadlocks.

Lantz provides context managers to ensure that that these methods are called.
For example::

    with A2023a.via_serial(1) as fungen:

        print(fungen.idn)
        fungen.frequency = Q_(20, 'MHz')
        print(fungen.amplitude)
        fungen.sweep()


will call the initializer in the first line and the finalizer when the program
exits the block even in the case of an unhandled exception as explained in :ref:`Safely-releasing-resources`.

This approach is very useful but inconvenient if the number of instruments
is large. For three instruments is still fine::

    with FrequenceMeter.via_serial(1) as fmeter, \
         A2023a.from_serial_port(2) as fungen, \
         SR844.from_serial_port(3) as lockin:

        freq = fmeter.frequency

        fungen.frequency = freq
        lockin.frequency = freq

but for a larger number it will be annoying. In addition in GUI applications,
you might want to initialize the drivers when a button is pressed so wrapping
the code in a `with` statement is not an option.

Lantz provides `initialize_many` and `finalize_many` to solve this problem.

The previous example will look like this::

    drivers = (FrequenceMeter.via_serial(1), A2023a.via_serial(2), SR844.via_serial(3))

    initialize_many(drivers)

Under the hood, `initialize_many` is calling the `initialize` method of each
driver and registering the `finalize` method to be executed when the Python
interpreter exits.

If you want to call the finalizers manually, you can::

    initialize_many(drivers, register_finalizer=False)
    # Do Something
    finalize_many(drivers)


Providing status
----------------

You can define two callback functions to be executed before and after driver
initialization::

    start = time.time()
    def initializing(driver):
        print('Initializing ' driver.name)

    def initialized(driver):
            print('Initialized {} in {} secs'.format(driver.name, time.time() - start))

    initialize_many(drivers, on_initializing=initializing, on_initialized=initialized)
    print('Done in {:.1f} secs'.format(time.time() - start))

will print (if we assume for each instrument certain initialization times)::

    Initializing FrequenceMeter1
    Initialized FrequenceMeter1 in 3.2 secs
    Initializing A2023a1
    Initialized A2023a1 in 4.1 secs
    Initializing SR8441
    Initialized SR8441 in 3.5 secs
    Done in 10.8 seconds.


`Initializing` and `Initialized` are interleaved as the initialization of all
drivers occurs serially.

Similarly, in `finalize_many` you can use `on_finalizing` and `on_finalized`.


Faster initialization and finalization
--------------------------------------

In most cases, the initialization of each driver is independent of the rest and
a significant speed up can be achieved by running the tasks concurrently::

    initialize_many(drivers, on_initializing=initializing, on_initialized=initialized, concurrent=True)

The output will no be::

    Initializing FrequenceMeter1
    Initializing SR8441
    Initializing A2023a1
    Initialized FrequenceMeter1 in 3.2 secs
    Initialized SR8441 in 3.5 secs
    Initialized A2023a1 in 4.1 secs
    Done in 4.1 seconds.

Initialization is now done concurrently yielding 2x speed up. For a larger number
of instruments, the speed up will be even larger.

You can also use this argument in `finalize_many`.


Initialization hierarchy
------------------------

If a particular order in the initialization is required, you can order the list
(or tuple) and do a serial (concurrent=False) initialization. But is slow again.

You can specify a hierarchy of initialization using the `dependencies` argument.
If the A2023a1 requires that SR8441 and FrequenceMeter1 are initialized
before, the call will be::

    initialize_many(drivers, on_initializing=initializing, on_initialized=initialized,
                    concurrent=True, dependencies={'A2023a1': ('SR8441', 'FrequenceMeter1')})

and the result will be::

    Initializing FrequenceMeter1
    Initializing SR8441
    Initialized FrequenceMeter1 in 3.2 secs
    Initialized SR8441 in 3.5 secs
    Initializing A2023a1
    Initialized A2023a1 in 4.1 secs
    Done in 7.6 seconds.

The `dependencies` argument takes a dictionary where each key is a driver name
and the corresponding value is a list of the drivers names that need to be
initialized before. It can have arbitrary complexity. If a driver is not present
in the dictionary, it will be initialized with the ones without dependencies.

You can use these arguments also in `finalize_many`, but the requirements are
interpreted in reverse. This allows to use the same dependency specification that
you have used for `initialized setup`.


Exception handling
------------------

If an exception occurs while initializing or finalizing a driver, it will be
bubbled up.

You can change this behaviour by providing an `on_exception` argument. It
takes a callback with two arguments, the driver and the exception.

If you want to print the exception::

    def print_and_continue(driver, ex):
        print('An exception occurred while initializing {}: {}'.format(driver, ex))

    initialize_many(drivers, on_exception=print_and_continue)

or if you want to re-raise the exception, you can define a different callback::

    def print_and_raise(driver, ex):
        print('An exception occurred while initializing {}: {}'.format(driver, ex))
        raise ex

    initialize_many(drivers, on_exception=print_and_raise)



.. seealso::

    :ref:`ui-initializing`




