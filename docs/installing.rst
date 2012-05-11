Building your development environment
=====================================

Lantz core requires only Python 3.2+. This guide also assumes that you have installed virtualenv and pip. If not, please install them by typing::

    $ easy_install virtualenv pip

(By the way, check out virtualenv wrapper as a way to easy handle your virtual environments)

Some lantz submodules have other requirements::

    - Colorama: `pip install colorama`

    - Sphinx: `pip install sphinx`

    - pySerial: use a binary package or `pip install pyserial`

    - NumPy: use a binary package or `pip install numpy`

    - Qt: use a binary package

    - pyQt: use a binary package or `pip install pyqt`



Linux
-----

Open a terminal and change to the folder where you will create your virtual environemnt. In this case, we have chosen the home directory::

    $ cd ~
    $ virtualenv -p python3 lantzenv
    $ cd lantzenv
    $ source bin/activate

and then install an editable package::

    $ pip install -e git+gitolite@glugcen.dc.uba.ar:lantz.git#egg=lantz

You will find the code in `~/lantzenv/src/lantz`.

The folder is a normal git repository from where you can pull and push to keep the repo in sync.

Windows
-------


Open a command windows and change to the folder where you will create your virtual environemnt. In this case, we have chosen the desktop::

    cd 	%USERPROFILE%\Desktop
    C:\Python32\Scripts\virtualenv --system-site-packages lantzenv
    cd lantzenv\Scripts
    activate

and then install an editable package::

    pip install -e git+gitolite@glugcen.dc.uba.ar:lantz.git#egg=lantz

You will find the code in `%USERPROFILE%\Desktop\lantzenv\src\lantz`.

The folder is a normal git repository from where you can pull and push to keep the repo in sync.
