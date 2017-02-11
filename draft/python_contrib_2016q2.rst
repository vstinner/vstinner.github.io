++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2016 Q1
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-02-09 17:00
:tags: cpython
:category: python
:slug: contrib-cpython-2016q1
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2016 Q2
(april, may, june)::

    hg log -r 'date("2016-04-01"):date("2016-06-30")' --no-merges -u Stinner

Statistics: 52 non-merge commits + 22 merge commits (total: 74 commits).

Previous report: `My contributions to CPython during 2016 Q1
<{filename}/python_contrib_2016q1.rst>`_.


Enhancements
============

subprocess now emits a ResourceWarning warning. Issue #26741:
subprocess.Popen destructor now emits a ResourceWarning warning if the child
process is still running.


asyncio: fix ResourceWarning related to subprocesses. Issue #26741: asyncio:
BaseSubprocessTransport._process_exited() now copies the return code from the
child watched to the returncode attribute of the Popen object. On Python 3.6,
it is required to avoid a ResourceWarning.

Issue #27416: clarify copy doc. Patch written by R. David Murray.


Security
========

Issue #22636: Avoid using a shell in the ctypes.util module. Replace os.popen()
with subprocess.Popen.  If the "gcc", "cc" or "objdump" command is not
available, the code was supposed to raise an OSError exception. But there was a
bug in the code. The shell code returns the exit code 10 if the required
command is missing, and the code tries to check for the status 10. The problem
is that os.popen() doesn't return the exit code directly, but a status which
should be processed by os.WIFEXITED() and os.WEXITSTATUS(). In practice, the
exception was never raised. The OSError exception was not documented and
ctypes.util.find_library() is expected to return None if the library is not
found.  Based on patch by Victor Stinner.


asyncio
=======

* asyncio: sync overlapped.c with GitHub. On Python 3.3, use aliases:

  - PyMem_RawMalloc = PyMem_Malloc
  - PyMem_RawFree = PyMem_Free

  These aliases are not need in Python 3.5, but this change makes
  synchronization of code base simpler.

* Issue #26509: In asyncio fatal error handlers, don't log
  ConnectionAbortedError which occur on Windows.


Optimization
============

PyMem_Malloc() now uses the fast pymalloc allocator. Issue #26249:
PyMem_Malloc() allocator family now uses the pymalloc allocator rather than
system malloc(). Applications calling PyMem_Malloc() without holding the GIL
can now crash: use ``PYTHONMALLOC=debug`` environment variable to validate the
usage of memory allocators in your application.

Issue #25349, #26249: Fix memleak in formatfloat().

Optimize pickle.load() and pickle.loads(). Issue #27056: Optimize
pickle.load() and pickle.loads(), up to 10% faster to deserialize a lot of
small objects. Optimization found by analyzing performances using Linux perf.


Bugfixes
========

* Issue #26741: POSIX implementation of subprocess.Popen._execute_child() now
  sets the returncode attribute using the child process exit status when exec
  failed.


Changes
=======

* Update fcntl doc: replace IOError with OSError. Issue #26716. IOError is a
  deprecated alias to OSError since Python 3.3.

* Update pygettext.py to get ride of imp. Issue #26639: Replace imp with
  importlib in Tools/i18n/pygettext.py. Remove _get_modpkg_path(), replaced
  with importlib.util.find_spec().

* Fix os.urandom() on Solaris 11.3. Issue #26735: Fix os.urandom() on Solaris
  11.3 and newer when reading more than 1,024 bytes: call getrandom() multiple
  times with a limit of 1024 bytes per call.

* configure: fix HAVE_GETRANDOM_SYSCALL check. syscall() function requires
  #include <unistd.h>.

* Issue #26766: Fix _PyBytesWriter_Finish(). Return a bytearray object when
  bytearray is requested and when the small buffer is used.. Fix also
  test_bytes: bytearray%args must return a bytearray type.

