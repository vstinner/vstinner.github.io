+++++++++++++++++++++++++++++++++++
Leaks discovered by subinterpreters
+++++++++++++++++++++++++++++++++++

:date: 2020-12-23 14:00
:tags: cpython, subinterpreters
:category: cpython
:slug: subinterpreter-leaks
:authors: Victor Stinner

This article is about old reference leaks discovered or caused by the work on
isolating subinterpreters: leaks in 6 different modules (gc, _weakref, _abc,
_signal, _ast and _thread).

.. image:: {static}/images/thread_gc_bug.jpg
   :alt: _thread GC bug

Refleaks buildbot failures
==========================

With my work on isolating subinterpreters, old bugs about Python objects leaked
at Python exit are suddenly becoming blocker issues on buildbots.

When subinterpreters still share Python objects with the main interpreter, it
is ok-ish to leak these objects at Python exit. Right now (current master
branch), there are still more than 18 000 Python objects which are not
destroyed at Python exit::

    $ ./python -X showrefcount -c pass
    [18411 refs, 6097 blocks]

This issue is being solved in the `bpo-1635741: Py_Finalize() doesn't clear all
Python objects at exit <https://bugs.python.org/issue1635741>`__ which was
opened almost 14 years ago (2007).

When subinterpreters are better isolated, objects are no longer shared, and
suddenly these leaks make subinterpreters tests failing on Refleak buildbots.
For example, when an extension module is converted to the multiphase
initialization API (PEP 489) or when static types are converted to heap types,
these issues pop up.

It is a blocker issue for me, since I care of having only "green" buildbots (no
test failure), otherwise more serious regressions can be easily missed.


Per-interpreter GC state
========================

In November 2019, I made the state of the GC module per-interpreter in
`bpo-36854 <https://bugs.python.org/issue36854>`_
(`commit <https://github.com/python/cpython/commit/7247407c35330f3f6292f1d40606b7ba6afd5700>`__)
and test_atexit started to leak::

    $ ./python -m test -R 3:3 test_atexit -m test.test_atexit.SubinterpreterTest.test_callbacks_leak
    test_atexit leaked [3988, 3986, 3988] references, sum=11962

I fixed the usage of the ``PyModule_AddObject()`` function in the ``_testcapi``
module (`commit
<https://github.com/python/cpython/commit/310e2d25170a88ef03f6fd31efcc899fe062da2c>`__).

I also pushed a **workaround** in ``finalize_interp_clear()``::

    +    /* bpo-36854: Explicitly clear the codec registry
    +       and trigger a GC collection */
    +    PyInterpreterState *interp = tstate->interp;
    +    Py_CLEAR(interp->codec_search_path);
    +    Py_CLEAR(interp->codec_search_cache);
    +    Py_CLEAR(interp->codec_error_registry);
    +    _PyGC_CollectNoFail();

I dislike having to push a "temporary" workaround, but the Python finalization
is really complex and fragile. Fixing the root issues would require too much
work, whereas I wanted to repair the Refleak buildbots as soon as possible.

In December 2019, the workaround was partially removed (`commit
<https://github.com/python/cpython/commit/ac0e1c2694bc199dbd073312145e3c09bee52cc4>`__)::

    -    Py_CLEAR(interp->codec_search_path);
    -    Py_CLEAR(interp->codec_search_cache);
    -    Py_CLEAR(interp->codec_error_registry);

The year after (December 2020), the last GC collection was moved into
``PyInterpreterState_Clear()``, before finalizating the GC (`commit
<https://github.com/python/cpython/commit/eba5bf2f5672bf4861c626937597b85ac0c242b9>`__).


Port _weakref to multiphase init
================================

In March 2020, the ``_weakref`` module was ported to the multiphase
initialization API (PEP 489) in `bpo-40050
<https://bugs.python.org/issue40050>`_ and test_importlib started to leak::

    $ ./python -m test -R 3:3 test_importlib
    test_importlib leaked [6303, 6299, 6303] references, sum=18905

The analysis was quite long and complicated. The importlib imported some
extension modules twice and it has to inject frozen modules to "bootstrap" the
code.

At the end, I fixed the issue by removing the now unused ``_weakref`` import in
``importlib._bootstrap_external``
(`commit <https://github.com/python/cpython/commit/83d46e0622d2efdf5f3bf8bf8904d0dcb55fc322>`__).
The fix also avoids importing an extension module twice.


Convert _abc static types to heap types
=======================================

In April 2020, the static types of the ``_abc`` extension module were converted
to heap types in `bpo-40077 <https://bugs.python.org/issue40077>`__
(`commit <https://github.com/python/cpython/commit/53e4c91725083975598350877e2ed8e2d0194114>`__) and
test_threading started to leak::

    $ ./python -m test -R 3:3 test_threading
    test_threading leaked [19, 19, 19] references, sum=57

