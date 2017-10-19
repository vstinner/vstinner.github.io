+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q3: Part 2 (dangling threads)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2017-10-19 15:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q3-part2
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q3
(july, august, september), Part 2: "Dangling threads".

Previous report: `My contributions to CPython during 2017 Q3: Part 1
<{filename}/python_contrib_2017q3_part1.rst>`_. Next report: `My contributions
to CPython during 2017 Q3: Part 3 (funny bugs)
<{filename}/python_contrib_2017q3_part3.rst>`_.

Summary:

* Bugfixes: Reference cycles
* socketserver leaking threads and processes

  * test_logging random bug
  * Skip failing tests
  * Fix socketserver for processes
  * Fix socketserver for threads
  * Issue not done yet

* Environment altered and dangling threads

  * Environment changed
  * test.support and regrtest enhancements
  * multiprocessing bug fixes
  * concurrent.futures bug fixes
  * test_threading and test_thread
  * Other fixes


Bugfixes: Reference cycles
==========================

While fixing "dangling threads" (see below), I found and fixed 4 reference
cycles which caused memory leaks and objects to live longer than expected. I
was surprised that the bug in the common ``socket.create_connection()``
function was not noticed before! So my work on dangling threads was useful!

The typical pattern of such reference cycle is::

    def func():
        err = None
        try:
            do_something()
        except Exception as exc:
            err = exc
        if err is not None:
            handle_error(exc)
        # the exception is stored in the 'err' variable

    func()
    # surprise, surprise, the exception is still alive at this point!

Or the variant::

    def func():
        try:
            do_something()
        except Exception as exc:
            exc_info = sys.exc_info()
            handle_error(exc_info)
        # the exception is stored in the 'exc_info' variable

    func()
    # surprise, surprise, the exception is still alive at this point!

It's not easy to spot the bug, the bug is subtle. An exception object in Python
3 has a ``__traceback__`` attribute which contains frames. If a frame stores
the exception in a variable, like ``err`` in the first example, or ``exc_info``
in the second example, a cycle exists between the exception and frames. In this
case, the exception, the traceback, the frames, **and all variables of all
frames are kept alive** by the reference cycle, **until the cycle is break by
the garbage collector**.

The problem is that the garbage collector is only called infrequently, so the
cycle may stay alive for a long time.

Sometimes, the reference cycle is even more subtle than the simple examples
above.

Fixed reference cycles:

* `bpo-31234 <https://bugs.python.org/issue31234>`__,
  ``socket.create_connection()``: Fix reference cycle.
* `bpo-31247 <https://bugs.python.org/issue31247>`__: ``xmlrpc.server`` now explicitly breaks reference cycles when using
  ``sys.exc_info()`` in code handling exceptions.
* `bpo-31249 <https://bugs.python.org/issue31249>`__, ``concurrent.futures``:
  ``WorkItem.run()`` used by ThreadPoolExecutor now explicitly breaks a
  reference cycle between an exception object and the ``WorkItem`` object.
  ``ThreadPoolExecutor.shutdown()`` now also clears its threads set.
* `bpo-31238 <https://bugs.python.org/issue31238>`__: ``pydoc``:
  ``ServerThread.stop()`` now joins itself to wait until
  ``DocServer.serve_until_quit()`` completes and then explicitly sets its
  docserver attribute to None to break a reference cycle. This change was made
  to fix ``test_doc``.
* `bpo-31323 <https://bugs.python.org/issue31323>`__: Fix reference leak in
  test_ssl. Store exceptions as string rather than object to prevent reference
  cycles which cause leaking dangling threads.

I also started a discussion on reference cycles caused by exceptions:
`[Python-Dev] Evil reference cycles caused Exception.__traceback__
<https://mail.python.org/pipermail/python-dev/2017-September/149586.html>`_.
Sadly, no action was taken, no obvious solution was found.

I found the ``socket.create_connection()`` reference cycle because of an
unrelated change in test.support::

    bpo-29639: change test.support.HOST to "localhost"

Read `my message <https://bugs.python.org/issue29639#msg302087>`_ on bpo-29639
for the full story. Extract:

    Modifying support.HOST to "localhost" triggered a reference cycle!?

