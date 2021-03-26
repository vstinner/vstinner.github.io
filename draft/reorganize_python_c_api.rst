+++++++++++++++++++++++++++
Reorganize the Python C API
+++++++++++++++++++++++++++

:date: 2021-03-26 12:00
:tags: c-api, cpython
:category: cpython
:slug: reorganize-python-c-api
:authors: Victor Stinner

Reorganize the C API
====================

Python 3.7
----------

Creation on the ``Internal/internal/`` directory.

Python 3.8
----------

Move PyInterpreterState structure to the internal C API.

Python 3.9
----------

Moved to the internal C API:

* PyGC_Head structure
* _PyDebug_PrintTotalRefs()
* _Py_AddToAllObjects()
* _Py_PrintReferenceAddresses()
* _Py_PrintReferences()
* _Py_tracemalloc_config

Python 3.10
-----------

Move header files from ``Include/`` to ``Include/cpython/``:

* odictobject.h
* parser_interface.h
* picklebufobject.h
* pyarena.h
* pyctype.h
* pydebug.h
* pyfpe.h
* pytime.h

Include/README.rst
------------------

The new `Include/README.rst documentation
<https://github.com/python/cpython/blob/master/Include/README.rst>`_ explains
the 3 C API and sets guidelines for adding new functions. For example, new
functions in the public C API must not steal references nor return borrowed
references.

Statistics
----------

Number of C API line numbers per Python version:

=======  =============  ===========  ============  =======
Python   Public         CPython      Internal      Total
=======  =============  ===========  ============  =======
2.7      12686 (100%)   0            0             12686
3.6      16011 (100%)   0            0             16011
3.7      16517 (96%)    0            705 (4%)      17222
3.8      13160 (70%)    3417 (18%)   2230 (12%)    18807
3.9      12264 (62%)    4343 (22%)   3066 (16%)    19673
3.10     10305 (52%)    4513 (23%)   5092 (26%)    19910
=======  =============  ===========  ============  =======

Fix the Limited C API
=====================

Python 3.9
----------

Add:

* Py_EnterRecursiveCall(), Py_LeaveRecursiveCall()
* PyFrame_GetLineNumber()

Remove:

* PyFPE_START_PROTECT(), PyFPE_END_PROTECT()
* PyThreadState_DeleteCurrent()
* PyTrash_UNWIND_LEVEL
* Py_TRASHCAN_BEGIN, Py_TRASHCAN_BEGIN_CONDITION, Py_TRASHCAN_END
* Py_TRASHCAN_SAFE_BEGIN, Py_TRASHCAN_SAFE_END
* _PyTraceMalloc_NewReference()
* _Py_CheckRecursionLimit
* _Py_GetRefTotal()
* _Py_NewReference(), _Py_ForgetReference()

The trashcan mechanism never worked in the limited C API.

Python 3.10
-----------

* Add PyUnicode_AsUTF8AndSize()

Remove functions
================

Python 3.6
----------

Deprecate 4 functions:

* PyUnicode_AsDecodedObject()
* PyUnicode_AsDecodedUnicode()
* PyUnicode_AsEncodedObject()
* PyUnicode_AsEncodedUnicode()

Python 3.7
----------

* Deprecate PyOS_AfterFork()
* Remove PyExc_RecursionErrorInst singleton (also removed in Python 3.6.4).

Python 3.8
----------

Remove 3 functions:

* PyByteArray_Init()
* PyByteArray_Fini()
* PyEval_ReInitThreads()

Python 3.9
----------

Remove 27 symbols:

* PyAsyncGen_ClearFreeLists()
* PyCFunction_ClearFreeList()
* PyCmpWrapper_Type
* PyContext_ClearFreeList()
* PyDict_ClearFreeList()
* PyFloat_ClearFreeList()
* PyFrame_ClearFreeList()
* PyFrame_ExtendStack()
* PyList_ClearFreeList()
* PyMethod_ClearFreeList()
* PyNoArgsFunction type
* PyNullImporter_Type
* PySet_ClearFreeList()
* PySortWrapper_Type
* PyTuple_ClearFreeList()
* PyUnicode_ClearFreeList()
* Py_UNICODE_MATCH()
* _PyAIterWrapper_Type
* _PyBytes_InsertThousandsGrouping()
* _PyBytes_InsertThousandsGroupingLocale()
* _PyFloat_Digits()
* _PyFloat_DigitsInit()
* _PyFloat_Repr()
* _PyThreadState_GetFrame() and _PyRuntime.getframe
* _PyUnicode_ClearStaticStrings()
* _Py_InitializeFromArgs()
* _Py_InitializeFromWideArgs()

Deprecate 15 functions:

* PyEval_CallFunction()
* PyEval_CallMethod()
* PyEval_CallObject()
* PyEval_CallObjectWithKeywords()
* PyNode_Compile()
* PyParser_SimpleParseFileFlags()
* PyParser_SimpleParseStringFlags()
* PyParser_SimpleParseStringFlagsFilename()
* PyUnicode_AsUnicode()
* PyUnicode_AsUnicodeAndSize()
* PyUnicode_FromUnicode()
* PyUnicode_WSTR_LENGTH()
* Py_UNICODE_COPY()
* Py_UNICODE_FILL()
* _PyUnicode_AsUnicode()

Python 3.10
-----------

Remove 42 symbols:

* PyAST_Compile()
* PyAST_CompileEx()
* PyAST_CompileObject()
* PyAST_Validate()
* PyArena_AddPyObject()
* PyArena_Free()
* PyArena_Malloc()
* PyArena_New()
* PyFuture_FromAST()
* PyFuture_FromASTObject()
* PyLong_FromUnicode()
* PyNode_Compile()
* PyOS_InitInterrupts()
* PyObject_AsCharBuffer()
* PyObject_AsReadBuffer()
* PyObject_AsWriteBuffer()
* PyObject_CheckReadBuffer()
* PyParser_ASTFromFile()
* PyParser_ASTFromFileObject()
* PyParser_ASTFromFilename()
* PyParser_ASTFromString()
* PyParser_ASTFromStringObject()
* PyParser_SimpleParseFileFlags()
* PyParser_SimpleParseStringFlags()
* PyParser_SimpleParseStringFlagsFilename()
* PyST_GetScope()
* PySymtable_Build()
* PySymtable_BuildObject()
* PySymtable_Free()
* PyUnicode_AsUnicodeCopy()
* PyUnicode_GetMax()
* Py_ALLOW_RECURSION, Py_END_ALLOW_RECURSION
* Py_SymtableString()
* Py_SymtableStringObject()
* Py_UNICODE_strcat()
* Py_UNICODE_strchr(), Py_UNICODE_strrchr()
* Py_UNICODE_strcmp()
* Py_UNICODE_strcpy(), Py_UNICODE_strncpy()
* Py_UNICODE_strlen()
* Py_UNICODE_strncmp()
* _PyUnicode_Name_CAPI structure
* _Py_CheckRecursionLimit

Deprecate 3 functions:

* PyUnicode_FromUnicode(NULL, size)
* PyUnicode_FromStringAndSize(NULL, size)
* PyUnicode_InternImmortal()

Statistics
----------

Symbols exported with PyAPI_FUNC() and PyAPI_DATA():

=======  ===========
Python   Symbols
=======  ===========
2.7      1098
3.6      1460
3.7      1547 (+87)
3.8      1561 (+14)
3.9      1552 (-9)
3.10     1495 (-57)
=======  ===========

