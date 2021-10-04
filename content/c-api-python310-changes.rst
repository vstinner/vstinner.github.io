++++++++++++++++++++++++++++++++++++++++
C API changes between Python 3.5 to 3.10
++++++++++++++++++++++++++++++++++++++++

:date: 2021-10-04 15:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-python3_10-changes
:authors: Victor Stinner

.. image:: {static}/images/homer_hiding.webp
   :alt: Homer Simpson hiding

I'm trying to enhance and to fix the Python C API for 5 years. My first goal
was to shrink the C API without breaking third party C extensions. I hid many
private functions from the public functions: I moved them to the "internal C
API". I also deprecated and removed many functions.

Between Python 3.5 and 3.10, 80 symbols have been removed. Python 3.10 is the
first Python version exporting less symbols than its previous version!

Since Python 3.8, the C API is organized as 3 parts:

1. ``Include/`` directory: Limited API
2. ``Include/cpython/`` directory: CPython implementation details
3. ``Include/internal/`` directory: The internal API

The devguide `Changing Python’s C API <https://devguide.python.org/c-api/>`_
documentation now gives guidelines for C API additions, like avoiding borrowed
references.

The limited C API got a few more functions, whereas broken and private
functions have been removed. The Stable ABI is now explicitly defined and
documented in the `C API Stability
<https://docs.python.org/dev/c-api/stable.html#stable>`_ page.

This article lists all C API changes, not only the ones done by me.

Shrink the the C API
====================

Between Python 3.5 and 3.10, 80 symbols (functions or variables) have been
removed, 3 structures have been removed, and 21 functions have been deprecated.
In meanwhile, other symbols have been added to implement new Python features at
each Python version.

Python 3.10 is the first Python version exporting less symbols than its
previous version.

Python 3.6
----------

Deprecate 4 functions:

* ``PyUnicode_AsDecodedObject()``
* ``PyUnicode_AsDecodedUnicode()``
* ``PyUnicode_AsEncodedObject()``
* ``PyUnicode_AsEncodedUnicode()``

Python 3.7
----------

* Deprecate ``PyOS_AfterFork()``
* Remove ``PyExc_RecursionErrorInst`` singleton (also removed in Python 3.6.4).

Python 3.8
----------

Remove 3 functions:

* ``PyByteArray_Init()``
* ``PyByteArray_Fini()``
* ``PyEval_ReInitThreads()``

Remove 1 structure:

* ``PyInterpreterState`` (moved to the internal C API)

Python 3.9
----------

Remove 32 symbols:

* ``PyAsyncGen_ClearFreeLists()``
* ``PyCFunction_ClearFreeList()``
* ``PyCmpWrapper_Type``
* ``PyContext_ClearFreeList()``
* ``PyDict_ClearFreeList()``
* ``PyFloat_ClearFreeList()``
* ``PyFrame_ClearFreeList()``
* ``PyFrame_ExtendStack()``
* ``PyList_ClearFreeList()``
* ``PyMethod_ClearFreeList()``
* ``PyNoArgsFunction type``
* ``PyNullImporter_Type``
* ``PySet_ClearFreeList()``
* ``PySortWrapper_Type``
* ``PyTuple_ClearFreeList()``
* ``PyUnicode_ClearFreeList()``
* ``Py_UNICODE_MATCH()``
* ``_PyAIterWrapper_Type``
* ``_PyBytes_InsertThousandsGrouping()``
* ``_PyBytes_InsertThousandsGroupingLocale()``
* ``_PyDebug_PrintTotalRefs()``
* ``_PyFloat_Digits()``
* ``_PyFloat_DigitsInit()``
* ``_PyFloat_Repr()``
* ``_PyThreadState_GetFrame()`` (and ``_PyRuntime.getframe``)
* ``_PyUnicode_ClearStaticStrings()``
* ``_Py_AddToAllObjects()``
* ``_Py_InitializeFromArgs()``
* ``_Py_InitializeFromWideArgs()``
* ``_Py_PrintReferenceAddresses()``
* ``_Py_PrintReferences()``
* ``_Py_tracemalloc_config``

