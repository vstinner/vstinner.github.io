+++++++++++++++++++++++++++++++++++++++++
Creation of the pythoncapi_compat project
+++++++++++++++++++++++++++++++++++++++++

:date: 2021-03-26 19:00
:tags: c-api, cpython
:category: cpython
:slug: pythoncapi_compat
:authors: Victor Stinner

pythoncapi_compat
=================

Py_SET_TYPE() macro
-------------------

In 2020, I converted Py_TYPE() and Py_SIZE() macros to static inline functions.
This change broke 17 C extensions. I started by documenting how to port C
extensions to new Py_SET_TYPE() and Py_SET_SIZE() functions (added in Python
3.9). The first version was::

    #if PY_VERSION_HEX < 0x030900A4
    #  define Py_SET_TYPE(obj, type) (Py_TYPE(obj) = (type))
    #endif

But a numpy developer noticed that the macro defined like that has a return
value and so is different than the static inline function which has no return
value::

    static inline void _Py_SET_REFCNT(PyObject *ob, Py_ssize_t refcnt) {
        ob->ob_refcnt = refcnt;
    }
    #define Py_SET_REFCNT(ob, refcnt) _Py_SET_REFCNT(_PyObject_CAST(ob), refcnt)

The macro became::

    #if PY_VERSION_HEX < 0x030900A4
    #  define Py_SET_TYPE(obj, type) ((Py_TYPE(obj) = (type)), (void)0)
    #endif

I quickly understood that backport compatibility is complex. My plan involved
to modify more than two macros, and the complexity will only grow.

Creationf of pythoncapi_compat
------------------------------

I decided to create a ``pythoncapi_compat.h`` header file providing new
functions to old Python versions. To get a behavior closer to the current
Python implement of the C API, I decided to use static inline function. Extract
of ``pythoncapi_compat.h``::

    // bpo-39573 added Py_SET_REFCNT() to Python 3.9.0a4
    #if PY_VERSION_HEX < 0x030900A4 && !defined(Py_SET_REFCNT)
    static inline void _Py_SET_REFCNT(PyObject *ob, Py_ssize_t refcnt)
    {
        ob->ob_refcnt = refcnt;
    }
    #define Py_SET_REFCNT(ob, refcnt) _Py_SET_REFCNT(_PyObject_CAST(ob), refcnt)
    #endif

I created the `pythoncapi_compat project
<https://github.com/pythoncapi/pythoncapi_compat>`_ for this header file with
documentation and tests.

Creation of the upgrade_pythoncapi.py script
--------------------------------------------

Fixing manually 17 broken C extensions made of many long C files is boring and
error-prone. I started to write a new ``upgrade_pythoncapi.py`` script using
regular expression based on my `old sixer.py project
<https://github.com/vstinner/sixer>`_ which adds Python 3 support without
losing Python 2 support thanks to the ``six`` module.

For example, replace ``Py_TYPE(obj) = type;`` with ``Py_SET_TYPE(obj, type);``.

Similar to ``sixer`` which adds ``import six`` to support Python 2 and Python 3
in a single code base, ``upgrade_pythoncapi.py`` adds ``#include
"pythoncapi_compat.h"`` to support old and new versions of the C API in a
single code base.

First, I created a new GitHub project for upgrade_pythoncapi.py. But since it
was too tightly coupled to the pythoncapi_compat.h header file, I moved the
script there.

I added more and more operations to update C extensions. For me, the most
important part is the test suite to ensure that the script doesn't introduce
bugs. It contains code which must not be replaced. For example, it ensures that
``frame->f_code = code`` is not replaced with ``_PyFrame_GetCodeBorrow(frame) =
code`` by mistake.

Borrowed references
-------------------

pythoncapi_compat.h defines private ``_Py_StealRef()`` and ``_Py_XStealRef()``
static inline functions which are used by "Borrow" variants of functions, like
``_PyFrame_GetCodeBorrow()``. First I proposed to add them in Python, but I
abandoned the idea (see `bpo-42522 <https://bugs.python.org/issue42522>`_).

Example::

    static inline PyCodeObject*
    _PyFrame_GetCodeBorrow(PyFrameObject *frame)
    {
        return (PyCodeObject *)_Py_StealRef(PyFrame_GetCode(frame));
    }

The "Borrow" variant is used to replace ``frame->f_code`` with ``_PyFrame_GetCodeBorrow(frame)``,
since PyFrame_GetCode() returns a strong reference and so cannot be used.

PyFrame_GetCode() is provided by Python on Python 3.9 and newer. On Python 3.8
and older, it is implemented in pythoncapi_compat.h as::

    static inline PyCodeObject*
    PyFrame_GetCode(PyFrameObject *frame)
    {
        return (PyCodeObject*)Py_NewRef(frame->f_code);
    }

The ``upgrade_pythoncapi.py`` script replaces ``frame->f_code`` pattern with
``_PyFrame_GetCodeBorrow(frame)``.

Thanks for "Borrow" suffix in function names, it becomes easier to discover
the usage of borrowed references. ``_PyFrame_GetCodeBorrow()`` can be replaced
with ``PyFrame_GetCode()`` but it requires to explicitly delete the created
strong reference (add ``Py_DECREF()``).


Creation of the header file
---------------------------

In 2020, I created the `pythoncapi_compat project
<https://github.com/pythoncapi/pythoncapi_compat>`_ to add Python 3.10 support
to C extensions without losing support for Python 2.7. The project is made of
two parts:

* ``pythoncapi_compat.h``: Header file providing new functions of the Python C
  API to old Python versions.
* ``upgrade_pythoncapi.py``: Script upgrading C extension modules to newer
  Python API without losing support for old Python versions. It relies on
  ``pythoncapi_compat.h``.

The ``pythoncapi_compat.h`` header provides new functions to old Python
versions as static inline functions. Example::

    // bpo-39573 added Py_SET_REFCNT() to Python 3.9.0a4
    #if PY_VERSION_HEX < 0x030900A4 && !defined(Py_SET_REFCNT)
    static inline void _Py_SET_REFCNT(PyObject *ob, Py_ssize_t refcnt)
    {
        ob->ob_refcnt = refcnt;
    }
    #define Py_SET_REFCNT(ob, refcnt) _Py_SET_REFCNT(_PyObject_CAST(ob), refcnt)
    #endif

For example, ``upgrade_pythoncapi.py`` replaces ``Py_REFCNT(obj) = refcnt;``
with ``Py_SET_REFCNT(obj, refcnt);``.

I succeeded to use the ``pythoncapi_compat.h`` header file in 4 projects:
bitarray, immutables, mercurial and python-zstandard.

The recommanded way to use the ``pythoncapi_compat.h`` header file is to copy
it into your project. There is no need to update your copy, until you need new
functions.
