+++++++++++++++++++++++++
Python 3.10 C API Changes
+++++++++++++++++++++++++

:date: 2021-03-26 12:00
:tags: c-api, cpython
:category: cpython
:slug: python310-c-api-changes
:authors: Victor Stinner

This article is about changes on the Python C API between Python 3.6 and Python
3.10. Most changes are driven by my `PEP 620 "Hide implementation details from
the C API" <https://www.python.org/dev/peps/pep-0620/>`_.


pythoncapi_compat
=================

In 2020, I created the `pythoncapi_compat project
<https://github.com/pythoncapi/pythoncapi_compat>`_ to add Python 3.10 support
to C extensions without losing support for Python 2.7. The project is made of
two parts:

* ``pythoncapi_compat.h``: Header file providing new functions of the Python C
  API to old Python versions.
* ``upgrade_pythoncapi.py``: Script upgrading C extension modules to newer
  Python API without losing support for old Python versions. It relies on
  ``pythoncapi_compat.h``.

The ``pythoncapi_compat.h`` header provides new functions to old Python
versions as static inline functions. Example::

    // bpo-39573 added Py_SET_REFCNT() to Python 3.9.0a4
    #if PY_VERSION_HEX < 0x030900A4 && !defined(Py_SET_REFCNT)
    static inline void _Py_SET_REFCNT(PyObject *ob, Py_ssize_t refcnt)
    {
        ob->ob_refcnt = refcnt;
    }
    #define Py_SET_REFCNT(ob, refcnt) _Py_SET_REFCNT(_PyObject_CAST(ob), refcnt)
    #endif

For example, ``upgrade_pythoncapi.py`` replaces ``Py_REFCNT(obj) = refcnt;``
with ``Py_SET_REFCNT(obj, refcnt);``.

I succeeded to use the ``pythoncapi_compat.h`` header file in 4 projects:
bitarray, immutables, mercurial and python-zstandard.

The recommanded way to use the ``pythoncapi_compat.h`` header file is to copy
it into your project. There is no need to update your copy, until you need new
functions.

Backward compatibility
----------------------

* pythoncapi_compat.h defines private _Py_StealRef() and _Py_XStealRef() static
  inline functions which are used for "Borrow" variants of functions, like
  ``_PyFrame_GetCodeBorrow()``.
* See also rejected idea: [C API] Add _Py_Borrow() private function: call Py_XDECREF() and return the object
  https://bugs.python.org/issue42522

Example::

    static inline PyCodeObject*
    _PyFrame_GetCodeBorrow(PyFrameObject *frame)
    {
        return (PyCodeObject *)_Py_StealRef(PyFrame_GetCode(frame));
    }

PyFrame_GetCode() is provided by Python on Python 3.9 and newer. On Python 3.8
and older, it is implemented in pythoncapi_compat.h as::

    static inline PyCodeObject*
    PyFrame_GetCode(PyFrameObject *frame)
    {
        return (PyCodeObject*)Py_NewRef(frame->f_code);
    }

The ``upgrade_pythoncapi.py`` script replaces ``frame->f_code`` pattern with
``_PyFrame_GetCodeBorrow(frame)``.

Thanks for "Borrow" suffix in function names, it becomes easier to discover
the usage of borrowed references. ``_PyFrame_GetCodeBorrow()`` can be replaced
with ``PyFrame_GetCode()`` but it requires to explicitly delete the created
strong reference (add ``Py_DECREF()``).

Don't access structure members
==============================

The C API currently exposes most object structures and so built C extensions
directly access structures. The stable ABI solved this issue by not exposing
structures into its limited C API. The idea is to bend the C API towards the
stable ABI.

Once most structures will be opaque, it will be possible to experiment
optimizations which require deep structures changes without breaking C
extensions.

Opaque structures
-----------------

* Python 3.8 made PyInterpreterState opaque
* Python 3.9 made PyGC_Head opaque

Add getter functions to Python 3.9
----------------------------------

