++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q2
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-07-05 15:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q2
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q2
(april, may, june)::

    # All branches
    $ git log --after=2017-03-31 --before=2017-06-30 --reverse --branches='*' --author=Stinner > 2017Q2
    $ grep '^commit ' 2017Q2|wc -l
    242

    # Master branch only
    $ git log --after=2017-03-31 --before=2017-06-30 --reverse --author=Stinner origin/master|grep '^commit '|wc -l
    85

Statistics: **85** commits in the master branch, a **total of 242 commits**:
most (but not all) of the remaining 157 commits are cherry-picked backports to
2.7, 3.5 and 3.6 branches.

I didn't use ``--no-merges`` since we don't use merge anymore, but ``git
cherry-pick -x`` to *backport* fixes. Before GitHub, we used **forwardport**
and Mercurial merges.

Previous report: `My contributions to CPython during 2017 Q1
<{filename}/python_contrib_2017q1.rst>`_.

Optimization
============

bpo-30228: FileIO seek() and tell() set seekable (#1384)

FileIO.seek() and FileIO.tell() method now set the internal seekable
attribute to avoid one syscall on open() (in buffered or text mode).

The seekable property is now also more reliable since its value is
set correctly on memory allocation failure.

make regen-all
==============

I started to look at this issue, because the compilation failed on "AMD64
FreeBSD 9.x 3.x" while trying to rebuild Include/opcode.h. The "make touch"
command used Mercurial.

bpo-23404: make touch becomes make regen-all (#1405)

Don't rebuild generated files based on file modification time
anymore, the action is now explicit. Replace "make touch"
with "make regen-all".

Changes:

* Remove "make touch", Tools/hg/hgtouch.py and .hgtouch
* Add a new "make regen-all" command to rebuild all generated files
* Add subcommands to only generate specific files:

  - regen-ast: Include/Python-ast.h and Python/Python-ast.c
  - regen-grammar: Include/graminit.h and Python/graminit.c
  - regen-importlib: Python/importlib_external.h and Python/importlib.h
  - regen-opcode: Include/opcode.h
  - regen-opcode-targets: Python/opcode_targets.h
  - regen-typeslots: Objects/typeslots.inc

* Rename PYTHON_FOR_GEN to PYTHON_FOR_REGEN
* pgen is now only built by by "make regen-grammar"
* Add $(srcdir)/ prefix to paths to source files to handle correctly
  compilation outside the source directory

Note: $(PYTHON_FOR_REGEN) is no more used nor needed by "make"
default target building Python.

bpo-30273: Update sysconfig (#1464)

The AST_H_DIR variable was removed from Makefile.pre.in by the commit
a5c62a8e9f0de6c4133825a5710984a3cd5e102b (bpo-23404).

AST_H_DIR was hardcoded to "Include", so replace the removed variable
by its content.

Remove also ASDLGEN variable from sysconfig example since this
variable was also removed.


Clang 4.0, dtoa and strict aliasing
===================================

::

    bpo-30104: Use -fno-strict-aliasing on clang (#1221)

    Python/dtoa.c is not compiled correctly with clang 4.0 and
    optimization level -O2 or higher, because of an aliasing issue on
    the double/ULong[2] union.

    LLVM bug report:
    https://bugs.llvm.org//show_bug.cgi?id=31928

    bpo-30104: configure now detects when cc is clang (#1233)

    Detect when the "cc" compiler (and the $CC variable) is the Clang
    compiler. The test is needed to add the -fno-strict-aliasing option
    on FreeBSD where cc is clang.

    bpo-30104: Only use -fno-strict-aliasing on dtoa.c (#1340)

    On clang, only compile dtoa.c with -fno-strict-aliasing, use strict
    aliasing to compile all other C files.

Tricky bugs
===========

* bpo-30225: is_valid_fd() now uses fstat() instead of dup() on macOS
  to return 0 on a pipe when the other side of the pipe is closed. fstat()
  fails with EBADF in that case, whereas dup() succeed.

::

    bpo-30131: test_logging now joins queue threads (#1298)

    QueueListenerTest of test_logging now closes the multiprocessing
    Queue and joins its thread to prevent leaking dangling threads to
    following tests.

    Add also @support.reap_threads to detect earlier if a test leaks
    threads (and try to "cleanup" these threads).

test_eintr
----------

bpo-30320: test_eintr now uses pthread_sigmask() (#1523)

Rewrite sigwaitinfo() and sigtimedwait() unit tests for EINTR using
pthread_sigmask() to fix a race condition between the child and the
parent process.

Remove the pipe which was used as a weak workaround against the race
condition.

sigtimedwait() is now tested with a child process sending a signal
instead of testing the timeout feature which is more unstable
(especially regarding to clock resolution depending on the platform).

regrtest
========

* regrtest: always show before/after values of modified environment.
* bpo-30263: regrtest: log system load and the number of CPUs.
  --verbose now also imply --header.
* [2.7] bpo-30283: Backport test_regrtest from master to 2.7

Buildbots
=========

Warnings:

* The @reap_threads decorator and the threading_cleanup() function of
  test.support now log a warning if they fail to clenaup threads. The log may
  help to debug such other warning seen on the AMD64 FreeBSD CURRENT Non-Debug
  3.x buildbot: "Warning -- threading._dangling was modified by test_logging".

Many fixes required backports to 2.7, 3.5 and 3.6 branches.

I also backported many fixes wrote by other developers, including fixes which
are 3 years old and older, to fix 2.7. Sometimes **finding** the proper fix
takes much more time than the cherry-pick itself which is usually
straighforward (no conflict, nothing to do). I am always impressed that Git is
able to detect that a file was renamed between Python 2 and Python 3, and
applies cleanly the change!

A few examples of backports:

* 2.7: test_distutils: Use EnvironGuard on InstallTestCase, UtilTestCase, and
  BuildExtTestCase  to prevent the following warning:
  ``Warning -- os.environ was modified by test_distutils``
* 2.7: Fix test_multprocessing: Relax test timing (bpo-29861) to avoid sporadic
  failures.

Fixes:

* bpo-29972: Skip tests known to fail on AIX. See `[Python-Dev] Fix or drop AIX
  buildbot?
  <https://mail.python.org/pipermail/python-dev/2017-April/147748.html>`_
  email.
* bpo-29925: Skip test_uuid1_safe() on OS X Tiger
* Fix/optimize test_asyncore.test_quick_connect(). Don't use addCleanup() in
  test_quick_connect() because it keeps the Thread object alive and so
  @reap_threads fails on its timeout of 1 second. "./python -m test -v
  test_asyncore -m test_quick_connect" now takes 185 ms, instead of 11 seconds.
* bpo-30106: Fix test_asyncore.test_quick_connect(). test_quick_connect() runs
  a thread up to 50 seconds, whereas the socket is connected in 0.2 second and
  then the thread is expected to end in less than 3 second. On Linux, the
  thread ends quickly because select() seems to always return quickly. On
  FreeBSD, sometimes select() fails with timeout and so the thread runs much
  longer than expected. Fix the thread timeout to fix a race condition in the
  test.
* bpo-30106: Fix tearDown() of test_asyncore. Call asyncore.close_all() with
  ignore_all=True in the tearDown() method of the test_asyncore base test case.
  It should prevent keeping alive sockets in asyncore.socket_map if close()
  fails with an unexpected error.
* bpo-30108: Restore sys.path in test_site. Add setUpModule() and
  tearDownModule() functions to test_site to save/restore sys.path at the
  module level to prevent warning if the user site directory is created, since
  site.addsitedir() modifies sys.path.
* bpo-30107: don't dump core on expected test_io crash. test_io has two unit
  tests which trigger a deadlock:
  test_daemon_threads_shutdown_stdout_deadlock() and
  test_daemon_threads_shutdown_stderr_deadlock(). These tests call
  Py_FatalError() if the expected bug is triggered which calls abort(). Use
  test.support.SuppressCrashReport to prevent the creation on a core dump, to
  fix the warning: "Warning -- files was modified by test_io (...)
  After:  ['python.core']"
* bpo-30125: Disable faulthandler to run test_SEH() of test_ctypes to prevent
  the following log with a traceback: "Windows fatal exception: access
  violation".
* bpo-30131: Cleanup threads in test_logging using @support.reap_threads.
* bpo-30132: BuildExtTestCase of test_distutils now uses support.temp_cwd() in
  setUp() to remove files created in the current working directory in all
  BuildExtTestCase unit tests.
* bpo-30107: On macOS, test.support.SuppressCrashReport now redirects
  /usr/bin/defaults command stderr into a pipe to not pollute stderr. It fixes
  a test_io.test_daemon_threads_shutdown_stderr_deadlock() failure when the
  CrashReporter domain doesn't exists.
* bpo-30175: Skip client cert tests of test_imaplib. The IMAP server
  cyrus.andrew.cmu.edu doesn't accept our randomly generated client x509
  certificate anymore. test_nntplib fails randomly with EOFError in
  NetworkedNNTPTests.setUpClass(). Catch EOFError to skip tests in that case.
* bpo-30199: AsyncoreEchoServer of test_ssl now calls
  asyncore.close_all(ignore_all=True) to ensure that asyncore.socket_map is
  cleared once the test completes, even if ConnectionHandler was not correctly
  unregistered. Fix the following warning:
  ``Warning -- asyncore.socket_map was modified by test_ssl``.
* Fix test_ftplib warning if IPv6 is not available. DummyFTPServer now calls
  del_channel() on bind() error to prevent the following warning in
  TestIPv6Environment.setUpClass():
  ``Warning -- asyncore.socket_map was modified by test_ftplib``

Python 2.7
==========

* Update gitignore
* bpo-30258: regrtest handles child process crash
* Fix "make tags" command.
* Add Appveyor: a Windows CI for GitHub
* bpo-30258: Fix handling of child error in regrtest. Don't stop the
  worker thread if a child failed.

GitHub
======

SCM, backported to 2.7::

    bpo-27593: Get SCM build info from git instead of hg (#1327)

    Based on commit 5c4b0d063aba0a68c325073f5f312a2c9f40d178 by Ned
    Deily, which is based on original patches by Brett Cannon and Steve
    Dower.

    Remove also the private _Py_svnversion() function and SVNVERSION
    variable.

    Note: Py_SubversionRevision() and Py_SubversionShortBranch() are
    unchanged, they are part of the public API.

::

    bpo-30232: Support Git worktree in configure.ac (#1391)

    Don't test if .git/HEAD file exists, but only if the .git file (or
    directory) exists.

Enhancements
============

* bpo-30265: support.unlink() now only ignores ENOENT and ENOTDIR, instead of
  ignoring all OSError exception.

Bugfixes
========

* test_locale now ignores the DeprecationWarning, don't fail anymore if test
  run with ``python3 -Werror``. Fix also deprecation message: add a space.
* Only define get_zone() and get_gmtoff() if needed, fix warnings on AIX.
* bpo-30125: On Windows, faulthandler.disable() now removes the exception
  handler installed by faulthandler.enable().
* tmtotuple(): use time_t for gmtoff.
* bpo-30264: ExpatParser closes the source on error. ExpatParser.parse() of
  xml.sax.xmlreader now always closes the source: close the file object or the
  urllib object if source is a string (not an open file-like object). The
  change fixes a ResourceWarning on parsing error. Add
  test_parse_close_source() unit test.
* Fix SyntaxWarning on importing test_inspect. Fix the following warning when
  test_inspect.py is compiled to test_inspect.pyc:
  ``SyntaxWarning: tuple parameter unpacking has been removed in 3.x``

Test fixes
==========

* bpo-29887: test_normalization handles PermissionError
* bpo-30257: _bsddb: Fix newDBObject(). Don't set cursorSetReturnsNone to
  DEFAULT_CURSOR_SET_RETURNS_NONE anymore if self->myenvobj is set.
  Fix a GCC warning on the strange indentation.
