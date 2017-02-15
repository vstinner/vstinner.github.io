++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2016 Q2
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-02-12 18:00
:tags: cpython
:category: python
:slug: contrib-cpython-2016q2
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2016 Q2
(april, may, june)::

    hg log -r 'date("2016-04-01"):date("2016-06-30")' --no-merges -u Stinner

Statistics: 52 non-merge commits + 22 merge commits (total: 74 commits).

Previous report: `My contributions to CPython during 2016 Q1
<{filename}/python_contrib_2016q1.rst>`_.


Start of my work on optimization
================================

During 2016 Q2, I started to spend more time on optimizing CPython.

I experimented a change on CPython: a new FASTCALL calling convention to avoid
the creation of a temporary tuple to pass positional argulments: `issue26814
<http://bugs.python.org/issue26814>`_. Early results were really good: calling
builtin functions became between 20% and 50% faster!

Quickly, my optimization work was blocked by unreliable benchmarks. I spent the
rest of the year 2016 analyzing benchmarks and making benchmarks more stable.


subprocess now emits ResourceWarning
====================================

subprocess.Popen destructor now emits a ResourceWarning warning if the child
process is still running (issue #26741). The warning helps to track and fix
zombi processes. I updated asyncio to prevent a false ResourceWarning (warning
whereas the child process completed): asyncio now copies the child process exit
status to the internal Popen object.

I also fixed the POSIX implementation of subprocess.Popen._execute_child(): it
now sets the returncode attribute from the child process exit status when exec
failed.


Security: fix potential shell injections in ctypes.util
=======================================================

I rewrote methods of the ctypes.util module using ``os.popen()``. I replaced
``os.popen()`` with ``subprocess.Popen`` without shell (issue #22636) to fix a
class of security vulneratiblity, "shell injection" (inject arbitrary shell
commands to take the control of a computer).

The ``os.popen()`` function uses a shell, so there is a risk if the command
line arguments are not properly escaped for shell. Using ``subproces.Popen``
without shell fixes completely the risk.

Note: the ``ctypes`` is generally not considered as "safe", but it doesn't harm
to make it more secure ;-)


Optimization: PyMem_Malloc() now uses pymalloc
==============================================

PyMem_Malloc() now uses the fast Python "pymalloc" memory allocator which is
optimized for small objects with a short lifetime (issue #26249). The change
makes some benchmarks up to 4% faster.

This change was possible thanks to the whole preparation work I did in the 2016
Q1, especially the new GIL check in memory allocator debug hooks and the new
``PYTHONMALLOC=debug`` environment variable enabling these hooks on a Python
compiled in released mode.

I tested lxml, Pillow, cryptography and numpy before pushing the change,
as asked by Marc-Andre Lemburg. All these projects work with the change, except
of numpy. I wrote a fix for numpy: `Use PyMem_RawMalloc on Python 3.4 and newer
<https://github.com/numpy/numpy/pull/7404>`_, merged one month later (my first
contribution to numy!).

The change indirectly helped to identify and fix a memory leak in the
``formatfloat()`` function used to format bytes strings: ``b"%f" % 1.2`` (issue
#25349, #26249).


Optimization
============

Issue #27056: Optimize pickle.load() and pickle.loads(), up to 10% faster to
deserialize a lot of small objects. I found this optimization using Linux perf
on Python compiled with PGO. My change implements manually the optimization if
Python is not compiled with PGO.

Issue #26770: When ``set_inheritable()`` is implemented with ``fcntl()``, don't
call ``fcntl()`` twice if the ``FD_CLOEXEC`` flag is already set to the
requested value. Linux uses ``ioctl()`` and so always only need a single
syscall.


Changes
=======

* Issue #26716: Replace IOError with OSError in fcntl documentation, IOError is
  a deprecated alias to OSError since Python 3.3.

* Issue #26639: Replace the deprecated ``imp`` module with the ``importlib``
  module in ``Tools/i18n/pygettext.py``. Remove ``_get_modpkg_path()``,
  replaced with ``importlib.util.find_spec()``.

* Issue #26735: Fix os.urandom() on Solaris 11.3 and newer when reading more
  than 1024 bytes: call getrandom() multiple times with a limit of 1024 bytes
  per call.

* configure: fix ``HAVE_GETRANDOM_SYSCALL`` check, syscall() function requires
  ``#include <unistd.h>``.

* Issue #26766: Fix _PyBytesWriter_Finish(). Return a bytearray object when
  bytearray is requested and when the small buffer is used. Fix also
  test_bytes: bytearray%args must return a bytearray type.

* Issue #26777: Fix random failure of test_asyncio.test_timeout_disable() on
  the "AMD64 FreeBSD 9.x 3.5" buildbot::

    File ".../Lib/test/test_asyncio/test_tasks.py", line 2398, in go
      self.assertTrue(0.09 < dt < 0.11, dt)
    AssertionError: False is not true : 0.11902812402695417

  Replace ``< 0.11`` with ``< 0.15``.

* Backport test_gdb fix for s390x buildbots to Python 3.5.

* Cleanup import.c: replace ``PyUnicode_RPartition()`` with
  ``PyUnicode_FindChar()`` and ``PyUnicode_Substring()`` to avoid the creation
  of a temporary tuple. Use ``PyUnicode_FromFormat()`` to build a string and
  avoid the single_dot ('.') singleton.

* regrtest now uses subprocesses when the ``-j1`` command line option is used:
  each test file runs in a fresh child process. Before, the -j1 option was
  ignored. ``Tools/buildbot/test.bat`` script now uses -j1 by default to run
  each test file in fresh child process.

* regrtest: display test result (passed, failed, ...) after each test
  completion. In multiprocessing mode: always display the result. In sequential
  mode: only display the result if the test did not pass

* Issue #27278: Fix ``os.urandom()`` implementation using ``getrandom()`` on
  Linux. Truncate size to ``INT_MAX`` and loop until we collected enough random
  bytes, instead of casting a directly ``Py_ssize_t`` to ``int``.


Contributions
=============

I also pushed a few changes written by other contributors.

Issue #26839: ``os.urandom()`` doesn't block on Linux anymore. On Linux,
``os.urandom()`` now calls getrandom() with ``GRND_NONBLOCK`` to fall back on
reading ``/dev/urandom`` if the urandom entropy pool is not initialized yet.
Patch written by **Colm Buckley**. This issue started a huge annoying discussion
around random number generation on the bug tracker and the python-dev mailing
list.  I later wrote the `PEP 524: Make os.urandom() blocking on Linux
<https://www.python.org/dev/peps/pep-0524/>`_ to fix the issue!

Other changes:

* Issue #26647: Cleanup opcode: simplify code to build ``opcode.opname``. Patch
  written by **Demur Rumed**.

* Issue #26647: Cleanup modulefinder: use ``dis.opmap[name]`` rather than
  ``dis.opname.index(name)``. Patch written by **Demur Rumed**.

* Issue #26801: Fix error handling in ``shutil.get_terminal_size()``: catch
  AttributeError instead of NameError. Skip the functional test of test_shutil
  using the ``stty size`` command if the ``os.get_terminal_size()`` function is
  missing. Patch written by **Emanuel Barry**.

* Issue #26802: Optimize function calls only using unpacking like
  ``func(*tuple)`` (no other positional argument, no keyword argument): avoid
  copying the tuple. Patch written by **Joe Jevnik**.

* Issue #21668: Add missing libm dependency in setup.py: link audioop,
  _datetime, _ctypes_test modules to libm, except on Mac OS X. Patch written by
  **Chi Hsuan Yen**.

* Issue #26799: Fix python-gdb.py: don't get C types at startup, only on
  demand. The C types can change if python-gdb.py is loaded before loading the
  Python executable in gdb. Patch written by **Thomas Ilsche**.

* Issue #27057: Fix os.set_inheritable() on Android, ioctl() is blocked by
  SELinux and fails with EACCESS. The function now falls back to fcntl(). Patch
  written by **Michał Bednarski**.

* Issue #26647: Fix typo in test_grammar. Patch written by **Demur Rumed**.
