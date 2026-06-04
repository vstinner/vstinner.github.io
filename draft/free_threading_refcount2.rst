++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Free Threading internals: reference counting (continued)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

In the `previous article <{filename}/free_threading_refcount.rst>`_, we have
seen how the reference count performance issue was addressed with *Biased
Reference Counting*. In this article, we will investigate further technics
reducing lock contention even more.

Immortal objects (PEP 683)
==========================

In Python 3.12 (in 2022), Eric Snow and Eddie Elizondo managed to convince the
Steering Council and the Python community that modifying ``Py_INCREF()`` and
``Py_DECREF()`` to do nothing on immortal objects is worth it.

My main worry was the negative impact on performance. About that, `PEP 683 says
<https://peps.python.org/pep-0683/#performance>`_:

    A naive implementation shows a 2% slowdown (3% with MSVC). We have
    demonstrated a return to ~performance-neutral~ with a handful of basic
    mitigations applied. See the mitigations section below.

    On the positive side, immortal objects save a significant amount of memory
    when used with a pre-fork model. Also, immortal objects provide
    opportunities for specialization in the eval loop that would improve
    performance.

The implementation basically adds the following code to ``Py_INCREF()`` and
``Py_DECREF()``::

    if (_Py_IsImmortal(op)) {
        return;
    }

``Py_INCREF()`` becomes::

    static inline void Py_INCREF(PyObject *op)
    {
        if (_Py_IsImmortal(op)) {
            return;
        }
        op->ob_refcnt++;
    }

``Py_DECREF()`` becomes::

    static inline void Py_DECREF(PyObject *op)
    {
        if (_Py_IsImmortal(op)) {
            return;
        }
        if (--op->ob_refcnt == 0) {
            _Py_Dealloc(op);
        }
    }

The exact ``Py_INCREF()`` and ``Py_DECREF()`` implementation evolved over time.
Above, I showed the common portable implementation.

The ``sys._is_immortal(obj)`` (added to Python 3.14) can be used to check if an
object is immortal.  Immortal objects use a special value for their reference
count which can be surprising. Example on Python 3.16::

    $ python3.16
    >>> obj = 1
    >>> import sys; sys._is_immortal(obj)
    True
    >>> sys.getrefcount(obj)
    3221225472

You should not rely on the reference count of immortal objects.

Free Threading
--------------

In Free Threading, reference counting on immortal objects is cheap, since
``Py_INCREF()`` and ``Py_DECREF()`` do nothing on them. There is no risk of
lock contention.

Python 3.16 static immortal objects
-----------------------------------

Python 3.16 creates many Python static objects at build time:

* 865 static Unicode strings
* 256 Unicode singletons (range [U+0000; U+00ff])
* 256 bytes singletons (``b'\x00'`` to ``b'\xff'``)
* 1030 integer singletons (range [-5; 1024])

These static objects are created as immortal objects. Examples::

    $ python3.16
    >>> sys._is_immortal('a')
    True
    >>> sys._is_immortal(b'a')
    True
    >>> sys._is_immortal(123)
    True

For details on static objects, see the internal header files:

* ``Include/internal/pycore_global_strings.h``: declare static strings.
* ``Include/internal/pycore_runtime_init_generated.h``: initialize all static
  objects.

Python 3.16 has more singletons objects, also created as immortal objects:

* ``None``, ``Ellipsis`` (``...``), ``False``, ``True``.
* Empty bytes and Unicode strings (``b''`` and ``''``)
* Empty tuple (``()``)

Examples::

    >>> sys._is_immortal(None)
    True
    >>> sys._is_immortal(True)
    True
    >>> sys._is_immortal(())
    True

And Python 3.16 has 120 "static types", including built-in types, which are
also created as immortal objects. Examples::

    $ python3.16
    >>> sys._is_immortal(int)
    True
    >>> sys._is_immortal(str)
    True
    >>> sys._is_immortal(dict)
    True