I created `bpo-40149 <https://bugs.python.org/issue40149>`_ to track the leak.


Objects hold a reference to heap types
--------------------------------------

In March 2019, the ``PyObject_Init()`` function was modified in `bpo-35810
<https://bugs.python.org/issue35810>`__ to keep a strong reference (``INCREF``)
to the type if the type is a heap type
(`commit <https://github.com/python/cpython/commit/364f0b0f19cc3f0d5e63f571ec9163cf41c62958>`__)::

    +    if (PyType_GetFlags(tp) & Py_TPFLAGS_HEAPTYPE) {
    +        Py_INCREF(tp);
    +    }

I opened `bpo-40217: The garbage collector doesn't take in account that objects
of heap allocated types hold a strong reference to their type
<https://bugs.python.org/issue40217>`_ to discuss the regression
(the test_threading leak).


First workaround (not merged): force a second garbage collection
----------------------------------------------------------------

While analysing test_threading regression leak, I identified a first
workaround: add a second ``_PyGC_CollectNoFail()`` call in
``finalize_interp_clear()``.

It was only a workaround which helped to understand the issue, it was not
merged.


First fix (merged): abc_data_traverse()
---------------------------------------

I merged a first fix: add a traverse function to the ``_abc._abc_data`` type
(`commit
<https://github.com/python/cpython/commit/9cc3ebd7e04cb645ac7b2f372eaafa7464e16b9c>`__)::

    +static int
    +abc_data_traverse(_abc_data *self, visitproc visit, void *arg)
    +{
    +    Py_VISIT(self->_abc_registry);
    +    Py_VISIT(self->_abc_cache);
    +    Py_VISIT(self->_abc_negative_cache);
    +    return 0;
    +}


Second workaround (not merged): visit the type in abc_data_traverse()
---------------------------------------------------------------------

A second workaround was identified: add ``Py_VISIT(Py_TYPE(self));`` to
the new ``abc_data_traverse()`` function.

Again, it was only a workaround which helped to understand the issue, but it
was not merged.

Second fix (merged): call Py_VISIT(Py_TYPE(self)) automatically
---------------------------------------------------------------

20 days after I opened `bpo-40217 <https://bugs.python.org/issue40217>`__,
**Pablo Galindo** modified ``PyType_FromSpec()`` to add a wrapper around the
traverse function of heap types to ensure that ``Py_VISIT(Py_TYPE(self))`` is
always called (`commit
<https://github.com/python/cpython/commit/0169d3003be3d072751dd14a5c84748ab63a249f>`__).

Last fix (merged): fix every traverse function
----------------------------------------------

In May 2020, **Pablo Galindo** changed his mind. He reverted his
``PyType_FromSpec()`` change and instead fixed traverse function of heap types
(`commit
<https://github.com/python/cpython/commit/1cf15af9a6f28750f37b08c028ada31d38e818dd>`__).

At the end, ``abc_data_traverse()`` calls ``Py_VISIT(Py_TYPE(self))``. The
second "workaround" was the correct fix!


Convert _signal to multiphase init
==================================

In September 2020, **Mohamed Koubaa** ported the ``_signal`` module to the
multiphase initialization API (PEP 489) in `bpo-1635741
<https://bugs.python.org/issue1635741>`__ (`commit 71d1bd95
<https://github.com/python/cpython/commit/71d1bd9569c8a497e279f2fea6fe47cd70a87ea3>`__)
and test_interpreters started to leak::

    $ ./python -m test -R 3:3 test_interpreters
    test_interpreters leaked [237, 237, 237] references, sum=711

I created `bpo-41713 <https://bugs.python.org/issue41713>`_ to track the
regression. Since I failed to find a simple fix, I started by reverting the
change which caused Refleak buildbots to fail (`commit
<https://github.com/python/cpython/commit/4b8032e5a4994a7902076efa72fca1e2c85d8b7f>`__).

I had to refactor the ``_signal`` extension module code with multiple commits
to fix all bugs.

The first fix was to remove the ``IntHandler`` variable: there was no need to
keep it alive, it was only needed once in ``signal_module_exec()``.

The second fix is to close the Windows event at exit::

    + #ifdef MS_WINDOWS
    +     if (sigint_event != NULL) {
    +         CloseHandle(sigint_event);
    +         sigint_event = NULL;
    +     }
    + #endif

The last fix, the most important, is to clear the strong reference to old
Python signal handlers when ``signal_module_exec()`` is called more than once::

    // If signal_module_exec() is called more than one, we must
    // clear the strong reference to the previous function.
    Py_XSETREF(Handlers[signum].func, Py_NewRef(func));

