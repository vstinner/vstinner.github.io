+++++++++++++++++++++++++++++++++++++++++
Creation of the pythoncapi_compat project
+++++++++++++++++++++++++++++++++++++++++

:date: 2021-03-30 20:00
:tags: c-api, cpython
:category: cpython
:slug: pythoncapi_compat
:authors: Victor Stinner

.. image:: {static}/images/strange_cat.jpg
   :alt: Strange Cat by Kéké
   :target: https://twitter.com/Kekeflipnote/status/1378034391872638980

In 2020, I created a new `pythoncapi_compat project
<https://github.com/pythoncapi/pythoncapi_compat>`_ to add Python 3.10 support
to C extensions without losing support for old Python versions. It supports
Python 2.7-3.10 and PyPy 2.7-3.7. The project is made of two parts:

* ``pythoncapi_compat.h``: Header file providing new C API functions to old
  Python versions, like ``Py_SET_TYPE()``.
* ``upgrade_pythoncapi.py``: Script upgrading C extension modules using
  ``pythoncapi_compat.h``. For example, it replaces ``Py_TYPE(obj) = type;``
  with ``Py_SET_TYPE(obj, type);``.

This article is about the creation of the header file and the upgrade script.

Photo: Strange cats 🐾 by Kéké.

Py_SET_TYPE() macro for Python 3.8 and older
============================================

Py_TYPE() macro converted to a static inline function
-----------------------------------------------------

In May 2020 in the `bpo-39573 "Make PyObject an opaque structure"
<https://bugs.python.org/issue39573>`_, `Py_TYPE()
<https://github.com/python/cpython/commit/ad3252bad905d41635bcbb4b76db30d570cf0087>`_
(change by Dong-hee Na), `Py_REFCNT() and Py_SIZE()
<https://github.com/python/cpython/commit/fe2978b3b940fe2478335e3a2ca5ad22338cdf9c>`_
(change by me) macros were converted to static inline functions. This change
broke 17 C extension modules (see my previous article `Make structures opaque
in the Python C API <{filename}/c-api-opaque-structures.rst>`_).


I prepared this change in Python 3.9 by adding Py_SET_REFCNT(), Py_SET_TYPE()
and Py_SET_SIZE() functions, and by modifying Python to use these functions. I
also `added Py_IS_TYPE() function
<https://github.com/python/cpython/commit/d905df766c367c350f20c46ccd99d4da19ed57d8>`_
which tests the type of an object::

    static inline int _Py_IS_TYPE(PyObject *ob, PyTypeObject *type) {
        return ob->ob_type == type;
    }
    #define Py_IS_TYPE(ob, type) _Py_IS_TYPE(_PyObject_CAST(ob), type)

For example, ``Py_TYPE(ob) == (tp)`` can be replaced with ``Py_IS_TYPE(ob, tp)``.

Cython and numpy fixes
----------------------

I fixed Cython by `adding __Pyx_SET_REFCNT() and __Pyx_SET_SIZE() macros
<https://github.com/cython/cython/commit/d8e93b332fe7d15459433ea74cd29178c03186bd>`_::

    #if PY_VERSION_HEX >= 0x030900A4
      #define __Pyx_SET_REFCNT(obj, refcnt) Py_SET_REFCNT(obj, refcnt)
      #define __Pyx_SET_SIZE(obj, size) Py_SET_SIZE(obj, size)
    #else
      #define __Pyx_SET_REFCNT(obj, refcnt) Py_REFCNT(obj) = (refcnt)
      #define __Pyx_SET_SIZE(obj, size) Py_SIZE(obj) = (size)
    #endif

The `numpy fix
<https://github.com/numpy/numpy/commit/a96b18e3d4d11be31a321999cda4b795ea9eccaa>`__::

    #if PY_VERSION_HEX < 0x030900a4
        #define Py_SET_TYPE(obj, typ) (Py_TYPE(obj) = typ)
        #define Py_SET_SIZE(obj, size) (Py_SIZE(obj) = size)
    #endif

`The numpy fix was updated
<https://github.com/numpy/numpy/commit/f1671076c80bd972421751f2d48186ee9ac808aa>`__
to not have a return value by adding ``", (void)0"``::

    #if PY_VERSION_HEX < 0x030900a4
        #define Py_SET_TYPE(obj, type) ((Py_TYPE(obj) = (type)), (void)0)
        #define Py_SET_SIZE(obj, size) ((Py_SIZE(obj) = (size)), (void)0)
    #endif

