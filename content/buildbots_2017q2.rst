+++++++++++++++++++++++++++++++++
Work on Python buildbots, 2017 Q2
+++++++++++++++++++++++++++++++++

:date: 2017-07-13 9:00
:tags: cpython
:category: python
:slug: python-buildbots-2017q2
:authors: Victor Stinner

I spent the last 6 months on working on buildbots: reduce the failure rate,
send email notitication on failure, fix random bugs, detect more bugs using
warnings, backport fixes to older branches, etc. I decided to fix *all*
buildbots issues: fix all warnings and all unstable tests!

The good news is that I made great progress, I fixed most random failures. A
random fail now became the exception rather than the norm. Some issues were not
bugs in tests, but real race conditions in the code. It's always good to fix
unlikely race conditions before users hit them on production!

* Introduction: Python Buildbots
* Orange Is The New Color
* New buildbot-status Mailing List
* Hardware issues

  * The vacuum cleaner
  * The memory stick

* Warnings
* regrtest
* Bug fixes
* Python 2.7
* Buildbot reports to python-dev


Introduction: Python Buildbots
==============================

CPython is running a `Buildbot <https://buildbot.net/>`_ server for continuous
integration, but tests are run as post-commit: see `Python buildbots
<https://www.python.org/dev/buildbot/>`_. CPython is tested by a wide range of
buildbot slaves:

* 6 operating systems:

  * Linux (Debian, Ubuntu, Gentoo, RHEL, SLES)
  * Windows (7, 8, 8.1 and 10)
  * macOS (Tiger, El Capitain, Sierra)
  * FreeBSD (9, 10, CURRENT)
  * AIX
  * OpenIndiana (currently offline)

* 5 CPU architectures:

  * ARMv7
  * x86 (Intel 32 bit)
  * x86-64 aka "AMD64" (Intel 64-bit)
  * PPC64, PPC64LE
  * s390x

* 3 C compilers:

  * GCC
  * Clang (FreeBSD, macOS)
  * Visual Studio (Windows)

There are different kinds of tests:

* Python test suite: the most common check
* Docs: check that the documentation can be build and doesn't contain warnings
* Refleaks: check for reference leaks and memory leaks, run the Python test
  suite with the ``--huntrleaks`` option
* DMG: Build the macOS installer with the
  ``Mac/BuildScript/build-installer.py`` script

Python is tested in different configurations:

* Debug: ``./configure --with-pydebug``, the most common configuration
* Non-debug: release mode, with compiler optimizations
* PGO: Profiled Guided Optimization, ``./configure --enable-optimizations``
* Installed: ``./configure --prefix=XXX && make install``
* Shared library (libpython): ``./configure --enable-shared``

Currently, 4 branches are tested:

* ``master``: called "3.x" on buildbots
* ``3.6``
* ``3.5``
* ``2.7``

There is also ``custom``, a special branch used by core developers for testing
patches.

The buildbot configuration can be found in the `buildmaster-config project
<https://github.com/python/buildmaster-config/>`_ (start with the
``master/master.cfg`` file).

Note: Thanks to the migration to GitHub, Pull Requests are now tested on Linux,
Windows and macOS by Travis CI and AppVeyor. It's the first time in the CPython
development history that we have automated pre-commit tests!


Orange Is The New Color
=======================

A buildbot now becomes orange when tests contain warnings.

My first change was to modify the buildbot configuration to extract warnings
from the raw test output to create a new "warnings" report, to more easily
detect warnings and tests failing randomly (test fail then pass when re-run).

Example of orange build, x86-64 El Capitain 3.x:

.. image:: {static}/images/buildbot_orange.png
   :alt: Buildbot: orange build

