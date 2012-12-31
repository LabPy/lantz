.. _tutorial-using-feats:

Using Feats
===========

Let's query all parameters and print their state in a nice format::

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

Valid values
------------

You can set property like `output_enabled`::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        print('output_enabled: {}'.format(inst.output_enabled))
        inst.output_enabled = True
        print('output_enabled: {}'.format(inst.output_enabled))

If you check the documentation for lantz.drivers.examples.LantzSignalGeneratorTCP),
`output_enabled` accepts only `True` or `False`. If your provide a different value::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        inst.output_enabled = 'Yes'

you will get an error message::

    Traceback (most recent call last):
      File "using7.py", line 5, in <module>
        inst.output_enabled = 'Yes'
    ...
    ValueError: 'Yes' not in (False, True)

Units
-----

Feats corresponding to physical quantities (magnitude and units), are declared
with a default unit. If try to set a number to them::

    from lantz.drivers.examples import LantzSignalGeneratorTCP

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        inst.amplitude = 1

Lantz will issue a warning::

    DimensionalityWarning: Assuming units `volt` for 1

Lantz uses the Pint_ package to declare units::

    from lantz.drivers.examples import LantzSignalGeneratorTCP
    from lantz import Q_

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        inst.amplitude = Q_(1, 'Volts')
        print('amplitude: {}'.format(inst.amplitude))

the output is::

    amplitude: 1.0 volt

The nice thing is that this will work even if the instruments and you program
opeate in different units. The conversion is done internally, minimizing errors
and allowing better interoperability::

    from lantz.drivers.examples import LantzSignalGeneratorTCP
    from lantz import Q_

    with LantzSignalGeneratorTCP('localhost', 5678) as inst:
        inst.amplitude = Q_(.1, 'decivolt')
        print('amplitude: {}'.format(inst.amplitude))

the output is::

    amplitude: 0.1 volt

Numerical Feats can also define the valid limits, for amplitude is 0 - 10 Volts.
If you provide a value out of range::

    inst.amplitude = Q_(20, 'volt')

you get::

    Traceback (most recent call last):
      File "using10.py", line 6, in <module>
        inst.amplitude = Q_(20, 'volt')
    ...
    ValueError: 20 not in range (0, 10)


.. rubric::
   While Lantz aims to provide drivers for most common instruments,
   sometimes you will need to build your own drivers.
   Learn how in the next part of the tutorial: :ref:`tutorial-building`.

.. _Pint: https://pint.readthedocs.org/
