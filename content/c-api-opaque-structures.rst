++++++++++++++++++++++++++++++++++++++++++
Make structures opaque in the Python C API
++++++++++++++++++++++++++++++++++++++++++

:date: 2021-03-26 12:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-opaque-structures
:authors: Victor Stinner

This article is about changes that I made, with the help other developers, in
the Python C API in Python 3.8, 3.9 and 3.10 to avoid accessing structures
members: prepare the C API to `make structures opaque
<https://en.wikipedia.org/wiki/Opaque_data_type>`_. These changes are related
to my `PEP 620 "Hide implementation details from the C API"
<https://www.python.org/dev/peps/pep-0620/>`_.

One change had **negative impact on performance** and had to be
reverted. Making Python slower just to make structures opaque would first
require to get the PEP 620 accepted.

While compatible changes merged in Python 3.8 and Python 3.9 went fine, one
Python 3.10 **incompatible change caused more troubles** and had to be
reverted.

.. image:: {static}/images/incendie-ovh.jpg
   :alt: OVHcloud datacenter fire in Strasbourg
   :target: https://fr.wikipedia.org/wiki/Incendie_du_centre_de_donn%C3%A9es_d%27OVHcloud_%C3%A0_Strasbourg

Photo: OVHcloud data center fire in Strasbourg.

Rationale
=========

The C API currently exposes most object structures, C extensions indirectly
access structures members through the API, but can also access them directly.
It causes different issues:

* Modifying a structure can break an unknown number of C extensions. To prevent
  any risk, CPython core developers avoid modifying structures. Once most
  structures will be opaque, it will be possible to experiment **optimizations**
  which require deep structures changes without breaking C extensions. The
  irony is that we first have to break the backward compatibility and C
  extensions for that.

* Any structure change breaks the ABI. The **stable ABI** solved this issue by
  not exposing structures into its limited C API. The idea is to bend the
  default C API towards the limited C API to provide a stable ABI for everyone
  in the long term.

Issues
======

* `PyObject: bpo-39573 <https://bugs.python.org/issue39573>`_
* `PyTypeObject: bpo-40170 <https://bugs.python.org/issue40170>`_
* `PyThreadState: bpo-39947 <https://bugs.python.org/issue39947>`_
* `PyFrameObject: bpo-40421 <https://bugs.python.org/issue40421>`_

Opaque structures
=================

* Python 3.8 made the PyInterpreterState structure opaque.
* Python 3.9 made the PyGC_Head structure opaque.

Add getter functions to Python 3.9
==================================

* PyObject, PyVarObject:

  * Py_SET_REFCNT()
  * Py_SET_TYPE()
  * Py_SET_SIZE()
  * Py_IS_TYPE()

* PyFrameObject:

  * PyFrame_GetCode()
  * PyFrame_GetBack()

* PyThreadState:

  * PyThreadState_GetInterpreter()
  * PyThreadState_GetFrame()
  * PyThreadState_GetID()

* PyInterpreterState:

  * PyInterpreterState_Get()

PyInterpreterState_Get() can be used to replace ``PyThreadState_Get()->interp``
and ``PyThreadState_GetInterpreter(PyThreadState_Get())``.

Convert macros to static inline functions in Python 3.8
=======================================================

Macro pitfalls
--------------

Macros are convenient but have `multiple pitfalls
<https://gcc.gnu.org/onlinedocs/cpp/Macro-Pitfalls.html>`_. Some macros
can be abused in surprising ways. For example, the following code is valid with
Python 3.9::

    if (obj == NULL || PyList_SET_ITEM (l, i, obj) < 0) { ... }

In Python 3.9, PyList_SET_ITEM() returns *obj* in this case, *obj* is a
pointer, and so the test checks if a pointer is negative which makes no sense
(but is accepted by C compilers by default). This code is likely a confusion
with PyList_SetItem() which returns a int, negative in case of an error.

Zackery Spytz and me modified `PyList_SET_ITEM()
<https://github.com/python/cpython/commit/556d97f473fa538cef780f84bd29239ecf57d9c5>`_
and `PyCell_SET()
<https://github.com/python/cpython/commit/0ef96c2b2a291c9d2d9c0ba42bbc1900a21e65f3>`_
macros in Python 3.10 to return void.

This change broke alsa-python: I proposed a `fix which was merged
<https://github.com/alsa-project/alsa-python/commit/5ea2f8709b4d091700750661231f8a3ddce0fc7c>`_.

