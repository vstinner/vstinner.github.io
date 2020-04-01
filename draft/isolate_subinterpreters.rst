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
* `bpo-36479: https://bugs.python.org/issue36479
  <Exit threads when interpreter is finalizing rather than runtime>`_
* `bpo-37127 <https://bugs.python.org/issue37127>`__:
  Handling pending calls during runtime finalization may cause problems.
* `bpo-39877 <https://bugs.python.org/issue39877>`__:
  Daemon thread is crashing in PyEval_RestoreThread() while the main thread is exiting the process
* `bpo-39984 <https://bugs.python.org/issue39984>`__:
  Move some ceval fields from _PyRuntime.ceval to PyInterpreterState.ceval
* `bpo-40010 <https://bugs.python.org/issue40010>`__:
  Inefficient signal handling in multithreaded applications

https://pythondev.readthedocs.io/subinterpreters.html

_PyThreadState_DeleteExcept
===========================

https://bugs.python.org/issue19466

2013-10-31: I open the issue to detect ResourceWarning in daemon threads.

Delete thread state
===================

https://bugs.python.org/issue19466

Clear daemon threads state in Py_Finalize() => new crashes

"It is possible to clear the Python threads earlier since Python 3.2, because
Python threads will now exit cleanly when they try to acquire the GIL: see
PyEval_RestoreThread()."

