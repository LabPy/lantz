.. _tutorial-installing:

Installation guide
==================

This guide describes Lantz requirements and provides platform specific
installation guides. Examples are given for Python 3.2 installing all
optional requirements as site-packages.

Requirements
------------

Lantz core requires only `Python`_ 3.2+.


Optional requirements
---------------------

Some lantz subpackages have other requirements which are listed below together
with a small explanation of where are used. Short installation instructions are
given, but we refer you to the package documentation for more information. For some
packages, a link to the binary distribution is given. Specifi

    - `Colorama`_ is used to colorize terminal output.
      It is optional when logging to screen and mandatory if you want to use `lantz-monitor`, the text-based log viewer.

    - `Sphinx`_ is used generate the documentation.
      It is optional and only needed if you want to generate the documentation yourself.

    - `Docutils`_ is used to transform the RST documentation to HTML which is then provided as tooltips in the GUI.
      It is optional. If not installed, unformatted documentation will be shown as tooltips.
      It will be already installed if you install Sphinx.

    - `pySerial`_ it is to communicate via serial port.
      It is optional and only needed if you are using a driver that uses lantz.serial.

    - `Qt4`_ is used to generate the graphical user interfaces. Due to a license issue there
      are two python bindings for Qt: `PyQt`_ and `PySide`_.

    - `NumPy`_ is used by many drivers to perform numerical calculations.

    - `VISA`_ National Instruments Library for communicating via  GPIB, VXI, PXI,
      Serial, Ethernet, and/or USB interfaces


- :ref:`linux`
- :ref:`mac`
- :ref:`windows`

.. _linux:

Linux
-----

Most linux distributions provide packages for Python 3.2, NumPy, PyQt (or PySide).
There might be some other useful packages. For some distributions, you will find
specific instructions below.

Ubuntu 12.04
^^^^^^^^^^^^
::

    $ sudo apt-get python3
    $ sudo apt-get install python3-pkg-resources python3-pyqt4 python3-setuptools python3-sphinx
    $ sudo apt-get install python3-numpy

and continue to to step 4 in OSX

Ubuntu 12.10
^^^^^^^^^^^^
::

    $ sudo apt-get python3
    $ sudo apt-get install python3-pkg-resources python3-pyqt4 python3-setuptools python3-sphinx python3-pip
    $ sudo apt-get install python3-numpy

and continue to to step 5 in OSX

openSUSE 12.2
^^^^^^^^^^^^^
::

    $ sudo zypper install python3
    $ sudo zypper install python3-pip python3-pyqt4 python3-Sphinx python-distutils-extra
    $ sudo zypper install python3-numpy

and continue to to step 5 in OSX

.. _mac:

OSX
---

1. Install Python 3.2
2. (optionally) Install PyQt_, NumPy_
3. (optionally) Install VISA_
4. Open a terminal to install pip::

    $ curl http://python-distribute.org/distribute_setup.py | python3.2
    $ curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python3.2

5. Using pip, install Lantz and its dependencies other optional dependencies::

    $ pip-3.2 install -r https://github.com/hgrecco/lantz/requirements-full.txt


.. _windows:

Windows
-------


.. note::

    We provide a simple script to run all the steps provided below. Download
    `get-lantz`_ to the folder in which you want to create the virtual environment.
    The run the script using a 32 bit version of `Python`_ 3.2+.

    In some of the steps, an installer application will pop-up. Just select all
    default options.

    As the script will download and install only necessary packages, it does not
    need a clean Python to start.


Install `Python`_, `NumPy binaries`_, `PyQt binaries`_ (or `PySide binaries`), `VISA`_.

Download and run with Python 3.2::

    - http://python-distribute.org/distribute_setup.py
    - https://raw.github.com/pypa/pip/master/contrib/get-pip.py

In the command prompt install using pip all other optional dependencies::

    $ C:\Python3.2\Scripts\pip install -r https://github.com/hgrecco/lantz/requirements-full.txt


.. rubric::
   If the driver from your instrument is available, you can start to use it right away.
   Learn how in the next part of the tutorial: :ref:`tutorial-using`.

.. _pip: http://www.pip-installer.org/en/latest/index.html
.. _virtualenv: http://www.virtualenv.org/en/latest/index.html
.. _Colorama: http://pypi.python.org/pypi/colorama/
.. _Sphinx: http://sphinx.pocoo.org/
.. _Docutils: http://docutils.sourceforge.net/
.. _pySerial: http://pyserial.sourceforge.net/
.. _pySerial binaries: http://pyserial.sourceforge.net/pyserial.html#packages
.. _Qt4: http://qt.nokia.com/products/
.. _PyQt: http://www.riverbankcomputing.co.uk/software/pyqt
.. _PyQt binaries: http://www.riverbankcomputing.co.uk/software/pyqt/download/
.. _PySide: http://www.pyside.org/
.. _PySide binaries: http://qt-project.org/wiki/Category:LanguageBindings::PySide::Downloads
.. _NumPy: http://numpy.scipy.org/
.. _NumPy binaries: http://sourceforge.net/projects/numpy/files/
.. _Lantz at Github: https://github.com/hgrecco/lantz
.. _get-lantz: https://raw.github.com/hgrecco/lantz/master/scripts/get-lantz.py
.. _Python: http://www.python.org/getit/
.. _VISA: http://www.ni.com/visa/
.. _git: http://git-scm.com/
.. _git binaries: http://git-scm.com/downloads