One nice side effect of converting macros to static inline functions is that
debuggers and profilers are able to retrieve the name of the function.

Converted macros
----------------

* Py_INCREF(), Py_XINCREF()
* Py_DECREF(), Py_XDECREF()
* PyObject_INIT(), PyObject_INIT_VAR()
* _PyObject_GC_TRACK(), _PyObject_GC_UNTRACK(), _Py_Dealloc()

Performance
-----------

Since ``Py_INCREF()`` is criticial for general Python performance, the impact
of the change was analyzed in depth before `being merged
<https://github.com/python/cpython/commit/2aaf0c12041bcaadd7f2cc5a54450eefd7a6ff12>`_
in `bpo-35059 <https://bugs.python.org/issue35059>`_. The usage of
``__attribute__((always_inline))`` and ``__forceinline`` to force inlining was
rejected.

Cast to PyObject*
-----------------

Old Py_INCREF() implementation in Python 3.7::

    #define Py_INCREF(op) (                   \
        _Py_INC_REFTOTAL  _Py_REF_DEBUG_COMMA \
        ((PyObject *)(op))->ob_refcnt++)

where ``_Py_INC_REFTOTAL _Py_REF_DEBUG_COMMA`` becomes ``_Py_RefTotal++,`` if
the ``Py_REF_DEBUG`` macro is defined, or nothing otherwise. Current
Py_INCREF() implementation in Python 3.10::

    static inline void _Py_INCREF(PyObject *op)
    {
    #ifdef Py_REF_DEBUG
        _Py_RefTotal++;
    #endif
        op->ob_refcnt++;
    }
    #define Py_INCREF(op) _Py_INCREF(_PyObject_CAST(op))

Most static inline functions go through a macro to cast their argument to
``PyObject*`` using the macro::

    #define _PyObject_CAST(op) ((PyObject*)(op))

Convert macros to regular functions in Python 3.9
=================================================

Converted macros
----------------

* PyIndex_Check()
* PyObject_CheckBuffer()
* PyObject_GET_WEAKREFS_LISTPTR()
* PyObject_IS_GC()
* PyObject_NEW(): alias to PyObject_New()
* PyObject_NEW_VAR(): alias to PyObjectVar_New()

Performance
-----------

PyType_HasFeature() was modified to always call PyType_GetFlags() function,
rather than accessing directly ``PyTypeObject.tp_flags``. The problem is that
on macOS, Python is built without LTO, the PyType_GetFlags() call is not
inlined, making functions like tuplegetter_descr_get() **slower**: see
`bpo-39542 <https://bugs.python.org/issue39542#msg372962>`_. I **reverted the
PyType_HasFeature() change** until the PEP 620 is accepted. macOS does not
use LTO to keep support support for macOS 10.6 (Snow Leopard): see `bpo-41181
<https://bugs.python.org/issue41181>`_.

Fast static inline functions
----------------------------

To keep best performances on Python built without LTO, fast private variants
were added as static inline functions to the internal C API:

* _PyIndex_Check()
* _PyObject_IS_GC()
* _PyType_HasFeature()
* _PyType_IS_GC()

For example, PyObject_IS_GC() is defined as a function, whereas
_PyObject_IS_GC() is defined as an internal static inline function. Header
file::

    /* Test if an object implements the garbage collector protocol */
    PyAPI_FUNC(int) PyObject_IS_GC(PyObject *obj);

    // Fast inlined version of PyObject_IS_GC()
    static inline int _PyObject_IS_GC(PyObject *obj)
    {
        return (PyType_IS_GC(Py_TYPE(obj))
                && (Py_TYPE(obj)->tp_is_gc == NULL
                    || Py_TYPE(obj)->tp_is_gc(obj)));
    }

C code::

    int
    PyObject_IS_GC(PyObject *obj)
    {
        return _PyObject_IS_GC(obj);
    }


Python 3.10 incompatible C API change
=====================================

The ``Py_REFCNT()`` macro was converted to a static inline function:
``Py_REFCNT(obj) = refcnt;`` now fails with a compiler error. It must be
replaced with ``Py_SET_REFCNT(obj, refcnt)``: Py_SET_REFCNT() was added to
Python 3.9.

The complex case of Py_TYPE() and Py_SIZE() macros
==================================================

Macros converted and then reverted
----------------------------------

The ``Py_TYPE()`` and ``Py_SIZE()`` macros were also converted to static inline
functions in Python 3.10, but the change `broke 17 C extensions
<https://bugs.python.org/issue39573#msg370303>`_.