socketserver leaking threads and processes
==========================================

test_logging random bug
-----------------------

This story starts at July, 3, with test_logging failing randomly on FreeBSD,
`bpo-30830 <https://bugs.python.org/issue30830>`__::

    test_output (test.test_logging.HTTPHandlerTest) ... ok
    Warning -- threading_cleanup() failed to cleanup -1 threads after 3 sec (count: 0, dangling: 1)

I failed to reproduce the bug on my FreeBSD VM, nor on Linux. The bug only
occurred on one specific FreeBSD buildbot. I even got access to the buildbot...
and I still failed to reproduce the bug! I tried to run test_logging multiple
times in parallel, increase the system load, etc. I felt disappointed. I used
my ``system_load.py`` script which spawns Python processes running ``while 1:
pass`` to stress the CPU.

After one month, I succeeded to reproduce the bug by running two commands in
parallel.

Command 1 to trigger the bug::

    ./python -m test -v test_logging \
        --fail-env-changed \
        --forever \
        -m test.test_logging.DatagramHandlerTest.test_output \
        -m test.test_logging.ConfigDictTest.test_listen_config_10_ok \
        -m test.test_logging.SocketHandlerTest.test_output

Command 2 to stress the system::

    ./python -m test -j4

It seems like the Python test suite is a very good tool to stress a system to
trigger a race condition!

Finally, I was able to identify the bug:

    The problem is that ``socketserver.ThreadingMixIn`` spawns threads without
    waiting for their completion in server_close().

Skip failing tests
------------------

To stabilize the buildbots and to be able to work on other bugs, I decided to
first skip all tests using ``socketserver.ThreadingMixIn`` until this class was
fixed to prevent "dangling threads".

Fix socketserver for processes
------------------------------

While trying to see how to fix ``socketserver.ThreadingMixIn``, I understood
that `bpo-31151 <https://bugs.python.org/issue31151>`__ was a similar bug in
the ``socketserver`` module but for processes::

    test_ForkingUDPServer (test.test_socketserver.SocketServerTest) ... creating server
    (...)
    Warning -- reap_children() reaped child process 18281

My analysis:

    The problem is that ``socketserver.ForkinMixin`` doesn't wait until all
    children completes. It only calls ``os.waitpid()`` in non-blocking module
    (using ``os.WNOHANG``) after each loop iteration. If a child process
    completes after the last call to ``ForkingMixIn.collect_children()``, the
    server leaks zombie processes.

I fixed ``socketserver.ForkingMixIn`` by modifying the ``server_close()``
method to **block** until all child processes complete: `commit
<https://github.com/python/cpython/commit/aa8ec34ad52bb3b274ce91169e1bc4a598655049>`__.

Just after pushing my fix, I understood that my fix changed the
``ForkingMixIn`` behaviour. I wrote an email to ask if it's the good behaviour
or if a change was needed: `[Python-Dev] socketserver ForkingMixin waiting for
child processes
<https://mail.python.org/pipermail/python-dev/2017-August/148826.html>`_.
The answer is that not everybody wants this behaviour. Sadly, I didn't have
time yet to let the user chooses the behaviour.

Fix socketserver for threads
----------------------------

Fixing ``socketserver.ForkinMixin`` was simple because the code already tracked
the (identifier of) child processes and already had code to wait for child
completion.

Fixing ``socketserver.ThreadingMixIn`` (`bpo-31233
<https://bugs.python.org/issue31233>`__) was more complicated since it didn't
keep track of spawned threads.

I chose to keep a list of ``threading.Thread`` objects, but only for
non-daemonic threads. ``socketserver.ThreadingMixIn.server_close()`` now joins
all threads: `commit
<https://github.com/python/cpython/commit/b8f4163da30e16c7cd58fe04f4b17e38d53cd57e>`__.

Issue not done yet
------------------

As I wrote above, the ``socketserver`` still needs to be reworked to let the
user decides if the server must gracefully wait for child completion or not.
Maybe expose also a method to explicitly wait for children, maybe with a
timeout?


Environment altered and dangling threads
========================================

