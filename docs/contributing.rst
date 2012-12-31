.. _contributing:

============
Contributing
============

You are most welcome to contribute to Lantz with code, documentation and
translations. Please read the following document for guidelines.

Python style
------------

    * Unless otherwise specified, follow :pep:`8` strictly.

    * Document every class and method according to :pep:`257`.

    * Before submitting your code, use a tool like `pep8.py`_ and
      `pylint.py`_ to check for style.

    * `Feat` and `DictFeat` should be named with a noun or an adjective.

    * `Action` should be named with a verb.

    * Files should be utf-8 formatted.


Header
------

All files must have first the encoding indication, and then a header indicating
the module, a small description and the copyright message. For example:

.. code-block:: python

     # -*- coding: utf-8 -*-
     """
         lantz.foreign
         ~~~~~~~~~~~~~

         Implements classes and methods to interface to foreign functions.

         :copyright: (c) 2012 by Lantz Authors, see AUTHORS for more details.
         :license: BSD, see LICENSE for more details.
     """

Copyright
---------

Files in the Lantz repository don't list author names, both to avoid clutter
and to avoid having to keep the lists up to date. Instead, your name will
appear in the Git change log and in the AUTHORS file. The Lantz maintainer
will update this file when you have submitted your first commit.

Before your first contribution you must submit the :ref:`Contributor Agreement <agreement>`.
Code that you contribute should use the standard copyright header::

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


The easiest way is to start :ref:`contributing-drivers`. Once that you gain
experience with `Lantz` you can start :ref:`contributing-core`.


.. _pep8.py: http://pypi.python.org/pypi/pep8/
.. _pylint.py: http://www.logilab.org/857
.. _git: http://git-scm.com/
.. _reStructuredText: http://docutils.sf.net/rst.html
.. _Sphinx: http://sphinx.pocoo.org/
