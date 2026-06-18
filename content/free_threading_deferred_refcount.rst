+++++++++++++++++++++++++++++++++++++++++++++++++++++
Free Threading internals: deferred reference counting
+++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2026-06-04 17:00
:tags: free-threading, cpython
:category: cpython
:slug: free-threading-deferred-reference-counting
:authors: Victor Stinner

.. image:: {static}/images/banksy_girl_balloon.jpg
   :alt: Banksy - Girl with balloon (2002)
   :target: https://en.wikipedia.org/wiki/Girl_with_Balloon

I'm writing an article series on Free Threading internals to learn more about
Free Threading, explain how it works, and explain how it solved the "remove the
GIL" issue where previous attempts failed.

* 1. `Reference counting <{filename}/free_threading_refcount.rst>`_
* 2. `Deferred reference counting <{filename}/free_threading_deferred_refcount.rst>`_ (this article)
* 3. `PyMutex <{filename}/free_threading_pymutex.rst>`_

In the `previous article <{filename}/free_threading_refcount.rst>`_, we have
seen how the reference count performance issue was addressed with *Biased
Reference Counting*. In this article, we will investigate further technics
reducing reference count contention even more.

In this second article, we will see how immortal objects avoid reference
count contention by doing nothing in ``Py_INCREF()`` and ``Py_DECREF()``. Then
we will see how deferred reference count combined with stack references can
avoid the need to call ``Py_INCREF()`` and ``Py_DECREF()``.

*Photo: Banksy - Girl with balloon (2002).*

Immortal objects (PEP 683)
==========================

In Python 3.12 (in 2022), before Free Threading (Python 3.13), Eric Snow and
Eddie Elizondo managed to convince the Steering Council and the Python
community with `PEP 683 <https://peps.python.org/pep-0683/>`_ that modifying
``Py_INCREF()`` and ``Py_DECREF()`` to do nothing on immortal objects is worth
it.

The implementation basically adds the following code at the beginning of
``Py_INCREF()`` and ``Py_DECREF()`` functions:

.. code-block:: c

   if (_Py_IsImmortal(op)) {
       return;
   }

The ``sys._is_immortal(obj)`` function (added to Python 3.14) can be used to
check if an object is immortal.  Immortal objects use a special value for their
reference count which can be surprising. Example on Python 3.16:

.. code-block:: pycon

   $ python3.16
   >>> obj = 1  # an immortal object
   >>> import sys; sys._is_immortal(obj)
   True
   >>> sys.getrefcount(obj)  # surprise!
   3221225472

Note: You should not rely on the reference count of immortal objects.

Free Threading
--------------

In Free Threading, reference counting on immortal objects is cheap, since
``Py_INCREF()`` and ``Py_DECREF()`` do nothing on them. There is no risk of
reference count contention.

Python 3.16 static immortal objects
-----------------------------------

Python 3.16 creates many Python static objects at build time:

* 1030 integer singletons (range [-5; 1024])
* 256 Unicode singletons (range [U+0000; U+00ff])
* 256 bytes singletons (``b'\x00'`` to ``b'\xff'``)
* around 865 static Unicode strings

These static objects are created as immortal objects. Examples:

.. code-block:: pycon

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

Examples:

.. code-block:: pycon

   >>> sys._is_immortal(None)
   True
   >>> sys._is_immortal(True)
   True
   >>> sys._is_immortal(())
   True

And Python 3.16 has 120 "static types", including built-in types, which are
also created as immortal objects. Examples:

.. code-block:: pycon

   $ python3.16
   >>> sys._is_immortal(int)
   True
   >>> sys._is_immortal(str)
   True
   >>> sys._is_immortal(dict)
   True

Python 3.16 runtime immortal objects
------------------------------------

On Free Threading, ``sys.intern(str)`` marks the interned string as immortal:

.. code-block:: pycon

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

If an object is `immortal
<https://docs.python.org/dev/glossary.html#term-immortal>`_, its reference
count is never modified, and therefore it is **never deallocated** while the
interpreter is running.

