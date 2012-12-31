.. _contributing-core:

========================
Contributing to the core
========================

To contribute to the core, you need to clone the `Lantz` repository first.


Version control system
----------------------

Lantz uses Git_ as version control system.

There are always at least two branches:
    * master: appropriate for users. It must always be in a working state.
    * develop: appropriate for developers. Might not be in a working state.

The master branch only accepts atomic, small commits. Larger changes that might break the master branch should happen in the develop branch. The develop branch will be merged into the master after deep testing. If you want to refactor major parts of the code or try new ideas, create a dedicated branch. This branch will merged into develop once tested.

The easiest way to start hacking Lantz codebase is using a virtual environment
and cloning an editable package.

Assuming that you have installed all the requirements described in
:ref:`tutorial-installing`, in OSX/Linux::

    $ pip-3.2 install virtualenv
    $ cd ~
    $ virtualenv -p python3.2 --system-site-packages lantzenv
    $ cd lantzenv
    $ source bin/activate

and in Windows::

    C:\Python3.2\Scripts\pip install virtualenv
    cd 	%USERPROFILE%\Desktop
    C:\Python32\Scripts\virtualenv --system-site-packages lantzenv
    cd lantzenv\Scripts
    activate

and then install an editable package::

    $ pip install -e git+gitolite@glugcen.dc.uba.ar:lantz.git#egg=lantz

or from `Lantz at Github`_::

    $ pip install -e git+git://github.com/hgrecco/lantz.git#egg=lantz

You will find the code in `~/lantzenv/src/lantz` (OSX/Linux) or
`%USERPROFILE%\\Desktop\\lantzenv\\src\\lantz` (Windows).


File system structure
---------------------

The distribution is organized in the following folders:

**docs**

    Documentation in reStructuredText_ format with Sphinx_ makefile. Files must have a ``.rst`` extension

    To generate, for example, HTML documentation change into this folder and run::

        $ make html

    You will find the generated documentation in ``docs/_build/html/index.html``

**examples**

    Root folder for the examples.      

**lantz**

    Root folder containing the core functionality

        **drivers**

            There is a package folder for each manufacturer and module file for each instrument model (or family of models). All files are named using lowercase. Class drivers are named according to the model. If the model starts with a number, then the first letter of the manufacturer should be prefixed. Finally, all classes should be imported in the __init__.py of the corresponding package.

        **simulators**

            Instrument simulators

        **ui**

            User interface related code.

**scripts**

    Python scripts to provide simple command line functionality.

**tests**

    Test cases.


Python style
------------

    * Unless otherwise specified, follow :pep:`8` strictly.

    * Document every class and method according to :pep:`257`.

    * Before submitting your code, use a tool like `pep8.py`_ and `pylint.py`_ to check for style.

    * `Feat` and `DictFeat` should be named with a noun or an adjective.

    * `Action` should be named with a verb.

    * Files should be utf-8 formatted.


Header
------

All files must have first the encoding indication, and then a header indicating the
module, a small description and the copyright message. For example:

.. code-block:: python

     # -*- coding: utf-8 -*-
     """
         lantz.foreign
         ~~~~~~~~~~~~~

         Implements classes and methods to interface to foreign functions.

         :copyright: (c) 2012 by Lantz Authors, see AUTHORS for more details.
         :license: BSD, see LICENSE for more details.
     """


Submitting your changes
-----------------------

Changes must be submitted for merging as patches or pull requests.

Before doing so, please check that:
    * The new code is functional.
    * The new code follows the style guidelines.
    * The new code is documented.
    * All tests are passed.
    * Any new file contains an appropriate header.
    * You commit to the head of the appropriate branch (usually develop).

Commits must include a one-line description of the intended change followed, if necessary, by an empty line and detailed description. You can send your patch by e-mail to `lantz.contributor@gmail.com`::

    $ git format-patch origin/develop..develop
    0001-Changed-Driver-class-to-enable-inheritance-of-Action.patch
    0002-Added-RECV_CHUNK-to-TextualMixin.patch


or send a pull request.


Copyright
---------

Files in the Lantz repository don't list author names, both to avoid clutter and to avoid having to keep the lists up to date. Instead, your name will appear in the Git change log and in the AUTHORS file. The Lantz maintainer will update this file when you have submitted your first commit.

Before your first contribution you must submit the :ref:`Contributor Agreement <agreement>`. Code that you contribute should use the standard copyright header::

    :copyright: (c) 2012 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.


Finally, we have a small Zen
----------------------------

::

    import this
    Lantz should not get in your way.
    Unless you actually want it to.
    Even then, python ways should not be void. 
    Provide solutions for common scenarios.
    Leave the special cases for the people who actually need them.
    Logging is great, do it often!


.. _pep8.py: http://pypi.python.org/pypi/pep8/
.. _pylint.py: http://www.logilab.org/857
.. _git: http://git-scm.com/
.. _reStructuredText: http://docutils.sf.net/rst.html
.. _Sphinx: http://sphinx.pocoo.org/