Remove 1 structure:

* ``PyGC_Head`` (moved to the internal C API)

Deprecate 15 functions:

* ``PyEval_CallFunction()``
* ``PyEval_CallMethod()``
* ``PyEval_CallObject()``
* ``PyEval_CallObjectWithKeywords()``
* ``PyNode_Compile()``
* ``PyParser_SimpleParseFileFlags()``
* ``PyParser_SimpleParseStringFlags()``
* ``PyParser_SimpleParseStringFlagsFilename()``
* ``PyUnicode_AsUnicode()``
* ``PyUnicode_AsUnicodeAndSize()``
* ``PyUnicode_FromUnicode()``
* ``PyUnicode_WSTR_LENGTH()``
* ``Py_UNICODE_COPY()``
* ``Py_UNICODE_FILL()``
* ``_PyUnicode_AsUnicode()``

Python 3.10
-----------

Remove 44 symbols:

* ``PyAST_Compile()``
* ``PyAST_CompileEx()``
* ``PyAST_CompileObject()``
* ``PyAST_Validate()``
* ``PyArena_AddPyObject()``
* ``PyArena_Free()``
* ``PyArena_Malloc()``
* ``PyArena_New()``
* ``PyFuture_FromAST()``
* ``PyFuture_FromASTObject()``
* ``PyLong_FromUnicode()``
* ``PyNode_Compile()``
* ``PyOS_InitInterrupts()``
* ``PyObject_AsCharBuffer()``
* ``PyObject_AsReadBuffer()``
* ``PyObject_AsWriteBuffer()``
* ``PyObject_CheckReadBuffer()``
* ``PyParser_ASTFromFile()``
* ``PyParser_ASTFromFileObject()``
* ``PyParser_ASTFromFilename()``
* ``PyParser_ASTFromString()``
* ``PyParser_ASTFromStringObject()``
* ``PyParser_SimpleParseFileFlags()``
* ``PyParser_SimpleParseStringFlags()``
* ``PyParser_SimpleParseStringFlagsFilename()``
* ``PyST_GetScope()``
* ``PySymtable_Build()``
* ``PySymtable_BuildObject()``
* ``PySymtable_Free()``
* ``PyUnicode_AsUnicodeCopy()``
* ``PyUnicode_GetMax()``
* ``Py_ALLOW_RECURSION``
* ``Py_END_ALLOW_RECURSION``
* ``Py_SymtableString()``
* ``Py_SymtableStringObject()``
* ``Py_UNICODE_strcat()``
* ``Py_UNICODE_strchr()``
* ``Py_UNICODE_strcmp()``
* ``Py_UNICODE_strcpy()``
* ``Py_UNICODE_strlen()``
* ``Py_UNICODE_strncmp()``
* ``Py_UNICODE_strncpy()``
* ``Py_UNICODE_strrchr()``
* ``_Py_CheckRecursionLimit``

Remove 1 structure:

* ``_PyUnicode_Name_CAPI``

Deprecate 1 function:

* ``PyUnicode_InternImmortal()``

Moreover, ``PyUnicode_FromStringAndSize(NULL, size)`` and
``PyUnicode_FromUnicode(NULL, size)`` have been deprecated.

Statistics
----------

Public Python symbols exported with ``PyAPI_FUNC()`` and ``PyAPI_DATA()``:

=======  ===========
Python   Symbols
=======  ===========
2.7      891
3.6      1041 (+150)
3.7      1068 (+27)
3.8      1105 (+37)
3.9      1115 (+10)
3.10     1080 (-35)
=======  ===========

