+++++++++++++++++++++++++++++++++
Fixing the C API may be a deadend
+++++++++++++++++++++++++++++++++

I tried different paths and many look like deadends:

* Add PyTuple_GetItemRef():
  https://github.com/python/cpython/issues/86460
  Problem: xxx
* Make PyObject opaque:
  https://github.com/python/cpython/issues/83754
  Problem: sizeof(PyObject) is used in the API.
  Problem: members are accessed directly.
* Make PyTypeObject opaque
  https://github.com/python/cpython/issues/84351 closed
  https://github.com/python/cpython/issues/105970 open
* Avoid borrowed references: Py_TYPE() case
  https://bugs.python.org/issue34595
  Rejected.
* Complex stable ABI issues.

  * The garbage collector doesn't take in account that objects of heap
    allocated types hold a strong reference to their type
    https://bugs.python.org/issue40217
  * PyEval_AcquireLock(): We cannot just remove functions from stable ABI.
    https://bugs.python.org/issue39998

* Private functions are not really private.
  _PyInterpreterState_GetEvalFrameFunc()
  _PyInterpreterState_SetEvalFrameFunc()
  PEP xxx
  https://bugs.python.org/issue46850
  SC: https://mail.python.org/archives/list/python-dev@python.org/message/GFOMU7LP63JUVFMWNJNZJLUMZDRPTUYJ/

* Py_REFCNT, Py_TYPE, Py_SIZE

  * Revert 1
  * Revert 2
  * Revert 3
  * PEP 674 rejected
  * But Py_TYPE accepted by the SC 2022
  * But Py_SIZE forgot to be reverted and so landed in Python 3.11

* Remove _Py_NewReference()
  https://github.com/python/cpython/issues/85161
  https://mail.python.org/archives/list/capi-sig@python.org/thread/4EOCN7P4HI56GQ74FY3TMIKDBIPGKL2G/
  Problem: I failed to find time to design a public C API to replace it

* PyDescr_NAME() and PyDescr_TYPE() used as l-value by SWIG
  https://bugs.python.org/issue46538
  Since making PyDescrObject opaque is not really worth it, I close this issue.

* [C API] Convert PyTuple_GET_ITEM() macro to a static inline function
  https://bugs.python.org/issue41078

* [C API] Add _Py_Borrow() private function: call Py_XDECREF() and return the object
  https://bugs.python.org/issue42522

* [C API] Rename private structs to use names closer to types
  https://bugs.python.org/issue35333
