++++++++++++++++++++++++++++++++++++++++++++++
Python C API: Add functions to access PyObject
++++++++++++++++++++++++++++++++++++++++++++++

:date: 2021-10-05 14:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-abstract-pyobject
:authors: Victor Stinner

``PyObject``.
Prepare the API for an ABI which would not leak implementation details.

Issue created
=============

2020-02-06:
https://bugs.python.org/issue39573#msg361513

Add
===

* Add Py_SET_REFCNT()
* Add Py_SET_TYPE()
* Add Py_SET_SIZE()
* Add Py_IS_TYPE()

Replace
=======

* Replace ``obj->ob_type`` with ``Py_TYPE(obj)``
* Replace ``Py_SIZE(obj) = size;`` with ``Py_SET_SIZE(obj, size);``
* Replace ``Py_TYPE(obj) = type`` with ``Py_IS_TYPE(obj, type)``

Change::

    -#define PyMethod_Check(op) (Py_TYPE(op)== &PyMethod_Type)
    +#define PyMethod_Check(op) Py_IS_TYPE(op, &PyMethod_Type)

In Python 3.10, performance critical functions like Py_INCREF() or Py_TYPE()
are implemented as static inline functions.

Static inline functions
=======================

* Convert Py_TYPE() to a static inline function: ``Py_TYPE(obj) = type``
  becomes a compiler error
* Convert Py_REFCNT() and Py_SIZE() macros to static inline functions

The Py_TYPE() and Py_SIZE() changes broke many C extensions:

* Cython
* numpy
* immutables
* pycurl
* breezy
* PyPAM
* bitarray
* boost
* duplicity
* gobject-introspection
* mercurial
* pybluez
* pygobject3
* pylibacl
* pyside2
* rdiff-backup

Update: https://bugs.python.org/issue39573#msg401378

Revert 1
========

2020-11-18:
https://bugs.python.org/issue39573#msg381345

Revert 2
========

2021-06-06:
https://bugs.python.org/issue39573#msg395205

test_exceptions.

Attempt 3
=========

https://bugs.python.org/issue39573#msg401365



pythoncapi_compat
=================

pythoncapi_compat.h header file has been created to provide new functions to
Python 3.6: https://github.com/pythoncapi/pythoncapi_compat

* Py_SET_REFCNT()
* Py_SET_TYPE()
* Py_SET_SIZE()
* Py_IS_TYPE()

Script has been created to upgrade C extensions to add support for Python 3.10
without losing support for old Python versions:
https://github.com/pythoncapi/pythoncapi_compat

PEP 620
=======

PEP 620 "Hide implementation details from the C API" written

Issue closed
============

2021-09-08:
https://bugs.python.org/issue39573#msg401399