Since the change broke too many C extensions, I reverted the change: I
`converted Py_TYPE() and Py_SIZE() back to macros
<https://github.com/python/cpython/commit/0e2ac21dd4960574e89561243763eabba685296a>`_
to have more time to fix fix C extensions.

I fixed 6 extensions
--------------------

* Cython: `my fix adding __Pyx_SET_SIZE() and __Pyx_SET_REFCNT()
  <https://github.com/cython/cython/commit/d8e93b332fe7d15459433ea74cd29178c03186bd>`_
* immutables: `my fix adding pythoncapi_compat.h for Py_SET_SIZE()
  <https://github.com/MagicStack/immutables/commit/45105ecd8b56a4d88dbcb380fcb8ff4b9cc7b19c>`_
* breezy: `my fix adding Py_SET_REFCNT() macro
  <https://bazaar.launchpad.net/~brz/brz/3.1/revision/7647>`__
* bitarray: `my fix adding pythoncapi_compat.h
  <https://github.com/ilanschnell/bitarray/commit/a0cca9f2986ec796df74ca8f42aff56c4c7103ba>`_
* python-zstandard: `my fix adding pythoncapi_compat.h
  <https://github.com/indygreg/python-zstandard/commit/e5a3baf61b65f3075f250f504ddad9f8612bfedf>`__
  followed by `a pythoncapi_compat.h update for Python 2.7
  <https://github.com/indygreg/python-zstandard/commit/477776e6019478ca1c0b5777b073afbec70975f5>`_
* mercurial: `my fix adding pythoncapi_compat.h
  <https://www.mercurial-scm.org/repo/hg/rev/e92ca942ddca>`__
  followed by a `fix for Python 2.7
  <https://www.mercurial-scm.org/repo/hg/rev/38b9a63d3a13>`_
  (then `fixed into upstream pythoncapi_compat.h
  <https://github.com/pythoncapi/pythoncapi_compat/commit/3e0bde93954ea8df328d36900c7060a3f3433eb0>`_)

Extensions fixed by others
--------------------------

* numpy: `fix defining Py_SET_TYPE() and Py_SET_SIZE()
  <https://github.com/numpy/numpy/commit/a96b18e3d4d11be31a321999cda4b795ea9eccaa>`_,
  followed by a `cleanup commit
  <https://github.com/numpy/numpy/commit/f1671076c80bd972421751f2d48186ee9ac808aa>`_
* pycurl: `fix defining Py_SET_TYPE()
  <https://github.com/pycurl/pycurl/commit/e633f9a1ac4df5e249e78c218d5fbbd848219042>`_
* boost: `fix adding Py_SET_TYPE() and Py_SET_SIZE() macros
  <https://github.com/boostorg/python/commit/500194edb7833d0627ce7a2595fec49d0aae2484#diff-b06ac66c98951b48056826c904be75263cdf56ec9b79d3274ea493e7d27cbac4>`_
* duplicity:
  `fix 1 <https://git.launchpad.net/duplicity/commit/?id=9c63dcb83e922e0afac206188203891e203b4e66>`__,
  `fix 2 <https://git.launchpad.net/duplicity/commit/?id=bbaae91b5ac6ef7e295968e508522884609fbf84>`__
* pylibacl: `fixed <https://github.com/iustin/pylibacl/commit/26712b8fd92f1146102248cac1c92cb344620eff>`_
* gobject-introspection: `fix adding Py_SET_TYPE() macro
  <https://gitlab.gnome.org/GNOME/gobject-introspection/-/commit/c4d7d21a2ad838077c6310532fdf7505321f0ae7>`__

Extensions still not fixed
--------------------------

* pyside2:

  * My patch is not merged upstream yet
  * https://bugreports.qt.io/browse/PYSIDE-1436
  * https://src.fedoraproject.org/rpms/python-pyside2/pull-request/7
  * https://bugzilla.redhat.com/show_bug.cgi?id=1898974
  * https://bugzilla.redhat.com/show_bug.cgi?id=1902618

* pybluez: `closed PR (not merged)
  <https://github.com/pybluez/pybluez/pull/371>`_
* PyPAM
* pygobject3
* rdiff-backup

What's Next?
============

* Convert again Py_TYPE() and Py_SIZE() macros to static inline functions.
* Add "%T" formatter for ``Py_TYPE(obj)->tp_name``:
  see `rejected bpo-34595 <https://bugs.python.org/issue34595>`_.
* Modify Cython to use getter functions.
* Attempt to make some structures opaque, like PyThreadState.
