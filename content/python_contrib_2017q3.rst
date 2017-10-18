++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q3
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-10-18 15:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q3
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q3
(july, august, september).

Previous report: `My contributions to CPython during 2017 Q2 (part1)
<{filename}/python_contrib_2017q2_part1.rst>`_.


Statistics
==========

::

    # All branches
    $ git log --after=2017-06-30 --before=2017-10-01 --reverse --branches='*' --author=Stinner|grep '^commit ' -c
    209

    # Master branch only
    $ git log --after=2017-06-30 --before=2017-10-01 --reverse --author=Stinner origin/master|grep '^commit ' -c
    97

Statistics: I pushed **97** commits in the master branch on a **total of 209
commits**, remaining: 112 commits in the other branches (backports, fixes
specific to Python 2.7, security fixes in Python 3.3 and 3.4, etc.)


Security
========

* bpo-30947: Update libexpat from 2.2.1 to 2.2.3. Fix applied to master, 3.6,
  3.5, 3.4, 3.3 and 2.7 branches! Expat 2.2.2 and 2.2.3 fixed multiple security
  vulnerabilities.
  http://python-security.readthedocs.io/vuln/expat_2.2.3.html
* Fix whichmodule() of _pickle: : _PyUnicode_FromId() can return NULL, replace
  Py_INCREF() with Py_XINCREF(). Fix coverity report: CID 1417269.
* bpo-30860: ``_PyMem_Initialize()`` contains code which is never executed.
  Replace the runtime check with a build assertion. Fix Coverity CID 1417587.


Enhancement: socket.close() now ignores ECONNRESET
==================================================

bpo-30319: socket.close() now ignores ECONNRESET. Previously, many network
tests failed randomly with ConnectionResetError on socket.close().

Patching all functions calling socket.close() would require a lot of work, and
it was surprising to get a "connection reset" when closing a socket.

Who cares that the peer closed the connection, since we are already closing
it!?

Note: socket.close() was modified in Python 3.6 to raise OSError on failure
(bpo-26685).


Removal of the macOS job of Travis CI
=====================================

.. image:: {filename}/images/travis-ci.png
   :alt: call_method microbenchmark
   :align: right
   :target: https://travis-ci.org/

While the Linux jobs of Travis CI usually takes 15 minutes, up to 30 minutes in
the worst case, the macOS job of Travis CI regulary took longer than 30
minutes, sometimes longer than 1 hour.

While the macOS job was optional, sometimes it gone mad and prevented a PR to
be merged. Cancelling the job marked Travis CI as failed on a PR, so it was
still not possible to merge the PR, whereas, again, the job is marked as
optional ("Allowed Failure").

Moreover, when the macOS job failed, the failure was not reported on the PR,
since the job was marked as optional. The only way to notify a failure was to
go to Travis CI and wait at least 30 minutes (whereas the Linux jobs already
completed and it was already possible merge a PR...).

I sent a first mail in June: `[python-committers] macOS Travis CI job became
mandatory?
<https://mail.python.org/pipermail/python-committers/2017-June/004661.html>`_

In september, we decided to remove the macOS job during the CPython sprint at
Instagram (see my previous `New C API <{filename}/new_python_c_api.rst>`_
article), to not slowdown our development speed (bpo-31355). I sent another
email to announce the change: `[python-committers] Travis CI: macOS is now
blocking -- remove macOS from Travis CI?
<https://mail.python.org/pipermail/python-committers/2017-September/004824.html>`_.

After the sprint, it was decided to not add again the macOS job, since we have
3 macOS buildbots. It's enough to detect regressions specific to macOS.

After the removal of the macOS end, at the end of september, Travis CI
published an article about the bad performances of their macOS fleet: `Updating
Our macOS Open Source Offering
<https://blog.travis-ci.com/2017-09-22-macos-update>`_. Sadly, the article
confirms that the situation is not going to evolve quickly.


FreeBSD minor() device bug
==========================

bpo-31044: Skip test_posix.test_makedev() on FreeBSD if ``dev_t`` is larger
than 32-bit.