* Avoid fcntl() if possible in set_inheritable(). Issue #26770:
  set_inheritable() avoids calling fcntl() twice if the FD_CLOEXEC is already
  set/cleared. This change only impacts platforms using the fcntl()
  implementation of set_inheritable() (not Linux nor Windows).

* Fix test_asyncio.test_timeout_disable(). Issue #26777: Fix random failing of
  the test on the "AMD64 FreeBSD 9.x 3.5" buildbot::

    File ".../Lib/test/test_asyncio/test_tasks.py", line 2398, in go
      self.assertTrue(0.09 < dt < 0.11, dt)
    AssertionError: False is not true : 0.11902812402695417

  Replace "< 0.11" with "< 0.15".

* Don't define _PyMem_PymallocEnabled() if pymalloc is disabled. Isse #26516.

* Backport test_gdb fix for s390x buildbots

* Cleanup import.c:

  - Replace PyUnicode_RPartition() with PyUnicode_FindChar() and
    PyUnicode_Substring() to avoid the creation of a temporary tuple.
  - Use PyUnicode_FromFormat() to build a string and avoid the single_dot ('.')
    singleton

  Thanks Serhiy Storchaka for your review.

* regrtest now uses subprocesses when the -j1 command line option
  is used: each test file runs in a fresh child process. Before, the -j1 option
  was ignored. Tools/buildbot/test.bat script now uses -j1 by default to run
  each test file in fresh child process.

* regrtest: display test result (passed, failed, ...) after each test
  completion. in multiprocessing mode: always display the result. sequential
  mode: only display the result if the test did not pass


Contributions
=============

* [sync] asyncio: allow None as wait timeout. Fix GH#325: Allow to pass None as a
  timeout value to disable timeout logic. Change written by Andrew Svetlov and
  merged by Guido van Rossum.

* Issue #26647: Cleanup opcode. Simplify code to build opcode.opname. Patch
  written by Demur Rumed.

* Issue #26647: Cleanup modulefinder. Use directly dis.opmap[name] rather than
  dis.opname.index(name). Patch written by Demur Rumed.

* Issue #26647: Fix typo in test_grammar. Patch written by Demur Rumed.

* Fix shutil.get_terminal_size() error handling. Issue #26801: Fix error
  handling in shutil.get_terminal_size(), catch AttributeError instead of
  NameError. Patch written by Emanuel Barry. test_shutil: skip the functional
  test using "stty size" command if os.get_terminal_size() is missing.

* Optimize ``func(*tuple)`` function call. Issue #26802: Optimize function
  calls only using unpacking like ``func(*tuple)`` (no other positional
  argument, no keyword): avoid copying the tuple. Patch written by Joe Jevnik.

* setup.py: add missing libm dependency. Issue #21668: Link audioop, _datetime,
  _ctypes_test modules to libm, except on Mac OS X. Patch written by Chi Hsuan
  Yen.

* python-gdb.py: get C types at runtime. Issue #26799: Fix python-gdb.py: don't
  get once C types when the Python code is loaded, but get C types on demand.
  The C types can change if python-gdb.py is loaded before the Python
  executable. Patch written by Thomas Ilsche.

* Fix os.set_inheritable() on Android. Issue #27057: Fix os.set_inheritable()
  on Android, ioctl() is blocked by SELinux and fails with EACCESS. The
  function now falls back to fcntl(). Patch written by Michał Bednarski.

* os.urandom() doesn't block on Linux anymore. Issue #26839: On Linux,
  os.urandom() now calls getrandom() with GRND_NONBLOCK to fall back on reading
  /dev/urandom if the urandom entropy pool is not initialized yet. Patch
  written by Colm Buckley.

  Followed-by (my change): Fix os.urandom() using getrandom() on Linux. Issue
  #27278: Fix os.urandom() implementation using getrandom() on Linux.  Truncate
  size to INT_MAX and loop until we collected enough random bytes, instead of
  casting a directly Py_ssize_t to int.