The ``_signal`` module is not well isolated for subinterpreters yet, but at
least it no longer leaks.


Per-interpreter _ast state
==========================

In September 2019, the ``_ast`` extension module was converted to PEP 384
(stable ABI) in `bpo-38113 <https://bugs.python.org/issue38113>`_ (`commit
<https://github.com/python/cpython/commit/ac46eb4ad6662cf6d771b20d8963658b2186c48c>`__):
the AST state moves into a module state.

This change caused 3 different bugs including crashes (`bpo-41194
<https://bugs.python.org/issue41194>`__, `bpo-41261
<https://bugs.python.org/issue41261>`__, `bpo-41631
<https://bugs.python.org/issue41631>`__). The issue is complex since there are
public C APIs which require to access AST types, whereas it became possible to
have multiple ``_ast`` extension module instances.

In July 2020, I fixed the root issue in `bpo-41194
<https://bugs.python.org/issue41194>`_ by replacing the module state with a
global state (`commit
<https://github.com/python/cpython/commit/91e1bc18bd467a13bceb62e16fbc435b33381c82>`__)::

    static astmodulestate global_ast_state;

A global state is bad for subinterpreters. In November 2020, I made the AST
state per-interpreter in `bpo-41796 <https://bugs.python.org/issue41796>`__
(`commit <https://github.com/python/cpython/commit/5cf4782a2630629d0978bf4cf6b6340365f449b2>`_
and test_ast started to leak::

    $ ./python -m test -R 3:3 test_ast
    test_ast leaked [23640, 23636, 23640] references, sum=70916

The fix is to call ``_PyAST_Fini()`` earlier (`commit
<https://github.com/python/cpython/commit/fd957c124c44441d9c5eaf61f7af8cf266bafcb1>`__).

Python types contain a reference to themselves in in their
``PyTypeObject.tp_mro`` member (the MRO tuple: Method Resolution Order).
``_PyAST_Fini()`` must called before the last GC collection to destroy AST
types.

``_PyInterpreterState_Clear()`` now calls ``_PyAST_Fini()``. It now also
calls ``_PyWarnings_Fini()`` on subinterpeters, not only on the main
interpreter.


_thread lock traverse
=====================

In December 2020, while I tried to port the ``_thread`` extesnion module to the multiphase initialization API
(PEP 489), test_threading started to leak::

    $ ./python -m test -R 3:3 test_threading
    test_threading leaked [56, 56, 56] references, sum=168

As usual, the workaround was to force a second GC collection in ``interpreter_clear()``::

         /* Last garbage collection on this interpreter */
         _PyGC_CollectNoFail(tstate);
    +    _PyGC_CollectNoFail(tstate);
         _PyGC_Fini(tstate);

It took me two days to full understand the problem. I drew reference cycles
on paper to help me to understand the problem:

.. image:: {static}/images/thread_gc_bug.jpg
   :alt: _thread GC bug

There are two cycles:

* Cycle 1:

  * at fork function
  * -> __main__ module dict
  * -> at fork function

* Cycle 2:

  * _thread lock type
  * -> lock type methods
  * -> _thread module dict
  * -> _thread local type
  * -> _thread module
  * -> _thread module state
  * -> _thread lock type

Moreover, there is a link between these two reference cycles: an instance of
the lock type.

I fixed the issue by adding a traverse function to the lock type and add
``Py_TPFLAGS_HAVE_GC`` flag to the type (`commit
<https://github.com/python/cpython/commit/6104013838e181e3c698cb07316f449a0c31ea96>`__)::

    +static int
    +lock_traverse(lockobject *self, visitproc visit, void *arg)
    +{
    +    Py_VISIT(Py_TYPE(self));
    +    return 0;
    +}


Notes on weird GC bugs
======================

* ``gc.get_referents()`` and ``gc.get_referrers()`` can be used to check
  traverse functions.
* ``gc.is_tracked()`` can be used to check if the GC tracks an object.
* Using the ``gdb`` debugger on ``gc_collect_main()`` helps to see which
  objects are collected. See for example the ``finalize_garbage()`` functions
  which calls finalizers on unreachable objects.
* The solution is usually a missing traverse functions or a missing
  ``Py_VISIT()`` in an existing traverse function.
* GC bugs are hard to debug :-)

Thanks **Pablo Galindo** for helping me to debug all these tricky GC bugs!

Thanks to everybody who are helping to better isolate subintrepreters by
converting extension modules to the multiphase initialization API (PEP 489) and
by converting dozens of static types to heap types. We made huge progresses
last months!