* PyObject, PyVarObject:

  * Py_SET_REFCNT()
  * Py_SET_TYPE()
  * Py_SET_SIZE()
  * Py_IS_TYPE()

* PyFrameObject:

  * PyFrame_GetCode()
  * PyFrame_GetBack()

* PyThreadState:

  * PyThreadState_GetInterpreter()
  * PyThreadState_GetFrame()
  * PyThreadState_GetID()

* PyInterpreterState:

  * PyInterpreterState_Get()

Later, PyInterpreterState_Get() may be optimized to become faster than
``PyThreadState_GetInterpreter(PyThreadState_Get())``, it is also shorter to
write :-)

Convert macros to static inline functions in Python 3.8
-------------------------------------------------------

* Py_INCREF(), Py_DECREF()
* Py_XINCREF(), Py_XDECREF()
* PyObject_INIT(), PyObject_INIT_VAR()
* _PyObject_GC_TRACK(), _PyObject_GC_UNTRACK(), _Py_Dealloc()

Since ``Py_INCREF()`` is criticial for general Python performance, the impact
of the change was analyzed in depth before being merged in `bpo-35059
<https://bugs.python.org/issue35059>`_. The usage of
``__attribute__((always_inline))`` and ``__forceinline`` to force inlining was
rejected.

One nice side effect of converting macros to static inline functions is that
debuggers and profilers are able to retrieve the name of the function.

Convert macros to regular functions in Python 3.9
-------------------------------------------------

* PyIndex_Check()
* PyObject_CheckBuffer()
* PyObject_GET_WEAKREFS_LISTPTR()
* PyObject_IS_GC()
* PyObject_NEW(): alias to PyObject_New()
* PyObject_NEW_VAR(): alias to PyObjectVar_New()

PyType_HasFeature() was modified to always call PyType_GetFlags() function,
rather than accessing directly ``PyTypeObject.tp_flags``. The problem is that
on macOS, Python is not built with LTO and so the PyType_GetFlags() call is not
inlined, making functions like tuplegetter_descr_get() slower: see
`bpo-39542 <https://bugs.python.org/issue39542#msg372962>`_
and `bpo-41181
<https://bugs.python.org/issue41181>`_. The PyType_HasFeature() change was
reverted until the PEP 620 is accepted. macOS does not use LTO to keep support
support for macOS 10.6 (Snow Leopard).

To keep best performances on Python not built with LTO, fast private variants
were added as static inline functions in the internal C API:

* _PyIndex_Check()
* _PyObject_IS_GC()
* _PyType_HasFeature()
* _PyType_IS_GC()

Python 3.10 incompatible C API changes
--------------------------------------

The ``Py_REFCNT()`` macro was converted to a static inline function:
``Py_REFCNT(obj) = refcnt;`` now fails with a compiler error.  The
``upgrade_pythoncapi.py`` script of pythoncapi_compat automatically replaces
the ``Py_REFCNT(obj) = refcnt;`` pattern with ``Py_SET_REFCNT(obj, refcnt)``.

The ``Py_TYPE()`` and ``Py_SIZE()`` macros were also converted to static inline
functions, but it broke too many C extensions and so has been reverted.

Borrowed references
===================

New Python 3.10 functions
-------------------------

* PyModule_AddObjectRef()
* Py_NewRef(), Py_XNewRef()

While ``ref = Py_NewRef(obj)`` is similar to ``Py_INCREF(obj); ref = obj;``,
it is more convenient since it can be used as an expression, like ``return
Py_NewRef(obj);``. Previously, the magic C syntax ``expr1, expr2`` was
used to work around this limitation. For example::

    #define Py_RETURN_NONE return Py_INCREF(Py_None), Py_None

was replaced with::

    #define Py_RETURN_NONE return Py_NewRef(Py_None)

**In terms of semantics**, Py_NewRef() makes it explicit
that it creates a new strong reference. ``Py_INCREF(obj);`` converts a borrowed
reference to a strong reference in-place, but ``Py_INCREF(obj); ref = obj;`` is
unclear: what is the new strong reference, *obj* or *ref*?

