+++++++++++++++++++++++++++++++++++++++++++++
GIL bugfixes for daemon threads in Python 3.9
+++++++++++++++++++++++++++++++++++++++++++++

:date: 2020-04-04 22:00
:tags: cpython, subinterpreters
:category: cpython
:slug: gil-bugfixes-daemon-threads-python39
:authors: Victor Stinner

.. image:: {static}/images/coronamaison_boulet.jpg
   :alt: `#CoronaMaison by Boulet
   :target: https://twitter.com/Bouletcorp/status/1241018332112998401

My previous article `Daemon threads and the Python finalization in Python 3.2 and 3.3
<{filename}/daemon-threads-python-finalization-python32.rst>`_ introduces
issues caused by daemon threads in the Python finalization and past changes to
make them work.

This article is about bugfixes of the infamous GIL (Global Interpreter Lock) in
Python 3.9, between March 2019 and March 2020, for daemon threads during Python
finalization. Some bugs were old: up to 6 years old. Some bugs were triggered
by the on-going work on isolating subinterpreters in Python 3.9.

Drawing: `#CoronaMaison by Boulet
<https://twitter.com/Bouletcorp/status/1241018332112998401>`_.

Fix 1: Exit PyEval_AcquireThread() if finalizing
================================================

In March 2019, **Remy Noel** created `bpo-36469
<https://bugs.python.org/issue36469>`_: a multithreaded Python application
using 20 daemon threads hangs randomly at exit on Python 3.5:

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
Python is finalizing. This function is called after each ``take_gil()`` call.

The fix is very similar to ``PyEval_RestoreThread()`` fix made in 2013 (`commit
0d5e52d3
<https://github.com/python/cpython/commit/0d5e52d3469a310001afe50689f77ddba6d554d1>`__)
to fix `bpo-1856 <https://bugs.python.org/issue1856#msg60014>`_ (Python crash
involving daemon threads during Python exit).


Fix 2: PyEval_RestoreThread() on freed tstate
=============================================

concurrent.futures crash on FreeBSD
-----------------------------------

In December 2019, I reported `bpo-39088 <https://bugs.python.org/issue39088>`_:
test_concurrent_futures **crashed randomly** with a coredump on AMD64 FreeBSD
Shared 3.x buildbot. In March 2020, I succeeded to reproduce the bug on FreeBSD
and I was able to debug the coredump in gdb::

    (gdb) frame
    #0  0x00000000003b518c in PyEval_RestoreThread (tstate=0x801f23790) at Python/ceval.c:387
    387         _PyRuntimeState *runtime = tstate->interp->runtime;

    (gdb) p tstate->interp
    $3 = (PyInterpreterState *) 0xdddddddddddddddd

The Python thread state (``tstate``) was freed. In debug mode, the "free()"
function of the Python memory allocator fills the freed memory block with
``0xDD`` byte pattern (``D`` stands for dead byte) to detect usage of freed
memory.

The problem is that Python finalization already freed the memory of all
PyThreadState structures, when ``PyEval_RestoreThread(tstate)`` is called by a
daemon thread. ``PyEval_RestoreThread()`` dereferences ``tstate``::

    _PyRuntimeState *runtime = tstate->interp->runtime;

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

I created `bpo-39877 <https://bugs.python.org/issue39877>`__ to investigate
this bug. I managed to reproduce the crash on Linux with a script spawning
daemon threads which sleep randomly between 0.0 and 1.0 second, and by adding
``sleep(1);`` call at ``Py_RunMain()`` exit.

I wrote a ``PyEval_RestoreThread()`` fix which access to
``_PyRuntimeState.finalizing`` without the GIL.

**Antoine Pitrou** asked me to convert ``_PyRuntimeState.finalizing`` to an
atomic variable to avoid inconsistencies in case of parallel accesses. At March
7, 2020, I pushed `commit 7b3c252d
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

The day after, I pushed my fix, `commit eb4e2ae2
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

I commented *naively*:

    Ok, it should now be fixed.


Clear Python thread states earlier: my first failed attempt in 2013
===================================================================

In 2013, I opened `bpo-19466 <https://bugs.python.org/issue19466>`_ to clear
earlier the Python thread state of threads during Python finalization. My
intent was to display ``ResourceWarning`` warnings of daemon threads as well.
In November 2013, I pushed `commit 45956b9a
<https://github.com/python/cpython/commit/45956b9a33af634a2919ade64c1dd223ab2d5235>`__::

    Close #19466: Clear the frames of daemon threads earlier during the Python
    shutdown to call objects destructors. So "unclosed file" resource warnings
    are now correctly emitted for daemon threads.

Later, I discovered a crash in the the garbage collector while trying to
reproduce a race condition in asyncio: I created `bpo-20526
<https://bugs.python.org/issue20526>`__. Sadly, this bug was trigger by my
previous change. I decided that it's safer to revert my change.

By the way, when I looked again at `bpo-20526
<https://bugs.python.org/issue20526>`__, I was able to reproduce again the
garbage collector bug, likely because of recent changes. With the help of
**Pablo Galindo Salgado**, Pablo and me `understood the root issue
<https://bugs.python.org/issue20526#msg364851>`_.  At March 24, 2020, I pushed
a fix (`commit
<https://github.com/python/cpython/commit/5804f878e779712e803be927ca8a6df389d82cdf>`__)
to finally fix this 6 years old bug! The fix removes the following line from
``PyThreadState_Clear()``::

     Py_CLEAR(tstate->frame);


