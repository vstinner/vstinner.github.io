Macros converted to functions, static inline functions or regular functions, in
the Python C API.

Python 3.12
===========

Converted 28 macros to static inline functions:

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
* ``_PyObject_SIZE()``
* ``_PyObject_VAR_SIZE()``

Python 3.11
===========

Convert 35 macros to static inline functions:

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
* ``PyUnicode_1BYTE_DATA()``
* ``PyUnicode_2BYTE_DATA()``
* ``PyUnicode_4BYTE_DATA()``
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
* ``Py_SIZE()``: ``Py_SET_SIZE()`` must be used instead
* ``Py_TYPE()``: ``Py_SET_TYPE()`` must be used instead
* ``_PyUnicode_COMPACT_DATA()``
* ``_PyUnicode_NONCOMPACT_DATA()``

Convert 2 macros to regular functions:

* ``Py_GETENV()``
* ``PyType_SUPPORTS_WEAKREFS()``

Remove 5 macros:

* ``PyHeapType_GET_MEMBERS()``: moved to the internal C API
* ``Py_FORCE_DOUBLE()``
* ``Py_OVERFLOWED()``
* ``Py_SET_ERANGE_IF_OVERFLOW()``
* ``Py_SET_ERRNO_ON_MATH_ERROR()``

Add ``_Py_RVALUE()`` to 7 macros to prevent using them as l-value:

* ``_PyGCHead_SET_FINALIZED()``
* ``_PyGCHead_SET_NEXT()``
* ``asdl_seq_GET()``
* ``asdl_seq_GET_UNTYPED()``
* ``asdl_seq_LEN()``
* ``asdl_seq_SET()``
* ``asdl_seq_SET_UNTYPED()``

``PyCell_SET()`` was modified to use ``_Py_RVALUE()``, but it already used
``(void)`` in Python 3.10.

Python 3.10
===========

Convert 2 macros to static inline functions:

* ``PyObject_TypeCheck()``
* ``Py_REFCNT()``: ``Py_SET_REFCNT()`` must be used

Convert 3 macros to regular functions:

* ``PyDescr_IsData()``
* ``PyExceptionClass_Name()``
* ``PyIter_Check()``

Remove 4 macros:

* ``PyAST_Compile()``
* ``PyParser_SimpleParseFile()``
* ``PyParser_SimpleParseString()``
* ``PySTEntry_Check()``: removed to the internal C API

Add ``(void)`` to 2 macros to prevent using them as l-value:

* ``PyCell_SET()``
* ``PyList_SET_ITEM()``
* ``PyTuple_SET_ITEM()``

Python 3.9
==========

Convert 6 macros to static inline functions:

* ``PyType_Check()``
* ``PyType_CheckExact()``
* ``PyType_HasFeature()``
* ``Py_EnterRecursiveCall()``
* ``Py_UNICODE_COPY()``
* ``Py_UNICODE_FILL()``

Convert 4 macros to regular functions:

* ``PyIndex_Check()``
* ``PyObject_CheckBuffer()``
* ``PyObject_GET_WEAKREFS_LISTPTR()``
* ``PyObject_IS_GC()``

Remove 2 macros:

* ``PyDoc_STRVAR_shared()``: moved to the internal C API
* ``Py_UNICODE_MATCH()``

Python 3.8
==========

Convert 6 macros to static inline functions:

* ``Py_DECREF()``
* ``Py_INCREF()``
* ``Py_XDECREF()``
* ``Py_XINCREF()``
* ``_Py_ForgetReference()``
* ``_Py_NewReference()``