This subtle difference can become a bug when a C extensions is converted to
HPy: see `HPy Handles documentation
<https://docs.hpyproject.org/en/latest/api.html#handles>`_ which explains the
HPy_Close() issue.

Enhance documentation
---------------------

* Define `borrowed reference
  <https://docs.python.org/dev/glossary.html#term-borrowed-reference>`_
  and `strong reference
  <https://docs.python.org/dev/glossary.html#term-strong-reference>`_
  terms
* Rephrase the `Reference Counting
  <https://docs.python.org/dev/c-api/refcounting.html#reference-counting>`_
  documentation to clarify the relationship between borrowed and strong
  references. Examples:

  * Py_NewRef(): **Create** a new strong reference to an object.
  * Py_INCREF(): **Convert** a borrowed reference to a strong reference in-place.
  * Py_DECREF(): **Delete** a strong reference before exiting its scope.

* Rephrase `PyWeakref_GetObject
  <https://docs.python.org/dev/c-api/weakref.html#c.PyWeakref_GetObject>`_ note
  to clarify when the object can be destroyed (change in bold):

    This function returns a borrowed reference to the referenced object. This
    means that you should always call ``Py_INCREF()`` on the object except when
    it **cannot be destroyed before the last usage of the borrowed reference**.

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


Process to deprecate
====================

* Add Py_DEPRECATED()
* Implement Py_DEPRECATED() for MSC
* The PEP 387 was updated to require deprecation during two Python releases,
  since the PEP 602 made the Python release shorter (12 months rather than
  18 months).
* The PEP 620 defines a `Process to reduce the number of broken C extensions
  <https://www.python.org/dev/peps/pep-0620/#process-to-reduce-the-number-of-broken-c-extensions>`_
  when introducing incompatible C API changes on purpose.
* Check PyPI top 4000 packages:

  * INADA Naoki wrote a recipe to download the source code of the top 4000 PyPI projects
    and then search for a regular expression in all sources:
    https://github.com/methane/notes/tree/master/2020/wchar-cache
  * `JSON file to the top 4000 PyPI Packages
    <https://hugovk.github.io/top-pypi-packages/>`_

* Fedora "continuous integration": Python packages of Fedora rebuilt with
  Python 3.10. Broken packages are reported to upstream projects, sometimes
  with fixes.

What's Next?
============

* Convert again Py_TYPE() and Py_SIZE() macros to static inline functions.
* Make upgrade_pythoncapi.py more popular! Try it on numpy. Maybe move the
  GitHub project under the PSF organization.
* Add "%T" formatter for Py_TYPE(obj)->tp_name:
  see `rejected bpo-34595 <https://bugs.python.org/issue34595>`_
* Avoid ``PyObject**`` type, direct access into an array of ``PyObject*``:

  * Deprecate PySequence_Fast_ITEMS()
  * Disallow ``&PyTuple_GET_ITEM(0)``: convert ``PyTuple_GET_ITEM()`` macro
    to static inline function:
    `bpo-41078 <https://bugs.python.org/issue41078>`_.
  * https://www.python.org/dev/peps/pep-0620/#avoid-functions-returning-pyobject
  * https://mail.python.org/archives/list/python-dev@python.org/thread/632CV42376SWVYAZTHG4ROOV2HRHOVZ7/

* Avoid funtions giving a direct access into object data with no API to signal
  when the resource can be released.

  * Issue for moving GC
  * Pin memory or copy memory, unpin or freed the copy when the resource is
    released
  * PyBytes_GetString()
  * Py_buffer with PyBuffer_Release() API notifies Python when the resource is
    no longer needed.

* Modify Cython to use getter functions. Attempt to make some structures
  opaque, like PyThreadState.

* `PEP 620 -- Hide implementation details from the C API
  <https://www.python.org/dev/peps/pep-0620/>`_ by Victor Stinner

See also the draft `PEP 652 -- Maintaining the Stable ABI
<https://www.python.org/dev/peps/pep-0652/>`_ by Petr Viktorin.
