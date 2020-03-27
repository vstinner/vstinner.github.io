++++++++++++++++++++++++++++++++++++++++++
Daemon threads and the Python finalization
++++++++++++++++++++++++++++++++++++++++++

:date: 2020-03-26 22:00
:tags: cpython
:category: cpython
:slug: daemon-threads-python-finalization
:authors: Victor Stinner

Daemon threads
==============

Python has a special kind of thread: "daemon" threads. The difference with
regular threads is that Python doesn't wait until daemon threads complete at
exit, whereas it blocks until all regular ("non-daemon") threads complete.

Example::

    import threading, time
    thread = threading.Thread(target=time.sleep, args=(5.0,), daemon=False)
    thread.start()

This Python program spawns a regular thread which sleeps for 5 seconds. Python
takes 5 seconds to exit::

    $ time python3 sleep.py

    real   0m5,047s

If I replace ``daemon=False`` with ``daemon=True`` to spawn a daemon thread
instead, Python exits immediately (57 ms)::

    $ time python3 sleep.py

    real   0m0,057s

Note: Calling explicitly ``Thread.join()`` waits until the thread complete and
it works for daemon threads as well.


Crashes during Python finalization
==================================

There are different projects trying to properly destroy all Python objects at
Python exit. There are different reasons: better track the lifetime of objects,
support multiple interpreters, support to start and stop Python multiple times
when Python is embedded in an application, etc.

Daemon threads is causing troubles since they are still running while Python is
finalizing and even while the process is exiting. What happens when a daemon
thread tries to use a Python object after Python destroyed all runtime states
(interpreter, Python thread state, modules, etc.)?

It works most of the time, but sometimes Python does crash randomly when a
daemon is still running at exit. This problem was known since at least April
2005: `bpo-1193099: Embedded python thread crashes
<https://bugs.python.org/issue1193099>`_.

In January 2008, **Gregory P. Smith** reports:
`bpo-1856: shutdown (exit) can hang or segfault with daemon threads running
<https://bugs.python.org/issue1856#msg60014>`_.

He wrote a short Python program to trigger the bug: spawn 40 daemon threads
which run a loop:

* do some I/O
* sleep randomly between 0 ms and 5 ms

**Adam Olsen** `proposes a solution
<https://bugs.python.org/issue1856#msg60059>`_ (with a patch):

    I think non-main threads should kill themselves off if they grab the
    interpreter lock and the interpreter is tearing down. They're about to get
    killed off anyway, when the process exits.

GIL bug
=======

September 2010, **Antoine Pitrou** found a variant of this bug while stressing
``test_threading``: `bpo-9901: GIL destruction can fail
<https://bugs.python.org/issue9901>`_. ``test_finalize_with_trace()`` fails
with::

    Fatal Python error: pthread_mutex_destroy(gil_mutex) failed

Antoine pushed a fix in Python 3.2::

    commit b0b384b7c0333bf1183cd6f90c0a3f9edaadd6b9
    Author: Antoine Pitrou <solipsis@pitrou.net>
    Date:   Mon Sep 20 20:13:48 2010 +0000

        Issue #9901: Destroying the GIL in Py_Finalize() can fail if some other
        threads are still running.  Instead, reinitialize the GIL on a second
        call to Py_Initialize().

First PyEval_RestoreThread() fix in Python 3.3
==============================================

May 2011, back to `bpo-1856 <https://bugs.python.org/issue1856#msg60014>`__,
**Antoine Pitrou** pushed a fix into Python 3.3::

    commit 0d5e52d3469a310001afe50689f77ddba6d554d1
    Author: Antoine Pitrou <solipsis@pitrou.net>
    Date:   Wed May 4 20:02:30 2011 +0200

        Issue #1856: Avoid crashes and lockups when daemon threads run while the
        interpreter is shutting down; instead, these threads are now killed when
        they try to take the GIL.

Simplified extract of the fix::

    @@ -440,6 +440,12 @@ PyEval_RestoreThread()
             take_gil(tstate);
    +        if (_Py_Finalizing && tstate != _Py_Finalizing) {
    +            drop_gil(tstate);
    +            PyThread_exit_thread();
    +        }

