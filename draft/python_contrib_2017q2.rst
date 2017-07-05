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
    248

    # Master branch only
    $ git log --after=2017-03-31 --before=2017-06-30 --reverse --author=Stinner origin/master|grep '^commit '|wc -l
    88

Statistics: **88** commits in the master branch, a **total of 248 commits**:
most (but not all) of the remaining 160 commits are cherry-picked backports to
2.7, 3.5 and 3.6 branches.

Note: The total number of commits is wrong, it includes up to 10 commits which
are pending Pull Requests (commits only in my "haypo" repository), not merged
upstream yet.

XXX try to count again after removing local branches.

I didn't use ``--no-merges`` since we don't use merge anymore, but ``git
cherry-pick -x`` to *backport* fixes. Before GitHub, we used **forwardport**
and Mercurial merges.

Previous report: `My contributions to CPython during 2017 Q1
<{filename}/python_contrib_2017q1.rst>`_.

Mentoring
=========

* Stéphane Wirtel
* Louie Lu

3.6 regression
==============

* bpo-30524: Fix _PyStack_UnpackDict(). I forgot to backport this major bugfix,
  causing tricky bugs. To prevent regressions, I wrote unit tests for FASTCALL
  (bpo-30524).

struct.Struct.format type
=========================

bpo-21071: struct.Struct.format type is now str.

Issue opened in March 2014.

[Python-Dev] `Issue #21071: change struct.Struct.format type from bytes to str
<https://mail.python.org/pipermail/python-dev/2017-March/147688.html>`_ (March
2017).  Followed by `Serhiy Storchaka email
<https://mail.python.org/pipermail/python-dev/2017-June/148360.html>`_ (June 2017).

Backport incompatible change pushed at June 23, 2017.

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

bpo-30273: update distutils.sysconfig for venv's created from Python.

compiled out-of-tree (builddir != srcdir). (see also bpo-15366)


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

signal
------

Change written by **Nathaniel J. Smith**.

