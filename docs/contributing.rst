.. _contributing:

============
Contributing
============

You are most welcome to contribute to Lantz with code, documentation and translations. Please read the following document for guidelines.


File system structure
---------------------

The distribution is organized in the following folders:

docs

    Documentation in reStructuredText_ format with Sphinx_ makefile. Files must have a ``.rst`` extension

    To generate, for example, HTML documentation change into this folder and run::

        $ make html

    You will find the generated documentation in ``docs/_build/html/index.html``

examples

    Root folder for the examples.      

lantz

    Root folder containing the core functionality

        ui


        drivers

            There is a package folder for each manufacturer and module file for each instrument model (or family of models). All files are named using lowercase. Class drivers are named according to the model. If the model starts with a number, then the first letter of the manufacturer should be prefixed. Finally, all classes should be imported in the __init__.py of the corresponding package.


scripts

    Python scripts to provide simple command line functionality.

tests

    Test cases.


Python style
------------

    * Unless otherwise specified, follow :pep:`8` strictly.

    * Document every class and method according to :pep:`257`.

    * Before submitting your code, use a tool like `pep8.py`_ and `pylint.py`_ to check for style.

    * `Feat` and `DictFeat` should be named with a noun or an adjective.

    * `Action` should be named with a verb.


Version control system
----------------------

Lantz uses Git_ as version control system.

There are always at least two branches:
    * master: appropriate for users. It must always be in a working state.
    * develop: appropriate for developers. Might not be in a working state.

The master branch only accepts atomic, small commits. Larger changes that might break the master branch should happen in the develop branch. The develop branch will be merged into the master after deep testing. If you want to refactor major parts of the code or try new ideas, create a dedicated branch. This branch will merged into develop once tested.


Submitting your changes
-----------------------

Changes must be submitted for merging as patches or pull requests.

Before doing so, please check that:
    * The new code is functional.
    * The new code follows the style guidelines.
    * The new code is documented.
    * All tests are passed.
    * Any new file contains the appropiate header.
    * You commit to the head of the appropriate branch.

Commits must include a one-line description of the intended change followed, if necessary, by an empty line and detailed description.

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
