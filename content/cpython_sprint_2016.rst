++++++++++++++++++++++++++++++
CPython sprint, september 2016
++++++++++++++++++++++++++++++

:date: 2017-02-14 18:00
:tags: cpython
:category: python
:slug: cpython-sprint-2016
:authors: Victor Stinner

I was invited at my first CPython sprint in September! Five days, September
5-9, at Instagram office in California, USA. The sprint was sponsored by
Instagram, Microsoft, and the PSF.

**First little game:** Many happy faces, but *Where is Victor?*

.. image:: {static}/images/cpython_sprint_2016_photo.jpg
   :alt: CPython developers at the Facebook sprint
   :target: http://blog.python.org/2016/09/python-core-development-sprint-2016-36.html

IMHO it was the most productive CPython week ever :-) Having Guido van Rossum
in a room helped to get many PEPs accepted. Having a lot of highly skilled
reviewers in the same room helped to get many new features and many PEP
implementations merged much faster than usual.

**Second little game:** try to spot the sprint on the CPython commit statistics of
the last 12 months (Feb, 2016-Feb, 2017) ;-)

.. image:: {static}/images/cpython_sprint_2016_commits.png
   :alt: CPython commits statistics
   :target: https://github.com/python/cpython/graphs/commit-activity

Compact dict
============

Issue #27350: I reviewed and pushed the "compact dict" implementation which
makes Python dictionaries ordered (by insertion order) by default. It reduces
the memory usage of dictionaries betwen 20% and 25%.

The implementation was written by INADA Naoki, based on the PyPy
implementation, with a design by Raymond Hettinger.

FASTCALL
========

"Fast calls": Python 3.6 has a new private C API and a new METH_FASTCALL
calling convention which avoids temporary tuple for positional arguments and
avoids temporary dictionary for keyword arguments. Changes:

* Add a new C calling convention: METH_FASTCALL
* Add _PyArg_ParseStack() function
* Add _PyCFunction_FastCallKeywords() function: issue #27810
* Add _PyObject_FastCallKeywords() function: issue #27830


More efficient CALL_FUNCTION bytecode
=====================================

I reviewed and pushed: "Rework CALL_FUNCTION* opcodes to produce shorter and
more efficient bytecode" (issue #27213).

Patch writen by Demur Rumed, design by Serhiy Storchaka, reviewed by Serhiy
Storchaka and me.


PEP 509: Add a private version to dict
======================================

Guido approved my PEP 509 "Add a new private version to the builtin dict type".

I pushed the implementation.


PEP 524: Make os.urandom() blocking on Linux
============================================

I pushed the implementation of my PEP 524: "Make os.urandom() blocking on
Linux".

Issue #27776: The os.urandom() function does now block on Linux 3.17 and newer
until the system urandom entropy pool is initialized to increase the security.

Read my previous blog post for the painful story behind the PEP:
`PEP 524: os.urandom() now blocks on Linux
<{filename}/pep_524_os_urandom_blocking.rst>`_.


Asynchronous PEP 525 and 530
============================

Guido van Rossum approved two PEPs of Yury Selivanov:

* PEP 525: Asynchronous Generators
* PEP 530: Asynchronous Comprehensions

I reviewed the huge C implementation with Yury on my side :-)


unicode_escape codec optimization
=================================

I reviewed and pushed "Optimize unicode_escape and raw_unicode_escape" (the
isue #16334), patch written by Serhiy Storchaka.


Python 3.6 bugfixes
===================

I happily found many issues including a major one: regular list-comprehension
were completely broken :-)

Another minor issue: SyntaxError didn't reported the correct line number in a
specific case.

Don't worry, Yury fixed both ;-)


Official sprint report
======================

Read also the official report: `Python Core Development Sprint 2016: 3.6 and
beyond!
<http://blog.python.org/2016/09/python-core-development-sprint-2016-36.html>`_.