This part kept me busy for the whole quarter. While trying to fix "all bugs", I
looked at two specific "environment changes": "dangling threads" and "zombie
processes". A dangling thread comes from a test spawning a thread but doesn't
proper "clean" the thread.

Leaking threads or processes is a very bad side effect since it is likely to
cause random bugs in following tests.

At the beginning, I expected that only 2 or 3 bugs should be fixed. At the end,
it was closer to 100 bugs. I don't regret, I'm now sure that I made the Python
test suite more reliable, and this work allowed me to catch **and fix** old
reference cycles bugs (see above).

Environment changed
-------------------

To detect bugs, I modified Travis CI jobs, AppVeyor and buildbots to run tests
with ``--fail-env-changed``. With this option, if a test alters the
environment, the full test suite is marked as failed with "ENV_CHANGED".

I also fixed ``python3 -m test --fail-env-changed --forever`` in `bpo-30764
<https://bugs.python.org/issue30764>`__: --forever now stops if a test alters
the environment.

test.support and regrtest enhancements
--------------------------------------

* `bpo-30845 <https://bugs.python.org/issue30845>`__: reap_children() now logs
  warnings.
* ``support.reap_children()`` now sets environment_altered to ``True`` if a
  test leaked a zombie process, to detect bugs using ``python3 -m test
  --fail-env-changed``.
* regrtest: count also "env changed" tests as failed tests in the test
  progress.
* `bpo-31234 <https://bugs.python.org/issue31234>`__:
  ``support.threading_cleanup()`` now emits a warning immediately if there are
  threads running in the background, to be able to catch bugs more easily.
  Previously, the warning was only emitted if the function failed to cleanup
  these threads after 1 second.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Add
  ``test.support.wait_threads_exit()``. Use ``_thread.count()`` to wait until
  threads exit. The new context manager prevents the "dangling thread" warning.
  Add also ``support.join_thread()`` helper: joins a thread but raises an
  AssertionError if the thread is still alive after *timeout* seconds.

multiprocessing bug fixes
-------------------------

The multiprocessing module is very complex. multiprocessing tests are failing
randomly for years, but nobody seems able to fix them. I can only hope that my
following fixes will help to make these tests more reliable.

* multiprocessing.Queue.join_thread() now waits until the thread
  completes, even if the thread was started by the same process which
  created the queue.
* `bpo-26762 <https://bugs.python.org/issue26762>`__: Avoid daemon processes in _test_multiprocessing. test_level() of
  _test_multiprocessing._TestLogging now uses regular processes rather than
  daemon processes to prevent zombi processes (to not "leak" processes).
* `bpo-26762 <https://bugs.python.org/issue26762>`__: Fix more dangling processes and threads in test_multiprocessing.
  Queue: call close() followed by join_thread(). Process: call join() or
  self.addCleanup(p.join).
* `bpo-26762 <https://bugs.python.org/issue26762>`__: test_multiprocessing now detects dangling processes and threads
  per test case classes.
* `bpo-26762 <https://bugs.python.org/issue26762>`__: test_multiprocessing close more queues. Close explicitly queues to
  make sure that we don't leave dangling threads. test_queue_in_process():
  remove unused queue. test_access() joins also the process to fix a random
  warning.
* `bpo-26762 <https://bugs.python.org/issue26762>`__: _test_multiprocessing now marks the test as ENV_CHANGED on
  dangling process or thread.
* `bpo-31069 <https://bugs.python.org/issue31069>`__, Fix a warning about dangling processes in test_rapid_restart() of
  _test_multiprocessing: join the process.
* `bpo-31234 <https://bugs.python.org/issue31234>`__, test_multiprocessing:
  Give 30 seconds to join_process(), instead of 5 or 10 seconds, to wait until
  the process completes.

concurrent.futures bug fixes
----------------------------

* `bpo-30845 <https://bugs.python.org/issue30845>`__: Enhance test_concurrent_futures cleanup. Make sure that tests
  don't leak threads nor processes. Clear explicitly the reference to the
  executor to make sure that it's destroyed.