In FreeBSD, at May 23, the dev_t type changed from 32 bits to 64 bits in the
kernel, but the ``minor()`` function wasn't updated. I reported a bug to
FreeBSD: `Bug 221048 - minor() truncates device number to 32 bits, whereas
dev_t type was extended to 64 bits
<https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=221048>`_. The bug was
quickly fixed.


Bugfixes
========

Reference cycles
----------------

* bpo-31234, socket.create_connection(): Fix reference cycle.
* bpo-31247: xmlrpc.server now explicitly breaks reference cycles when using
  sys.exc_info() in code handling exceptions.
* bpo-31238: pydoc ServerThread.stop() now joins itself to wait until
  DocServer.serve_until_quit() completes and then explicitly sets its docserver
  attribute to None to break a reference cycle.
* bpo-31249, concurrent.futures: WorkItem.run() used by ThreadPoolExecutor now
  explicitly breaks a reference cycle between an exception object and the
  WorkItem object. ThreadPoolExecutor.shutdown() now also clears its threads
  set.

I also started a discussion on reference cycles because by exceptions:
`[Python-Dev] Evil reference cycles caused Exception.__traceback__
<https://mail.python.org/pipermail/python-dev/2017-September/149586.html>`_.
Sadly, no action was taken since no obvious fix was found.

Other bugfixes
--------------

* bpo-30892: Fix _elementtree module initialization. Handle
  ``getattr(copy, 'deepcopy')`` error in ``_elementtree`` module
  initialization.
* bpo-30891: Fix again importlib ``_find_and_load()``. Call
  ``sys.modules.get()`` in the ``with _ModuleLockManager(name):`` block to
  protect the dictionary key with the module lock and use an atomic get to
  prevent race conditions.
* bpo-31019:  multiprocessing.Process.is_alive() now removes the process from
  the _children set if the process completed. The change prevents leaking
  "dangling" processes.
* bpo-31326, concurrent.futures: ProcessPoolExecutor.shutdown() now explicitly
  closes the call queue. Moreover, shutdown(wait=True) now also joins the call
  queue thread, to prevent leaking a dangling thread.
* bpo-31170: Update libexpat from 2.2.3 to 2.2.4. Fix copying of partial
  characters for UTF-8 input (`libexpat bug 115
  <https://github.com/libexpat/libexpat/issues/115>`_). Later, I also wrote
  non-regression tests for this bug.
* bpo-31499, xml.etree: xmlparser_gc_clear() now sets self.parser to NULL to
  prevent a crash in xmlparser_dealloc() if xmlparser_gc_clear() was called
  previously by the garbage collector, because the parser was part of a
  reference cycle. Fix co-written with **Serhiy Storchaka**.


test.pythoninfo
===============

To understand the "Segfault when readline history is more then 2 * history
size" crash (bpo-29854), I modified test_readline to log libreadline  versions.
I also added readline._READLINE_LIBRARY_VERSION. My colleague **Nir Soffer**
wrote the final readline fix: skip the test on old readline versions.

As a follow-up of this issue, I added a new ``test.pythoninfo`` program to log
many information to debug Python tests (bpo-30871). pythoninfo is now run on
Travis CI, AppVeyor and buildbots.

Example of output::

    $ ./python -m test.pythoninfo
    (...)
    _decimal.__libmpdec_version__: 2.4.2
    expat.EXPAT_VERSION: expat_2.2.4
    gdb_version: GNU gdb (GDB) Fedora 8.0.1-26.fc26
    locale.encoding: UTF-8
    os.cpu_count: 4
    (...)
    time.timezone: -3600
    time.tzname: ('CET', 'CEST')
    tkinter.TCL_VERSION: 8.6
    tkinter.TK_VERSION: 8.6
    tkinter.info_patchlevel: 8.6.6
    zlib.ZLIB_RUNTIME_VERSION: 1.2.11
    zlib.ZLIB_VERSION: 1.2.11


Revert commits if buildbots are broken
======================================