Python 3.16 runtime immortal objects
------------------------------------

On a Free-Threaded build, ``sys.intern(str)`` marks the interned string as
immortal::

    $ python3.16t
    >>> import sys
    >>> s = sys.intern("long unique string")
    >>> sys._is_immortal(s)
    True

``PyUnstable_SetImmortal()``
----------------------------

Python 3.15 added `PyUnstable_SetImmortal()
<https://docs.python.org/dev/c-api/object.html#c.PyUnstable_SetImmortal>`_ C
API which can be used to mark an object as immortal.

    The argument should be uniquely referenced by the calling thread. This is
    intended to be used for reducing reference counting contention in the
    free-threaded build for objects which are shared across threads.

Unicode strings cannot be made immortal with this API. See
`InternalDocs/string_interning.md
<https://github.com/python/cpython/blob/aa8a43d179bad5cd9fbfce63b630e2ee0bd617e4/InternalDocs/string_interning.md?plain=1#L57>`_
for the rationale:

    Invariant: Every immortal string is interned. In practice, this means that
    you must not use `_Py_SetImmortal` on a string. The converse is not true:
    interned strings can be mortal.

The C function ``PyUnicode_InternInPlace()`` can be used to intern a string and
so make it immortal.

If an object is `immortal
<https://docs.python.org/dev/glossary.html#term-immortal>`_, its reference
count is never modified, and therefore it is **never deallocated** while the
interpreter is running.


Deferred reference count
========================

Python 3.14 added `PyUnstable_Object_EnableDeferredRefcount(obj)
<https://docs.python.org/dev/c-api/object.html#c.PyUnstable_Object_EnableDeferredRefcount>`_
function:

    Enable deferred reference counting on *obj*, if supported by the runtime.
    In the free-threaded build, this allows the interpreter to avoid reference
    count adjustments to *obj*, which may improve multi-threaded performance.
    The tradeoff is that *obj* will only be deallocated by the tracing garbage
    collector, and not when the interpreter no longer has any references to it.

`PEP 703: Deferred Reference Counting <https://peps.python.org/pep-0703/#deferred-reference-counting>`_.

The function sets ``_PyGC_BITS_DEFERRED`` flag in the object GC bits
(*ob_gc_bits*) and sets the shared reference count (*ob_ref_shared*) to the
special value ``_Py_REF_DEFERRED``:

    This value is added to *ob_ref_shared* for objects that use deferred
    reference counting so that they are not immediately deallocated when the
    non-deferred reference count drops to zero.

The function only works on types implementing the GC protocol
(``Py_TPFLAGS_HAVE_GC`` flag). It's the case for all types implemented in
Python, but not for all types implemented in C.

Python 3.16 creates static immortal objects with deferred reference count.

For example, a dictionary lookup can avoid the ``Py_INCREF()``/``Py_DECREF()``
dance when using ``_PyStackRef``::

    if (_PyObject_HasDeferredRefcount(value)) {
        *value_addr =  (_PyStackRef){ .bits = (uintptr_t)value | Py_TAG_REFCNT };
        return ix;
    }

Stack reference (``_PyStackRef``)
================================

Read `InternalDocs/stackrefs.md <https://github.com/python/cpython/blob/038495db33723849b1c206e1bf7e3af1e1c41f0a/InternalDocs/stackrefs.md>`_.

    Stack references are the interpreter's tagged representation of values on
    the evaluation stack. They carry metadata to track ownership and support
    optimizations such as tagged small ints.

- A `_PyStackRef` is a tagged pointer-sized value (see `Include/internal/pycore_stackref.h`).
- Tag bits distinguish three cases:
  - `Py_TAG_REFCNT` unset - reference count lives on the pointed-to object.
  - `Py_TAG_REFCNT` set - ownership is "borrowed" (no refcount to drop on close) or the object is immortal.
  - `Py_INT_TAG` set - tagged small integer stored directly in the stackref (no heap allocation).
