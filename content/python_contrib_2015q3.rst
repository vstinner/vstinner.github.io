++++++++++++++++++++++++++++++++++++++
My contributions to CPython in 2015 Q3
++++++++++++++++++++++++++++++++++++++

:date: 2016-02-17 01:00
:tags: cpython
:category: python
:slug: contrib-cpython-2015q3
:authors: Victor Stinner
:summary: My contributions to CPython in 2015 Q3

My contributions to CPython in 2015 Q3 (july, august, september)::

    hg log --no-merge -u Stinner -r 'date("2015-07-01"):date("2015-09-30")'

Python 3.5.0 was released at 2015-09-13.

As usual, I pushed changes of various contributors and helped them to polish
their change.

I found a bug in FreeBSD kernel! Issue #25122. fix will be released in FreeBSD 10.3

Most complex bugs:

* FreeBSD bug
* sys recursion limit: Issue #25274 (fixed during 2015 Q4)
* timestamp rounding

Major changes:

* Polish the implementation of the PEP 475 (retry syscall on EINTR)
* Rework the PyTime API: round to nearest with ties going away from zero
  (ROUND_HALF_UP), fix bugs on FreeBSD and Windows (support again year after
  2038). datetime must support this equality for any timestamp:

   (datetime(1970,1,1) + timedelta(seconds=t)) == datetime.utcfromtimestamp(t)

* Enhancement on the test suite (regrtest): add function tests to test_regrtest

Enhancements:

* type_call() now detect bugs in type new and init: Call
_Py_CheckFunctionResult() to check for bugs in type constructors (tp_new).
 Add assertions to ensure an exception was raised if tp_init failed or that no
 exception was raised if tp_init succeed.

Optimizations:

* Issue #25227: Optimize ASCII and latin1 encoders with the ``surrogateescape``
  error handler: the encoders are now up to 3 times as fast.

Changes:

* Work on the What's New in Python 3.5 document, to document my changes
  (PEP 475, socket timeout, os.urandom)
* Work on asyncio: fix ResourceWarning, fix on Windows
* Issue #23517: fromtimestamp() and utcfromtimestamp() methods of
  datetime.datetime now round microseconds to nearest with ties going away from
  zero (ROUND_HALF_UP), as Python 2 and Python older than 3.3, instead of
  rounding towards -Infinity (ROUND_FLOOR).
* test_time: rewrite PyTime API rounding tests
* Issue #24707: Remove assertion in monotonic clock. Don't check anymore at
  runtime that the monotonic clock doesn't go backward.  Yes, it happens. It
  occurs sometimes each month on a Debian buildbot slave running in a VM.
* Rewrite eintr_tester.py to avoid os.fork()
* Issue #25220: Create Lib/test/libregrtest/
* Issue #25220: Add functional tests to test_regrtest
* Issue #25220: Add test for --wait in test_regrtest
* Issue #25220: Split the huge main() function of libregrtest.main into a class
  with attributes and methods.
* Issue #25220: Enhance regrtest --coverage
* Issue #25220: Enhance regrtest -jN. Running the Python test suite with -jN now:

  - Display the duration of tests which took longer than 30 seconds
  - Display the tests currently running since at least 30 seconds
  - Display the tests we are waiting for when the test suite is interrupted

* Issue #25220, libregrtest: Call setup_python(ns) in the slaves. Slaves (child
  processes running tests for regrtest -jN) now inherit --memlimit/-M,
  --threshold/-t and --nowindows/-n options.

Changes specific to Python 2.7:

* python-gdb.py: enhance py-bt command
* Issue #23375: Fix test_py3kwarn for modules implemented in C

Bug fixes:

* Closes #23247: Fix a crash in the StreamWriter.reset() of CJK codecs
* Issue #24732, #23834: Fix sock_accept_impl() on Windows. Regression of the
  PEP 475 (retry syscall on EINTR)
* test_gdb: fix regex to parse the GDB version and fix ResourceWarning on error
* Fix test_warnings: don't modify warnings.filters, to fix random failures.
* Various bugfixes as usual: C implementation of OrderedDict, new namereplace
  error handler, etc.
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
* Issue #25122: Fix test_eintr.test_open() on FreeBSD. Skip test_open() and
  test_os_open(): both tests uses a FIFO and signals, but there is a bug in
  the FreeBSD kernel which blocks the test. Skip the tests until the bug is
  fixed in FreeBSD kernel.
* Issue #25155: Add _PyTime_AsTimevalTime_t() function to support again year
  after 2038.
* Issue #25150: Hide the private _Py_atomic_xxx symbols from the public
  Python.h header to fix a compilation error with OpenMP. PyThreadState_GET()
  becomes an alias to PyThreadState_Get() to avoid ABI incompatibilies.
* Issue #25003: On Solaris 11.3 or newer, os.urandom() now uses the getrandom()
  function instead of the getentropy() function.
