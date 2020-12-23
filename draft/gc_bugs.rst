+++++++
GC bugs
+++++++

For my work on isolating subinterpreters, I had to deal with multiple complex
garbage collector (GC) bugs.

When an extension module is converted to the multiphase initialization API (PEP
489), sometimes tests using subinterpreters start to leak.

Bug
===

November 2019.

`bpo-36854: Make GC module state per-interpreter
<https://bugs.python.org/issue36854>`_: test_atexit started to leak.

Bug::

    $ ./python -m test -R 3:3 test_atexit -m test.test_atexit.SubinterpreterTest.test_callbacks_leak
    test_atexit leaked [3988, 3986, 3988] references, sum=11962

* FIX: Fix refleak in PyInit__testcapi()
* WORKAROUND: clear manually the interpreter codecs attributes (search path,
  search cache, error registry)
* `commit <https://github.com/python/cpython/commit/310e2d25170a88ef03f6fd31efcc899fe062da2c>`__

https://github.com/python/cpython/commit/310e2d25170a88ef03f6fd31efcc899fe062da2c

Workaround in ``finalize_interp_clear()``::

    +    /* bpo-36854: Explicitly clear the codec registry
    +       and trigger a GC collection */
    +    PyInterpreterState *interp = tstate->interp;
    +    Py_CLEAR(interp->codec_search_path);
    +    Py_CLEAR(interp->codec_search_cache);
    +    Py_CLEAR(interp->codec_error_registry);
    +    _PyGC_CollectNoFail();


weakref
=======

March 2020.

2020-03-24: `bpo-40050: Port _weakref to multiphase init
<https://bugs.python.org/issue40050>`_: test_importlib started to leak.

Bug::

    $ ./python -m test -R 3:3 test_importlib
    test_importlib leaked [6303, 6299, 6303] references, sum=18905

* FIX/WORKAROUND: remove unused _weakref (and _thread) import in
  ``importlib._bootstrap_external``
  (`commit <https://github.com/python/cpython/commit/83d46e0622d2efdf5f3bf8bf8904d0dcb55fc322>`__)


GC and traverse function
========================

April 2020.

Fix the traverse function of heap types for GC collection (bpo-40217,
bpo-40149).

2020-04-02: `bpo-40149: Convert _abc module to use PyType_FromSpec()
<https://bugs.python.org/issue40149>`_: test_threading leaks.

* WORKAROUND 1 (not merged): add a second ``_PyGC_CollectNoFail()`` call in
  ``finalize_interp_clear()``.
* FIX 1: Implement traverse in _abc._abc_data
  (`commit <https://github.com/python/cpython/commit/9cc3ebd7e04cb645ac7b2f372eaafa7464e16b9c>`__)
* WORKAROUND 2 (not merged): add ``Py_VISIT(Py_TYPE(self));`` in ``abc_data_traverse()``.
* Regression caused by `bpo-35810: Object Initialization does not incref
  Heap-allocated Types <https://bugs.python.org/issue35810>`_?
* `bpo-40217: The garbage collector doesn't take in account that objects of
  heap allocated types hold a strong reference to their type
  <https://bugs.python.org/issue40217>`_
* FIX 2 (bpo-40217): inject a magic function to visit the heap type in traverse functions
  (`commit <https://github.com/python/cpython/commit/0169d3003be3d072751dd14a5c84748ab63a249f>`__)
* FIX 3 (bpo-40217): Revert FIX 2 and traverse functions must explicitly
  visit their type
  (`commit <https://github.com/python/cpython/commit/1cf15af9a6f28750f37b08c028ada31d38e818dd>`__).
  ``abc_data_traverse()`` now calls ``Py_VISIT(Py_TYPE(self))``.


_signal bug
===========

https://bugs.python.org/issue41713

Introduce the leak: commit 71d1bd9569c8a497e279f2fea6fe47cd70a87ea3

Bug::

    $ ./python -m test -R 3:3 test_interpreters
    test_interpreters leaked [237, 237, 237] references, sum=711

The following three variables are also initialized multiple times by
``signal_exec()``::

    static PyObject *DefaultHandler;
    static PyObject *IgnoreHandler;
    static PyObject *IntHandler;

Revert: https://github.com/python/cpython/commit/4b8032e5a4994a7902076efa72fca1e2c85d8b7f

Fix::

    - static PyObject *IntHandler;

Fix::

        // If signal_module_exec() is called more than one, we must
        // clear the strong reference to the previous function.
        Py_XSETREF(Handlers[signum].func, Py_NewRef(func));

Fix::

    + #ifdef MS_WINDOWS
    +     if (sigint_event != NULL) {
    +         CloseHandle(sigint_event);
    +         sigint_event = NULL;
    +     }
    + #endif


_ast bug
========

November 2020.

2020-11-03: `bpo-41796: Make _ast module state per interpreter
<https://bugs.python.org/issue41796>`_: test_ast leaks.

Bug::

    $ ./python -m test -R 3:3 test_ast
    test_ast leaked [23640, 23636, 23640] references, sum=70916

There are two problems:

* _PyAST_Fini() is only called in the main interpreter, I forgot to remove the
  "if _Py_IsMainInterpreter()".
* _PyAST_Fini() is called after the last GC collection, whereas AST_type
  contains a reference to itself (as any Python type) in its tp_mro member. A
  GC collection is required to destroy the type. _PyAST_Fini() must be called
  before the last GC collection.

FIX: Call _PyAST_Fini() earlier (`commit
<https://github.com/python/cpython/commit/fd957c124c44441d9c5eaf61f7af8cf266bafcb1>`__).

Python types contain a reference to themselves in in their
``PyTypeObject.tp_mro`` member. ``_PyAST_Fini()`` must called before the
last GC collection to destroy AST types.

``_PyInterpreterState_Clear()`` now calls ``_PyAST_Fini()``. It now also
calls ``_PyWarnings_Fini()`` on subinterpeters, not only on the main
interpreter.

Add an assertion in AST ``init_types()`` to ensure that the ``_ast`` module
is no longer used after ``_PyAST_Fini()`` has been called.


_thread lock traverse
=====================

December 2020.

2020-12-18: bpo-1635741.

https://github.com/python/cpython/commit/6104013838e181e3c698cb07316f449a0c31ea96

Bug::

    $ ./python -m test test_threading -R 3:3 -m test_leak
    test_threading leaked [56, 56, 56] references, sum=168

Extract of the fix::

    +static int
    +lock_traverse(lockobject *self, visitproc visit, void *arg)
    +{
    +    Py_VISIT(Py_TYPE(self));
    +    return 0;
    +}

    @@ -292,6 +299,7 @@ static PyType_Slot lock_type_slots[] = {
         {Py_tp_repr, (reprfunc)lock_repr},
         {Py_tp_doc, (void *)lock_doc},
         {Py_tp_methods, lock_methods},
    +    {Py_tp_traverse, lock_traverse},
         {Py_tp_members, lock_type_members},
         {0, 0}
     };

    @@ -299,7 +307,7 @@ static PyType_Slot lock_type_slots[] = {
     static PyType_Spec lock_type_spec = {
         .name = "_thread.lock",
         .basicsize = sizeof(lockobject),
    -    .flags = Py_TPFLAGS_DEFAULT,
    +    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
         .slots = lock_type_slots,
     };

Analysis: https://twitter.com/VictorStinner/status/1339729884113977347
