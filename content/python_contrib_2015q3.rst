++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2015 Q3
++++++++++++++++++++++++++++++++++++++++++

:date: 2016-02-18 01:00
:tags: cpython
:category: python
:slug: contrib-cpython-2015q3
:authors: Victor Stinner
:summary: My contributions to CPython during 2015 Q3

A few years ago, someone asked me: "Why do you contribute to CPython? Python is
perfect, there are no more bugs, right?". The article list most of my
contributions to CPython during 2015 Q3 (july, august, september). It gives an
idea of which areas of Python are not perfect yet :-)

My contributions to `CPython <https://www.python.org/>`_ during 2015 Q3
(july, august, september)::

    hg log -r 'date("2015-07-01"):date("2015-09-30")' --no-merges -u Stinner

Statistics: 153 non-merge commits + 75 merge commits (total: 228 commits).

The major event in Python of this quarter was the release of Python 3.5.0.

As usual, I helped various contributors to refine their changes and I pushed
their final changes.

Next report: `My contributions to CPython during 2015 Q4
<{filename}/python_contrib_2015q4.rst>`_.


FreeBSD kernel bug
==================

It took me a while to polish the implementation of the `PEP 475 (retry syscall
on EINTR) <https://www.python.org/dev/peps/pep-0475/>`_ especially its unit
test ``test_eintr``. The unit test is supposed to test Python, but as usual,
it also tests indirectly the operating system.

I spent some days investigating a random hang on the FreeBSD buildbots: `issue
#25122 <https://bugs.python.org/issue25122>`_. I quickly found the guilty test
(test_eintr.test_open), but it took me a while to understand that it was a
kernel bug in the FIFO driver. Hopefully at the end, I was able to reproduce
the bug with a short C program in my FreeBSD VM. It is the best way to ask a
fix upstream.

My `FreeBSD bug report #203162
<https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=203162>`_ ("when close(fd)
on a fifo fails with EINTR, the file descriptor is not really closed") was
quickly fixed. The FreeBSD team is reactive!

I like free softwares because it's possible to investigate bugs deep in the
code, and it's usually quick to get a fix.


Timestamp rounding issue
========================

Even if the `issue #23517 <http://bugs.python.org/issue23517>`_ is well defined
and simple to fix, it took me days (weeks?) to understand exactly how
timestamps are supposed to be rounded and agree on the "right" rounding method.
Alexander Belopolsky reminded me the important property::

    (datetime(1970,1,1) + timedelta(seconds=t)) == datetime.utcfromtimestamp(t)

Tim Peters helped me to understand why Python rounds to nearest with ties going
away from zero (ROUND_HALF_UP) in ``round(float)`` and other functions. At
the first look, the rounding method doesn't look natural nor logical::

    >>> round(0.5)
    0
    >>> round(1.5)
    2

See my previous article on the _PyTime API for the long story of rounding
methods between Python 3.2 and Python 3.6: `History of the Python private C API
_PyTime <{filename}/pytime.rst>`_.




Enhancements
============

* type_call() now detect C bugs in type __new__() and __init__() methods.
* Issue #25220: Enhancements of the test runner: add more info when regrtest runs
  tests in parallel, fix some features of regrtest, add functional tests to
  test_regrtest.


Optimizations
=============

* Issue #25227: Optimize ASCII and latin1 encoders with the ``surrogateescape``
  error handler: the encoders are now up to 3 times as fast.


Changes
=======

* Polish the implementation of the PEP 475 (retry syscall on EINTR)
* Work on the "What's New in Python 3.5" document: add my changes
  (PEP 475, socket timeout, os.urandom)
* Work on asyncio: fix ResourceWarning warnings, fixes specific to Windows
* test_time: rewrite rounding tests of the private pytime API
* Issue #24707: Remove an assertion in monotonic clock. Don't check anymore at
  runtime that the monotonic clock doesn't go backward.  Yes, it happens! It
  occurs sometimes each month on a Debian buildbot slave running in a VM.
* test_eintr: replace os.fork() with subprocess (fork+exec) to make the test
  more reliable


Changes specific to Python 2.7
==============================

* Backport python-gdb.py changes: enhance py-bt command
* Issue #23375: Fix test_py3kwarn for modules implemented in C


Bug fixes
=========

* Closes #23247: Fix a crash in the StreamWriter.reset() of CJK codecs
* Issue #24732, #23834: Fix sock_accept_impl() on Windows. Regression of the
  PEP 475 (retry syscall on EINTR)
* test_gdb: fix regex to parse the GDB version and fix ResourceWarning on error
* Fix test_warnings: don't modify warnings.filters to fix random failures of
  the test.
* Issue #24891: Fix a race condition at Python startup if the file descriptor
  of stdin (0), stdout (1) or stderr (2) is closed while Python is creating
  sys.stdin, sys.stdout and sys.stderr objects.
* Issue #24684: socket.socket.getaddrinfo() now calls
  PyUnicode_AsEncodedString() instead of calling the encode() method of the
  host, to handle correctly custom string with an encode() method which doesn't
  return a byte string. The encoder of the IDNA codec is now called directly
  instead of calling the encode() method of the string.
* Issue #25118: Fix a regression of Python 3.5.0 in os.waitpid() on Windows.
  Add an unit test on os.waitpid()
* Issue #25122: Fix test_eintr, kill child process on error
* Issue #25155: Add _PyTime_AsTimevalTime_t() function to fix a regression:
  support again years after 2038.
* Issue #25150: Hide the private _Py_atomic_xxx symbols from the public
  Python.h header to fix a compilation error with OpenMP. PyThreadState_GET()
  becomes an alias to PyThreadState_Get() to avoid ABI incompatibilies.
* Issue #25003: On Solaris 11.3 or newer, os.urandom() now uses the getrandom()
  function instead of the getentropy() function.
