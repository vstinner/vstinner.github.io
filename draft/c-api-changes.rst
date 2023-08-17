Examples of Python 3.7-3.13 changes done incrementally
======================================================

Move private and internal API to the internal C API
---------------------------------------------------

In Python 3.7, a new ``Include/internal/`` directory was created for the
"internal C API". Between Python 3.7 and 3.13, more and more private
functions are moved to the internal C API: each release moves a bunch of
private functions there.

The internal C API can be used by third party projects, but it requires
to define a specific ``Py_BUILD_CORE`` macro and multiple header files
should be included.

Moreover, more and more internal C API symbols are no longer exported
and so cannot be used by third party projects. Debuggers and profilers
can use internal C API structures to inspect Python internal state
without modifying this state nor having to call functions.

Make PyGC_Head structure opaque
-------------------------------

In Python 3.9 (2020), see `issue GH-84422
<https://github.com/python/cpython/issues/84422>`_ and `commit
<https://github.com/python/cpython/commit/0135598d729d01f35ce08d47160adaa095a6149f>`__.

No project was affected by this change.

`Issue GH-83780 <https://github.com/python/cpython/issues/83780>`_:
ABI breakage between Python 3.7.4 and 3.7.5: change in PyGC_Head structure.

Deprecate and remove functions
------------------------------

See `C API changes between Python 3.5 to 3.10
<https://vstinner.github.io/c-api-python3_10-changes.html>`_ (2021) by
Victor Stinner.

Prepare making PyObject structure opaque
----------------------------------------

See `issue GH-83754 <https://github.com/python/cpython/issues/83754>`_.
Avoid accessing directly PyObject members in the public C API. Add
Py_IS_TYPE() function.

Disallow using macros as l-value
--------------------------------

Py_REFCNT(), Py_TYPE() and Py_SIZE() macros can no longer be used as
l-value to set an object reference count, type or size:

* ``Py_SET_REFCNT()``, ``Py_SET_TYPE()`` and ``Py_SET_SIZE()`` were
  added to Python 3.9.
* ``Py_REFCNT()`` macro was `converted to a static inline function
  <https://github.com/python/cpython/commit/fe2978b3b940fe2478335e3a2ca5ad22338cdf9c>`_
  in Python 3.10: cannot be used as l-value to set the reference count
  anymore.
* ``Py_TYPE()`` and ``Py_SIZE()`` macros was converted to static inline
  functions in a similar way in Python 3.11. This change was first done
  in May 2020, but had to be reverted in November. Most affected
  projects were updated before the `change was done again
  <https://github.com/python/cpython/commit/cb15afcccffc6c42cbfb7456ce8db89cd2f77512>`_
  in September 2021.  See `PEP 674: Py_TYPE() and Py_SIZE() macros
  <https://peps.python.org/pep-0674/#py-type-and-py-size-macros>`_.

Py_TYPE() got a steering council exception, whereas Py_SIZE() didn't and
PEP 674 got rejected. Sadly, nobody reminded to revert Py_SIZE() change
(done before PEP 674 was written and then rejected) and so it landed in
Python 3.11.

Most affected projects use the pythoncapi-project to get new "SET"
functions on Python 3.8 and older.

Prepare making PyTypeObject structure opaque
--------------------------------------------

Python 3.9 (2020), avoid accessing PyTypeObject members in the public
C API:

* `issue GH-84351 <https://github.com/python/cpython/issues/84351>`_

Prepare making PyTheaadState structure opaque
---------------------------------------------

See `issue GH-84128 <https://github.com/python/cpython/issues/84128>`_

Python 3.9: add getter functions:

* PyThreadState_GetFrame()
* PyThreadState_GetID()
* PyThreadState_GetInterpreter()

Python 3.11:

* PyThreadState_EnterTracing()
* PyThreadState_LeaveTracing()

Convert macros to functions
---------------------------

Convert macros to static inline functions.

Implemented in Python 3.11 and 3.12, see
`PEP 670 – Convert macros to functions in the Python C API
<https://peps.python.org/pep-0670/>`_
and
`Convert macros to functions <https://vstinner.github.io/c-api-convert-macros-functions.html>`_.

Work started in Python 3.8:

* Py_INCREF(), Py_XINCREF()
* Py_DECREF(), Py_XDECREF()
* PyObject_INIT(), PyObject_INIT_VAR()
* _PyObject_GC_TRACK(), _PyObject_GC_UNTRACK(), _Py_Dealloc()

Python 3.9:

* PyIndex_Check()
* PyObject_CheckBuffer()
* PyObject_GET_WEAKREFS_LISTPTR()
* PyObject_IS_GC()
* PyObject_NEW(): alias to PyObject_New()
* PyObject_NEW_VAR(): alias to PyObjectVar_New()

Move PyInterpreterState to the internal C API
---------------------------------------------

Remove PyInterpreterState members from the public C API in Python 3.8.
See `issue bpo-35886 <https://bugs.python.org/issue35886>`_.

Borrowed references
-------------------

* Python 3.10:

  * Add ``Py_NewRef()`` and ``Py_XNewRef()``
  * Add `borrowed reference
    <https://docs.python.org/dev/glossary.html#term-borrowed-reference>`_
    and `strong reference
    <https://docs.python.org/dev/glossary.html#term-strong-reference>`_
    to the documentation glossary.
  * Add ``PyModule_AddObjectRef()``

* Python 3.13

  * Add ``PyDict_GetItemRef()``, ``PyWeakref_GetRef()``,
    ``PyImport_AddModuleRef()``.

In 2021, adding PyTuple_GetItemRef() got rejected:
`issue GH-86460 <https://github.com/python/cpython/issues/86460>`_

Move PyFrameObject to the internal C API
-----------------------------------------

Remove PyFrameObject members from the public C API in Python 3.11
alpha6:
see `issue GH-90992 <https://github.com/python/cpython/issues/90992>`_
and `commit <https://github.com/python/cpython/commit/18b5dd68c6b616257ae243c0b6bb965ffc885a23>`__

The change affected Cython, greenlet and gevent which were quickly
upgraded.

Helper functions were added for this change in Python 3.11:

* PyFrame_GetBuiltins()
* PyFrame_GetGenerator()
* PyFrame_GetGlobals()
* PyFrame_GetLasti()
* PyFrame_GetLocals()

The change was prepared in Python 3.9 by adding two getter functions:

* PyFrame_GetBack()
* PyFrame_GetCode()
* Moreover, PyFrame_GetLineNumber() was moved to the limited C API

In Python 3.12, new helper functions were added:

* PyFrame_GetVar()
* PyFrame_GetVarString()