``PyEval_RestoreThread()`` now checks if Python is finalizing (or has been
finalized) using a new ``_Py_Finalizing`` variable which is set by
``Py_Finalize()``. ``PyEval_RestoreThread()`` is called when a threads tries
to acquire the GIL. Example of code releasing the GIL to call ``fchmod()``::

        Py_BEGIN_ALLOW_THREADS
        res = fchmod(fd, mode);
        Py_END_ALLOW_THREADS

The ``Py_BEGIN_ALLOW_THREADS`` macro calls ``PyEval_SaveThread()`` which
releases the GIL, whereas the ``Py_END_ALLOW_THREADS`` macro acquires the GIL.

With Antoine's change, a thread now exits immediately when it attempts to
acquire the GIL.

Changing Python finalization is risky. In June 2014, **Benjamin Peterson**
(Python 2.7 release manager) backports Antoine's change to Python 2.7: fix
included in 2.7.8. Problem, Ceph project `started to crash
<https://tracker.ceph.com/issues/8797>`_. in November 2014, the change is
reverted: see `bpo-21963 discussion <https://bugs.python.org/issue21963>`_.

In 2014, I already wrote:

    Anyway, **daemon threads are evil** :-( Expecting them to exit cleanly
    automatically is not good. Last time I tried to improve code to cleanup
    Python at exit in Python 3.4, I also had a regression (just before the
    release of Python 3.4.0): see the `issue #21788
    <https://bugs.python.org/issue21788>`_.


Race condition in Python finalization
=====================================

In March 2019, I notices that ``test_threading.test_threads_join_2()`` was
killed by SIGABRT on the FreeBSD CURRENT buildbot, `bpo-36402
<https://bugs.python.org/issue36402>`_::

    Fatal Python error: Py_EndInterpreter: not the last thread

It is a race condition: the build is a success since the test passed when
re-run.

I already saw the bug in 2016 (`bpo-27791
<https://bugs.python.org/issue27791>`_, and `bpo-28084
<https://bugs.python.org/issue28084>`_ reported by Christian Heimes) on a
FreeBSD buildbot, but I closed the issue since I only saw it twice in 4 months
and I didn't have access to FreeBSD to attempt to reproduce the crash.

A similar bug, `bpo-36989 <https://bugs.python.org/issue36989>`_, was reported
on AIX in May 2019: ``test_threading.test_daemon_threads_fatal_error()``.

In June 2019, I find a reliable way to reproduce the bug: `add random sleeps
to the test <https://github.com/python/cpython/pull/13889/files>`_. Since it
becomes easy for me to reproduce the issue, I can analyze it more easily. I
identify a race condition in the Python finalization. I also understand that
the bug is not specific to subinterpreters:

    The test shows the bug using subinterpreters (Py_EndInterpreter), but the
    bug also exists in Py_Finalize() which hash the same race condition.

I write a patch for Py_Finalize() to help me to reproduce the bug without
subinterpreters::

    +    if (tstate != interp->tstate_head || tstate->next != NULL) {
    +        Py_FatalError("Py_EndInterpreter: not the last thread");
    +    }

I fix the race condition in ``threading._shutdown()``::

    commit 468e5fec8a2f534f1685d59da3ca4fad425c38dd
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Thu Jun 13 01:30:17 2019 +0200

        bpo-36402: Fix threading._shutdown() race condition (GH-13948)

        Fix a race condition at Python shutdown when waiting for threads.
        Wait until the Python thread state of all non-daemon threads get
        deleted (join all non-daemon threads), rather than just wait until
        Python threads complete.

Note: This change introduced a regression (memory leak) which is not fixed yet:
`bpo-37788 <https://bugs.python.org/issue37788>`_.


Forbid daemon threads in subinterpreters
========================================

In June 2019, while working on `bpo-36402
<https://bugs.python.org/issue36402>`_ fix, I find a reliable way with daemon
threads to trigger a bug when a subinterpreter is finalized (even with
bpo-36402 fix)::

    Fatal Python error: Py_EndInterpreter: not the last thread

I report `bpo-37266 <https://bugs.python.org/issue37266>`_ to propose to forbid
the creation of daemon threads in subinterpreters.

Change::

    commit 066e5b1a917ec2134e8997d2cadd815724314252
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Fri Jun 14 18:55:22 2019 +0200

        bpo-37266: Daemon threads are now denied in subinterpreters (GH-14049)

        In a subinterpreter, spawning a daemon thread now raises an
        exception. Daemon threads were never supported in subinterpreters.
        Previously, the subinterpreter finalization crashed with a Pyton
        fatal error if a daemon thread was still running.

        * Add _thread._is_main_interpreter()
        * threading.Thread.start() now raises RuntimeError if the thread is a
          daemon thread and the method is called from a subinterpreter.
        * The _thread module now uses Argument Clinic for the new function.
        * Use textwrap.dedent() in test_threading.SubinterpThreadingTests

XXX::

        if self.daemon and not _is_main_interpreter():
            raise RuntimeError("daemon thread are not supported "
                               "in subinterpreters")

I commented:

    **Daemon threads must die.** That's a first step towards their death!

**Antoine Pitrou** created `bpo-39812: Avoid daemon threads in
concurrent.futures <https://bugs.python.org/issue39812>`_ as a follow-up.

In February 2020, when rebuilding Fedora Rawhide with Python 3.9, **Miro
Hrončok** of my team notices that my change `broke the python-jep project
<https://bugzilla.redhat.com/show_bug.cgi?id=1792062>`_. I `report the bug
upstream <https://github.com/ninia/jep/issues/229>`_. The fix is to use regular
threads rather than daemon threads (`commit
<https://github.com/ninia/jep/commit/a31d461c6cacc96de68d68320eaa83e19a45d0cc>`__).


Daemon threads strike back
==========================

In March 2019, **Remy Noel** reports that a multithreaded Python application
using 20 daemon threads hangs randomly at exit with Python 3.5:

    The bug happens about once every two weeks on a script that is fired more
    than 10K times a day.

**Eric Snow** investigates.

XXX fix XXX


Second fix
==========

bpo-36475

Python 3.8::

    commit f781d202a2382731b43bade845a58d28a02e9ea1
    Author: Joannah Nanjekye <33177550+nanjekyejoannah@users.noreply.github.com>
    Date:   Mon Apr 29 04:38:45 2019 -0400

        bpo-36475: Finalize PyEval_AcquireLock() and PyEval_AcquireThread() properly (GH-12667)

        PyEval_AcquireLock() and PyEval_AcquireThread() now
        terminate the current thread if called while the interpreter is
        finalizing, making them consistent with PyEval_RestoreThread(),
        Py_END_ALLOW_THREADS, and PyGILState_Ensure().

Third fix
=========

December 2019, I report `bpo-39088 <https://bugs.python.org/issue39088>`_:
test_concurrent_futures crashed with python.core core dump on AMD64 FreeBSD
Shared 3.x.

Sometimes, test_multiprocessing_spawn does crash in PyEval_RestoreThread() on
FreeBSD with a coredump. This issue should be the root cause of bpo-39088:
"test_concurrent_futures crashed with python.core core dump on AMD64 FreeBSD
Shared 3.x", where the second comment is a test_multiprocessing_spawn failure
with "...  After:  ['python.core'] ..."

March 2019, I succeed to reproduce the bug on FreeBSD and debug it in gdb::

    (gdb) frame
    #0  0x00000000003b518c in PyEval_RestoreThread (tstate=0x801f23790) at Python/ceval.c:387
    387         _PyRuntimeState *runtime = tstate->interp->runtime;

    (gdb) p tstate->interp
    $3 = (PyInterpreterState *) 0xdddddddddddddddd

The Python thread state was freed: its memory was filled with ``0xDD`` byte
("dead byte") to detect when freed memory is read.

The problem is that Python already freed the memory of all PyThreadState
structures, whereas PyEval_RestoreThread(tstate) dereferences tstate to get the
_PyRuntimeState structure.

A daemon thread crash in ``PyEval_RestoreThread()``, while the main thread is
exiting the process after ``Py_Finalize()`` has been called.

This bug is a regression caused by my change:
`Add PyInterpreterState.runtime field
<https://github.com/python/cpython/commit/01b1cc12e7c6a3d6a3d27ba7c731687d57aae92a>`_
of `bpo-36710 <https://bugs.python.org/issue36710>`_. I replaced::

    void PyEval_RestoreThread(PyThreadState *tstate) {
        _PyRuntimeState *runtime = &_PyRuntime;
        ...
    }

with::

    void PyEval_RestoreThread(PyThreadState *tstate) {
        _PyRuntimeState *runtime = tstate->interp->runtime;
        ...
    }

I create `bpo-39877 <https://bugs.python.org/issue39877>`_ to investigate this
bug.

I write a patch (add ``sleep(1);`` at ``Py_RunMain()`` exit) and a script
(spawn daemon threads with a random sleep between 0.0 and 1.0 second) to
reproduce the bug on Linux.

Prepare fix 1::

    commit 7b3c252dc7f44d4bdc4c7c82d225ebd09c78f520
    Author: Victor Stinner <vstinner@python.org>
    Date:   Sat Mar 7 00:24:23 2020 +0100

        bpo-39877: _PyRuntimeState.finalizing becomes atomic (GH-18816)

        Convert _PyRuntimeState.finalizing field to an atomic variable:

        * Rename it to _finalizing
        * Change its type to _Py_atomic_address
        * Add _PyRuntimeState_GetFinalizing() and _PyRuntimeState_SetFinalizing()
          functions
        * Remove _Py_CURRENTLY_FINALIZING() function: replace it with testing
          directly _PyRuntimeState_GetFinalizing() value

        Convert _PyRuntimeState_GetThreadState() to static inline function.

Fix 1::

    commit eb4e2ae2b8486e8ee4249218b95d94a9f0cc513e
    Author: Victor Stinner <vstinner@python.org>
    Date:   Sun Mar 8 11:57:45 2020 +0100

        bpo-39877: Fix PyEval_RestoreThread() for daemon threads (GH-18811)

        * exit_thread_if_finalizing() does now access directly _PyRuntime
          variable, rather than using tstate->interp->runtime since tstate
          can be a dangling pointer after Py_Finalize() has been called.
        * exit_thread_if_finalizing() is now called *before* calling
          take_gil(). _PyRuntime.finalizing is an atomic variable,
          we don't need to hold the GIL to access it.
        * Add ensure_tstate_not_null() function to check that tstate is not
          NULL at runtime. Check tstate earlier. take_gil() does not longer
          check if tstate is NULL.

        Cleanup:

        * PyEval_RestoreThread() no longer saves/restores errno: it's already
          done inside take_gil().
        * PyEval_AcquireLock(), PyEval_AcquireThread(),
          PyEval_RestoreThread() and _PyEval_EvalFrameDefault() now check if
          tstate is valid with the new is_tstate_valid() function which uses
          _PyMem_IsPtrFreed().

I comment:

    Ok, it should now be fixed.

While trying to fix bpo-19466, work on PR 18848, I noticed that my commit
eb4e2ae2b8486e8ee4249218b95d94a9f0cc513e introduced a race condition :-(

The problem is that while the main thread is executing Py_FinalizeEx(), daemon
threads can be waiting in take_gil(). Py_FinalizeEx() calls
_PyRuntimeState_SetFinalizing(runtime, tstate). Later, Py_FinalizeEx() executes
arbitrary Python code in _PyImport_Cleanup(tstate) which releases the GIL to
give a chance to other threads to execute: (...)

At this point, one daemon thread manages to get the GIL: take_gil()
completes... even if runtime->finalizing is not NULL. I expected that
exit_thread_if_finalizing() would exit the thread, but
exit_thread_if_finalizing() is now called *after* take_gil().

Prepare::

    commit 3225b9f9739cd4bcca372d0fa939cea1ae5c6402
    Author: Victor Stinner <vstinner@python.org>
    Date:   Mon Mar 9 20:56:57 2020 +0100

        bpo-39877: Remove useless PyEval_InitThreads() calls (GH-18883)

        Py_Initialize() calls PyEval_InitThreads() since Python 3.7. It's no
        longer needed to call it explicitly.

Prepare::

    commit 111e4ee52a1739e7c7221adde2fc364ef4954af2
    Author: Victor Stinner <vstinner@python.org>
    Date:   Mon Mar 9 21:24:14 2020 +0100

        bpo-39877: Py_Initialize() pass tstate to PyEval_InitThreads() (GH-18884)


Prepare::

    commit 85f5a69ae1541271286bb0f0e0303aabf792dd5c
    Author: Victor Stinner <vstinner@python.org>
    Date:   Mon Mar 9 22:12:04 2020 +0100

        bpo-39877: Refactor take_gil() function (GH-18885)

        * Remove ceval parameter of take_gil(): get it from tstate.
        * Move exit_thread_if_finalizing() call inside take_gil(). Replace
          exit_thread_if_finalizing() with tstate_must_exit(): the caller is
          now responsible to call PyThread_exit_thread().
        * Move is_tstate_valid() assertion inside take_gil(). Remove
          is_tstate_valid(): inline code into take_gil().
        * Move gil_created() assertion inside take_gil().

Fix 2::

    commit 9229eeee105f19705f72e553cf066751ac47c7b7
    Author: Victor Stinner <vstinner@python.org>
    Date:   Mon Mar 9 23:10:53 2020 +0100

        bpo-39877: take_gil() checks tstate_must_exit() twice (GH-18890)

        take_gil() now also checks tstate_must_exit() after acquiring
        the GIL: exit the thread if Py_Finalize() has been called.


Funny/not funny, bpo-36818 added a similar bug with commit
396e0a8d9dc65453cb9d53500d0a620602656cfe in June 2019: bpo-37135. I reverted
the change to fix the issue.

Hopefully, it should now be fixed and the rationale for accessing directly
_PyRuntime should now be better documented.

I comment:

    I tested (run multiple times) daemon_threads_exit.py with slow_exit.patch:
    no crash.

    I also tested (run multiple times) stress.py + sleep_at_exit.patch of
    bpo-37135: no crash.

    And I tested  asyncio_gc.py of bpo-19466: no crash neither.

    Python finalization now looks reliable. I'm not sure if it's "more"
    reliable than previously, but at least, I cannot get a crash anymore, even
    after bpo-19466 has been fixed (clear Python thread states of daemon
    threads earlier).

Cleanup::

    commit 175a704abfcb3400aaeb66d4f098d92ca7e30892
    Author: Victor Stinner <vstinner@python.org>
    Date:   Tue Mar 10 00:37:48 2020 +0100

        bpo-39877: PyGILState_Ensure() don't call PyEval_InitThreads() (GH-18891)

        PyGILState_Ensure() doesn't call PyEval_InitThreads() anymore when a
        new Python thread state is created. The GIL is created by
        Py_Initialize() since Python 3.7, it's not needed to call
        PyEval_InitThreads() explicitly.

        Add an assertion to ensure that the GIL is already created.

I comment:

    The initial issue is now fixed. I close the issue.

    take_gil() only checks if the thread must exit once the GIL is acquired.
    Maybe it would be able to exit earlier, but I took the safe approach. If we
    must exit, drop the GIL and then exit. That's basically Python 3.8
    behavior.

But I pushed two more fixes!

While working on https://bugs.python.org/issue39984 I write fix 3::

    commit 29356e03d4f8800b04f799efe7a10e3ce8b16f61
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Mar 18 03:04:33 2020 +0100

        bpo-39877: Fix take_gil() for daemon threads (GH-19054)

        bpo-39877, bpo-39984: If the thread must exit, don't access tstate to
        prevent a potential crash: tstate memory has been freed.

While working on https://bugs.python.org/issue40010 I write fix 4::

    commit a36adfa6bbf5e612a4d4639124502135690899b8
    Author: Victor Stinner <vstinner@python.org>
    Date:   Thu Mar 19 19:48:25 2020 +0100

        bpo-39877: 4th take_gil() fix for daemon threads (GH-19080)

        bpo-39877, bpo-40010: Add a third tstate_must_exit() check in
        take_gil() to prevent using tstate which has been freed.