So the macros better mimicks the static inline functions behavior.

C API Porting Guide
-------------------

I copied the numpy macros `to the C API section of the Python 3.10 porting
guide (What's New in Python 3.10)
<https://github.com/python/cpython/commit/dc24b8a2ac32114313bae519db3ccc21fe45c982>`_.
Py_SET_TYPE() documentation.

    Since ``Py_TYPE()`` is changed to the inline static function,
    ``Py_TYPE(obj) = new_type`` must be replaced with
    ``Py_SET_TYPE(obj, new_type)``: see ``Py_SET_TYPE()`` (available since
    Python 3.9). For backward compatibility, this macro can be used::

        #if PY_VERSION_HEX < 0x030900A4
        #  define Py_SET_TYPE(obj, type) ((Py_TYPE(obj) = (type)), (void)0)
        #endif

Copy/paste macros
-----------------

Up to 3 macros must be copied/pasted for backward compatibility in each
project::

    #if PY_VERSION_HEX < 0x030900A4
    #  define Py_SET_TYPE(obj, type) ((Py_TYPE(obj) = (type)), (void)0)
    #endif

    #if PY_VERSION_HEX < 0x030900A4
    #  define Py_SET_REFCNT(obj, refcnt) ((Py_REFCNT(obj) = (refcnt)), (void)0)
    #endif

    #if PY_VERSION_HEX < 0x030900A4
    #  define Py_SET_SIZE(obj, size) ((Py_SIZE(obj) = (size)), (void)0)
    #endif

These macros started to be copied into multiple projects. Examples:

* `breezy
  <https://bazaar.launchpad.net/~brz/brz/3.1/revision/7647>`_
* `numpy
  <https://github.com/numpy/numpy/commit/f1671076c80bd972421751f2d48186ee9ac808aa>`__
* `pycurl
  <https://github.com/pycurl/pycurl/commit/e633f9a1ac4df5e249e78c218d5fbbd848219042>`_

There might be a better way than copying/pasting these compatibility layer in
each project, adding macros one by one...

Creation of the pythoncapi_compat.h header file
===============================================

While the code for Py_SET_REFCNT(), Py_SET_TYPE() and Py_SET_SIZE() macros is
short, I also wanted to use the new seven Python 3.9 getter functions on Python
3.8 and older:

* Py_IS_TYPE()
* PyFrame_GetBack()
* PyFrame_GetCode()
* PyInterpreterState_Get()
* PyThreadState_GetFrame()
* PyThreadState_GetID()
* PyThreadState_GetInterpreter()

In June 2020, I created `the pythoncapi_compat project
<https://github.com/pythoncapi/pythoncapi_compat>`__ project with a
`pythoncapi_compat.h header file
<https://github.com/pythoncapi/pythoncapi_compat/blob/main/pythoncapi_compat.h>`_
which defines these functions as static inline functions. An
``"#if PY_VERSION_HEX"`` guard prevents to define a function if it's already
provided by ``Python.h``. Example of the current implementation of
PyThreadState_GetInterpreter() for Python 3.8 and older::

    // bpo-39947 added PyThreadState_GetInterpreter() to Python 3.9.0a5
    #if PY_VERSION_HEX < 0x030900A5
    static inline PyInterpreterState *
    PyThreadState_GetInterpreter(PyThreadState *tstate)
    {
        assert(tstate != NULL);
        return tstate->interp;
    }
    #endif

I wrote tests on each function using a C extension. The project initially
supported Python 3.6 to Python 3.10. The test runner checks also for reference
leaks.

Mercurial and Python 2.7
========================

The Mercurial project has multiple C extensions, was broken on Python 3.10 by
the Py_TYPE() change, and is one of the last project still requiring Python 2.7
in 2021. It's a good candidate to check if pythoncapi_compat.h is useful.

`I proposed a patch <https://bz.mercurial-scm.org/show_bug.cgi?id=6451>`_ then
`converted to a merge request
<https://foss.heptapod.net/octobus/mercurial-devel/-/merge_requests/61>`_. It
got accepted in the "next" branch, but compatibility with Visual Studio 2008
had to be fixed for Python 2.7 on Windows. I fixed pythoncapi_compat.h by
defining ``inline`` as ``__inline``::

    // Compatibility with Visual Studio 2013 and older which don't support
    // the inline keyword in C (only in C++): use __inline instead.
    #if (defined(_MSC_VER) && _MSC_VER < 1900 \
         && !defined(__cplusplus) && !defined(inline))
    #  define inline __inline
    #  define PYTHONCAPI_COMPAT_MSC_INLINE
       // These two macros are undefined at the end of this file
    #endif

    (...)

    #ifdef PYTHONCAPI_COMPAT_MSC_INLINE
    #  undef inline
    #  undef PYTHONCAPI_COMPAT_MSC_INLINE
    #endif

