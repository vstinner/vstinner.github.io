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
`bpo-37788 <https://bugs.python.org/issue37788>`.


Daemon threads in subinterpreters
=================================

In June 2016, while working on `bpo-36402
<https://bugs.python.org/issue36402>`_ fix, I find a reliable way to trigger a
bug when a subinterpreter is finalized (even with bpo-36402 fix)::

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

XXX


Second fix
==========

Python 3.8::

    commit f781d202a2382731b43bade845a58d28a02e9ea1
    Author: Joannah Nanjekye <33177550+nanjekyejoannah@users.noreply.github.com>
    Date:   Mon Apr 29 04:38:45 2019 -0400

        bpo-36475: Finalize PyEval_AcquireLock() and PyEval_AcquireThread() properly (GH-12667)

        PyEval_AcquireLock() and PyEval_AcquireThread() now
        terminate the current thread if called while the interpreter is
        finalizing, making them consistent with PyEval_RestoreThread(),
        Py_END_ALLOW_THREADS, and PyGILState_Ensure().


Since Python doesn't wait until daemon threads complete at exit, daemon threads
are still running while Python is being "finalized" and are still running while
the process exits. The Python finalization destroys the interpreter, Python
thread states, Python modules, etc.

What happens when a daemon thread tries to access the Python runtime after this
runtime is destroyed?

In the past, Python sometimes crashed in this case.




XXX disallow spawning daemon threads in subinterpreters.

        if self.daemon and not _is_main_interpreter():
            raise RuntimeError("daemon thread are not supported "
                               "in subinterpreters")
