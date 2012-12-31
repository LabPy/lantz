.. _faq:

====
FAQs
====

Why building an instrumentation toolkit?
----------------------------------------

Instrumentation and experiment automation became a cornerstone of modern science. Most of the devices that we use to quantify and perturb natural processes can or should be computer controlled. Moreover, the ability to control and synchronize multiple devices, enables complex experiments to be accomplished in a reproducible manner.

This toolkit emerges from my frustration with existing languages, libraries and frameworks for instrumentation:

  - Domain specific languages that make extremely difficult to achieve things that are
    trivial in most general-purpose   languages.
  - Lots of boilerplate code to achieve consistent behaviour across an application.
  - Inability to use existing libraries.

Lantz aims to reduce the burden of writing a good instrumentation software by providing base classes from which you can derive your own. These classes provide the boilerplate code that enables advanced functionality, allowing you to concentrate in the program logic.


Why not using LabVIEW/LabWindows/Matlab?
----------------------------------------

LabVIEW is a development environment for a graphical programming language called "G" in which the flow of information in the program is determined by the connections between functions. While this concept is clear for non programmers, it quickly becomes a burden in big projects. Common procedures for source control, maintainable documentation, testing, and metaprogramming are cumbersome or just unavailable.

On the other hand, Matlab is a text based programming language with focus in numerical methods. It provides a set of additional function via its instrumentation toolbox.

Common to these two plataforms is that they have *evolved* a full fledged programming language from domain specific one while trying to maintain backwards compatibility. Many of the weird ways of doing things in these languages arise from this organic growth.

Unlike LabVIEW, LabWindows/CVI is ANSI C plus a set of convenient libraries for instrumentation. It brings all the goodies of C but it also all the difficulties such as memmory management.

Last but not least, these languages are propietary and expensive, locking your development. We need a free, open source toolkit for instrumentation build using a proven, mature, cross-plataform and well-though programming language.


But ... there are a lot of drivers already available for these languages
------------------------------------------------------------------------

It is true, but many of these drivers are contributed by the users themselves. If a new toolkit emerges with enough momentum, many of those users will start to contribute to it. And due to the fact that building good drivers in Lantz is much easier than doing it in any of the other language we expect that this happens quite fast.

By the way, did you know we already have some :ref:`drivers`. If your instrument is not listed, let us know!


Why Python?
-----------

Python is an interpreted, general-purpose high-level programming language. It combines a clear syntax, an excelent documentation and a large and comprehensive standard library. It is an awesome glue language that allows you to call already existing code in other languages. Finally, it is available in many platforms and is free.


Isn't Python slow?
------------------

Python is not slow. But even if it was, in instrumentation software the communication with the instrument is (by far) the rate limiting step. Sending a serial command that modifies the instrument function and receiving a response can easily take a few miliseconds and frequently much longer. While this might be fast in human terms, is an eternity for a computer. For this reason rapid prototyping, good coding practices and maintainability are more important for an instrumentation toolkit than speed.


But I do a lot of mathematical operations!
------------------------------------------

Slow operations such as numerical calculations are done using libraries such as NumPy and SciPy. This puts Python in the same line as Matlab and similar languages. 


How do I start?
---------------

The :ref:`tutorial` is a good place.


I want to help. What can I do?
------------------------------

Please send comments and bug reports allowing us to make the code and documentation better to the `issue tracker in GitHub`_

If you want to contribute with code, the drivers are a good place to start. If you have a programmed a new driver o improved an existing one, let us know.

If you have been using Lantz for a while, you can also write or clarify documentation helping people to use the toolkit. 

The user interface also can use some help. We aim to provide widgets for common instrumentation scenarios. 

Finally, talk to us if you have an idea that can be added to the core. We aim to keep the core small, robust and easy to maintain. However, patterns that appear recurrently when we work on drivers are factored out to the core after proven right.

Take a look at the :ref:`contributing` section for more information.


Where does the name comes from?
-------------------------------

It is a tribute to friend, Maximiliano Lantz. He was passionate scientist, teacher and science popularizer. We dreamt many times about having an instrumentation software simple to be used for teaching but powerful to be used for research. I hope that this toolkit fulfills these goals.


.. _`issue tracker in GitHub`: https://github.com/hgrecco/lantz/issues
