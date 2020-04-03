++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Daemon threads and the Python finalization in Python 3.9
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2020-04-02 22:00
:tags: cpython
:category: cpython
:slug: daemon-threads-python-finalization-python39
:authors: Victor Stinner

My previous article `Daemon threads and the Python finalization in Python 3.2 and 3.3
<{filename}/daemon-threads-python-finalization-python32.rst>`_ introduces
issues caused by daemon threads in the Python finalization and past changes to
make them work.

This article is about new issues arisen by the work on isolating
subinterpreters done in Python 3.9.

PyEval_AcquireThread() exits if Python is finalizing
====================================================

In March 2019, **Remy Noel** created `bpo-36469
<https://bugs.python.org/issue36469>`_: a multithreaded Python application
using 20 daemon threads hangs randomly at exit with Python 3.5:

    The bug happens about once every two weeks on a script that is fired more
    than 10K times a day.

**Eric Snow** analyzed the bug and understood that it is related to daemon
threads and Python finalization. He identified that ``PyEval_AcquireLock()``
and ``PyEval_AcquireThread()`` function take the GIL but don't exit the thread
if Python is finalizing.

When Python is finalizing and a daemon thread takes the GIL, Python can hang
randomly.

Eric created `bpo-36475 <https://bugs.python.org/issue36475>`__ to propose to
modify ``PyEval_AcquireLock()`` and ``PyEval_AcquireThread()`` to also exit
the thread in this case. In April 2019, **Joannah Nanjekye** fixed the issue
with `commit f781d202
<https://github.com/python/cpython/commit/f781d202a2382731b43bade845a58d28a02e9ea1>`__::

    bpo-36475: Finalize PyEval_AcquireLock() and PyEval_AcquireThread() properly (GH-12667)

    PyEval_AcquireLock() and PyEval_AcquireThread() now
    terminate the current thread if called while the interpreter is
    finalizing, making them consistent with PyEval_RestoreThread(),
    Py_END_ALLOW_THREADS, and PyGILState_Ensure().

The fix adds ``exit_thread_if_finalizing()`` function which exit the thread if
Python is finalizing. This function is called after each to ``take_gil()``.

The fix is very similar to ``PyEval_RestoreThread()`` fix made in 2013 (`commit
0d5e52d3
<https://github.com/python/cpython/commit/0d5e52d3469a310001afe50689f77ddba6d554d1>`__)
to fix `bpo-1856 <https://bugs.python.org/issue1856#msg60014>`_ (Python crash
involving daemon threads during Python exit).


Third fix
=========

Crash on FreeBSD
----------------

In December 2019, I reported `bpo-39088 <https://bugs.python.org/issue39088>`_:
test_concurrent_futures crashed with ``python.core core`` dump on AMD64 FreeBSD
Shared 3.x. In March 2019, I succeeded to reproduce the bug on FreeBSD and was
able to debug the coredump in gdb::

    (gdb) frame
    #0  0x00000000003b518c in PyEval_RestoreThread (tstate=0x801f23790) at Python/ceval.c:387
    387         _PyRuntimeState *runtime = tstate->interp->runtime;

    (gdb) p tstate->interp
    $3 = (PyInterpreterState *) 0xdddddddddddddddd

The Python thread state (``tstate``) was freed. In debug mode, the "free()"
function of the Python memory allocator fills freed memory with ``0xDD`` byte
pattern ("dead byte") to detect usage of freed memory.

The problem is that Python finalization already freed the memory of all
PyThreadState structures, when ``PyEval_RestoreThread(tstate)`` is called by a
daemon thread and dereferences tstate to get the ``_PyRuntimeState`` structure.

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

Fix PyEval_RestoreThread() for daemon threads
---------------------------------------------

I created `bpo-39877 <https://bugs.python.org/issue39877>`__ to investigate this
bug.

I was able to reproduce the crash on Linux with a script which spawns daemon
threads which sleep between 0.0 and 1.0 second and by adding ``sleep(1);`` at
``Py_RunMain()`` exit.

I wrote a ``PyEval_RestoreThread()`` fix which access to
``_PyRuntimeState.finalizing`` without the GIL.  **Antoine Pitrou** asked me to
convert this variable to an atomic variable to avoid inconsistencies in
parallel accesses. In March 2020, I pushed `commit 7b3c252d
<https://github.com/python/cpython/commit/7b3c252dc7f44d4bdc4c7c82d225ebd09c78f520>`__::

    bpo-39877: _PyRuntimeState.finalizing becomes atomic (GH-18816)

    Convert _PyRuntimeState.finalizing field to an atomic variable:

    * Rename it to _finalizing
    * Change its type to _Py_atomic_address
    * Add _PyRuntimeState_GetFinalizing() and _PyRuntimeState_SetFinalizing()
      functions
    * Remove _Py_CURRENTLY_FINALIZING() function: replace it with testing
      directly _PyRuntimeState_GetFinalizing() value

    Convert _PyRuntimeState_GetThreadState() to static inline function.

