++++++++++++++++++++++++++++++++++++++++
Convert Python C API macros to functions
++++++++++++++++++++++++++++++++++++++++

:date: 2022-12-12 23:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-convert-macros-functions
:authors: Victor Stinner

.. image:: {static}/images/loeil_cyclone.jpg
   :alt: L'oeil du cyclone - Théo Grosjean
   :target: https://www.exemplaire-editions.fr/librairie/livre/loeil-du-cyclone

Macros converted to functions, static inline functions or regular functions, in
the Python C API.

Converting macros to functions
==============================

Between 2018 (Python 3.7) and 2022 (Python 3.12), I made many changes on macros
on the Python C API to make the API less error prone (avoid macro pitfalls) and
better define the API: parameter types and return types, variable scope, etc.
`PEP 670 <https://peps.python.org/pep-0670/>`_ "Convert macros to functions in
the Python C API" describes the rationale for these changes in length.

To reduce the size of the C API, I moved many private functions to the internal
C API.

Some changes are also related to preparing the API to make members of
structures like ``PyObject`` or ``PyTypeObject`` private.

Converting macros and static inline functions to regular functions hide
implementation details and moves the whole API closer to the stable ABI (build
a C extension once, use the binary on multiple Python versions). Regular
functions are usable in programming languages and use cases which cannot use C
macros and C static inline functions.

Most macros are converted to static inline functions, rather regular functions,
to have no impact on performance.

This work was made incrementally in 5 Python versions (3.8, 3.9, 3.10, 3.11 and
3.12) to limit the number of impacted projects at each Python release.

Changing ``Py_TYPE()`` and ``Py_SIZE()`` macros impacted most projects. Python
3.11 contains the change. During Python 3.10 development cycle, the change has
to be reverted since it impacted too many projects.

Statistics
==========

Statistics on public functions:

* Python 3.7: 893 regular functions, 315 macros.
* Python 3.12: 943 regular functions, 246 macros, 69 static inline functions.

Cumulative changes on macros between Python 3.7 and Python 3.12 on public,
private and internal APIs:

* Converted 88 macros to static inline functions
* Converted 11 macros to regular functions
* Converted 3 static inline functions to regular functions:
* Removed 47 macros

See `Statistics on the Python C API
<https://pythoncapi.readthedocs.io/stats.html>`_ for more numbers.

Python 3.12
===========

Converted 39 macros to static inline functions:

* ``PyCell_GET()``
* ``PyCell_SET()``
* ``PyCode_GetNumFree()``
* ``PyDict_GET_SIZE()``
* ``PyFloat_AS_DOUBLE()``
* ``PyFunction_GET_ANNOTATIONS()``
* ``PyFunction_GET_CLOSURE()``
* ``PyFunction_GET_CODE()``
* ``PyFunction_GET_DEFAULTS()``
* ``PyFunction_GET_GLOBALS()``
* ``PyFunction_GET_KW_DEFAULTS()``
* ``PyFunction_GET_MODULE()``
* ``PyInstanceMethod_GET_FUNCTION()``
* ``PyMemoryView_GET_BASE()``
* ``PyMemoryView_GET_BUFFER()``
* ``PyMethod_GET_FUNCTION()``
* ``PyMethod_GET_SELF()``
* ``PySet_GET_SIZE()``
* ``Py_UNICODE_HIGH_SURROGATE()``
* ``Py_UNICODE_ISALNUM()``
* ``Py_UNICODE_ISSPACE()``
* ``Py_UNICODE_IS_HIGH_SURROGATE()``
* ``Py_UNICODE_IS_LOW_SURROGATE()``
* ``Py_UNICODE_IS_SURROGATE()``
* ``Py_UNICODE_JOIN_SURROGATES()``
* ``Py_UNICODE_LOW_SURROGATE()``
* ``_PyGCHead_FINALIZED()``
* ``_PyGCHead_NEXT()``
* ``_PyGCHead_PREV()``
* ``_PyGCHead_SET_FINALIZED()``
* ``_PyGCHead_SET_NEXT()``
* ``_PyGCHead_SET_PREV()``
* ``_PyGC_FINALIZED()``
* ``_PyGC_SET_FINALIZED()``
* ``_PyObject_GC_IS_TRACKED()``
* ``_PyObject_GC_MAY_BE_TRACKED()``
* ``_PyObject_SIZE()``
* ``_PyObject_VAR_SIZE()``
* ``_Py_AS_GC()``