* `bpo-31249 <https://bugs.python.org/issue31249>`__: test_concurrent_futures checks dangling threads. Add a
  BaseTestCase class to test_concurrent_futures to check for dangling threads
  and processes on all tests, not only tests using ExecutorMixin.
* `bpo-31249 <https://bugs.python.org/issue31249>`__: Fix test_concurrent_futures dangling thread.
  ProcessPoolShutdownTest.test_del_shutdown() now closes the call queue and
  joins its thread, to prevent leaking a dangling thread.

test_threading and test_thread
------------------------------

* `bpo-31234 <https://bugs.python.org/issue31234>`__: test_threaded_import: fix
  test_side_effect_import().  Don't leak the module into sys.modules. Avoid
  also dangling threads.
* `bpo-31234 <https://bugs.python.org/issue31234>`__:
  test_thread.test_forkinthread() now waits until the thread completes.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Try to fix the
  threading_cleanup() warning in test.lock_tests: wait a little bit longer to
  give time to the threads to complete. Warning seen on test_thread and
  test_importlib.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Join threads in test_threading. Call thread.join() to prevent the
  "dangling thread" warning.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Join timers in
  test_threading. Call the .join() method of threading.Timer timers to prevent
  the threading_cleanup() warning.

Other fixes
-----------

* test_urllib2_localnet: clear server variable. Set the server attribute to
  None in cleanup to avoid dangling threads.
* `bpo-30818 <https://bugs.python.org/issue30818>`__: test_ftplib calls asyncore.close_all(). Always clear asyncore
  socket map using asyncore.close_all(ignore_all=True) in tearDown() method.
* `bpo-30908 <https://bugs.python.org/issue30908>`__: Fix dangling thread in test_os.TestSendfile. tearDown() now clears
  explicitly the self.server variable to make sure that the thread is
  completely cleared when tearDownClass() checks if all threads have been
  cleaned up.
* `bpo-31067 <https://bugs.python.org/issue31067>`__: test_subprocess now also calls reap_children() in tearDown(), not
  only on setUp().
* `bpo-31160 <https://bugs.python.org/issue31160>`__: Fix test_builtin for zombie process. PtyTests.run_child() now calls
  os.waitpid() to read the exit status of the child process to avoid creating
  zombie process and leaking processes in the background.
* `bpo-31160 <https://bugs.python.org/issue31160>`__: Fix test_random for zombie process. TestModule.test_after_fork()
  now calls os.waitpid() to read the exit status of the child process to avoid
  creating a zombie process.
* `bpo-31160 <https://bugs.python.org/issue31160>`__: test_tempfile: TestRandomNameSequence.test_process_awareness() now
  calls os.waitpid() to avoid leaking a zombie process.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: fork_wait.py tests now joins threads, to not leak running threads
  in the background.
* `bpo-30830 <https://bugs.python.org/issue30830>`__: test_logging uses threading_setup/cleanup. Replace
  @support.reap_threads on some methods with support.threading_setup() in
  setUp() and support.threading_cleanup() in tearDown() in BaseTest.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: test_httpservers joins the server thread.
* `bpo-31250 <https://bugs.python.org/issue31250>`__, test_asyncio: fix dangling threads. Explicitly call
  shutdown(wait=True) on executors to wait until all threads complete to
  prevent side effects between tests. Fix test_loop_self_reading_exception():
  don't mock loop.close().  Previously, the original close() method was called
  rather than the mock, because how set_event_loop() registered loop.close().
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Explicitly clear the server attribute in test_ftplib and
  test_poplib to prevent dangling thread. Clear also self.server_thread
  attribute in TestTimeouts.tearDown().
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Join threads in tests. Call thread.join() on threads to prevent
  the "dangling threads" warning.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Join threads in test_hashlib: use thread.join() to wait until the
  parallel hash tasks complete rather than using events. Calling thread.join()
  prevent "dangling thread" warnings.
* `bpo-31234 <https://bugs.python.org/issue31234>`__: Join threads in test_queue. Call thread.join() to prevent the
  "dangling thread" warning.

**Next report:** `My contributions to CPython during 2017 Q3: Part 3 (funny
bugs) <{filename}/python_contrib_2017q3_part3.rst>`_.