Thanks to my work done last months on the Python test suite, the buildbots are
now very reliable. When a buildbot fails, it becomes very likely that it's a
real regression, and not a random failure caused by a bug in the test itself.

So I proposed a new rule: **revert a change if it breaks builbots**:

    So I would like to set a new rule: if I'm unable to fix buildbots
    failures caused by a recent change quickly (say, in less than 2
    hours), I propose to revert the change.

    It doesn't mean that the commit is bad and must not be merged ever.
    No. It would just mean that we need time to work on fixing the issue,
    and it shouldn't impact other pending changes, to keep a sane master
    branch.

`[python-committers] Revert changes which break too many buildbots
<https://mail.python.org/pipermail/python-committers/2017-June/004588.html>`__.

test_datetime
-------------

The first revert was an enhancement of test_datetime::

    commit 98b6bc3bf72532b784a1c1fa76eaa6026a663e44
    Author: Utkarsh Upadhyay <mail@musicallyut.in>
    Date:   Sun Jul 2 14:46:04 2017 +0200

        bpo-30822: Fix testing of datetime module. (#2530)

        Only C implementation was tested.

Revert test_datetime: `[python-committers] Revert changes which break too many buildbots
<https://mail.python.org/pipermail/python-committers/2017-July/004673.html>`__.

Revert "bpo-30822: Fix testing of datetime module. Revert::

Eval frame
----------

Revert::

    commit 2e0f4db114424a00354eab889ba8f7334a2ab8f0
    Author: Bruno "Polaco" Penteado <polaco@gmail.com>
    Date:   Mon Aug 14 23:14:17 2017 +0100

        bpo-30983: eval frame rename in pep 0523 broke gdb's python extension (#2803)

        pep 0523 renames PyEval_EvalFrameEx to _PyEval_EvalFrameDefault while the gdb python extension only looks for PyEval_EvalFrameEx to understand if it is dealing with a frame.

        Final effect is that attaching gdb to a python3.6 process doesnt resolve python objects. Eg. py-list and py-bt dont work properly.

        This patch fixes that. Tested locally on python3.6

I chose to revert the change because I don't have the bandwidth right now to
investigate why the change broke test_gdb.

I'm surprised that a change affecting python-gdb.py wasn't properly tested
manually using test_gdb.py :-( I understand that Travis CI doesn't have gdb
and/or that the test pass in some cases?

The revert only gives us more time to design the proper solution.

A new fixed commit was pushed 4 days later.


socketserver
============

Email: `[Python-Dev] socketserver ForkingMixin waiting for child processes
<https://mail.python.org/pipermail/python-dev/2017-August/148826.html>`_.

bpo-31151: Add socketserver.ForkingMixIn.server_close() now waits until all
child processes completed to prevent leaking zombie processes.

::

    commit 6966960468327c958b03391f71f24986bd697307
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Fri Aug 18 23:47:54 2017 +0200

        bpo-30830: test_logging uses threading_setup/cleanup (#3137)

        * bpo-30830: test_logging uses threading_setup/cleanup

        Replace @support.reap_threads on some methods with
        support.threading_setup() in setUp() and support.threading_cleanup()
        in tearDown() in BaseTest.

        * bpo-30830: test_logging disables threaded socketserver tests

        Disable tests because of socketserver.ThreadingMixIn leaks threads,
        whereas leaking threads now makes a test to fail on buildbots.

        Disable tests until socketserver is fixed: bpo-31233.

        * Skip also setup_via_listener()

next::

    commit 97d7e65dfed1d42d40d9bc2f630af56240555f02
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Sep 13 01:44:08 2017 -0700

        bpo-30830: logging.config.listen() calls server_close() (#3524)

        The ConfigSocketReceiver.serve_until_stopped() method from
        logging.config.listen() now calls server_close() (of
        socketserver.ThreadingTCPServer) rather than closing manually the
        socket.

        While this change has no effect yet, it will help to prevent dangling
        threads once ThreadingTCPServer.server_close() will join spawned
        threads (bpo-31233).

fix::

    commit b8f4163da30e16c7cd58fe04f4b17e38d53cd57e
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Sep 13 01:47:22 2017 -0700

        bpo-31233: socketserver.ThreadingMixIn.server_close() (#3523)

        socketserver.ThreadingMixIn now keeps a list of non-daemonic threads
        to wait until all these threads complete in server_close().

        Reenable test_logging skipped tests.

        Fix SocketHandlerTest.tearDown(): close the socket handler before
        stopping the server, so the server can join threads.



Tests
=====

* bpo-30822: Exclude ``tzdata`` from ``regrtest --all``. When running the test suite
  using ``--use=all`` / ``-u all``, exclude ``tzdata`` since it makes
  test_datetime too slow (15-20 min on some buildbots) which then times out on
  some buildbots. ``-u tzdata`` must now be enabled explicitly.
* bpo-30188: test_nntplib catch also ssl.SSLEOFError. Catch also
  ssl.SSLEOFError in NetworkedNNTPTests setUpClass().  EOFError was already
  catched. Sadly, test_nntplib still fails *randomly* with EOFError or
  SSLEOFError...
* bpo-31009: Fix support.fd_count() on Windows. Call msvcrt.CrtSetReportMode()
  to not kill the process nor log any error on stderr on os.dup(fd) if the file
  descriptor is invalid.
* bpo-31034: Reliable signal handler for test_asyncio. Don't rely on the
  current SIGHUP signal handler, make sure that it's set to the "default"
  signal handler: SIG_DFL. A colleague reported me that the Python test suite
  hangs on running test_subprocess_send_signal() of test_asyncio. After
  analysing the issue, it seems like the test hangs becaues the RPM package
  builder ignores SIGHUP.
* bpo-31028: Fix test_pydoc when run directly. Fix get_pydoc_link() fix
  ``./python Lib/test/test_pydoc.py``: get the absolute path to __file__ to
  prevent relative directories.
* bpo-31066: Fix test_httpservers.test_last_modified(). Write the temporary
  file on disk and then get its modification time.
* bpo-31173: Rewrite WSTOPSIG test of test_subprocess.

  The current test_child_terminated_in_stopped_state() function test creates a
  child process which calls ptrace(PTRACE_TRACEME, 0, 0) and then crash
  (SIGSEGV). The problem is that calling os.waitpid() in the parent process is
  not enough to close the process: the child process remains alive and so the
  unit test leaks a child process in a strange state. Closing the child process
  requires non-trivial code, maybe platform specific.

  Remove the functional test and replaces it with an unit test which mocks
  os.waitpid() using a new _testcapi.W_STOPCODE() function to test the
  WIFSTOPPED() path.
* bpo-31008: Fix asyncio test_wait_for_handle on Windows.
* bpo-31235: Fix ResourceWarning in test_logging: always close all asyncore
  dispatchers (ignoring errors if any).
* bpo-30121: Add test_subprocess.test_nonexisting_with_pipes(). Test the Popen
  failure when Popen was created with pipes. Create also NONEXISTING_CMD
  variable in test_subprocess.py.
* bpo-31250, test_asyncio: fix EventLoopTestsMixin.tearDown(). Call
  doCleanups() to close the loop after calling executor.shutdown(wait=True):
  see TestCase.set_event_loop() of asyncio.test_utils.
* bpo-31323: Fix reference leak in test_ssl. Store exceptions as string rather
  than object to prevent reference cycles which cause leaking dangling threads.
* test_ssl: Implement timeout in ssl_io_loop(). The timeout parameter was not
  used.
* bpo-31448, test_poplib: Call POP3.close(), don't close close directly the
  sock attribute, to fix a ResourceWarning.
* os.test_utime_current(): tolerate 50 ms delta.
* bpo-31135: ttk: fix LabeledScale and OptionMenu destroy() method. Call the
  parent destroy() method even if the used attribute doesn't exist. The
  LabeledScale.destroy() method now also explicitly clears label and scale
  attributes to help the garbage collector to destroy all widgets.
* bpo-31479: Always reset the signal alarm in tests. Use
  the ``try: ... finally: signal.signal(0)`` pattern to make sure that tests
  don't "leak" a pending fatal signal alarm. Move some signal.alarm() calls
  into the try block.


regrtest
========

::

    bpo-31217: Fix regrtest -R for small integer (#3260)

    Use a pool of integer objects toprevent false alarm when checking for
    memory block leaks. Fill the pool with values in -1000..1000 which
    are the most common (reference, memory block, file descriptor)
    differences.

    Co-Authored-By: Antoine Pitrou <pitrou@free.fr>


Environment altered and dangling threads
========================================

Fix "dangling threads" and "zombie processes" bugs in tests.

env changed
-----------

* buildbot, AppVeyor: run tests with --fail-env-changed. Make tests fail if a
  test altered the environment.
* bpo-30764: Fix regrtest --fail-env-changed --forever. --forever now stops if
  a test changes the environment.
* Travis CI: run coverage test using --fail-env-changed.

test.support and regrtest
-------------------------

* Enhance support.reap_children() now sets environment_altered
  to ``True`` to detect bugs using ``python3 -m test --fail-env-changed``.
* regrtest: count also "env changed" as failures in the test progress.
* bpo-31234: support.threading_cleanup() waits for 1 second before emitting a
  warning if there are threads running in the background. With this change, it
  now emits the warning immediately, to be able to catch bugs more easily.
* bpo-31234: Add test.support.wait_threads_exit(). Use _thread.count() to wait
  until threads exit. The new context manager prevents the "dangling thread"
  warning.
* bpo-31234: Add support.join_thread() helper. join_thread() joins a thread but
  raises an AssertionError if the thread is still alive after timeout seconds.

multiprocessing
---------------

* multiprocessing.Queue.join_thread() now waits until the thread
  completes, even if the thread was started by the same process which
  created the queue.
* bpo-26762: Avoid daemon processes in _test_multiprocessing. test_level() of
  _test_multiprocessing._TestLogging now uses regular processes rather than
  daemon processes to prevent zombi processes (to not "leak" processes).
* bpo-26762: Fix more dangling processes and threads in test_multiprocessing.
  Queue: call close() followed by join_thread(). Process: call join() or
  self.addCleanup(p.join).
* bpo-26762: test_multiprocessing now detects dangling processes and threads
  per test case classes.
* bpo-26762: test_multiprocessing close more queues. Close explicitly queues to
  make sure that we don't leave dangling threads. test_queue_in_process():
  remove unused queue. test_access() joins also the process to fix a random
  warning.
* bpo-26762: _test_multiprocessing now marks the test as ENV_CHANGED on
  dangling process or thread.
* bpo-31069, Fix a warning about dangling processes in test_rapid_restart() of
  _test_multiprocessing: join the process.
* bpo-31234: test_multiprocessing: wait 30 seconds. Give 30 seconds to
  join_process(), instead of 5 or 10 seconds, to wait until the process
  completes.

concurrent.futures
------------------

* bpo-30845: Enhance test_concurrent_futures cleanup. Make sure that tests
  don't leak threads nor processes. Clear explicitly the reference to the
  executor to make it that it's destroyed.
* bpo-31249: test_concurrent_futures checks dangling threads. Add a
  BaseTestCase class to test_concurrent_futures to check for dangling threads
  and processes on all tests, not only tests using ExecutorMixin.
* bpo-31249: Fix test_concurrent_futures dangling thread.
  ProcessPoolShutdownTest.test_del_shutdown() now closes the call queue and
  joins its thread, to prevent leaking a dangling thread.

test_threading and test_thread
------------------------------

* bpo-31234: test_threaded_import: fix test_side_effect_import().
  Don't leak the module into sys.modules. Avoid dangling thread.
* bpo-31234: Enhance test_thread.test_forkinthread():

  * test_thread.test_forkinthread() now waits until the thread completes.
  * Check the status in the test method, not in the thread function
  * Don't ignore RuntimeError anymore: since the commit
    346cbd351ee0dd3ab9cb9f0e4cb625556707877e (bpo-16500,
    os.register_at_fork(), os.fork() cannot fail anymore with
    RuntimeError.
  * Replace 0.01 literal with a new POLL_SLEEP constant
  * test_forkinthread(): test if os.fork() exists rather than testing
    the platform.

* bpo-31234: Try to fix lock_tests warning. Try to fix the "Warning --
  threading_cleanup() failed to cleanup 1 threads" warning in test.lock_tests:
  wait a little bit longer to give time to the threads to complete. Warning
  seen on test_thread and test_importlib.
* bpo-31234: Join threads in test_threading. Call thread.join() to prevent the
  "dangling thread" warning.
* bpo-31234: Join timers in test_threading. Call the .join() method of
  threading.Timer timers to prevent the "threading_cleanup() failed to cleanup
  1 threads" warning.

Other fixes
-----------

* test_urllib2_localnet: clear server variable. Set the server attribute to
  None in cleanup to avoid dangling threads.
* bpo-30818: test_ftplib calls asyncore.close_all(). Always clear asyncore
  socket map using asyncore.close_all(ignore_all=True) in tearDown() method.
* bpo-30845: reap_children() now logs warnings
* bpo-30908: Fix dangling thread in test_os.TestSendfile. tearDown() now clears
  explicitly the self.server variable to make sure that the thread is
  completely cleared when tearDownClass() checks if all threads have been
  cleaned up.
* bpo-31067: test_subprocess now also calls reap_children() in tearDown(), not
  only on setUp().
* bpo-31160: Fix test_builtin for zombie process. PtyTests.run_child() now calls
  os.waitpid() to read the exit status of the child process to avoid creating
  zombie process and leaking processes in the background.
* bpo-31160: Fix test_random for zombie process. TestModule.test_after_fork()
  now calls os.waitpid() to read the exit status of the child process to avoid
  creating a zombie process.
* bpo-31160: test_tempfile: TestRandomNameSequence.test_process_awareness() now
  calls os.waitpid() to avoid leaking a zombie process.
* bpo-31234: fork_wait.py tests now joins threads, to not leak running threads
  in the background.
* bpo-30830: test_logging uses threading_setup/cleanup. Replace
  @support.reap_threads on some methods with support.threading_setup() in
  setUp() and support.threading_cleanup() in tearDown() in BaseTest.
* bpo-31234: test_httpservers joins the server thread.
* bpo-31250, test_asyncio: fix dangling threads. Explicitly call
  shutdown(wait=True) on executors to wait until all threads complete to
  prevent side effects between tests. Fix test_loop_self_reading_exception():
  don't mock loop.close().  Previously, the original close() method was called
  rather than the mock, because how set_event_loop() registered loop.close().
* bpo-31234: Explicitly clear the server attribute in test_ftplib and
  test_poplib to prevent dangling thread. Clear also self.server_thread
  attribute in TestTimeouts.tearDown().
* bpo-31234: Join threads in tests. Call thread.join() on threads to prevent
  the "dangling threads" warning.
* bpo-31234: Join threads in test_hashlib: use thread.join() to wait until the
  parallel hash tasks complete rather than using events. Calling thread.join()
  prevent "dangling thread" warnings.
* bpo-31234: Join threads in test_queue. Call thread.join() to prevent the
  "dangling thread" warning.


Misc
====

* bpo-30866: Add _testcapi.stack_pointer(). I used it to write the "Stack
  consumption" section of a previous report: `My contributions to CPython
  during 2017 Q1 <{filename}/python_contrib_2017q1.rst>`_
* _ssl_: Fix compiler warning. Cast Py_buffer.len (Py_ssize_t, signed) to
  size_t (unsigned) to prevent the "comparison between signed and unsigned
  integer expressions" warning.
* bpo-30486: Make cell_set_contents() symbol private. Don't export the
  ``cell_set_contents()`` symbol in the C API.
