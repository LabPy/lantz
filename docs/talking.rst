
Talking to instruments
======================

From the programming point of view, there are two possible ways of establishing a communication between an instrument and your program::

	- Exchanging (sometimes text) messages defined in an API via a standard port (Serial, Parallel, etc)
    - Calling a library (such as a DLL) that contains a predefined set of commands to talk to the instrument


Via message exchange
--------------------

Lantz provides appropiate base classes to 

In addition to the methods defined by :class:`Driver`, these classes define 


It is quite common

options: encoding, end of line, etc
methods: query, recv, send

serial and network examples

feat from text


Via library calls
-----------------

foreign module

