
lantz.stringparser
==================

A stand alone module used by lantz. (`website <http://pypi.python.org/pypi/stringparser/>`_)

Motivation
----------

The ``stringparser`` module provides a simple way to match patterns and extract
information within strings. As patterns are given using the familiar format
string specification :pep:`3101`, writing them is much easier than writing
regular expressions (albeit less powerful).


Examples
--------

You can build a reusable parser object::

    >>> parser = Parser('The answer is {:d}')
    >>> parser('The answer is 42')
    42
    >>> parser('The answer is 54')
    54

Or directly::

    >>> Parser('The answer is {:d}')('The answer is 42')
    42

You can retrieve many fields::

    >>> Parser('The {:s} is {:d}')('The answer is 42')
    ('answer', 42)

And you can use numbered fields to order the returned tuple::

    >>> Parser('The {1:s} is {0:d}')('The answer is 42')
    (42, 'answer')

Or named fields to return an OrderedDict::

    >>> Parser('The {a:s} is {b:d}')('The answer is 42')
    OrderedDict([('a', 'answer'), ('b', 42)])

You can ignore some fields using _ as a name::

    >>> Parser('The {_:s} is {:d}')('The answer is 42')
    42


Limitations
-----------

- From the format string:
  `[[fill]align][sign][#][0][minimumwidth][.precision][type]`
  only `type`, `sign` and `#` are currently implemented.
  This might cause trouble to match certain notation like:

  - decimal: '-4' written as '-     4'
  - etc

- Lines are matched from beginning to end. {:d} will NOT return all
  the numbers in the string. Use regex for that.

