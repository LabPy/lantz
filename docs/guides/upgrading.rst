.. _upgrading:

===========================
Upgrading to newer releases
===========================

Like any other package, Lantz is changing over time. Most of the changes are backwards compatible and you don’t have to change anything in your code to enjoy the new release.

But every once in a while we to introduce some disruptive changes. We might realize that something error prone or the API was confusing. Or we might introduce a better way to do things and you might need to change your code to take advantage of it.

This section of the documentation enumerates all the backwards incompatible changes in Lantz, helping you to transition your code from release to release.

You can upgrade to the latest version of Lantz using pip::

    pip install -U lantz


Upgrading to 0.3
----------------

We introduced the :class:`lantz.messagebased.MessageBasedDriver`, a class to rule them all. Replaces :class:`SerialDriver`, :class:`TCPDriver`, :class:`VisaDriver`, :class:`USBDriver`, :class:`USBTMCDriver`, :class:`SerialVisaDriver`, :class:`GPIBVisaDriver`, :class:`USBVisaDriver`.

Migrating your driver to use `MessageBasedDriver` is easy:

    1. Add the necessary imports::

            from lantz.messagebased import MessageBasedDriver

    2. Change the base class of your driver::

            class MyDriver(MessageBasedDriver):

                # Your code

    3. In the class methods, change `self.send` by `self.write`; and `self.recv` by `self.read`.
       This was done to homogenize the API with PyVISA

    4. Change the class defaults to use the :ref:`defaults_dictionary`.

You are **NOT** forced to migrate you classes. The old base classes are still available under :mod:`lantz.drivers.legacy`. So you can just change the import.

While all instrument drivers have been migrated to the new :class:`MessageBasedDriver` you can still used the drivers based on the legacy classes from :mod:`lantz.drivers.legacy`.

The only backwards incompatib
