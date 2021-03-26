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

Rationale
---------

The C API currently exposes most object structures, C extensions indirectly
access structures through the API, but can also access them directly. It causes
different issues:

* Modifying a structure can break an unknown number of C extensions. To prevent
  any risk, developers avoid modifying structures, whereas many optimizations
  would benefit of the ability to modify structures.

* Once most structures will be opaque, it will be possible to experiment
  optimizations which require deep structures changes without breaking C
  extensions. The irony is that we first have to break C extensions and the
  backward compatibility for that.

* Any structure change breaks the ABI. The stable ABI solved this issue by not
  exposing structures into its limited C API. The idea is to bend the default C
  API towards the limited C API to provide a stable ABI for everyone in the
  long term.

Issues
------

* `PyObject: bpo-39573 <https://bugs.python.org/issue39573>`_
* `PyTypeObject: bpo-40170 <https://bugs.python.org/issue40170>`_
* `PyThreadState: bpo-39947 <https://bugs.python.org/issue39947>`_
* `PyFrameObject: bpo-40421 <https://bugs.python.org/issue40421>`_

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

PyInterpreterState_Get() can be used to replace ``PyThreadState_Get()->interp``
or ``PyThreadState_GetInterpreter(PyThreadState_Get())``.

Convert macros to static inline functions in Python 3.8
-------------------------------------------------------

* Py_INCREF(), Py_XINCREF()
* Py_DECREF(), Py_XDECREF()
* PyObject_INIT(), PyObject_INIT_VAR()
* _PyObject_GC_TRACK(), _PyObject_GC_UNTRACK(), _Py_Dealloc()

Since ``Py_INCREF()`` is criticial for general Python performance, the impact
of the change was analyzed in depth before being merged in `bpo-35059
<https://bugs.python.org/issue35059>`_. The usage of
``__attribute__((always_inline))`` and ``__forceinline`` to force inlining was
rejected.

Old Py_INCREF() implementation in Python 3.7::

    #define Py_INCREF(op) (                         \
        _Py_INC_REFTOTAL  _Py_REF_DEBUG_COMMA       \
        ((PyObject *)(op))->ob_refcnt++)

where ``_Py_INC_REFTOTAL _Py_REF_DEBUG_COMMA`` becomes ``_Py_RefTotal++,`` if
the ``Py_REF_DEBUG`` macro is defined, or nothing otherwise. Current
Py_INCREF() implementation in Python 3.10::

    static inline void _Py_INCREF(PyObject *op)
    {
    #ifdef Py_REF_DEBUG
        _Py_RefTotal++;
    #endif
        op->ob_refcnt++;
    }
    #define Py_INCREF(op) _Py_INCREF(_PyObject_CAST(op))

Most static inline functions go through a macro to cast their argument to
``PyObject*`` using the macro::

    #define _PyObject_CAST(op) ((PyObject*)(op))

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
on macOS, Python is built without LTO and so the PyType_GetFlags() call is not
inlined, making functions like tuplegetter_descr_get() slower: see
`bpo-39542 <https://bugs.python.org/issue39542#msg372962>`_
and `bpo-41181
<https://bugs.python.org/issue41181>`_. The PyType_HasFeature() change was
reverted until the PEP 620 is accepted. macOS does not use LTO to keep support
support for macOS 10.6 (Snow Leopard).

To keep best performances on Python built without LTO, fast private variants
were added as static inline functions in the internal C API:

* _PyIndex_Check()
* _PyObject_IS_GC()
* _PyType_HasFeature()
* _PyType_IS_GC()

For example, PyObject_IS_GC() is defined as a function, whereas
_PyObject_IS_GC() is defined as an internal static inline function. Header
code::

    /* Test if an object implements the garbage collector protocol */
    PyAPI_FUNC(int) PyObject_IS_GC(PyObject *obj);

    // Fast inlined version of PyObject_IS_GC()
    static inline int _PyObject_IS_GC(PyObject *obj)
    {
        return (PyType_IS_GC(Py_TYPE(obj))
                && (Py_TYPE(obj)->tp_is_gc == NULL
                    || Py_TYPE(obj)->tp_is_gc(obj)));
    }

In the C code, the function simply calls the internal static inline function::

    int
    PyObject_IS_GC(PyObject *obj)
    {
        return _PyObject_IS_GC(obj);
    }


Python 3.10 incompatible C API change
-------------------------------------

The ``Py_REFCNT()`` macro was converted to a static inline function:
``Py_REFCNT(obj) = refcnt;`` now fails with a compiler error.  The
``upgrade_pythoncapi.py`` script of pythoncapi_compat automatically replaces
the ``Py_REFCNT(obj) = refcnt;`` pattern with ``Py_SET_REFCNT(obj, refcnt)``.

Reverted Python 3.10 Py_TYPE() and Py_SIZE() changes
----------------------------------------------------

The ``Py_TYPE()`` and ``Py_SIZE()`` macros were also converted to static inline
functions, but the change `broke 17 C extensions
<https://bugs.python.org/issue39573#msg370303>`_.

