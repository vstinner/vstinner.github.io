++++++++++++++++++++++++++++++++++++++++++++++
Python C API: Add functions to access PyObject
++++++++++++++++++++++++++++++++++++++++++++++

:date: 2021-10-05 14:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-abstract-pyobject
:authors: Victor Stinner

.. image:: {static}/images/spider.png
   :alt: A spider in my bedroom
   :target: https://twitter.com/Kekeflipnote/status/1433139994516934663

The PyObject structure prevents indirectly to optimize CPython. We will see why
and how I prepared the C API to make this structure opaque. It took me 1 year
and a half to add functions and to introduce incompatible C API changes.

I added functions like Py_SET_TYPE() to abstract access to the ``PyObject``
structure. I modified the standard library to use functions like Py_TYPE() and
Py_SET_TYPE().

I converted the ``Py_TYPE()`` macro to a static inline function, but my change
was reverted twice. I had to fix many C extensions and fix a test_exceptions
crash on Windows to be able to finally merge my change in September 2021.

Finally, we will also see what can be done next to be able to fully make the
PyObject structure opaque.

This article is a follow-up of the `Make structures opaque in the Python C API
<{filename}/c-api-opaque-structures.rst>`_ article.

*Drawing: "A spider in my bedroom" by Kéké*

The C API prevents to optimize CPython
======================================

The C API allows to access directly to structure members by deferencing an
``PyObject*`` pointer. Example getting directly the reference count of an
object::

    Py_ssize_t get_refcnt(PyObject *obj)
    {
        return obj->ob_refcnt;
    }

This ability to access directly structure members prevents optimizing CPython.

Mandatory inefficient boxing/unboxing
-------------------------------------

The ability to dereference a ``PyObject*`` pointer prevents optimizations which
avoid inefficient boxing/unboxing, like tagged pointers or list strategies.

No tagged pointer
-----------------

Tagged pointers require adding code to all functions which currently
dereference object pointers. The current C API prevents doing that in C
extensions, since pointers can be dereferenced directly.

No list strategies
------------------

Since all Python object structures must start with a ``PyObject ob_base;``
member, it is not possible to make other structures opaque before PyObject is
made opaque. It prevents implementing PyPy list strategies to reduce the memory
footprint, like storing an array of numbers directly as numbers, not as boxed
numbers (``PyLongObject`` objects).

Currently, the ``PyListObject`` structure cannot be made opaque. If
``PyListObject`` could be made opaque, it would be possible to store an array
of numbers directly as numbers, and to box objects in ``PyList_GetItem()`` on
demand.

No moving garbage collector
---------------------------

Being able to dereference a ``PyObject**`` pointer also prevents to move
objects in memory. A moving garbage collector can compact memory to reduce the
fragmentation. Currently, it cannot be implemented in CPython.

Cannot allocate temporarily objects on the stack
------------------------------------------------

In CPython, all objects must be allocated on the heap. If an object is
allocated on the stack, stored in a list and the list is still accessible after
the function completes: the stack memory is no longer valid, and so the list is
corrupted at the function exit.

If objects would only be referenced by opaque handles, as the HPy project does,
it would be possible to copy the object from the stack to the heap memory, when
the object is added to the list.

Reference counting doesn't scale
--------------------------------

The ``PyObject`` structure has a reference count (``ob_refcnt`` member),
whereas reference counting is a performance bottleneck when using the same
objects from multiple threads running in parallel. Quickly, there is a race for
the memory cacheline which contains the ``PyObject.ob_refcnt`` counter. It is
especially true for the most commonly used Python objects like None and True
singletons. All CPUs want to read or modify it in parallel.

This problem killed the Gilectomy project which attempted to remove the GIL
from CPython.

A `tracing garbage collector
<https://en.wikipedia.org/wiki/Tracing_garbage_collection>`_ doesn't need
reference counting, but it cannot be implemented currently because of the
``PyObject`` structure.


Creation of the issue (Feb 2020)
================================

In February 2020, I created the `bpo-39573
<https://bugs.python.org/issue39573>`_ : "[C API] Make PyObject an opaque
structure in the limited C API". It is related to my work on the my `PEP 620
(Hide implementation details from the C API)
<https://www.python.org/dev/peps/pep-0620/>`_.

My initial plan was to make the PyObject structure fully opaque in the C API.

Add functions
=============

In Python 3.8, ``Py_REFCNT()`` and ``Py_TYPE()`` macros can be used to set directly an
object reference count or an object type::

    Py_REFCNT(obj) = new_refcnt;
    Py_TYPE(obj) = new_type;

Such syntax requires a direct access to ``PyObject.ob_refcnt`` and
``PyObject.ob_type`` members as l-value.

In Python 3.9, I added Py_SET_REFCNT() and Py_SET_TYPE() functions to add an
abstraction to ``PyObject`` members, and I added ``Py_SET_SIZE()`` to add an
abstraction to the ``PyVarObject.ob_size`` member.

In Python 3.9, I also added ``Py_IS_TYPE(obj, type,)`` helper function to test
an object type. It is equivalent to: ``Py_TYPE(obj) == type``.

Use Py_TYPE() and Py_SET_SIZE() in the stdlib
=============================================

I modified the standard library (C extensions) to no longer access directly
``PyObject`` and ``PyVarObject`` members directly:

