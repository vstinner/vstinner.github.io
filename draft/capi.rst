+++++++++++++++++++++++
Update the Python C API
+++++++++++++++++++++++

Big tasks:

* Reorganize header files
* Don't access structure members
* Process to introduce incompatible C API changes
* Make the C API smaller
* Guidelines to prevent flaws in new C APIs

Python 3.9:

* Add Py_SET_REFCNT(), Py_SET_TYPE(), Py_SET_SIZE()
* Add Py_IS_TYPE()
* Add PyModule_AddType()
* PyFrameObject:

  * PyFrame_GetCode()
  * PyFrame_GetBack()

* PyThreadState:

  * PyThreadState_GetInterpreter()
  * PyThreadState_GetFrame()
  * PyThreadState_GetID()

* PyInterpreterState:

  * PyInterpreterState_Get()

Python 3.10:

* Py_REFCNT() becomes a static inline function: ``Py_REFCNT(obj) = refcnt;``
  becomes illegal.
* Add Py_NewRef() and Py_XNewRef()
* Add PyModule_AddObjectRef()

Enhance documentation:

* Define `borrowed reference
  <https://docs.python.org/dev/glossary.html#term-borrowed-reference>`_
  and `strong reference
  <https://docs.python.org/dev/glossary.html#term-strong-reference>`_
  terms
* Rephrase the `Reference Counting
  <https://docs.python.org/dev/c-api/refcounting.html#reference-counting>`_
  documentation to clarify the relationship between borrowed and strong
  references. Examples:

  * Py_NewRef(): "Create a new strong reference to an object"
  * Py_INCREF(): "convert a borrowed reference to a strong reference in-place"
  * Py_DECREF(): "delete a strong reference before exiting its scope"

* Rephrase `PyWeakref_GetObject
  <https://docs.python.org/dev/c-api/weakref.html#c.PyWeakref_GetObject>`_ note
  to clarify when the object can be destroyed:

    This function returns a borrowed reference to the referenced object. This
    means that you should always call ``Py_INCREF()`` on the object except when
    it **cannot be destroyed before the last usage of the borrowed reference**.

Rejected idea:

[C API] Add _Py_Borrow() private function: call Py_XDECREF() and return the object
https://bugs.python.org/issue42522

pythoncapi_compat.h defines private _Py_StealRef() and _Py_XStealRef() static
inline functions which are used for "Borrow" variants of functions, like
``_PyFrame_GetCodeBorrow()``.

TODO:

* "%T" formatter for Py_TYPE(obj)->tp_name
* Guidelines to avoid PyBytes_GetString(): Py_buffer with PyBuffer_Release()
  API notifies Python when the resource is no longer needed.