bpo-30038: fix race condition in signal delivery + wakeup fd (#1082) (#2075)

Before, it was possible to get the following sequence of
events (especially on Windows, where the C-level signal handler for
SIGINT is run in a separate thread):

- SIGINT arrives
- trip_signal is called
- trip_signal writes to the wakeup fd
- the main thread wakes up from select()-or-equivalent
- the main thread checks for pending signals, but doesn't see any
- the main thread drains the wakeup fd
- the main thread goes back to sleep
- trip_signal sets is_tripped=1 and calls Py_AddPendingCall to notify
  the main thread the it should run the Python-level signal handler
- the main thread doesn't notice because it's asleep

This has been causing repeated failures in the Trio test suite:
  https://github.com/python-trio/trio/issues/119
(cherry picked from commit 4ae01496971624c75080431806ed1c08e00f22c7)

Misc
----

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

FreeBSD core dump
-----------------

bpo-30764: test_subprocess uses SuppressCrashReport. bpo-30764, bpo-29335:
test_child_terminated_in_stopped_state() of test_subprocess now uses
support.SuppressCrashReport() to prevent the creation of a core dump on
FreeBSD.

For an unknown reason, the bug only occurs on Koobs' buildbot, not on my VM,
nor bapt's machine.

regrtest
========

* regrtest: always show before/after values of modified environment.
* bpo-30263: regrtest: log system load and the number of CPUs.
  --verbose now also imply --header.
* [2.7] bpo-30283: Backport test_regrtest from master to 2.7
* bpo-27103: regrtest disables -W if -R is used. Workaround for a regrtest bug.
* bpo-30284: Fix regrtest for out of tree build. Use a build/ directory in the
  build directory, not in the source directory, since the source directory may
  be read-only and must not be modified. Fallback on the source directory if
  the build directory is not available (missing "abs_builddir" sysconfig
  variable).
* Synchronize libregrtest from master to 3.6
* [3.5] bpo-30383: Backport regrtest and test_regrtest enhancements from master to 3.5 (#2279)
* 2.7 and 3.5: bpo-30383: Add NEWS entry for backported regrtest (#2438)

regrtest bisect
===============

* bpo-30540: regrtest: add --matchfile option.
* bpo-30523: Add --list-cases options to regrtest.
  Co-Authored-By: **Louie Lu**.
* bpo-29512: Add test.bisect, bisect failing tests.

Add a new "python3 -m test.bisect" tool to bisect failing tests. It can be used
to find which test method(s) leak references, leak files, etc.

Security
========

expat 2.2
---------

See `CVE-2016-0718: expat 2.2, bug #537
<http://python-security.readthedocs.io/vuln/cve-2016-0718_expat_2.2_bug_537.html>`_.

2.2::

    bpo-29591: Upgrade Modules/expat to libexpat 2.2 (#2164)

    * bpo-29591: Upgrade Modules/expat to libexpat 2.2

    * bpo-29591: Restore Python changes on expat

    * bpo-29591: Remove expat config of unsupported platforms

    Remove the configuration (Modules/expat/*config.h) of unsupported
    platforms:

    * Amiga
    * MacOS Classic on PPC32
    * Open Watcom

    * bpo-29591: Remove useless XML_HAS_SET_HASH_SALT

    The XML_HAS_SET_HASH_SALT define of Modules/expat/expat.h became
    useless since our local expat copy was upgrade to expat 2.1 (it's now
    expat 2.2.0).

Fixed in master, 3.6, 3.5, 2.7. Pending PR for 3.4 and 3.3: XXX.

expat 2.2.1
-----------

See `CVE-2017-9233: Expat 2.2.1
<http://python-security.readthedocs.io/vuln/cve-2017-9233_expat_2.2.1.html>`_

bpo-30694: Upgrade expat copy from 2.2.0 to 2.2.1 to get fixes
of multiple security vulnerabilities including: CVE-2017-9233 (External
entity infinite loop DoS), CVE-2016-9063 (Integer overflow, re-fix),
CVE-2016-0718 (Fix regression bugs from 2.2.0's fix to CVE-2016-0718)
and CVE-2012-0876 (Counter hash flooding with SipHash).
Note: the CVE-2016-5300 (Use os-specific entropy sources like getrandom)
doesn't impact Python, since Python already gets entropy from the OS to set
the expat secret using ``XML_SetHashSalt()``.

Fixed in master, 3.6, 3.5, 2.7. Pending PR for 3.4 and 3.3: XXX.

urllib splithost() vulnerability
--------------------------------

See `bpo-30500: urllib connects to a wrong host
<http://python-security.readthedocs.io/vuln/bpo-30500_urllib_connects_to_a_wrong_host.html>`_
vulnerability.

bpo-30500: Fix urllib.parse.splithost() to correctly parse fragments. For
example, ``splithost('//127.0.0.1#@evil.com/')`` now correctly returns the
``127.0.0.1`` host, instead of treating ``@evil.com`` as the host in an
authentification (``login@host``).

Fix applied to master, 3.6, 3.5 and 2.7. Pending PR for 3.4 and 3.3: XXX.

Travis CI
---------

Pending PR adding Travis CI and AppVeyor to 3.4 and 3.3 branches.


Buildbots
=========

Warnings:

* The @reap_threads decorator and the threading_cleanup() function of
  test.support now log a warning if they fail to clenaup threads. The log may
  help to debug such other warning seen on the AMD64 FreeBSD CURRENT Non-Debug
  3.x buildbot: "Warning -- threading._dangling was modified by test_logging".
* bpo-30764: regrtest: add --fail-env-changed option.
* threading_cleanup() failure marks test as ENV_CHANGED. If threading_cleanup()
  fails to cleanup threads, set a a new support.environment_altered flag to
  true, flag uses by save_env which is used by regrtest to check if a test
  altered the environment. At the end, the test file fails with ENV_CHANGED
  instead of SUCCESS, to report that it altered the environment.

Many fixes required backports to 2.7, 3.5 and 3.6 branches.

Fixes
-----

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
* bpo-30329: Catch Windows error 10022 on shutdown(). Catch the Windows socket
  WSAEINVAL error (code 10022) in imaplib and poplib on shutdown(SHUT_RDWR): An
  invalid operation was attempted. This error occurs sometimes on SSL
  connections.
* bpo-30357: test_thread now uses threading_cleanup(). test_thread: setUp() now
  uses support.threading_setup() and support.threading_cleanup() to wait until
  threads complete to avoid random side effects on following tests.
  Co-Authored-By: **Grzegorz Grzywacz**.
* bpo-30339: test_multiprocessing_main_handling timeout.
  test_multiprocessing_main_handling: increase the test_source timeout from 10
  seconds to 60 seconds, since the test fails randomly on busy buildbots.
  Sadly, this change wasn't enough to fix buildbots.
* bpo-30387: Fix warning in test_threading. test_is_alive_after_fork() now
  joins directly the thread to avoid the following warning added by bpo-30357:
  "Warning -- threading_cleanup() failed to cleanup 0 threads after 2 sec
  (count: 0, dangling: 21)". Use also a different exit code to catch generic
  exit code 1.
* bpo-30649: test_os tolerates 50 ms delta for utime. On Windows, tolerate a
  delta of 50 ms instead of 20 ms in test_utime_current() and
  test_utime_current_old() of test_os. On other platforms, reduce the delta
  from 20 ms to 10 ms. Revert utime delta in test_os: PPC64 Fedora 3.x buildbot
  requires at least a delta of 14 ms: revert the utime delta to 20 ms.
* bpo-30595: Increase test_queue_feeder_donot_stop_onexc() timeout.
  _test_multiprocessing.test_queue_feeder_donot_stop_onexc() now uses a timeout
  of 1 second on Queue.get(), instead of 0.1 second, for slow buildbots.
* bpo-30764: test_subprocess uses SuppressCrashReport. bpo-30764, bpo-29335:
  test_child_terminated_in_stopped_state() of test_subprocess now uses
  support.SuppressCrashReport() to prevent the creation of a core dump on
  FreeBSD.
* bpo-30280: TestBaseSelectorEventLoop of
  test.test_asyncio.test_selector_events now correctly closes the event loop:
  cleanup its executor to not leak threads: don't override the close() method
  of the event loop, only override the_close_self_pipe() method. asyncio base
  TestCase now uses threading_setup() and threading_cleanup() of test.support
  to cleanup threads.
* bpo-30812: Fix test_warnings, restore _showwarnmsg. bpo-26568, bpo-30812: Fix
  test_showwarnmsg_missing(): restore the attribute after removing it.

Python 2.7
==========

* Update gitignore from master.
* gitignore: add rules for the PC/ directory
* bpo-30258: regrtest handles child process crash
* Fix "make tags" command.
* Add Appveyor: a Windows CI for GitHub
* bpo-30258: Fix handling of child error in regrtest. Don't stop the
  worker thread if a child failed.
* bpo-30342: Fix sysconfig.is_python_build() on VS9.0. Fix
  sysconfig.is_python_build() if Python is built with Visual Studio 2008 (VS
  9.0).
* bpo-30764: support.SuppressCrashReport backported to 2.7, "ported" to Windows.
  Add Windows support to test.support.SuppressCrashReport: call SetErrorMode()
  and CrtSetReportMode(). _testcapi: add CrtSetReportMode() and
  CrtSetReportFile() functions and CRT_xxx and CRTDBG_xxx constants needed by
  SuppressCrashReport.
* bpo-30705: Fix test_regrtest.test_crashed(). Add test.support._crash_python()
  which triggers a crash but uses test.support.SuppressCrashReport() to prevent
  a crash report from popping up. Modify
  test_child_terminated_in_stopped_state() of test_subprocess and
  test_crashed() of test_regrtest to use _crash_python().

Backports
---------

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

Backport old fixes
------------------

* [2.7] bpo-15526: test_startfile changes the cwd. Try to fix test_startfile's
  inability to clean up after itself in time. Patch by Jeremy Kloth.
  Fix the following support.rmtree() error while trying to remove the temporary
  working directory used by Python tests:
  "WindowsError: [Error 32] The process cannot access the file because it is
  being used by another process: ...".
  Original commit written in September 2012!
* [2.7] bpo-6393: Fix locale.getprerredencoding() on macOS. Python crashes on OSX
  when ``$LANG`` is set to some (but not all) invalid values due to an invalid
  result from nl_langinfo(). Fix written in September 2009!
* bpo-11790: Fix sporadic failures in
  test_multiprocessing.WithProcessesTestCondition.
  Fixed written in April 2011. This backported commit was tricky to identify!
* bpo-8799, fix test_threading: Reduce timing sensitivity of condition test by
  explicitly.  delaying the main thread so that it doesn't race ahead of the
  workers.  Fix written in Nov 2013.

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
* bpo-30054: Expose tracemalloc C API: make PyTraceMalloc_Track() and
  PyTraceMalloc_Untrack() functions public. numpy is now able to use
  tracemalloc since numpy 1.13 (XXX check version XXX link to PR).

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
* bpo-30418: Popen.communicate() always ignore EINVAL. On Windows,
  subprocess.Popen.communicate() now also ignore EINVAL on stdin.write() if the
  child process is still running but closed the pipe.

Refleaks
========

* bpo-30598: _PySys_EndInit() now duplicates warnoptions. Fix a reference leak
  in subinterpreters, like test_callbacks_leak() of test_atexit. warnoptions is
  a list used to pass options from the command line to the sys module
  constructor. Before this change, the list was shared by multiple interpreter
  which is not the expected behaviour. Each interpreter should have their own
  independent mutable world. This change duplicates the list in each
  interpreter. So each interpreter owns its own list, so each interpreter can
  clear its own list.
* bpo-30601: Fix a refleak in WindowsConsoleIO. Fix a reference leak in
  _io._WindowsConsoleIO: PyUnicode_FSDecoder() always initialize decodedname
  when it succeed and it doesn't clear input decodedname object.
* bpo-30599: Fix test_threaded_import reference leak. Mock
  os.register_at_fork() when importing the random module, since this function
  doesn't allow to unregister callbacks and so leaked memory.
* 2.7: _tkinter: Fix refleak in getint(). PyNumber_Int() creates a new reference:
  need to decrement result reference counter.
* bpo-30635: Fix refleak in test_c_locale_coercion. When checking for reference
  leaks, test_c_locale_coercion is run multiple times and so
  _LocaleCoercionTargetsTestCase.setUpClass() is called multiple times.
  setUpClass() appends new value at each call, so it looks like a reference
  leak. Moving the setup from setUpClass() to setUpModule() avoids this,
  eliminating the false alarm.
* bpo-30602: Fix refleak in os.spawnve(). When os.spawnve() fails while
  handling arguments, free correctly argvlist: pass lastarg+1 rather than
  lastarg to free_string_array() to also free the first item.
* bpo-30602: Fix refleak in os.spawnv(). When os.spawnv() fails while handling
  arguments, free correctly argvlist: pass lastarg+1 rather than lastarg to
  free_string_array() to also free the first item.
* Fix ref cycles in TestCase.assertRaises(). bpo-23890:
  unittest.TestCase.assertRaises() now manually breaks a reference cycle to not
  keep objects alive longer than expected.
* Python 2.7: bpo-30675: Fix refleak hunting in regrtest. regrtest now warms up
  caches: create explicitly all internal singletons which are created on demand
  to prevent false positives when checking for reference leaks.
* _winconsoleio: Fix memory leak. Fix memory leak when _winconsoleio tries to
  open a non-console file: free the name buffer.
* bpo-30813: Fix unittest when hunting refleaks. bpo-11798, bpo-16662,
  bpo-16935, bpo-30813: Skip
  test_discover_with_module_that_raises_SkipTest_on_import() and
  test_discover_with_init_module_that_raises_SkipTest_on_import() of
  test_unittest when hunting reference leaks using regrtest.

Fix for Python 3.5::

    bpo-30675: Fix multiprocessing code in regrtest (#2220)

    * Rewrite code to pass slaveargs from the master process to worker
      processes: reuse the same code of the Python master branch
    * Move code to initialize tests in a new setup_tests() function,
      similar change was done in the master branch
    * In a worker process, call setup_tests() with the namespace built
      from slaveargs to initialize correctly tests

    Before this change, warm_caches() was not called in worker processes
    because the setup was done before rebuilding the namespace from
    slaveargs. As a consequence, the huntrleaks feature was unstable. For
    example, test_zipfile reported randomly false positive on reference
    leaks.
* bpo-30704, bpo-30604: Fix memleak in code_dealloc(): Free also
  co_extra->ce_extras, not only co_extra. XXX Serhiy rewrote the structure in
  master to use a single memory block, implemented my idea.

False positives
---------------

bpo-30776: reduce regrtest -R false positives (#2422)

* Change the regrtest --huntrleaks checker to decide if a test file
  leaks or not. Require that each run leaks at least 1 reference.
* Warmup runs are now completely ignored: ignored in the checker test
  and not used anymore to compute the sum.
* Add an unit test for a reference leak.

Example of reference differences previously considered a failure
(leak) and now considered as success (success, no leak)::

    [3, 0, 0]
    [0, 1, 0]
    [8, -8, 1]

bpo-30776: regrtest: reduce memleak false positive.

Only report a leak if each run leaks at least one memory block.


Contributions
=============

* bpo-9850: Deprecate the macpath module. Co-Authored-By: **Chi Hsuan Yen**.
* bpo-30595: Fix multiprocessing.Queue.get(timeout).
  multiprocessing.Queue.get() with a timeout now polls its reader in
  non-blocking mode if it succeeded to aquire the lock but the acquire took
  longer than the timeout. Co-Authored-By: **Grzegorz Grzywacz**.

Test fixes
==========

* bpo-29887: test_normalization handles PermissionError
* bpo-30257: _bsddb: Fix newDBObject(). Don't set cursorSetReturnsNone to
  DEFAULT_CURSOR_SET_RETURNS_NONE anymore if self->myenvobj is set.
  Fix a GCC warning on the strange indentation.
* bpo-30231: Remove skipped test_imaplib tests. The public cyrus.andrew.cmu.edu
  IMAP server (port 993) doesn't accept TLS connection using our self-signed
  x509 certificate. Remove the two tests which are already skipped. Write a new
  test_certfile_arg_warn() unit test for the certfile deprecation warning.
