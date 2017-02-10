++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2015 Q4
++++++++++++++++++++++++++++++++++++++++++

:date: 2016-03-01 15:00
:tags: cpython
:category: python
:slug: contrib-cpython-2015q4
:authors: Victor Stinner
:summary: My contributions to CPython during 2015 Q4

My contributions to CPython during 2015 Q4 (october, november, december).

As usual, I pushed changes of various contributors and helped them to polish
their change.

I fighted against a recursion error, a regression introduced by my recent work
on the Python test suite.

I focused on optimizing the bytes type during this quarter. It started with the
issue #24870 opened by INADA Naoki who works on PyMySQL: decoding bytes
using the surrogateescape error handler was the bottleneck of this benchmark.
For me, it was an opportunity for a new attempt to implement a fast "bytes
writer API".

I pushed my first change related to `FAT Python
<http://faster-cpython.readthedocs.org/fat_python.html>`_! Fix parser and AST:
fill lineno and col_offset of "arg" node when compiling AST from Python
objects.

Previous report: `My contributions to CPython during 2015 Q3
<{filename}/python_contrib_2015q3.rst>`_.



Recursion error
===============

The bug: issue #25274
---------------------

During the previous quarter, I refactored Lib/test/regrtest.py huge file (1,600
lines) into a new Lib/test/libregrtest/ library (8 files). The problem is that
test_sys started to crash with "Fatal Python error: Cannot recover from stack
overflow" on test_recursionlimit_recovery(). The regression was introduced by a
change on regrtest which indirectly added one more Python frame in the code
executing test_sys.

CPython has a limit on the depth of a call stack: ``sys.getrecursionlimit()``,
1000 by default. The limit is a weak protection against overflow of the C
stack. Weak because it only counts Python frames, intermediate C functions may
allocate a lot of memory on the stack.

When we reach the limit, an "overflow" flag is set, but we still allow up to
limit+50 frames, because handling a RecursionError may need a few more frames.
The overflow flag is cleared when the stack level goes below a "low-water
mark".

After the regrtest change, test_recursionlimit_recovery() was called at stack
level 36. Before, it was called at level 35. The test triggers a RecursionError.
The problem is that we never goes again below the low-water mark, so the
overflow flag is never cleared.

The fix
-------

Another problem is that the function used to compute the "low-level mark" was
not monotonic::

    if limit > 100:
        low_water_mark = limit - 50
    else:
        low_water_mark = 3 * limit // 4

The gap occurs near a limit of 100 frames:

* limit = 99 => low_level_mark = 74
* limit = 100 => low_level_mark = 75
* limit = 101 => low_level_mark = 51

The formula was replaced with::

    if limit > 200:
        low_water_mark = limit - 50
    else:
        low_water_mark = 3 * limit // 4

The fix (`change eb0c76442cee
<https://hg.python.org/cpython/rev/eb0c76442cee>`_) modified the
``sys.setrecursionlimit()`` function to raise a ``RecursionError`` exception if
the new limit is too low depending on the *current* stack depth.


Optimizations
=============

As usual for performance, Serhiy Storchaka was very helpful on reviews, to run
independant benchmarks, etc.

Optimizations on the ``bytes`` type, ASCII, Latin1 and UTF-8 codecs:

* Issue #25318: Add _PyBytesWriter API. Add a new private API to optimize
  Unicode encoders. It uses a small buffer of 512 bytes allocated on the stack
  and supports configurable overallocation.
* Use _PyBytesWriter API for UCS1 (ASCII and Latin1) and UTF-8 encoders. Enable
  overallocation for the UTF-8 encoder with error handlers.
* unicode_encode_ucs1(): initialize collend to collstart+1 to not check the
  current character twice, we already know that it is not ASCII.
* Issue #25267: The UTF-8 encoder is now up to 75 times as fast for error
  handlers: ``ignore``, ``replace``, ``surrogateescape``, ``surrogatepass``.
  Patch co-written with Serhiy Storchaka.
* Issue #25301: The UTF-8 decoder is now up to 15 times as fast for error
  handlers: ``ignore``, ``replace`` and ``surrogateescape``.
* Issue #25318: Optimize backslashreplace and xmlcharrefreplace error handlers
  in UTF-8 encoder. Optimize also backslashreplace error handler for ASCII and
  Latin1 encoders.
* Issue #25349: Optimize bytes % args using the new private _PyBytesWriter API
* Optimize error handlers of ASCII and Latin1 encoders when the replacement
  string is pure ASCII: use _PyBytesWriter_WriteBytes(), don't check individual
  character.
* Issue #25349: Optimize bytes % int. Formatting is between 30% and 50% faster
  on a microbenchmark.
* Issue #25357: Add an optional newline paramer to binascii.b2a_base64().
  base64.b64encode() uses it to avoid a memory copy.
* Issue #25353: Optimize unicode escape and raw unicode escape encoders: use
  the new _PyBytesWriter API.
* Rewrite PyBytes_FromFormatV() using _PyBytesWriter API
* Issue #25399: Optimize bytearray % args. Most formatting operations are now
  between 2.5 and 5 times faster.
* Issue #25401: Optimize bytes.fromhex() and bytearray.fromhex(): they are now
  between 2x and 3.5x faster.


Changes
=======

* Issue #25003: On Solaris 11.3 or newer, os.urandom() now uses the getrandom()
  function instead of the getentropy() function. The getentropy() function is
  blocking to generate very good quality entropy, os.urandom() doesn't need
  such high-quality entropy.
* Issue #22806: Add ``python -m test --list-tests`` command to list tests.
* Issue #25670: Remove duplicate getattr() in ast.NodeTransformer
* Issue #25557: Refactor _PyDict_LoadGlobal(). Don't fallback to
  PyDict_GetItemWithError() if the hash is unknown: compute the hash instead.
  Add also comments to explain the _PyDict_LoadGlobal() optimization.
* Issue #25868: Try to make test_eintr.test_sigwaitinfo() more reliable
  especially on slow buildbots


Changes specific to Python 2.7
==============================

* Closes #25742: locale.setlocale() now accepts a Unicode string for its second
  parameter.


Bugfixes
========

* Fix regrtest --coverage on Windows
* Fix pytime on OpenBSD
* More fixes for test_eintr on FreeBSD
* Close #25373: Fix regrtest --slow with interrupted test
* Issue #25555: Fix parser and AST: fill lineno and col_offset of "arg" node
  when compiling AST from Python objects. First contribution related
  to FAT Python ;-)
* Issue #25696: Fix installation of Python on UNIX with make -j9.
