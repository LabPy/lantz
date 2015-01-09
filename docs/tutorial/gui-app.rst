.. _tutorial-gui-app:


A simple GUI app
================

In this part of the tutorial you will build an application to custom function
generator GUI:

Start the simulated instrument running the following command::

    $ lantz-sim fungen tcp

Using Qt Designer, create a window like this:

.. image:: ../_static/tutorial/gui-app.png

and save it as `fungen.ui` in the folder in which you have created
the driver (:ref:`tutorial-building`). For the example, we have labeled
each control as corresponding label in lower caps (amplitude, offset,
waveform). The button is named `scan`.
You can also download
:download:`the ui file <../_static/tutorial/fungen.ui>` if you prefer.

Notice that the `amplitude` and `offset` don't show units and that the `waveform`
combobox is not populated. These widgets will be connected to the corresponding
Feats of the drivers and Lantz will take care of setting the right values, items,
etc.

Create a python file named `fungen-gui.py` with the following content:

.. code-block:: python

    import sys

    # Import from a lantz the start_gui helper function
    from lantz.ui.app import start_gui

    #
    with LantzSignalGenerator('TCPIP::localhost::5678::SOCKET') as inst:
        start_gui('fungen.ui', inst)

Run it and enjoy::

    $ python scanfrequency-gui.py

.. note:: In Windows, you can use `pythonw` instead of `python` to suppress the
   terminal window.

:func:start_gui take at leas two arguments. First, the fullpath of an QtDesigner ui file. As a second argument, an instrument instance.

Under the hood, `start_gui` is creating a Qt Application and loading the ui file. Then it matches by name Widgets to Feats and then connects them. Under the hood, for each match it:

    1.- Wraps the widget to make it Lantz compatible.

    2.- If applicable, configures minimum, maximum, steps and units.

    3.- Add a handler such as when the widget value is changed, the Feat is updated.

    4.- Add a handler such as when the Feat value is changed, the widget is updated.

You can learn more fine grained alternatives in :ref:`ui-driver`.


.. rubric::
   Learn how in the next part of the tutorial: :ref:`tutorial-gui-app`.
