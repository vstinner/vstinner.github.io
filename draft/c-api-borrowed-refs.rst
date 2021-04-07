+++++++++++++++++++++++++++++++++++++++
Borrowed references in the Python C API
+++++++++++++++++++++++++++++++++++++++

:date: 2021-03-26 17:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-borrowed-references
:authors: Victor Stinner

In a Python implementations not implemented with reference counting, like PyPy,
emulating borrowed references is inefficient and so borrowed references should
be avoided in the public C API.

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