Remove 5 macros:

* ``PyUnicode_AS_DATA()``
* ``PyUnicode_AS_UNICODE()``
* ``PyUnicode_GET_DATA_SIZE()``
* ``PyUnicode_GET_SIZE()``
* ``PyUnicode_WSTR_LENGTH()``

The following 4 macros can still be used as l-values in Python 3.12:

* ``PyList_GET_ITEM()``
* ``PyTuple_GET_ITEM()``:
* ``PyDescr_NAME()``
* ``PyDescr_TYPE()``

Code like ``&PyTuple_GET_ITEM(tuple, 0)`` is still commonly used to get a
direct access to items as ``PyObject**``. ``PyDescr_NAME()`` and
``PyDescr_TYPE()`` are used by SWIG: see
`<https://bugs.python.org/issue46538>`_

Python 3.11
===========

Convert 33 macros to static inline functions:

* ``PyByteArray_AS_STRING()``
* ``PyByteArray_GET_SIZE()``
* ``PyBytes_AS_STRING()``
* ``PyBytes_GET_SIZE()``
* ``PyCFunction_GET_CLASS()``
* ``PyCFunction_GET_FLAGS()``
* ``PyCFunction_GET_FUNCTION()``
* ``PyCFunction_GET_SELF()``
* ``PyList_GET_SIZE()``
* ``PyList_SET_ITEM()``
* ``PyTuple_GET_SIZE()``
* ``PyTuple_SET_ITEM()``
* ``PyUnicode_AS_DATA()``
* ``PyUnicode_AS_UNICODE()``
* ``PyUnicode_CHECK_INTERNED()``
* ``PyUnicode_DATA()``
* ``PyUnicode_GET_DATA_SIZE()``
* ``PyUnicode_GET_LENGTH()``
* ``PyUnicode_GET_SIZE()``
* ``PyUnicode_IS_ASCII()``
* ``PyUnicode_IS_COMPACT()``
* ``PyUnicode_IS_COMPACT_ASCII()``
* ``PyUnicode_IS_READY()``
* ``PyUnicode_MAX_CHAR_VALUE()``
* ``PyUnicode_READ()``
* ``PyUnicode_READY()``
* ``PyUnicode_READ_CHAR()``
* ``PyUnicode_WRITE()``
* ``PyWeakref_GET_OBJECT()``
* ``Py_SIZE()``: ``Py_SET_SIZE()`` must be used to set an object size
* ``Py_TYPE()``: ``Py_SET_TYPE()`` must be used to set an object type
* ``_PyUnicode_COMPACT_DATA()``
* ``_PyUnicode_NONCOMPACT_DATA()``

Convert 2 macros to regular functions:

* ``PyType_SUPPORTS_WEAKREFS()``
* ``Py_GETENV()``

Remove 11 macros:

* Moved to the internal C API:

  * ``PyHeapType_GET_MEMBERS()``: renamed to ``_PyHeapType_GET_MEMBERS()``
  * ``_Py_InIntegralTypeRange()``
  * ``_Py_IntegralTypeMax()``
  * ``_Py_IntegralTypeMin()``
  * ``_Py_IntegralTypeSigned()``

* ``PyFunction_AS_FRAME_CONSTRUCTOR()``
* ``Py_FORCE_DOUBLE()``
* ``Py_OVERFLOWED()``
* ``Py_SET_ERANGE_IF_OVERFLOW()``
* ``Py_SET_ERRNO_ON_MATH_ERROR()``
* ``_Py_SET_EDOM_FOR_NAN()``

