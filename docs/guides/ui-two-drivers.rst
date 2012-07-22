.. _ui-two-drivers:

================================
Connecting two (or more) drivers
================================

Real application consists not only of a single instrument but many. In a custom UI, you can connect different drivers to different widgets. Consider the following interace for two signal generators.

.. image:: ../_static/guides/ui-two-drivers-1.png
   :alt: Two signal generators

(We use twice the same kind for simplicity, but it is not necessary).

The widgets are named `fungen1__frequency` and `fungen2__frequency`.


The long way
------------

Get a reference to each widget and connect them manually::

    import sys

    # Import lantz.ui register an import hook that will replace calls to Qt by PyQt4 or PySide ...
    import lantz.ui

    # and here we just use Qt and will work with both bindings!
    from Qt.QtGui import QApplication, QWidget
    from Qt.uic import loadUi

    # From lantz we import the driver ...
    from lantz.drivers.examples.fungen import LantzSignalGeneratorTCP

    # and a function named connect_feat that does the work.
    from lantz.ui.qtwidgets import connect_feat

    app = QApplication(sys.argv)

    # We load the UI from the QtDesigner file. You can also use pyuic4 to generate a class.
    main = loadUi('ui-two-drivers.ui')

    # We get a reference to each of the widgets.
    freq1 = main.findChild((QWidget, ), 'fungen1__frequency')
    freq2 = main.findChild((QWidget, ), 'fungen2__frequency')

    with LantzSignalGeneratorTCP('localhost', 5678) as inst1, \
         LantzSignalGeneratorTCP('localhost', 5679) as inst2:

        # We connect each widget to each feature
        # The syntax arguments are widget, target (driver), Feat name
        connect_feat(freq1, inst1, 'frequency')
        connect_feat(freq2, inst2, 'frequency')
        main.show()
        exit(app.exec_())



The not so long way
-------------------

If you have use a prefix to solve the name collision you can use it and connect the driver::

    import sys

    # Import lantz.ui register an import hook that will replace calls to Qt by PyQt4 or PySide ...
    import lantz.ui

    # and here we just use Qt and will work with both bindings!
    from Qt.QtGui import QApplication, QWidget
    from Qt.uic import loadUi

    # From lantz we import the driver ...
    from lantz.drivers.examples.fungen import LantzSignalGeneratorTCP

    # and a function named connect_feat that does the work.
    from lantz.ui.qtwidgets import connect_feat

    app = QApplication(sys.argv)

    # We load the UI from the QtDesigner file. You can also use pyuic4 to generate a class.
    main = loadUi('ui-two-drivers.ui')

    with LantzSignalGeneratorTCP('localhost', 5678) as inst1, \
         LantzSignalGeneratorTCP('localhost', 5679) as inst2:

        # We connect each widget to each feature
        # The syntax arguments are widget, target (driver), Feat name
        connect_driver(main, inst1, prefix='fungen1')
        connect_driver(main, inst2, prefix='fungen1')
        main.show()
        exit(app.exec_())

This does not look like too much saving but if more than one Feat per driver to connect, `connect_driver` will do them all for you. Under the hood, `connect_driver` is iterating over all widgets and checking if the driver contains a Feat with the widget name prefixed by `prefix`. Note that we have used `fungen1` instead of `fungen1__` as the prefix. That is because `connect_driver` uses the double underscore as a separator by default. You can change it by passing the `sep` keyword argument.


The short way
-------------

If you have named the widgets according to the Feat name and added a prefix corresponding to the feat::

    import sys

    # Import lantz.ui register an import hook that will replace calls to Qt by PyQt4 or PySide ...
    import lantz.ui

    # and here we just use Qt and will work with both bindings!
    from Qt.QtGui import QApplication, QWidget
    from Qt.uic import loadUi

    # From lantz we import the driver ...
    from lantz.drivers.examples.fungen import LantzSignalGeneratorTCP

    # and a function named connect_feat that does the work.
    from lantz.ui.qtwidgets import connect_feat

    app = QApplication(sys.argv)

    # We load the UI from the QtDesigner file. You can also use pyuic4 to generate a class.
    main = loadUi('ui-two-drivers.ui')

    # Notice that now we specify the instrument name!
    with LantzSignalGeneratorTCP('localhost', 5678, name='fungen1') as inst1, \
         LantzSignalGeneratorTCP('localhost', 5679, name='fungen2') as inst2:

        # We connect the whole main widget, and we give a list of drivers.
        connect_setup(main, [inst1, inst2])
        main.show()
        exit(app.exec_())


Under the hood, `connect_setup` iterates over all drivers in the second argument and executes `connect_driver` using the driver name.


.. seealso::

    :ref:`ui-driver`

    :ref:`ui-feat-two-widgets`


