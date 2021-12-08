My Contributions to the Python C API (Python 3.11)

xxx
===

* Identify bad C APIs: borrowed references, PyBytes_AS_STRING(), steal references
* Identify root motivations for introducing incompatible changes

  * Optimize Python
  * Support the C API on other Python implementations: PyPy, GraalPython
  * Stable ABI
  * Fix bugs

* Process to introduce C API incompatible changes

  * Code search: GitHub, grep.app, PyPI top 5000 projects
  * First, fix Cython and pybind11, then pip and numpy.
  * Rebuild Fedora with the next Python
  * pythonci project
  * PEP 620 section

* Add better functions which are less error prones
* Remove or changes functions leaking implementation details: fix the API

Code and documentation changes
==============================

* 2020-11-05: Add Py_NewRef() and Py_XNewRef()
  https://github.com/python/cpython/commit/53a03aafd5812018a3821a2e83063fd3d6cd2576
* 2020-11-09: Enhance reference counting documentation

  * https://github.com/python/cpython/commit/23c5f93b83f78f295313e137011edb18b24c37c2
  * https://docs.python.org/dev/glossary.html#term-strong-reference
  * https://docs.python.org/dev/glossary.html#term-borrowed-reference
  * https://docs.python.org/dev/c-api/refcounting.html#c.Py_INCREF
  * https://docs.python.org/dev/c-api/refcounting.html#c.Py_NewRef
  * https://docs.python.org/dev/c-api/refcounting.html#c.Py_DECREF
  * https://docs.python.org/dev/c-api/weakref.html#c.PyWeakref_GetObject

* Py_Is(), Py_IsNone(), Py_IsTrue(), Py_IsFalse()
  https://bugs.python.org/issue43753

* Add Py_SET_REFCNT(), Py_SET_TYPE(), Py_SET_SIZE()
* Add Py_IS_TYPE() by Dong-hee Na
  https://github.com/python/cpython/commit/d905df766c367c350f20c46ccd99d4da19ed57d8
* Python 3.10: Py_REFCNT() can no longer be used as l-value
* Python 3.11: Py_TYPE() and Py_SIZE() can no longer be used as l-value
* Add PyThreadState_EnterTracing() and PyThreadState_LeaveTracing()

Documents
=========

* 2017-07-11: python-dev: "PEP: Hide implementation details in the C API"
  https://mail.python.org/archives/list/python-ideas@python.org/thread/6XATDGWK4VBUQPRHCRLKQECTJIPBVNJQ/
* 2018-07-29: Create pythoncapi project: https://pythoncapi.readthedocs.io/
* 2018-09-04: Creation of CPython fork to experiment a new incompatible C API excluding borrowed references and not access directly structure members.
* 2019-02-22: [capi-sig] Update on CPython header files reorganization
  https://mail.python.org/archives/list/capi-sig@python.org/thread/WS6ATJWRUQZESGGYP3CCSVPF7OMPMNM6/
* 2020-04-10: python-dev: "PEP: Modify the C API to hide implementation details"
  https://mail.python.org/archives/list/python-dev@python.org/thread/HKM774XKU7DPJNLUTYHUB5U6VR6EQMJF/
* 2020-06-19: PEP 620: Hide implementation details from the C API
  https://www.python.org/dev/peps/pep-0620/
* 2020-12-08: pythoncapi: "Fix the Python C API to optimize Python" article
  https://github.com/pythoncapi/pythoncapi/blob/main/doc/optimize_python.rst
* 2020-11-09: bpo-42294: [C API] Add new C functions with more regular reference counting like PyTuple_GetItemRef()
  https://bugs.python.org/issue42294
  => REJECTED, but doc enhanced
* 2021-10-19: PEP 670: "Convert macros to functions in the Python C API"
  https://www.python.org/dev/peps/pep-0670/
* 2021-12-01: PEP 674: "Disallow using macros as l-value"
  https://www.python.org/dev/peps/pep-0674/