- Special constants: `PyStackRef_NULL`, `PyStackRef_ERROR`, and embedded `None`/`True`/`False`.

The API avoids the ``Py_INCREF()``/``Py_DECREF()`` dance whenever possible.

For example, the following function doesn't call ``Py_INCREF()`` or ``Py_DECREF()``
even if *ref* "owns" a reference to the object *obj*.

::

    void func(PyObject *obj)
    {
        _PyStackRef ref = PyStackRef_FromPyObjectBorrow(obj);

        // Check that Py_TAG_REFCNT flag is set
        assert(!PyStackRef_RefcountOnObject(ref));

        // ... use ref ...

        PyStackRef_CLOSE(ref);
    }

On a Free-threaded Python build, ``_PyStackRef_FromPyObjectNew()`` can
use ``Py_TAG_REFCNT`` flag is the object uses deferred reference count.

The ``Py_TAG_REFCNT`` flag can also be used if the object is immortal.

Read `pycore_stackref.h internal header
<https://github.com/python/cpython/blob/038495db33723849b1c206e1bf7e3af1e1c41f0a/Include/internal/pycore_stackref.h>`_
for more information on stack reference.

Otherwise, ``Py_INCREF()`` is called.

* ``PyStackRef_FromPyObjectSteal()``
* ``PyStackRef_IsNull()``
* ``PyStackRef_DUP()``
* Can be used in ``Python/ceval.c``

``_PyCStackRef`` API
--------------------

``_PyCStackRef`` is a stackref that can be stored in a regular C local variable
and be visible to the GC in the free threading build. Used in combination with
``_PyThreadState_PushCStackRef()``.

``_PyThreadState_PushCStackRef()`` adds the ``_PyCStackRef`` to the linked list
``tstate_impl->c_stack_refs``.

Example::

    _PyCStackRef mro_ref;
    _PyThreadState_PushCStackRef(tstate, &mro_ref);
    mro_ref.ref = PyStackRef_FromPyObjectNew(mro);
    ...
    _PyThreadState_PopCStackRef(tstate, &mro_ref);

Ref counting API
================

Is uniquely referenced?
-----------------------

`PyUnstable_Object_IsUniquelyReferenced() <https://docs.python.org/dev/c-api/object.html#c.PyUnstable_Object_IsUniquelyReferenced>`_.

    Check if obj is a unique temporary object. Returns 1 if obj is known to be
    a unique temporary object, and 0 otherwise. This function cannot fail, but
    the check is conservative, and may return 0 in some cases even if obj is a
    unique temporary object.

    If an object is a unique temporary, it is guaranteed that the current code
    has the only reference to the object. For arguments to C functions, this
    should be used instead of checking if the reference count is 1. Starting
    with Python 3.14, the interpreter internally avoids some reference count
    modifications when loading objects onto the operands stack by borrowing
    references when possible, which means that a reference count of 1 by itself
    does not guarantee that a function argument uniquely referenced.

`PyUnstable_Object_IsUniqueReferencedTemporary() <https://docs.python.org/dev/c-api/object.html#c.PyUnstable_Object_IsUniqueReferencedTemporary>`_

    Check if obj is a unique temporary object. Returns 1 if obj is known to be
    a unique temporary object, and 0 otherwise. This function cannot fail, but
    the check is conservative, and may return 0 in some cases even if obj is a
    unique temporary object.

    If an object is a unique temporary, it is guaranteed that the current code
    has the only reference to the object. For arguments to C functions, this
    should be used instead of checking if the reference count is 1. Starting
    with Python 3.14, the interpreter internally avoids some reference count
    modifications when loading objects onto the operands stack by borrowing
    references when possible, which means that a reference count of 1 by itself
    does not guarantee that a function argument uniquely referenced.

Misc
----

``_Py_TryXGetRef()``