Unicode strings cannot be made immortal with this API. See
`InternalDocs/string_interning.md
<https://github.com/python/cpython/blob/aa8a43d179bad5cd9fbfce63b630e2ee0bd617e4/InternalDocs/string_interning.md?plain=1#L57>`_
for the rationale. Extract:

    Invariant: Every immortal string is interned. In practice, this means that
    you must not use ``_Py_SetImmortal()`` on a string. The converse is not
    true: interned strings can be mortal.

On a Free-Threaded build, ``sys.intern(str)`` marks the interned string as
immortal, and so the C function ``PyUnicode_InternInPlace()`` can be used to
mark a string as immortal.


Deferred reference count
========================

Python 3.13 added deferred reference counting with the implementation of Free
Threading. Python 3.14 added `PyUnstable_Object_EnableDeferredRefcount(obj)
<https://docs.python.org/dev/c-api/object.html#c.PyUnstable_Object_EnableDeferredRefcount>`_
function:

    Enable deferred reference counting on *obj*, if supported by the runtime.
    In the free-threaded build, this allows the interpreter to avoid reference
    count adjustments to *obj*, which may improve multi-threaded performance.

    The tradeoff is that *obj* **will only be deallocated by the tracing
    garbage collector**, and not when the interpreter no longer has any
    references to it.

On Free Threading, the function sets the ``_PyGC_BITS_DEFERRED`` flag in the
object GC bits (*ob_gc_bits*) and sets the shared reference count
(*ob_ref_shared*) to the special value ``_Py_REF_DEFERRED``:

    This value is added to *ob_ref_shared* for objects that use deferred
    reference counting so that they are not immediately deallocated when the
    non-deferred reference count drops to zero.

The function only works on types implementing the GC protocol
(``Py_TPFLAGS_HAVE_GC`` flag). It's the case for all types implemented in
Python, but not for static types implemented in C.

Python 3.16 creates static immortal objects with deferred reference count.

Deferred reference counting is also used for modules, top-level functions (but
not nested functions), class and static methods, and some other objects.
Examples on Free Threading:

.. code-block:: pycon

   $ python3.16t
   >>> import _testinternalcapi
   >>> import sys
   >>> _testinternalcapi.has_deferred_refcount(sys)  # module
   True
   >>> _testinternalcapi.has_deferred_refcount(sys.getrefcount)  # function
   True


Stack reference
===============

`PEP 703: Deferred Reference Counting
<https://peps.python.org/pep-0703/#deferred-reference-counting>`_ promises:

    Typically, the interpreter modifies objects’ reference counts as they are
    pushed to and popped from the interpreter’s stack. The interpreter **skips
    these reference counting operations** for objects that use deferred
    reference counting.

To implement this optimization, stack references were added to Python 3.13.
Extract of `InternalDocs/stackrefs.md
<https://github.com/python/cpython/blob/038495db33723849b1c206e1bf7e3af1e1c41f0a/InternalDocs/stackrefs.md>`_:

    Stack references are the interpreter's tagged representation of values on
    the evaluation stack. They carry metadata to track ownership and support
    optimizations such as tagged small ints.

A ``_PyStackRef`` is a tagged pointer-sized value. Tag bits distinguish three
cases:

* ``Py_TAG_REFCNT`` unset - reference count lives on the pointed-to object.
* ``Py_TAG_REFCNT`` set - ownership is "borrowed" (**no refcount to drop on
  close**) or the object is immortal.
* ``Py_INT_TAG`` set - tagged small integer stored directly in the stackref (no heap allocation).

Since the Python memory allocator uses at least an alignment on 8 bytes, the 3
least significant bits are available to store a tag. (Currently, ``_PyStackRef``
only uses 2 bits for the tag.)

For example, the following functions can use the ``Py_TAG_REFCNT`` tag and so
avoid calling ``Py_INCREF()`` and ``Py_DECREF()``:

.. code-block:: c

   void another_func(_PyStackRef ref)
   {
       PyObject *obj = PyStackRef_AsPyObjectBorrow(ref);  // borrowed ref
       // ... use obj ...
   }

   void func(PyObject *obj)
   {
       // Make the assumption that the caller owns a strong reference to obj
       _PyStackRef ref = PyStackRef_FromPyObjectBorrow(obj);

       // Check that Py_TAG_REFCNT flag is set
       assert(!PyStackRef_RefcountOnObject(ref));

       another_func(ref);

       PyStackRef_CLOSE(ref);
   }