I chose to continue writing ``static inline``, so pythoncapi_compat.h remains
close to Python header files. I also modified the pythoncapi_compat test suite
to also test Python 2.7.

pybind11 and PyPy
=================

More recently, I added PyPy 2.7, 3.6 and 3.7 support for pybind11, since PyPy
is tested by their CI. The fix is to no longer define the following functions
on PyPy:

* PyFrame_GetBack(), _PyFrame_GetBackBorrow()
* PyThreadState_GetFrame(), _PyThreadState_GetFrameBorrow()
* PyThreadState_GetID()
* PyObject_GC_IsTracked()
* PyObject_GC_IsFinalized()


Creation of the upgrade_pythoncapi.py script
============================================

upgrade_pythoncapi.py
---------------------

In November 2020, I created a new ``upgrade_pythoncapi.py`` script to replace
``"Py_TYPE(obj) = type;"`` with ``"Py_SET_TYPE(obj, type);"``. The script is
based on my `old sixer.py project <https://github.com/vstinner/sixer>`_ which
adds Python 3 support to a Python project without losing Python 2 support. The
``upgrade_pythoncapi.py`` script uses regular expressions to replace one
pattern with another.

Similar to ``sixer`` which adds ``import six`` to support Python 2 and Python 3
in a single code base, ``upgrade_pythoncapi.py`` adds
``#include "pythoncapi_compat.h"`` to support old and new versions of the
Python C API in a single code base.

I first created a new GitHub project for upgrade_pythoncapi.py, but since it
was too tightly coupled to the pythoncapi_compat.h header file, I moved the
script to the pythoncapi_compat project.

Tests
-----

I added more and more "operations" to update C extensions. For me, **the most
important part is the test suite** to ensure that the script doesn't introduce
bugs. It contains code which must not be replaced. For example, it ensures that
``frame->f_code = code`` is not replaced with ``_PyFrame_GetCodeBorrow(frame) =
code`` by mistake.

Borrowed references
-------------------

Code accessing ``frame->f_code`` directly must use ``PyFrame_GetCode()`` but
this function returns a strong reference, whereas
``frame->f_code`` gives a borrowed reference. I added "Borrow" variants of the
functions to ``pythoncapi_compat.h`` for ``upgrade_pythoncapi.py``. For
example, ``frame->f_code`` is replaced with ``_PyFrame_GetCodeBorrow()`` which
is defined as::

    static inline PyCodeObject*
    _PyFrame_GetCodeBorrow(PyFrameObject *frame)
    {
        return (PyCodeObject *)_Py_StealRef(PyFrame_GetCode(frame));
    }

The ``_Py_StealRef(obj)`` function converts a strong reference to a borrowed
reference (simplified code)::

    static inline PyObject* _Py_StealRef(PyObject *obj)
    {
        Py_DECREF(obj);
        return obj;
    }

It is the opposite of ``Py_NewRef()``. It is similar to ``Py_DECREF(obj)`` but
it can be used as an expression: it returns *obj*.  pythoncapi_compat.h defines
private ``_Py_StealRef()`` and ``_Py_XStealRef()`` static inline functions.
First I proposed to add them to Python, but I abandoned the idea (see
`bpo-42522 <https://bugs.python.org/issue42522>`_).

Thanks to the "Borrow" suffix in function names, it becomes easier to discover
the usage of borrowed references. Using a borrowed reference is unsafe if it is
possible that the object is destroyed before the last usage of borrowed
reference. In case of doubt, it's better to use a strong reference. For
example, ``_PyFrame_GetCodeBorrow()`` can be replaced with
``PyFrame_GetCode()``, but it requires to explicitly delete the created strong
reference with ``Py_DECREF()``.


Practical solution for incompatible C API changes
=================================================

So far, I succeeded to convince 4 projects to use pythoncapi_compat.h:
bitarray, immutables, Mercurial and python-zstandard.

In my opinion, pythoncapi_compat.h is the right approach to introduce
incompatible C API changes: provide a practical solution to support old and new
Python versions in a single code base.

The next steps is to get it adopted more widely and get it endorsed by the
Python project, maybe by moving it under the PSF organization on GitHub.
