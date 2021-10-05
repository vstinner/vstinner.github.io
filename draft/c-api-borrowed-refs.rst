+++++++++++++++++++++++++++++++++++++++
Borrowed references in the Python C API
+++++++++++++++++++++++++++++++++++++++

:date: 2021-10-04 19:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-borrowed-references
:authors: Victor Stinner

In a Python implementations not implemented with reference counting, like PyPy,
emulating borrowed references is inefficient and so borrowed references should
be avoided in the public C API.

Problem caused by borrowed references
=====================================

A borrowed reference is a pointer which doesn't "hold" a reference. If the
object is destroyed, the borrowed reference becomes a `dangling pointer
<https://en.wikipedia.org/wiki/Dangling_pointer>`_: point to freed memory which
might be reused by a new object. Borrowed references can lead to bugs and
crashes when misused. Recent example of CPython bug: `bpo-25750: crash in
type_getattro() <https://bugs.python.org/issue25750>`_.

Borrowed references are a problem whenever there is no reference to borrow:
they assume that a referenced object already exists (and thus have a positive
refcount), so that it is just borrowed.

Tagged pointers are an example of this: since there is no concrete
``PyObject*`` to represent the integer, it cannot easily be manipulated.

PyPy has a similar problem with list strategies: if there is a list containing
only integers, it is stored as a compact C array of longs, and the W_IntObject
is only created when an item is accessed (most of the time the W_IntObject is
optimized away by the JIT, but this is another story).

But for PyPy cpyext module, this is a problem: ``PyList_GetItem()`` returns a borrowed
reference, but there is no any concrete ``PyObject*`` to return! The current
``cpyext`` solution is very bad: basically, the first time ``PyList_GetItem()``
is called, the *whole* list is converted to a list of ``PyObject*``, just to
have something to return: see `cpyext get_list_storage()
<https://bitbucket.org/pypy/pypy/src/b9bbd6c0933349cbdbfe2b884a68a16ad16c3a8a/pypy/module/cpyext/listobject.py#lines-28>`_.

See also the Specialized list for small integers
optimization: same optimization applied to CPython. This optimization is
incompatible with borrowed references, since the runtime cannot guess when the
temporary object should be destroyed.


If ``PyList_GetItem()`` returned a strong reference, the ``PyObject*`` could
just be allocated on the fly and destroy it when the user decref it. Basically,
by putting borrowed references in the API, we are fixing in advance the data
structure to use!

C API using borrowed references
===============================

Examples of C API functions returning borrowed references:

* ``PyDict_GetItem()``
* ``PyFunction_GetCode()``
* ``PyList_GetItem()``
* ``PyMethod_Self()``
* ``PySys_GetObject()``
* ``PyTuple_GET_ITEM()``
* ``PyWeakref_GET_OBJECT()``

Py_NewRef()
===========

New Python 3.10 functions:

* PyModule_AddObjectRef()
* Py_NewRef(), Py_XNewRef()

While ``ref = Py_NewRef(obj)`` is similar to ``Py_INCREF(obj); ref = obj;``,
it is more convenient since it can be used as an expression, like ``return
Py_NewRef(obj);``. Previously, the magic C syntax ``expr1, expr2`` was
used to work around this limitation. For example::

    #define Py_RETURN_NONE return Py_INCREF(Py_None), Py_None

was replaced with::

    #define Py_RETURN_NONE return Py_NewRef(Py_None)

**In terms of semantics**, Py_NewRef() makes it explicit
that it creates a new strong reference. ``Py_INCREF(obj);`` converts a borrowed
reference to a strong reference in-place, but ``Py_INCREF(obj); ref = obj;`` is
unclear: what is the new strong reference, *obj* or *ref*?

HPy API
=======

This subtle difference can become a bug when a C extensions is converted to
HPy: see `HPy Handles documentation
<https://docs.hpyproject.org/en/latest/api.html#handles>`_ which explains the
HPy_Close() issue.

C API
-----

Thus, the following perfectly valid piece of Python/C code::

    void foo(void)
    {
        PyObject *x = PyLong_FromLong(42);  // implicit INCREF on x
        PyObject *y = x;
        Py_INCREF(y);                       // INCREF on y
        /* ... */
        Py_DECREF(x);
        Py_DECREF(x);                       // two DECREF on x
    }

HPy API
-------

Becomes using HPy API::

    void foo(HPyContext *ctx)
    {
        HPy x = HPyLong_FromLong(ctx, 42);
        HPy y = HPy_Dup(ctx, x);
        /* ... */
        // we need to close x and y independently
        HPy_Close(ctx, x);
        HPy_Close(ctx, y);
    }

Calling any HPy function on a closed handle is an error. Calling HPy_Close() on
the same handle twice is an error. Forgetting to call HPy_Close() on a handle
results in a memory leak. When running in debug mode, HPy actively checks that
you that you don’t close a handle twice and that you don't forget to close any.


Enhance documentation
=====================

* Define `borrowed reference
  <https://docs.python.org/dev/glossary.html#term-borrowed-reference>`_
  and `strong reference
  <https://docs.python.org/dev/glossary.html#term-strong-reference>`_
  terms in the glossary.
* Rephrase the `Reference Counting
  <https://docs.python.org/dev/c-api/refcounting.html#reference-counting>`_
  documentation to clarify the relationship between borrowed and strong
  references. Examples:

  * Py_NewRef(): **Create** a new strong reference to an object.
  * Py_INCREF(): **Convert** a borrowed reference to a strong reference
    **in-place**.
  * Py_DECREF(): **Delete** a strong reference before exiting its scope.

* Rephrase `PyWeakref_GetObject
  <https://docs.python.org/dev/c-api/weakref.html#c.PyWeakref_GetObject>`_ note
  to clarify when the object can be destroyed (change in bold):

    This function returns a borrowed reference to the referenced object. This
    means that you should always call ``Py_INCREF()`` on the object except when
    it **cannot be destroyed before the last usage of the borrowed reference**.