* Replace ``"obj->ob_refcnt"`` with ``Py_REFCNT(obj)``
* Replace ``"obj->ob_type"`` with ``Py_TYPE(obj)``
* Replace ``"obj->ob_size"`` with ``Py_SIZE(obj)``
* Replace ``"Py_REFCNT(obj) = new_refcnt"`` with ``Py_SET_REFCNT(obj, new_refcnt)``
* Replace ``"Py_TYPE(obj) = new_type"`` with ``Py_SET_TYPE(obj, new_type)``
* Replace ``"Py_SIZE(obj) = new_size"`` with ``Py_SET_SIZE(obj, new_size)``
* Replace ``"Py_TYPE(obj) == type"`` test with ``Py_IS_TYPE(obj, type)``

Enforce Py_SET_TYPE()
=====================

In Python 3.10, I converted Py_REFCNT(), Py_TYPE() and Py_SIZE() macros to
static inline functions, so ``Py_TYPE(obj) = new_type`` becomes a compiler
error.

Static inline functions still access directly ``PyObject`` and ``PyVarObject``
members at the ABI level, and so don't solve the initial goal: "make the
PyObject structure opaque". Not accessing members at the ABI level can have a
negative impact on performance and I prefer to address it later. I already get
enough backfire with the other C API changes that I made :-)

Broken C extensions (first revert)
==================================

Converting Py_TYPE() and Py_SIZE() macros to static inline functions broke 16 C
extensions:

* **Cython**
* PyPAM
* bitarray
* boost
* breezy
* duplicity
* gobject-introspection
* immutables
* mercurial
* **numpy**
* pybluez
* pycurl
* pygobject3
* pylibacl
* pyside2
* rdiff-backup

In November 2020, during the Python 3.10 devcycle, I preferred to revert
Py_TYPE() and Py_SIZE() changes.

I kept the Py_REFCNT() change since it only broke a single C extension
(PySide2) and it was simple to update it to Py_SET_REFCNT().


pythoncapi_compat
=================

I created the `pythoncapi_compat
<https://github.com/pythoncapi/pythoncapi_compat>`_ project to provide the
following functions to Python 3.8 and older:

* ``Py_SET_REFCNT()``
* ``Py_SET_TYPE()``
* ``Py_SET_SIZE()``
* ``Py_IS_TYPE()``

I also wrote a upgrade_pythoncapi.py script to upgrade C extensions to use
these functions, without losing support for Python 3.8 and older.

Using the pythoncapi_compat project, I succeeded to update multiple C
extensions to prepare them for Py_TYPE() becoming a static inline function.


test_exceptions crash (second revert)
=====================================

In June 2021, during the Python 3.11 devcycle, I changed again Py_TYPE() and
Py_SIZE() since `most C extensions have been fixed in the meanwhile
<https://bugs.python.org/issue39573#msg401378>`_.

Problem: ``test_recursion_in_except_handler()`` of ``test_exceptions`` started
to crash on a Python debug build on Windows: see `bpo-44348
<https://bugs.python.org/issue44348>`_.

Since nobody understood the issue, it was decided to revert my change again to
repair buildbots.

Fix BaseException deallocator
=============================

In September 2021, I looked at the test_exceptions crash. In a **debug build**,
the MSC compiler **doesn't inline** calls to static inline functions. Because
of that, converting Py_TYPE() macro to a static inline functions **increases
the stack memory usage** on a Python debug build on Windows.

I proposed to enable compiler optimizations when building Python in debug mode
on Windows, to inline calls to static inline functions like Py_TYPE(). This
idea was rejected, since the debug build must remain fully usable in a
debugger.

I looked again at the crash and found the root issue.
test_recursion_in_except_handler() creates chained of exceptions. When an
exception is deallocated, it calls the deallocator of another exception, etc.

* recurse_in_except() sub-test creates chains of 11 nested deallocator calls
* recurse_in_body_and_except() sub-test creates a chain of **8192 nested deallocator calls**

I proposed a change to use the **trashcan mechanism**. It limits the call stack to
50 function calls. I checked with a benchmark that the performance overhead is
acceptable. My change fixed the test_exceptions crash!

Close the PyObject issue
========================

Since most C extensions have been fixed and test_exceptions is fixed, I was
able to change Py_TYPE() and Py_SIZE() for the third time. My final commit:
`Py_TYPE becomes a static inline function
<https://github.com/python/cpython/commit/cb15afcccffc6c42cbfb7456ce8db89cd2f77512>`__.

I changed the issue topic to restrict it to adding functions to access PyObject
members. Previously, the goal was to make the PyObject structure opaque.
It took 1 year and a half to add made all these changes.


What's Next to Make PyObject opaque?
====================================

The ``PyObject`` structure is used to define structurres of all Python types,
like ``PyListObject``. All structures start with ``PyObject ob_base;`` and so
the compiler must have access to the ``PyObject`` structure.

Moreover, ``PyType_FromSpec()`` and ``PyType_Spec`` API use indirectly
``sizeof(PyObject)`` in the ``PyType_Spec.basicsize`` member when defining a
type.

One option to make the ``PyObject`` structure opaque would be to modify the
``PyObject`` structure to make it empty, and move its members into a new
private ``_PyObject`` structure. This ``_PyObject`` structure would be
allocated before the ``PyObject*`` pointer, same idea as the current
``PyGC_Head`` header which is also allocated before the ``PyObject*`` pointer.

These changes are more complex than what I expected and so I prefer to open a
new issue later to propose these changes. Also, the performance of these
changes must be checked with benchmarks, to ensure that there is no performance
overhead or that the overhead is acceptable.