Extract of the current ``master/custom/steps.py``::

    class Test(BaseTest):
        # Regular expression used to catch warnings, errors and bugs
        warningPattern = (
            # regrtest saved_test_environment warning:
            # Warning -- files was modified by test_distutils
            # test.support @reap_threads:
            # Warning -- threading_cleanup() failed to cleanup ...
            r"Warning -- ",
            # Py_FatalError() call
            r"Fatal Python error:",
            # PyErr_WriteUnraisable() exception: usually, error in
            # garbage collector or destructor
            r"Exception ignored in:",
            # faulthandler_exc_handler(): Windows exception handler installed with
            # AddVectoredExceptionHandler() by faulthandler.enable()
            r"Windows fatal exception:",
            # Resource warning: unclosed file, socket, etc.
            # NOTE: match the "ResourceWarning" anywhere, not only at the start
            r"ResourceWarning",
            # regrtest: At least one test failed. Log a warning even if the test
            # passed on the second try, to notify that a test is unstable.
            r'Re-running failed tests in verbose mode',
            # Re-running test 'test_multiprocessing_fork' in verbose mode
            r'Re-running test .* in verbose mode',
            # Thread last resort exception handler in t_bootstrap()
            r'Unhandled exception in thread started by ',
            # test_os leaked [6, 6, 6] memory blocks, sum=18,
            r'test_[^ ]+ leaked ',
        )
        # Use ".*" prefix to search the regex anywhere since stdout is mixed
        # with stderr, so warnings are not always written at the start
        # of a line. The log consumer calls warningPattern.match(line)
        warningPattern = r".*(?:%s)" % "|".join(warningPattern)
        warningPattern = re.compile(warningPattern)

        # if tests have warnings, mark the overall build as WARNINGS (orange)
        warnOnWarnings = True


New buildbot-status Mailing List
================================

To check buildbots, previously I had to analyze manually the huge "waterfall"
view of four Python branches: 2.7, 3.5, 3.6 and master ("3.x").

* `Python master ("3.x") <http://buildbot.python.org/all/waterfall?category=3.x.stable&category=3.x.unstable>`_
* `Python 3.6 <http://buildbot.python.org/all/waterfall?category=3.6.stable&category=3.6.unstable>`_
* `Python 3.5 <http://buildbot.python.org/all/waterfall?category=3.5.stable&category=3.5.unstable>`_
* `Python 2.7 <http://buildbot.python.org/all/waterfall?category=2.7.stable&category=2.7.unstable>`_

Example of typical buildbot waterfall:

.. image:: {static}/images/buildbot_waterfall.png
   :alt: Buildbot waterfall
   :target: http://buildbot.python.org/all/waterfall?category=3.x.stable&category=3.x.unstable

The screenshot is obviously truncated since the webpage is giant: I have to
scroll in all directions... It's not convenient to check the status of all
builds, detect random failures, etc.

We also have an IRC bot reporting buildbot failures: when a green (success) or
orange (warning) buildbot becomes red (failure). I wanted to have the same
thing, but by email. Technically, it's trivial to enable email notification,
but I never did it because buildbots were simply too unstable: most failures
were not related to the newly tested changes.

But I decided to fix *all* buildbots issues, so I enabled email notification
(`bpo-30325 <https://bugs.python.org/issue30325>`_). Since May 2017,
buildbots are now sending notifications to a new `buildbot-status mailing list
<https://mail.python.org/mm3/mailman3/lists/buildbot-status.python.org/>`_.

I use the mailing list to check if the failure is known or not: I try to answer
to all failure notification emails. If the failure is known, I copy the link to
the issue. Otherwise, I create a new issue and then copy the link to the new
issue.


Hardware issues
===============

Unit tests versus real life :-) (or "software versus hardware")

The vacuum cleaner
------------------

Fixing buildbot issues can be boring sometimes, so let's start with a funny
bug. At June 25, Nick Coghlan wrote to the `python-buildbots
<https://mail.python.org/mailman/listinfo/python-buildbots>`_ mailing list:

    It looks like the FreeBSD buildbots had an outage a little while ago,
    and the FreeBSD 10 one may need a nudge to get back online (the
    FreeBSD Current one looks like it came back automatically).