Add ``_Py_RVALUE()`` to 7 macros to disallow using them as l-value:

* ``_PyGCHead_SET_FINALIZED()``
* ``_PyGCHead_SET_NEXT()``
* ``asdl_seq_GET()``
* ``asdl_seq_GET_UNTYPED()``
* ``asdl_seq_LEN()``
* ``asdl_seq_SET()``
* ``asdl_seq_SET_UNTYPED()``

Note: the ``PyCell_SET()`` macro was modified to use ``_Py_RVALUE()``, but it
already used ``(void)`` in Python 3.10.

Python 3.10
===========

Convert 3 macros to regular functions:

* ``PyDescr_IsData()``
* ``PyExceptionClass_Name()``
* ``PyIter_Check()``

Convert 2 macros to static inline functions:

* ``PyObject_TypeCheck()``
* ``Py_REFCNT()``: ``Py_SET_REFCNT()`` must be used to set an object reference
  count

Remove 6 macros:

* ``PyAST_Compile()``
* ``PyParser_SimpleParseFile()``
* ``PyParser_SimpleParseString()``
* ``PySTEntry_Check()``: moved to the internal C API
* ``_PyErr_OCCURRED()``
* ``_PyList_ITEMS()``: moved to the internal C API

Modify 3 macros to disallow using them as l-values by adding ``(void)`` cast:

* ``PyCell_SET()``
* ``PyList_SET_ITEM()``
* ``PyTuple_SET_ITEM()``

Python 3.9
==========

Convert 6 macros to regular functions:

* ``PyIndex_Check()``
* ``PyObject_CheckBuffer()``
* ``PyObject_GET_WEAKREFS_LISTPTR()``
* ``PyObject_IS_GC()``
* ``Py_EnterRecursiveCall()``
* ``Py_LeaveRecursiveCall()``

Convert 5 macros to static inline functions:

* ``PyType_Check()``
* ``PyType_CheckExact()``
* ``PyType_HasFeature()``
* ``Py_UNICODE_COPY()``
* ``Py_UNICODE_FILL()``

Convert 3 static inline functions to regular functions:

* ``_Py_Dealloc()``
* ``_Py_ForgetReference()``
* ``_Py_NewReference()``

Remove 18 macros:

* Moved to the internal C API:

  * ``PyDoc_STRVAR_shared()``:
  * ``PyObject_GC_IS_TRACKED()``
  * ``PyObject_GC_MAY_BE_TRACKED()``
  * ``Py_AS_GC()``
  * ``_PyGCHead_FINALIZED()``
  * ``_PyGCHead_NEXT()``
  * ``_PyGCHead_PREV()``
  * ``_PyGCHead_SET_FINALIZED()``
  * ``_PyGCHead_SET_NEXT()``
  * ``_PyGCHead_SET_PREV()``
  * ``_PyGC_SET_FINALIZED()``

* ``Py_UNICODE_MATCH()``
* ``_Py_DEC_TPFREES()``
* ``_Py_INC_TPALLOCS()``
* ``_Py_INC_TPFREES()``
* ``_Py_MakeEndRecCheck()``
* ``_Py_MakeRecCheck()``
* ``_Py_RecursionLimitLowerWaterMark()``

Python 3.8
==========

Convert 9 macros to static inline functions:

* ``Py_DECREF()``
* ``Py_INCREF()``
* ``Py_XDECREF()``
* ``Py_XINCREF()``
* ``_PyObject_CallNoArg()``
* ``_PyObject_FastCall()``
* ``_Py_Dealloc()``
* ``_Py_ForgetReference()``
* ``_Py_NewReference()``

Remove 7 macros:

* ``_PyGCHead_DECREF()``
* ``_PyGCHead_REFS()``
* ``_PyGCHead_SET_REFS()``
* ``_PyGC_REFS()``
* ``_PyObject_GC_TRACK()``: moved to the internal C API
* ``_PyObject_GC_UNTRACK()``: moved to the internal C API
* ``_Py_CHECK_REFCNT()``