Attempt #1, 12 Nov 2013: https://hg.python.org/cpython/rev/c2a13acd5e2b

    Close #19466: Clear the frames of daemon threads earlier during the Python
    shutdown to call objects destructors. So "unclosed file" resource warnings are
    now corretly emitted for daemon threads. [#19466]

Py_Finalize() calls _PyThreadState_DeleteExcept()::


    +    /* Destroy the state of all threads except of the current thread: in
    +       practice, only daemon threads should still be alive. Clear frames of
    +       other threads to call objects destructor. Destructors will be called in
    +       the current Python thread. Since _Py_Finalizing has been set, no other
    +       Python threads can lock the GIL at this point (if they try, they will
    +       exit immediatly). */
    +    _PyThreadState_DeleteExcept(tstate);

2019-11-20: https://github.com/python/cpython/commit/9da7430675ceaeae5abeb9c9f7cd552b71b3a93a ::

    bpo-36854: Clear the current thread later (GH-17279)

    Clear the current thread later in the Python finalization.

    * The PyInterpreterState_Delete() function is now responsible
      to call PyThreadState_Swap(NULL).
    * The tstate_delete_common() function is now responsible to clear the
      "autoTSSKey" thread local storage and it only clears it once the
      thread state is fully cleared. It allows to still get the current
      thread from TSS in tstate_delete_common().

https://github.com/python/cpython/commit/4d96b4635aeff1b8ad41d41422ce808ce0b971c8

    bpo-39511: PyThreadState_Clear() calls on_delete (GH-18296)

    PyThreadState.on_delete is a callback used to notify Python when a
    thread completes. _thread._set_sentinel() function creates a lock
    which is released when the thread completes. It sets on_delete
    callback to the internal release_sentinel() function. This lock is
    known as Threading._tstate_lock in the threading module.

    The release_sentinel() function uses the Python C API. The problem is
    that on_delete is called late in the Python finalization, when the C
    API is no longer fully working.

    The PyThreadState_Clear() function now calls the
    PyThreadState.on_delete callback. Previously, that happened in
    PyThreadState_Delete().

    The release_sentinel() function is now called when the C API is still
    fully working.


Daemon threads, take_gil()
==========================

A very old issues...

First fix: XXX

* `bpo-39877 <https://bugs.python.org/issue39877>`__:
  Daemon thread is crashing in PyEval_RestoreThread() while the main thread is exiting the process

4 changes in bpo-39877

take_gil() now checks if the thread must exit at 3 different places.

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

2019-04-24 to 2019-06-19, then 2019-11-12 to 2019-11-20: I started to **pass
runtime to some functions** (``_PyRuntimeState``): `Pass _PyRuntimeState as an
argument rather than using the _PyRuntime global variable
<https://bugs.python.org/issue36710>`_.

2019-10-30 to 2020-02-11: Then I pushed more changes to **pass tstate to some
other functions** (``PyThreadState``): `Pass explicitly tstate to function
calls <https://bugs.python.org/issue38644>`_.

GC module
=========

2019-05-08: Eric Snow opens the issue.

2019-11-20 to 2019-11-22 (issue opened at 2019-05-08): https://bugs.python.org/issue36854

::

    commit 7247407c35330f3f6292f1d40606b7ba6afd5700
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Nov 20 12:25:50 2019 +0100

        bpo-36854: Move _PyRuntimeState.gc to PyInterpreterState (GH-17287)

        * Rename _PyGC_InitializeRuntime() to _PyGC_InitState()
        * finalize_interp_clear() now also calls _PyGC_Fini() in
          subinterpreters (clear the GC state).

Big change to get GC state from state: https://github.com/python/cpython/commit/67e0de6f0b060ac8f373952f0ca4b3117ad5b611

Final commit: https://github.com/python/cpython/commit/7247407c35330f3f6292f1d40606b7ba6afd5700


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



Move
====

``_PyRuntimeState.finalizing (PyThreadState *)``
becomes
``_PyRuntimeState _finalizing (_Py_atomic_address: PyThreadState *)``
+ ``PyInterpreterState.finalizing (int)`` (NEW!)

Move ``_PyRuntimeState.gc`` to ``PyInterpreterState.gc``

Move ``_PyRuntimeState.warnings`` to ``PyInterpreterState.warnings``

NEW: PyInterpreterState.dict
NEW: PyInterpreterState.audit_hooks
NEW: PyInterpreterState.parser
NEW: PyInterpreterState.small_ints

Warnings
========

Move ``_PyRuntimeState.warnings`` to ``PyInterpreterState.warnings``

https://bugs.python.org/issue36737

commit 86ea58149c3e83f402cecd17e6a536865fb06ce1
Author: Eric Snow <ericsnowcurrently@gmail.com>
Date:   Fri May 10 13:29:55 2019 -0400

    bpo-36737: Use the module state C-API for warnings. (gh-13159)



Share code for initialization and finalization
==============================================

Share more code between main interpreter and subinterpreters for
initialization: Py_Initialize() and Py_NewInterpreter(), and finalization:
Py_Finalize() and Py_EndInterpreter().

2019-11-19 to 2019-12-17: https://bugs.python.org/issue38858

    Currently, new_interpreter() is a subset of Py_InitializeFromConfig(): the
    code was duplicated. I would prefer that both functions stay in sync and so
    that new_interpreter() reuses more Py_InitializeFromConfig() code.

16 commits

Better isolate builtins and sys modules.

Preparation work to cleanup types in subinterpreters as well.

Share more code between main and subinterpreters for the finalization. +++

Call init_set_builtins_open() in subinterpreter: "Set builtins.open to io.OpenWrapper".

bpo-38858: _PyImport_FixupExtensionObject() handles subinterpreters (GH-17350)

    If _PyImport_FixupExtensionObject() is called from a subinterpreter,
    leave extensions unchanged and don't copy the module dictionary
    into def->m_base.m_copy.

bpo-38858: new_interpreter() reuses pycore_init_builtins() (GH-17351)

    new_interpreter() now calls _PyBuiltin_Init() to create the builtins
    module and calls _PyImport_FixupBuiltin(), rather than using
    _PyImport_FindBuiltin(tstate, "builtins").

    pycore_init_builtins() is now responsible to initialize
    intepr->builtins_copy: inline _PyImport_Init() and remove this
    function.

bpo-38858: new_interpreter() reuses _PySys_Create() (GH-17481)

    new_interpreter() now calls _PySys_Create() to create a new sys
    module isolated from the main interpreter. It now calls
    _PySys_InitCore() and _PyImport_FixupBuiltin().

    init_interp_main() now calls _PySys_InitMain().

small_ints
==========

Commit: https://github.com/python/cpython/commit/ef5aa9af7c7e493402ac62009e4400aed7c3d54e

    FYI this change broke librepo which calls PyLong_FromLong() without holding
    the GIL. In Python 3.8, "it works". In Python 3.9, it does crash:
    get_small_int() gets a NULL tstate and then dereference a NULL pointer.

    librepo bug:
    https://bugzilla.redhat.com/show_bug.cgi?id=1788918

    IMHO it's a bug in librepo: the GIL must be held to use Python C API.

Reference leaks
===============

IGNORE: https://bugs.python.org/issue38858#msg357052

GC state: https://bugs.python.org/issue36854#msg357150

Long analysis.

    bpo-36854: Fix refleak in subinterpreter (GH-17331)
    https://github.com/python/cpython/commit/310e2d25170a88ef03f6fd31efcc899fe062da2c

I'm not fully happy with this solution, but at least, it allows me to move on
to the next tasks to implement subinterpreters like PR 17315 (bpo-38858: Small
integer per interpreter).

importlib vs _weakref: https://bugs.python.org/issue40050


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

TODO
====

* Move _PyRuntimeState.gilstate to PyInterpreterState.
* Decide how to handle None, True, False and Ellipsis singletons:
  https://bugs.python.org/issue39511


Isolate module state: PEP 489
=============================

Replace PyModule_Create with PyModule_Init?

* reload
* unload
* per-interpreter

tstate
======

bpo-20526: Fix PyThreadState_Clear(): don't decref frame

* https://bugs.python.org/issue20526
* https://github.com/python/cpython/commit/5804f878e779712e803be927ca8a6df389d82cdf
