+++++++++++++++++++++++
Isolate subinterpreters
+++++++++++++++++++++++

:date: 2020-03-20 23:00
:tags: subinterpreters, capi
:category: cpython
:slug: isolate-subinterpreters
:authors: Victor Stinner

`Pass the Python thread state explicitly <{filename}/tstate.rst>`_

* `bpo-33608 <https://bugs.python.org/issue33608>`__:
  Add a cross-interpreter-safe mechanism to indicate that an object may be destroyed.
* `bpo-37127 <https://bugs.python.org/issue37127>`__:
  Handling pending calls during runtime finalization may cause problems.
* `bpo-39877 <https://bugs.python.org/issue39877>`__:
  Daemon thread is crashing in PyEval_RestoreThread() while the main thread is exiting the process
* `bpo-39984 <https://bugs.python.org/issue39984>`__:
  Move some ceval fields from _PyRuntime.ceval to PyInterpreterState.ceval
* `bpo-40010 <https://bugs.python.org/issue40010>`__:
  Inefficient signal handling in multithreaded applications

Eric
====

Factor out a private, per-interpreter _Py_AddPendingCall():

* 2019-02-24: commit => reverted 8 days later
* 2019-04-12: 2nd commit => reverted 1h later
* 2019-06-01: 3rd commit => reverted 2 days later

Latest attempt: `commit 6a150bca
<https://github.com/python/cpython/commit/6a150bcaeb190d1731b38ab9c7a5d1a352847ddc>`__.

Isolate
=======

I started to **pass runtime to some functions** (``_PyRuntimeState``): `Pass
_PyRuntimeState as an argument rather than using the _PyRuntime global variable
<https://bugs.python.org/issue36710>`_.

Then I pushed more changes to **pass tstate to some other functions**
(``PyThreadState``): `Pass explicitly tstate to function calls
<https://bugs.python.org/issue38644>`_.

GC module
=========

XXX

C API
=====

::

    commit f4b1e3d7c64985f5d5b00f6cc9a1c146bbbfd613
    Author: Victor Stinner <vstinner@python.org>
    Date:   Mon Nov 4 19:48:34 2019 +0100

        bpo-38644: Add Py_EnterRecursiveCall() to the limited API (GH-17046)

        Provide Py_EnterRecursiveCall() and Py_LeaveRecursiveCall() as
        regular functions for the limited API. Previously, there were defined
        as macros, but these macros didn't work with the limited API which
        cannot access PyThreadState.recursion_depth field.

        Remove _Py_CheckRecursionLimit from the stable ABI.

        Add Include/cpython/ceval.h header file.



Move some ceval fields from _PyRuntime.ceval to PyInterpreterState.ceval
========================================================================

Changes::

    commit dab8423d220243efabbbcafafc12d90145539b50
    Author: Victor Stinner <vstinner@python.org>
    Date:   Tue Mar 17 18:56:44 2020 +0100

        bpo-39984: Add PyInterpreterState.ceval (GH-19047)

        subinterpreters: Move _PyRuntimeState.ceval.tracing_possible to
        PyInterpreterState.ceval.tracing_possible: each interpreter now has
        its own variable.

        Changes:

        * Add _ceval_state structure.
        * Add PyInterpreterState.ceval field.
        * _PyEval_EvalFrameDefault(): add ceval2 variable (struct _ceval_state*).
        * Rename _PyEval_Initialize() to _PyEval_InitRuntimeState().
        * Add _PyEval_InitState().
        * Don't export internal _Py_FinishPendingCalls() and
          _PyEval_FiniThreads() functions anymore.


    commit d7fabc116269e4650a684eb04f9ecd84421aa247
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Mar 18 01:56:21 2020 +0100

        bpo-39984: Pass tstate to handle_signals() (GH-19050)

        handle_signals() and make_pending_calls() now expect tstate rather
        than runtime.

    commit 23ef89db7ae46d160650263cc80479c2ed6693fb
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Mar 18 02:26:04 2020 +0100

        bpo-39984: _PyThreadState_DeleteCurrent() takes tstate (GH-19051)

        * _PyThreadState_DeleteCurrent() now takes tstate rather than
          runtime.
        * Add ensure_tstate_not_null() helper to pystate.c.
        * Add _PyEval_ReleaseLock() function.
        * _PyThreadState_DeleteCurrent() now calls
          _PyEval_ReleaseLock(tstate) and frees PyThreadState memory after
          this call, not before.
        * PyGILState_Release(): rename "tcur" variable to "tstate".

    commit 29356e03d4f8800b04f799efe7a10e3ce8b16f61
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Mar 18 03:04:33 2020 +0100

        bpo-39877: Fix take_gil() for daemon threads (GH-19054)

        bpo-39877, bpo-39984: If the thread must exit, don't access tstate to
        prevent a potential crash: tstate memory has been freed.

    commit 56bfdebfb17ea9d3245b1f222e92b8e3b1ed6118
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Mar 18 09:26:25 2020 +0100

        bpo-39984: Pass tstate to _PyEval_SignalAsyncExc() (GH-19049)

        _PyEval_SignalAsyncExc() and _PyEval_FiniThreads() now expect tstate,
        instead of ceval.

    commit 8849e5962ba481d5d414b3467a256aba2134b4da
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Mar 18 19:28:53 2020 +0100

        bpo-39984: trip_signal() uses PyGILState_GetThisThreadState() (GH-19061)

        bpo-37127, bpo-39984:

        * trip_signal() and Py_AddPendingCall() now get the current Python
          thread state using PyGILState_GetThisThreadState() rather than
          _PyRuntimeState_GetThreadState() to be able to get it even if the
          GIL is released.
        * _PyEval_SignalReceived() now expects tstate rather than ceval.
        * Remove ceval parameter of _PyEval_AddPendingCall(): ceval is now
          get from tstate parameter.

    commit 50e6e991781db761c496561a995541ca8d83ff87
    Author: Victor Stinner <vstinner@python.org>
    Date:   Thu Mar 19 02:41:21 2020 +0100

        bpo-39984: Move pending calls to PyInterpreterState (GH-19066)

        If Py_AddPendingCall() is called in a subinterpreter, the function is
        now scheduled to be called from the subinterpreter, rather than being
        called from the main interpreter.

        Each subinterpreter now has its own list of scheduled calls.

        * Move pending and eval_breaker fields from _PyRuntimeState.ceval
          to PyInterpreterState.ceval.
        * new_interpreter() now calls _PyEval_InitThreads() to create
          pending calls lock.
        * Fix Py_AddPendingCall() for subinterpreters. It now calls
          _PyThreadState_GET() which works in a subinterpreter if the
          caller holds the GIL, and only falls back on
          PyGILState_GetThisThreadState() if _PyThreadState_GET()
          returns NULL.