``_PyStackRef_FromPyObjectNew()``:

* On a Free-threaded Python build, if the object uses **deferred reference
  count**, use ``Py_TAG_REFCNT`` flag.
* If the object is **immortal**, use the ``Py_TAG_REFCNT`` flag.
* Otherwise, ``Py_INCREF()`` is called.

``PyStackRef_CLOSE()`` only calls ``Py_DECREF()`` if the ``Py_TAG_REFCNT`` flag
is not set.

Read `pycore_stackref.h internal header
<https://github.com/python/cpython/blob/038495db33723849b1c206e1bf7e3af1e1c41f0a/Include/internal/pycore_stackref.h>`_
for more information on the stack reference API.

The API was added to Python 3.13 (2024) by Ken Jin (`PR gh-118330
<https://github.com/python/cpython/pull/118330>`_) to implement tagged
pointers. It only started to be used widely in Python 3.14 (2025) internals (in
``Python/ceval.c``). See `faster-python issue #632
<https://github.com/faster-cpython/ideas/issues/632>`_ for the background on
this work.


``_PyCStackRef`` API
--------------------

``_PyCStackRef`` is a stack reference that can be stored in a regular C local
variable and be visible to the garbage collector in the free threading build.
Used in combination with ``_PyThreadState_PushCStackRef()``.

On Free-Threading, ``_PyThreadState_PushCStackRef()`` adds the reference to the
linked list ``tstate->c_stack_refs``, and the garbage collector traverses this
list.

Example of usage:

.. code-block:: c

   _PyCStackRef mro_ref;
   _PyThreadState_PushCStackRef(tstate, &mro_ref);
   mro_ref.ref = PyStackRef_FromPyObjectNew(mro);
   // ... use mro_ref ...
   _PyThreadState_PopCStackRef(tstate, &mro_ref);

Bytecode evaluation loop
========================

To explain how stack reference avoids calling ``Py_INCREF()`` and
``Py_DECREF()``, let's see how LOAD_CONST and POP_TOP opcodes are implemented
in Python 3.16 with stack reference, compared to Python 3.13. The bytecode
evaluation loop in implemented in ``Python/ceval.c`` and opcodes are
implemented in ``Python/generated_cases.c.h``.

Python 3.13 LOAD_CONST opcode:

.. code-block:: c

   PyObject *value = GETITEM(FRAME_CO_CONSTS, oparg);
   Py_INCREF(value);
   stack_pointer[0] = value;
   stack_pointer += 1;

Python 3.16 LOAD_CONST opcode using stack reference:

.. code-block:: c

   PyObject *obj = GETITEM(FRAME_CO_CONSTS, oparg);
   _PyStackRef value = PyStackRef_FromPyObjectBorrow(obj);
   stack_pointer[0] = value;
   stack_pointer += 1;

``PyStackRef_FromPyObjectBorrow(obj)`` uses the ``Py_TAG_REFCNT`` flag and
doesn't call ``Py_INCREF(obj)``.

Python 3.13 POP_TOP opcode:

.. code-block:: c

   Py_DECREF(stack_pointer[-1]);
   stack_pointer -= 1;

Python 3.16 POP_TOP opcode using stack reference:

.. code-block:: c

   _PyStackRef value = stack_pointer[-1];
   PyStackRef_XCLOSE(value);
   stack_pointer -= 1;

Since LOAD_CONST creates the stack reference with the ``Py_TAG_REFCNT`` flag,
``PyStackRef_XCLOSE(value)`` does nothing: it doesn't call
``Py_DECREF(value)``.

At the end, using stack references avoid many ``Py_INCREF()`` and
``Py_DECREF()`` calls in the bytecode evalution loop, making Python faster.


Conclusion
==========

Python 3.16 marks many objects as immortal which avoids reference count
contention, since ``Py_INCREF()`` and ``Py_DECREF()`` do nothing in this case.

Python 3.16 also uses deferred reference counting combined with stack
references to avoid calling ``Py_INCREF()`` and ``Py_DECREF()`` which is even
faster.

Biased Reference Counting, immortal objects, deferred reference counting and
stack reference solved the reference count contention issue and makes sure that
threads scales well with the number of CPU cores. At least, reference counting
is no longer the bottleneck.