Command used to count public symbols::

    grep -E 'PyAPI_(FUNC|DATA)' Include/*.h Include/cpython/*.h|grep -v ' _Py'|wc -l


Reorganize header files
=======================

Since Python 3.8, the C API is organized as 3 parts:

1. ``Include/`` directory: Limited API
2. ``Include/cpython/`` directory: CPython implementation details
3. ``Include/internal/`` directory: The internal API

The intent is to help developers to think about if their additions must be part
of the limited C API, the CPython C API or the internal C API.

Python 3.7
----------

Creation on the ``Include/internal/`` directory.

Python 3.8
----------

Creation on the ``Include/cpython/`` directory.

Python 3.10
-----------

Move 8 header files from ``Include/`` to ``Include/cpython/``:

* ``odictobject.h``
* ``parser_interface.h``
* ``picklebufobject.h``
* ``pyarena.h``
* ``pyctype.h``
* ``pydebug.h``
* ``pyfpe.h``
* ``pytime.h``

Python 3.10 added a `Include/README.rst documentation
<https://github.com/python/cpython/blob/master/Include/README.rst>`_ to explain
this organization and give guidelines for adding new functions. For example,
new functions in the public C API must not steal references nor return borrowed
references. In the meanwhile, this documentation moved to the devguide:
`Changing Python’s C API <https://devguide.python.org/c-api/>`_.

Statistics
----------

Number of C API line numbers per Python version:

=======  ==============  ===========  ============  =======
Python   Limited API     CPython API  Internal API  Total
=======  ==============  ===========  ============  =======
2.7      12,686 (100%)   0            0             12,686
3.6      16,011 (100%)   0            0             16,011
3.7      16,517 (96%)    0            705 (4%)      17,222
3.8      13,160 (70%)    3,417 (18%)  2,230 (12%)   18,807
3.9      12,264 (62%)    4,343 (22%)  3,066 (16%)   19,673
3.10     10,305 (52%)    4,513 (23%)  5,092 (26%)   19,910
=======  ==============  ===========  ============  =======

Commands:

* Limited: ``wc -l Include/*.h``
* CPython: ``wc -l Include/cpython/*.h``
* Internal: ``wc -l Include/internal/*.h``


Changes in the Limited C API
============================

Between Python 3.8 and 3.10, 4 new functions have been and 14 symbols
(functions or variables) have been removed from the limited C API.

The trashcan API was excluded from the limited C API since it never worked.
The implementation accessed directly PyThreadState members, whereas this
structure is opaque in the limited C API.

On the other side, Py_EnterRecursiveCall() and Py_LeaveRecursiveCall()
functions have been added to the limited C API. In Python 3.8, they were
defined as macros accessing directly PyThreadState members. In Python 3.9, they
became opaque function calls and so are now compatible with the stable ABI.

Python 3.9
----------

Add 3 functions to the limited C API:

* ``Py_EnterRecursiveCall()``
* ``Py_LeaveRecursiveCall()``
* ``PyFrame_GetLineNumber()``

Remove 14 symbols from the limited C API:

* ``PyFPE_START_PROTECT()``
* ``PyFPE_END_PROTECT()``
* ``PyThreadState_DeleteCurrent()``
* ``PyTrash_UNWIND_LEVEL``
* ``Py_TRASHCAN_BEGIN``
* ``Py_TRASHCAN_BEGIN_CONDITION``
* ``Py_TRASHCAN_END``
* ``Py_TRASHCAN_SAFE_BEGIN``
* ``Py_TRASHCAN_SAFE_END``
* ``_PyTraceMalloc_NewReference()``
* ``_Py_CheckRecursionLimit``
* ``_Py_GetRefTotal()``
* ``_Py_NewReference()``
* ``_Py_ForgetReference()``

Python 3.10
-----------

Add 1 function to the limited C API:

* ``PyUnicode_AsUTF8AndSize()``

PEP 652: Maintaining the Stable ABI
===================================

Petr Viktorin wrote and implemented the `PEP 652: Maintaining the Stable ABI
<https://www.python.org/dev/peps/pep-0652/>`_ in Python 3.10.

The Stable ABI (Application Binary Interface) for extension modules or
embedding Python is now explicitly defined. The `C API Stability
<https://docs.python.org/dev/c-api/stable.html#stable>`_ documentation
describes C API and ABI stability guarantees along with best practices for
using the Stable ABI.