Fix 3: Exit also take_gil() at exit point if finalizing
=======================================================

After fixing ``PyEval_RestoreThread()``, I decided to attempt again to fix
`bpo-19466 <https://bugs.python.org/issue19466>`_ (clear earlier Python thread
states). Sadly, I discovered that my ``PyEval_RestoreThread()`` fix
**introduced a race condition**!

While the main thread finalizes Python, daemon threads can be waiting for the
GIL: they block in ``take_gil()``. When the main thread releases the GIL during
finalization, a daemon thread take the GIL instead of exiting. Daemon threads
only check if they must exit **before** trying to take the GIL.

The solution is to call ``exit_thread_if_finalizing()`` twice in
``take_gil()``: before **and** after taking the GIL.

In March 2020, I pushed `commit 9229eeee <https://github.com/python/cpython/commit/9229eeee105f19705f72e553cf066751ac47c7b7>`__::

    bpo-39877: take_gil() checks tstate_must_exit() twice (GH-18890)

    take_gil() now also checks tstate_must_exit() after acquiring
    the GIL: exit the thread if Py_Finalize() has been called.

I commented:

    I ran multiple times ``daemon_threads_exit.py`` with ``slow_exit.patch``:
    no crash.

    I also ran multiple times ``stress.py`` + ``sleep_at_exit.patch`` of
    bpo-37135: no crash.

    And I tested ``asyncio_gc.py`` of bpo-19466: no crash neither.

    **Python finalization now looks reliable.** I'm not sure if it's "more"
    reliable than previously, but at least, I cannot get a crash anymore, even
    after bpo-19466 has been fixed (clear Python thread states of daemon
    threads earlier).

Funny fact, in June 2019, **Eric Snow** added a very similar bug in `bpo-36818
<https://bugs.python.org/issue36818>`_ with `commit 396e0a8d
<https://github.com/python/cpython/commit/396e0a8d9dc65453cb9d53500d0a620602656cfe>`__:
test_multiprocessing_spawn segfault on FreeBSD (`bpo-37135
<https://bugs.python.org/issue37135>`_). I reverted his change to fix the
issue. At this time, I didn't have the bandwidth to investigate the root cause.
I just reverted Eric's change.

Fix 4: Exit take_gil() while waiting for the GIL if finalizing
==============================================================

While I was working on moving pending calls from ``_PyRuntime`` to
``PyInterpreterState``, `bpo-3998 <https://bugs.python.org/issue39984>`_, I had
another bug.

At March 18, 2020, I pushed a ``take_gil()`` fix to avoid accessing ``tstate``
if Python is finalizing, `commit 29356e03
<https://github.com/python/cpython/commit/29356e03d4f8800b04f799efe7a10e3ce8b16f61>`__::

    bpo-39877: Fix take_gil() for daemon threads (GH-19054)

    bpo-39877, bpo-39984: If the thread must exit, don't access tstate to
    prevent a potential crash: tstate memory has been freed.

And while working on the inefficient signal handling in multithreaded
applications (`bpo-40010 <https://bugs.python.org/issue40010>`_), I discovered
that the previous fix was not enough!

At March 19, 2020, I pushed a ``take_gil()`` fix to exit while ``take_gil()``
is waiting for the GIL if Python is finalizing, `commit a36adfa6
<https://github.com/python/cpython/commit/a36adfa6bbf5e612a4d4639124502135690899b8>`__::

    bpo-39877: 4th take_gil() fix for daemon threads (GH-19080)

    bpo-39877, bpo-40010: Add a third tstate_must_exit() check in
    take_gil() to prevent using tstate which has been freed.

I can only hope that this fix is the last one to fix all corner cases with
daemon threads in ``take_gil()`` (`bpo-39877
<https://bugs.python.org/issue39877>`__)!


Summary of GIL bugfixes
=======================

The GIL got 5 main bugfixes for daemon threads and Python finalization:

* May 2011, **Antoine Pitrou**,
  `commit 0d5e52d3 <https://github.com/python/cpython/commit/0d5e52d3469a310001afe50689f77ddba6d554d1>`__:
  ``take_gil()`` exits if finalizing **after** taking the GIL (1 check)
* April 2019, **Joannah Nanjekye**,
  `commit f781d202 <https://github.com/python/cpython/commit/f781d202a2382731b43bade845a58d28a02e9ea1>`__:
  PyEval_AcquireLock() and PyEval_AcquireThread() also exit if Python is finalizing
* March 8, 2020, **Victor Stinner**,
  `commit eb4e2ae2 <https://github.com/python/cpython/commit/eb4e2ae2b8486e8ee4249218b95d94a9f0cc513e>`__:
  ``take_gil()`` exits if finalizing **before** taking the GIL (1 check)
* March 9, 2020, **Victor Stinner**,
  `commit 9229eeee <https://github.com/python/cpython/commit/9229eeee105f19705f72e553cf066751ac47c7b7>`__:
  ``take_gil()`` exits if finalizing **before and after** taking the GIL (2 checks)
* March 19, 2020, **Victor Stinner**,
  `commit a36adfa6 <https://github.com/python/cpython/commit/a36adfa6bbf5e612a4d4639124502135690899b8>`__:
  ``take_gil()`` exits if finalizing **before, while, and after** taking the GIL (3 checks)