The reason is unexpected :-) `Kubilay Kocak, owner of the buildbot, answered
<https://mail.python.org/pipermail/python-buildbots/2017-June/000122.html>`_:

    Vacuum cleaner tripped RCD pulling too much current from the same circuit
    as heater was running on. Buildbot worker host on same circuit.


The memory stick
----------------

I opened at least 50 issues to report random buildbot failures. In the middle
of these issues, you can find `bpo-30371
<http://bugs.python.org/issue30371>`_::

    http://buildbot.python.org/all/builders/AMD64%20Windows7%20SP1%203.x/builds/436/steps/test/logs/stdio

    ======================================================================
    FAIL: test_long_lines (test.test_email.test_email.TestFeedParsers)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\buildbot.python.org\3.x.kloth-win64\build\lib\test\test_email\test_email.py", line 3526, in test_long_lines
        self.assertEqual(m.get_payload(), 'x'*M*N)
    AssertionError: 'xxxx[17103482 chars]xxxxxzxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx[2896464 chars]xxxx' != 'xxxx[17103482 chars]xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx[2896464 chars]xxxx'

    Notice the "z" in "...xxxxxz...".

and::

    New fail, same buildbot:

    ======================================================================
    FAIL: test_long_lines (test.test_email.test_email.TestFeedParsers)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\buildbot.python.org\3.x.kloth-win64\build\lib\test\test_email\test_email.py", line 3534, in test_long_lines
        self.assertEqual(m.items(), [('a', ''), ('b', 'x'*M*N)])
    AssertionError: Lists differ: [('a'[1845894 chars]xxxxxzxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx[18154072 chars]xx')] != [('a'[1845894 chars]xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx[18154072 chars]xx')]

    First differing element 1:
    ('b',[1845882 chars]xxxxxzxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx[18154071 chars]xxx')
    ('b',[1845882 chars]xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx[18154071 chars]xxx')

      [('a', ''),
       ('b',


    Don't click on http://buildbot.python.org/all/builders/AMD64%20Windows7%20SP1%203.x/builds/439/steps/test/logs/stdio
    : the log contains lines of 2 MB which make my Firefox super slow :-)

Jeremy Kloth, owner the buildbot, answered:

    Watch this space, but I'm pretty sure that it is (was) bad memory.

He fixed the issue:

    That's the real problem, I'm not *sure* it's the memory, but it does have
    the symptoms. And that is why my buildbot was down earlier, I was
    attempting to determine the bad stick and replace it.


Warnings
========

To fix test warnings, I enhanced the test suite to report more information when
a warning is emitted and to ease detection of failures.

A major change is the new ``--fail-env-changed`` option I added to regrtest
(bpo-30764): make tests fail if the "environment" is changed. This option is
now used on buildbots, Travis CI and AppVeyor, but only for the *master* branch
yet.

Other changes:

* The @reap_threads decorator and the threading_cleanup() function of
  test.support now log a warning if they fail to clenaup threads. The log may
  help to debug such other warning seen on the AMD64 FreeBSD CURRENT Non-Debug
  3.x buildbot: "Warning -- threading._dangling was modified by test_logging".
* threading_cleanup() failure marks test as ENV_CHANGED. If threading_cleanup()
  fails to cleanup threads, set a a new support.environment_altered flag to
  true, flag uses by save_env which is used by regrtest to check if a test
  altered the environment. At the end, the test file fails with ENV_CHANGED
  instead of SUCCESS, to report that it altered the environment.
* regrtest: always show before/after values of modified environment.

I backported all these changes to the 2.7, 3.5 and 3.6 branches to make sure
that warnings are fixed in all maintained branches.


regrtest
========

As usual, I spent time our specialized test runner, regrtest:

* bpo-30263: regrtest: log system load and the number of CPUs. I tried to find
  a relationship between race conditions and the system load. I failed to
  find any obvious correlation yet, but I still consider that the system load
  is useful.
* bpo-27103: regrtest disables -W if -R (reference hunting) is used. Workaround
  for a regrtest bug.

But the most complex task was to backport *all* regrtest features and
enhancements from master to regrtest of 3.6, 3.5 and then 2.7 branches.

In Python 3.6, I rewrote regrtest.py file to split it into smaller files a in
new Lib/test/libregrtest/ library, so it was painful to backport changes to 3.5
(bpo-30383) which still uses the single regrtest.py file.

In Python 2.7 (bpo-30283), it is even worse. Lib/test/regrtest.py uses the old
``getopt`` module to parse the command line instead of the new ``argparse``
used in 3.5 and newer. But I succeeded to backport all features and
enhancements from master!

Python 2.7, 3.5, 3.6 and master now have almost the same CLI for ``python -m
test``, almost the same features (except of one or two missing feature), and
should provide the same level of information on failures and warnings.

By the way, the new ``test.bisect`` tool is now also available in all these
branches. See my `New Python test.bisect tool
<{filename}/python_test_bisect.rst>`_ article.


Bug fixes
=========

As expected, the longest section here is the list of changes I wrote to fix all
buildbot failures and warnings:

* bpo-29972: Skip tests known to fail on AIX. See `[Python-Dev] Fix or drop AIX
  buildbot?
  <https://mail.python.org/pipermail/python-dev/2017-April/147748.html>`_
  email.
* bpo-29925: Skip test_uuid1_safe() on OS X Tiger
* Fix and optimize test_asyncore.test_quick_connect(). Don't use addCleanup() in
  test_quick_connect() because it keeps the Thread object alive and so
  @reap_threads times out after 1 second. "./python -m test -v
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
  It prevents keeping alive sockets in asyncore.socket_map if close()
  fails with an unexpected error.
* bpo-30108: Restore sys.path in test_site. Add setUpModule() and
  tearDownModule() functions to test_site to save/restore sys.path at the
  module level to prevent warning if the user site directory is created, since
  site.addsitedir() modifies sys.path.
* bpo-30107: test_io doesn't dump a core file on an expected crash anymore.
  test_io has two unit tests which trigger a deadlock:
  test_daemon_threads_shutdown_stdout_deadlock() and
  test_daemon_threads_shutdown_stderr_deadlock(). These tests call
  Py_FatalError() if the expected bug is triggered which calls abort(). Use
  test.support.SuppressCrashReport to prevent the creation on a core dump, to
  fix the warning:
  ``Warning -- files was modified by test_io (...) After: ['python.core']``
* bpo-30125: Disable faulthandler to run test_SEH() of test_ctypes to prevent
  the following log with a traceback:
  ``Windows fatal exception: access violation``
* bpo-30131: test_logging cleans up threads using @support.reap_threads.
* bpo-30132: BuildExtTestCase of test_distutils now uses support.temp_cwd() in
  setUp() to remove files created in the current working directory by
  BuildExtTestCase unit tests.
* bpo-30107: On macOS, test.support.SuppressCrashReport now redirects
  /usr/bin/defaults command stderr into a pipe to not pollute stderr. It fixes
  a test_io.test_daemon_threads_shutdown_stderr_deadlock() failure when the
  CrashReporter domain doesn't exists.
* bpo-30175: Skip client cert tests of test_imaplib. The IMAP server
  cyrus.andrew.cmu.edu doesn't accept our randomly generated client x509
  certificate anymore.
* bpo-30175: test_nntplib fails randomly with EOFError in NetworkedNNTPTests.setUpClass():
  catch EOFError to skip tests in that case.
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
* bpo-30649: On Windows, test_os now tolerates a delta of 50 ms instead of 20
  ms in test_utime_current() and test_utime_current_old(). On other platforms,
  reduce the delta from 20 ms to 10 ms. PPC64 Fedora 3.x buildbot requires at
  least a delta of 14 ms.
* bpo-30595: test_queue_feeder_donot_stop_onexc() of _test_multiprocessing now
  uses a timeout of 1 second on Queue.get(), instead of 0.1 second, for slow
  buildbots.
* bpo-30764, bpo-29335: test_child_terminated_in_stopped_state() of
  test_subprocess now uses support.SuppressCrashReport() to prevent the
  creation of a core dump on FreeBSD.
* bpo-30280: TestBaseSelectorEventLoop of
  test.test_asyncio.test_selector_events now correctly closes the event loop:
  cleanup its executor to not leak threads: don't override the close() method
  of the event loop, only override the_close_self_pipe() method. asyncio base
  TestCase now uses threading_setup() and threading_cleanup() of test.support
  to cleanup threads.
* bpo-26568, bpo-30812: Fix test_showwarnmsg_missing(): restore the attribute
  after removing it.


Python 2.7
==========

I wanted to fix *all* buildbot issues of *all* branches including 2.7, whereas
I didn't touch much the Python 2.7 code base last months (last years???). The
first six months of 2017, I backported dozens of commits from master to 2.7!

For example, I added AppVeyor on 2.7: a Windows CI for GitHub!

On Windows we support multiple versions of Visual Studio. I use Visual Studio
2008, whereas most 2.7 Windows buildbots use Visual Studio 2010 or newer.  I
fixed sysconfig.is_python_build() if Python is built with Visual Studio 2008
(VS 9.0) (bpo-30342).

Other Python 2.7 changes:

* Fix "make tags" command.
* bpo-30764: support.SuppressCrashReport backported to 2.7 and "ported" to
  Windows.  Add Windows support to test.support.SuppressCrashReport: call
  SetErrorMode() and CrtSetReportMode(). _testcapi: add CrtSetReportMode() and
  CrtSetReportFile() functions and CRT_xxx and CRTDBG_xxx constants needed by
  SuppressCrashReport.
* bpo-30705: Fix test_regrtest.test_crashed(). Add test.support._crash_python()
  which triggers a crash but uses test.support.SuppressCrashReport() to prevent
  a crash report from popping up. Modify
  test_child_terminated_in_stopped_state() of test_subprocess and
  test_crashed() of test_regrtest to use _crash_python().

I also backported many fixes wrote by other developers, including old fixes up
to 8 years old!

Usually, **finding** the proper fix takes much more time than the cherry-pick
itself which is usually straighforward (no conflict, nothing to do). I am
always impressed that Git is able to detect that a file was renamed between
Python 2 and Python 3, and applies cleanly the change!

Example of backports from master to 2.7:

* bpo-6393: Fix locale.getprerredencoding() on macOS. Python crashes on OSX
  when ``$LANG`` is set to some (but not all) invalid values due to an invalid
  result from nl_langinfo(). Fix written in **September 2009** (8 years ago)!
* bpo-15526: test_startfile changes the cwd. Try to fix test_startfile's
  inability to clean up after itself in time. Patch by **Jeremy Kloth**.
  Fix the following support.rmtree() error while trying to remove the temporary
  working directory used by Python tests:
  "WindowsError: [Error 32] The process cannot access the file because it is
  being used by another process: ...".
  Original commit written in **September 2012**!
* bpo-11790: Fix sporadic failures in
  test_multiprocessing.WithProcessesTestCondition.
  Fixed written in **April 2011**. This backported commit was tricky to
  identify!
* bpo-8799, fix test_threading: Reduce timing sensitivity of condition test by
  explicitly.  delaying the main thread so that it doesn't race ahead of the
  workers.  Fix written in **Nov 2013**.
* test_distutils: Use EnvironGuard on InstallTestCase, UtilTestCase, and
  BuildExtTestCase  to prevent the following warning:
  ``Warning -- os.environ was modified by test_distutils``
* Fix test_multprocessing: Relax test timing (bpo-29861) to avoid sporadic
  failures.


Buildbot reports to python-dev
==============================

I also wrote 3 reports to the Python-Dev mailing list:

* May 3: `Status of Python buildbots
  <https://mail.python.org/pipermail/python-dev/2017-May/147838.html>`_
* June 8: `Buildbot report, june 2017
  <https://mail.python.org/pipermail/python-dev/2017-June/148271.html>`_
* June 29: `Buildbot report (almost July)
  <https://mail.python.org/pipermail/python-dev/2017-June/148511.html>`_