I fixed 6 extensions:

* Cython: `my fix adds __Pyx_SET_SIZE() and __Pyx_SET_REFCNT()
  <https://github.com/cython/cython/commit/d8e93b332fe7d15459433ea74cd29178c03186bd>`_
* immutables: `issue <https://github.com/MagicStack/immutables/issues/46>`_
  fixed by `my commit adding pythoncapi_compat.h to get Py_SET_SIZE()
  <https://github.com/MagicStack/immutables/commit/45105ecd8b56a4d88dbcb380fcb8ff4b9cc7b19c>`_
  (`PR 52 <https://github.com/MagicStack/immutables/pull/52>`_)
* breezy: `my fix adding Py_SET_REFCNT() macro
  <https://bazaar.launchpad.net/~brz/brz/3.1/revision/7647>`__
* bitarray: `my fix adding pythoncapi_compat.h
  <https://github.com/ilanschnell/bitarray/commit/a0cca9f2986ec796df74ca8f42aff56c4c7103ba>`_
* python-zstandard: `my fix adding pythoncapi_compat.h
  <https://github.com/indygreg/python-zstandard/commit/e5a3baf61b65f3075f250f504ddad9f8612bfedf>`__
  followed by `a pythoncapi_compat.h update for Python 2.7
  <https://github.com/indygreg/python-zstandard/commit/477776e6019478ca1c0b5777b073afbec70975f5>`_
* mercurial: `my fix adding pythoncapi_compat.h
  <https://www.mercurial-scm.org/repo/hg/rev/e92ca942ddca>`__
  followed by a `fix for Python 2.7
  <https://www.mercurial-scm.org/repo/hg/rev/38b9a63d3a13>`_
  (then `fixed into upstream pythoncapi_compat.h
  <https://github.com/pythoncapi/pythoncapi_compat/commit/3e0bde93954ea8df328d36900c7060a3f3433eb0>`_)

Extensions fixed by others:

* numpy: `fix defining Py_SET_TYPE() and Py_SET_SIZE() on Python 3.8 and older
  <https://github.com/numpy/numpy/commit/a96b18e3d4d11be31a321999cda4b795ea9eccaa>`_,
  followed by a `cleanup commit
  <https://github.com/numpy/numpy/commit/f1671076c80bd972421751f2d48186ee9ac808aaz>`_
* pycurl: `fix defining Py_SET_TYPE() on Python 3.8 and older
  <https://github.com/pycurl/pycurl/commit/e633f9a1ac4df5e249e78c218d5fbbd848219042>`_
* boost: `fix adding Py_SET_TYPE() and Py_SET_SIZE() macros
  <https://github.com/boostorg/python/commit/500194edb7833d0627ce7a2595fec49d0aae2484#diff-b06ac66c98951b48056826c904be75263cdf56ec9b79d3274ea493e7d27cbac4>`_
* duplicity:
  `fix 1 <https://git.launchpad.net/duplicity/commit/?id=9c63dcb83e922e0afac206188203891e203b4e66>`__,
  `fix 2 <https://git.launchpad.net/duplicity/commit/?id=bbaae91b5ac6ef7e295968e508522884609fbf84>`__
* pylibacl: `fixed <https://github.com/iustin/pylibacl/commit/26712b8fd92f1146102248cac1c92cb344620eff>`_
* gobject-introspection: `fix adding Py_SET_TYPE() macro
  <https://gitlab.gnome.org/GNOME/gobject-introspection/-/commit/c4d7d21a2ad838077c6310532fdf7505321f0ae7>`__

Extensions not fixed:

* pyside2:

  * My patch is not merged upstream yet
  * https://bugreports.qt.io/browse/PYSIDE-1436
  * https://src.fedoraproject.org/rpms/python-pyside2/pull-request/7
  * https://bugzilla.redhat.com/show_bug.cgi?id=1898974
  * https://bugzilla.redhat.com/show_bug.cgi?id=1902618

* pybluez: `closed PR <https://github.com/pybluez/pybluez/pull/371>`_
* PyPAM
* pygobject3
* rdiff-backup

Since the change broke too many C extensions, I `converted Py_TYPE() and
Py_SIZE() back to macros
<https://github.com/python/cpython/commit/0e2ac21dd4960574e89561243763eabba685296a>`_
to have more time to fix fix C extensions.


Borrowed references
===================

In a Python implementations not implemented with reference counting, like PyPy,
emulating borrowed references is inefficient and so borrowed references should
be avoided in the public C API.

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
  terms in the glossary.
* Rephrase the `Reference Counting
  <https://docs.python.org/dev/c-api/refcounting.html#reference-counting>`_
  documentation to clarify the relationship between borrowed and strong
  references. Examples:

  * Py_NewRef(): **Create** a new strong reference to an object.
  * Py_INCREF(): **Convert** a borrowed reference to a strong reference
    **in-place**.
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