The day after, I pushed `commit eb4e2ae2
<https://github.com/python/cpython/commit/eb4e2ae2b8486e8ee4249218b95d94a9f0cc513e>`__::

    bpo-39877: Fix PyEval_RestoreThread() for daemon threads (GH-18811)

    * exit_thread_if_finalizing() does now access directly _PyRuntime
      variable, rather than using tstate->interp->runtime since tstate
      can be a dangling pointer after Py_Finalize() has been called.
    * exit_thread_if_finalizing() is now called *before* calling
      take_gil(). _PyRuntime.finalizing is an atomic variable,
      we don't need to hold the GIL to access it.

``exit_thread_if_finalizing()`` is now called **before** ``take_gil()`` to
ensure that ``take_gil()`` cannot be called with an invalid Python thread state
(``tstate``).

I commented:

    Ok, it should now be fixed.


Clear Python thread states earlier: failed attempt in 2013
==========================================================

In 2013, I opened `bpo-19466 <https://bugs.python.org/issue19466>`_ to clear
earlier the Python thread state of threads during Python finalization. My
intent was to get ``ResourceWarning`` warnings in daemon threads as well.
In November 2013, I pushed `commit 45956b9a
<https://github.com/python/cpython/commit/45956b9a33af634a2919ade64c1dd223ab2d5235>`__::

    Close #19466: Clear the frames of daemon threads earlier during the Python
    shutdown to call objects destructors. So "unclosed file" resource warnings
    are now corretly emitted for daemon threads.

Later, I discovered a crash in the the garbage collector while trying to
reproduce a race condition in asyncio: I created `bpo-20526
<https://bugs.python.org/issue20526>`_. Sadly, this bug was trigger by my
previous change. I decided that it's safer to revert my change.


take_gil() also exits thread at exit point
==========================================

After fixing ``PyEval_RestoreThread()``, I decided to attempt again to fix
`bpo-19466 <https://bugs.python.org/issue19466>`_. Sadly, I discovered that my
``PyEval_RestoreThread()`` fix **introduced a race condition**!

While the main thread finalizes Python, daemon threads can be waiting for the
GIL: they block in ``take_gil()`` after, they already checked
``exit_thread_if_finalizing()``. When the main thread releases the GIL during
finalization, a daemon thread take the GIL instead of exiting.

The solution is to call ``exit_thread_if_finalizing()`` twice in
``take_gil()``: at entry point **and** at exit point.

In March 2020, I pushed `commit 9229eeee <https://github.com/python/cpython/commit/9229eeee105f19705f72e553cf066751ac47c7b7>`__::

    bpo-39877: take_gil() checks tstate_must_exit() twice (GH-18890)

    take_gil() now also checks tstate_must_exit() after acquiring
    the GIL: exit the thread if Py_Finalize() has been called.

Funny/not funny, in June 2019, Eric Snow added a very similar bug in `bpo-36818
<https://bugs.python.org/issue36818>`_ with `commit 396e0a8d
<https://github.com/python/cpython/commit/396e0a8d9dc65453cb9d53500d0a620602656cfe>`__:
`bpo-37135 <https://bugs.python.org/issue37135>`_ (test_multiprocessing_spawn
segfault on FreeBSD). I reverted his change to fix the issue. At this time, I
didn't have the bandwidth to investigate the root cause.

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

More bugs
=========

While working on move pending calls from _PyRuntime to PyInterpreterState,
`bpo-3998 <https://bugs.python.org/issue39984>`_, I had another bug. At March 18, 2020, I pushed
yet another ``take_gil()`` fix, `commit 29356e03
<https://github.com/python/cpython/commit/29356e03d4f8800b04f799efe7a10e3ce8b16f61>`__::

    bpo-39877: Fix take_gil() for daemon threads (GH-19054)

    bpo-39877, bpo-39984: If the thread must exit, don't access tstate to
    prevent a potential crash: tstate memory has been freed.

And while working on the inefficient signal handling in multithreaded
applications (`bpo-40010 <https://bugs.python.org/issue40010>`_), I discovered
that the previous fix was not enough! At March 19, 2020, I had to push yet another
``take_gil()`` fix, `commit a36adfa6
<https://github.com/python/cpython/commit/a36adfa6bbf5e612a4d4639124502135690899b8>`__::

    bpo-39877: 4th take_gil() fix for daemon threads (GH-19080)

    bpo-39877, bpo-40010: Add a third tstate_must_exit() check in
    take_gil() to prevent using tstate which has been freed.

I can only hope that this fix should be the last one to fix all `bpo-39877
<https://bugs.python.org/issue39877>`__ corner cases with daemon threads in
``take_gil()``!


Conclusion
==========

xxx
