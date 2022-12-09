C++
===

* Add test_cppext
* Add _Py_NULL
* Add and use _Py_CAST()
* Add _Py_STATIC_CAST()
* Many variants like _PyObject_CAST(), all bases on _Py_CAST()
* Attempt for avoid old-style C cast in _Py_CAST()
* Test C++11
* Enhance test suite to also test C++14
* Fix for C++03: xxx
* Add C++ support to pythoncapi_compat.h

ISO C89 compatibility
=====================

Some projects still build the Python C API in strict ISO C89: variables
must be declared at the top of static inline functions. That's weird: C89
didn't support static inline functions.

Limited C API
=============

Don't cast the argument to ``PyObject*``.

Type punning issue in Py_CLEAR()
================================

* Add temporary variables to only evaluate macro arguments once
* These variables need to cast arguments to PyObject*
* Casting a pointer from another type to PyObject* causes type punning issue
* With strict aliasing, which is the default in C compilers, Python is
  miscompiled with the type punning issue.
* History

  * Commit with the type punning issue
  * Commit to revert
  * Commit fixing again the macro, now using __typeof__() of memcpy()

* The limited C API doesn't include <string.h>: need to add _Py_Clear().

const PyObject*
===============

Remove _PyObject_CAST_CONST() and _PyVarObject_CAST_CONST() in Python 3.10.



PEP 674, Py_TYPE() and Py_SIZE()
================================

* Py_TYPE() and Py_SIZE() changed
* Too many affected projects: reverted
* Py_TYPE() and Py_SIZE() changed again
* Buildbot failure: revert
* test_exceptions fixed on the Windows Debug build
* Py_TYPE() and Py_SIZE() changed again for the 3rd time
* PEP 670 written
* l-value in PEP 670 was unclear
* PEP 670 restricted to macros which cannot be used as l-value
* Write PEP 674
* SC gives an exception for Py_TYPE()
* SC rejects PEP 674: require a slow migration over 5 years

Affected projects
=================

See PEP 674.

Most projects updated between 2020 and 2022.

Creation of the pythoncapi-compat project to provide Py_SET_TYPE() and
Py_SET_SIZE() to old Python projects.

More readable
=============

* PyWeakref_GET_OBJECT

Misc
====

* ``PyUnicode_KIND()`` was not converted: signness issue.
* Add assertions.
* Add variables to only evalute an expression once.
* Not converted:

  * PyTuple_GET_ITEM()
  * PyList_GET_ITEM()
  * ``PyDescr_NAME()``, ``PyDescr_TYPE()``:
    see `bpo-46538 <https://bugs.python.org/issue46538>`_
