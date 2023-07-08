++++++++++++++++++++++++++++++++++++++
My contributions to Python (July 2023)
++++++++++++++++++++++++++++++++++++++

:date: 2023-07-08 23:00
:tags: c-api, cpython
:category: cpython
:slug: contrib-python-july-2023
:authors: Victor Stinner

In 2023, between May 4 and July 8, I made 144 commits in the Python main
branch. Here I describe a few of the most important contributions that I made
to Python 3.12 and Python 3.13 in these months.

C API: Strong reference
=======================

When I `analyzed issues of Python C API
<https://pythoncapi.readthedocs.io/>`_., I quickly identified that the usage of
borrowed references is causing a lot of troubles. By the way, I recently
updated the `list of the 41 functions returning borrowed refererences
<https://pythoncapi.readthedocs.io/bad_api.html#functions>`_. This issue is
also tracked as `Returning borrowed references is fundamentally unsafe
<https://github.com/capi-workgroup/problems/issues/21>`_ in the recently
created `C API workgroup: problems
<https://github.com/capi-workgroup/problems/>`_ project.

In Python 3.10, I added ``Py_NewRef()`` and ``Py_XNewRef()`` functions which
have a better semantics: they create a new strong reference to a Python object.
I also added the ``PyModule_AddObjectRef()`` function, variant of
``PyModule_AddObject()``, which returns a strong reference.  And I added
`borrowed reference
<https://docs.python.org/dev/glossary.html#term-borrowed-reference>`_ and
`strong reference
<https://docs.python.org/dev/glossary.html#term-strong-reference>`_ to the
glossary.

In Python 3.13, I added two functions:

* ``PyImport_AddModuleRef()``: variant of ``PyImport_AddModule()``
* ``PyWeakref_GetRef()``: variant of ``PyWeakref_GetObject()``.
  By the way, I deprecated ``PyWeakref_GetObject()`` and
  ``PyWeakref_GET_OBJECT()`` functions.

``PyWeakref_GetRef()`` has an interesting API: ``int PyWeakref_GetRef(PyObject
*ref, PyObject **pobj)``. It returns ``-1`` on error, and only set ``*pobj`` on
success. If the reference is dead, ``*pobj`` is set to ``NULL``, whereas
``PyWeakref_GetObject()`` returns ``Py_None`` in this case.

I updated pythoncapi-compat to `provide these functions to Python 3.12 and
older
<https://pythoncapi-compat.readthedocs.io/en/latest/api.html#python-3-13>`_.

I also added ``Py_TYPE()`` to ``Doc/data/refcounts.dat``: file listing how C
functions handle references, it's maintained manually.

I also want to `add PyDict_GetItemRef()
<https://github.com/python/cpython/pull/106005>`_, but there is more friction
around this API.

C API: PyList_SET_ITEM()
========================

In Python 3.9, ``Include/cpython/listobject.h`` was created: API excluded from
the limited C API. ``PyList_SET_ITEM()`` was implemented as::

    #define PyList_SET_ITEM(op, i, v) (_PyList_CAST(op)->ob_item[i] = (v))

In Python 3.10, the `return value was removed to fix as bug
<https://github.com/python/cpython/issues/74644>`_::

    #define PyList_SET_ITEM(op, i, v) ((void)(_PyList_CAST(op)->ob_item[i] = (v)))

In Python 3.11, PEP 670 was accepted and I converted the macro to a static
inline function::

    static inline void
    PyList_SET_ITEM(PyObject *op, Py_ssize_t index, PyObject *value) {
        PyListObject *list = _PyList_CAST(op);
        list->ob_item[index] = value;
    }

I tried to add an assertion to check bounds of the index, but I got assertion
failures when running the Python test suite. Recently, I tried again and I
updated the PyStructSequence API to check the bounds differently. The tricky
part is that getting the number of fields of a PyStructSequence requires to get
an item of dictionary, and ``PyDict_GetItemWithError()`` can raise an
exception. Moreover, ``PyStructSequence_SET_ITEM()`` was still implemented as
a macro in Python 3.12::

    #define PyStructSequence_SET_ITEM(op, i, v) PyTuple_SET_ITEM((op), (i), (v))

Old PyStructSequence_SetItem() implementation::

    void
    PyStructSequence_SetItem(PyObject* op, Py_ssize_t i, PyObject* v)
    {
        PyStructSequence_SET_ITEM(op, i, v);
    }

New implementation::

    void
    PyStructSequence_SetItem(PyObject *op, Py_ssize_t index, PyObject *value)
    {
        PyTupleObject *tuple = _PyTuple_CAST(op);
        assert(0 <= index);
    #ifndef NDEBUG
        Py_ssize_t n_fields = REAL_SIZE(op);
        assert(n_fields >= 0);
        assert(index < n_fields);
    #endif
        tuple->ob_item[index] = value;
    }

The ``REAL_SIZE()`` macro is only available in ``Objects/structseq.c``.
Exposing it in the public C API would be a bad idea since it can fail.  So I
just converted PyStructSequence_SET_ITEM() macro to an alias to
PyStructSequence_SetItem()::

    #define PyStructSequence_SET_ITEM PyStructSequence_SetItem

This way, PyStructSequence_SET_ITEM() and PyStructSequence_SetItem() are
implemented as opaque function calls.

So it became possible to check bounds in PyList_SET_ITEM()::

    static inline void
    PyList_SET_ITEM(PyObject *op, Py_ssize_t index, PyObject *value) {
        PyListObject *list = _PyList_CAST(op);
        assert(0 <= index);
        assert(index < Py_SIZE(list));
        list->ob_item[index] = value;
    }

I had to modify code calling PyList_SET_ITEM() *before* setting the list size:
list_extend() and _PyList_AppendTakeRef() functions. The size is now set before
calling PyList_SET_ITEM().

I made a similar change to ``PyTuple_SET_ITEM()`` to also checks the index.

These bound checks are implemented with an assertion if Python is built in
debug mode or if Python is built with assertions.


C API: Python 3.12 Py_INCREF()
==============================

`PEP 683 – Immortal Objects, Using a Fixed Refcount
<https://peps.python.org/pep-0683/>`_ was accepted and implemented in Python
3.12. It made Py_INCREF() and Py_DECREF() static inline functions even more
complicated than before. The implementation required to expose private
``_Py_IncRefTotal_DO_NOT_USE_THIS()`` and ``_Py_DecRefTotal_DO_NOT_USE_THIS()``
functions in the stable ABI, whereas the function names say "DO NOT USE THIS".

In Python 3.10, I modified Py_INCREF() and Py_DECREF() to implement them as
opaque function calls in the limited C API version 3.10 or newer if Python is
built in debug mode (if ``Py_REF_DEBUG`` macro is defined). Thanks to this
change, the limited C API is now supported if Python is built in debug mode.

In Python 3.12, I modified Py_INCREF() and Py_DECREF() to implement them as
opaque function calls in any limited C API version, not only in the limited C
API version 3.10 and newer. This way, implementation details are now hidden and
no longer leaked in the stable ABI. I removed ``_Py_NegativeRefcount()`` in the
limited C API and I removed ``_Py_IncRefTotal_DO_NOT_USE_THIS()`` and
``_Py_DecRefTotal_DO_NOT_USE_THIS()`` in the stable ABI.

Later, I discovered that my fix broke backward compatibility with Python 3.9.
My implementation used ``_Py_IncRef()`` and ``_Py_DecRef()`` that I added to
Python 3.10. I updated the implementation to use ``Py_IncRef()`` and
``Py_DecRef()`` on Python 3.9 and older, these functions are available since
Python 2.4.

C API: Py_INCREF() opaque function call
=======================================

In Python 3.8, I converted Py_INCREF() and Py_DECREF() macros to static inline
functions. I already wanted to convert them as opaque function calls, but it
can have an important cost on performance and so I left them as static inline
functions.

As a follow-up of my Python 3.12 Py_INCREF() fix for the debug build, I
modified Py_INCREF() and Py_DECREF() to always implemented them as **opaque
function calls in the limited C API version 3.12** and newer.

* Discussion: `Limited C API: implement Py_INCREF() and Py_DECREF() as function calls
  <https://discuss.python.org/t/limited-c-api-implement-py-incref-and-py-decref-as-function-calls/27592>`_
* `Pull request <https://github.com/python/cpython/pull/105388>`_

For me, it's a **major enhancement** to make the stable ABI more **future
proof** by leaking less implementation details.


Tests
=====

The Python test runner *regrtest* has specific constraints because tests
are run in subprocesses, on different platforms, with custom encodings
and options. Over the last year, an annoying regrtest came and go: if
a subprocess standard output (stdout) cannot be decoded, the test is treated
as a success!

I fixed the bug and I made the code more reliable by marking this bug class as
"test failed".

I fixed test_counter_optimizer() of test_capi when run twice: create a new
function at each call, so each run starts in a known state. Previously, the
second run was in a different state since the function was already optimized.

I cleaned up old test_ctypes. My main goal was to remove ``from ctypes import
*`` to be able to use pyflakes on these tests. I found many skipped tests: I
reenabled 3 of them, and removed the other ones. I also removed dead code.

I removed test_xmlrpc_net: it was skipped since 2017. The public
``buildbot.python.org`` server has no XML-RPC interface anymore, and no
replacement public XML-RPC server was found in 6 years.

I fixed dangling threads in ``test_importlib.test_side_effect_import()``: the
import spawns threads, wait until they complete.


C API: Deprecate
================

* gh-105373: Doc lists pending C API removals (#106537)

* Deprecate the old Py_UNICODE and PY_UNICODE_TYPE types in the C API: use
  wchar_t instead. I modified Python code base to avoid this type as well: use
  "wchar_t" instead.

* Deprecate old Python initialization functions:

  * PySys_ResetWarnOptions()
  * Py_GetExecPrefix()
  * Py_GetPath()
  * Py_GetPrefix()
  * Py_GetProgramFullPath()
  * Py_GetProgramName()
  * Py_GetPythonHome()

* Deprecate PyImport_ImportModuleNoBlock() function.

* Deprecate Py_HasFileSystemDefaultEncoding.

The PyArg_Parse() function is no longer deprecated. In 2007, the deprecation
was added as a comment to the documentation, but the function remains relevant
in Python 3.13 for some specific use cases.


Soft Deprecation
================

I updated `PEP 387: Backwards Compatibility Policy
<https://peps.python.org/pep-0387/>`_ to add `Soft Deprecation <https://peps.python.org/pep-0387/#soft-deprecation>`_:

    A soft deprecation can be used when using an API which should no longer be
    used to write new code, but it remains safe to continue using it in
    existing code. The API remains documented and tested, but will not be
    developed further (no enhancement).

    The main difference between a “soft” and a (regular) “hard” deprecation is
    that the soft deprecation does not imply scheduling the removal of the
    deprecated API.

I converted optparse deprecation to a soft deprecation.

I soft deprecated the getopt module: it remains available and maintained,
but argparse should be preferred for new projects.


Deprecate
=========

I deprecated the ``getmark()``, ``setmark()`` and ``getmarkers()`` methods of
the Wave_read and Wave_write classes. These methods only existed for
compatibility with the aifc module, but they did nothing and the aifc module
was removed in Python 3.13.

I also deprecated ``SetPointerType()`` and ``ARRAY()`` functins of ctypes.


C API: Remove
=============

* I removed the following old functions to configure the Python initialization,
  that I deprecated in Python 3.11:

  * PySys_AddWarnOptionUnicode()
  * PySys_AddWarnOption()
  * PySys_AddXOption()
  * PySys_HasWarnOptions()
  * PySys_SetArgvEx()
  * PySys_SetArgv()
  * PySys_SetPath()
  * Py_SetPath()
  * Py_SetProgramName()
  * Py_SetPythonHome()
  * Py_SetStandardStreamEncoding()
  * _Py_SetProgramFullPath()

* I also deprecated removed "call" functions:

  * PyCFunction_Call()
  * PyEval_CallFunction()
  * PyEval_CallMethod()
  * PyEval_CallObject()
  * PyEval_CallObjectWithKeywords()

* I removed deprecated PyEval_AcquireLock() and PyEval_InitThreads() functions.

* Remove old aliases which were kept backwards compatibility with Python 3.8:

  * _PyObject_CallMethodNoArgs()
  * _PyObject_CallMethodOneArg()
  * _PyObject_CallOneArg()
  * _PyObject_FastCallDict()
  * _PyObject_Vectorcall()
  * _PyObject_VectorcallMethod()
  * _PyVectorcall_Function()

In `issue #106320 <https://github.com/python/cpython/issues/106320>`_, I removed
181 private C API functions:

* ``_PyArg_NoKwnames()``
* ``_PyBytesWriter_Alloc()``
* ``_PyBytesWriter_Dealloc()``
* ``_PyBytesWriter_Finish()``
* ``_PyBytesWriter_Init()``
* ``_PyBytesWriter_Prepare()``
* ``_PyBytesWriter_Resize()``
* ``_PyBytesWriter_WriteBytes()``
* ``_PyCodecInfo_GetIncrementalDecoder()``
* ``_PyCodecInfo_GetIncrementalEncoder()``
* ``_PyCodec_DecodeText()``
* ``_PyCodec_EncodeText()``
* ``_PyCodec_Forget()``
* ``_PyCodec_Lookup()``
* ``_PyCodec_LookupTextEncoding()``
* ``_PyComplex_FormatAdvancedWriter()``
* ``_PyDeadline_Get()``
* ``_PyDeadline_Init()``
* ``_PyErr_CheckSignals()``
* ``_PyErr_FormatFromCause()``
* ``_PyErr_GetExcInfo()``
* ``_PyErr_GetHandledException()``
* ``_PyErr_GetTopmostException()``
* ``_PyErr_ProgramDecodedTextObject()``
* ``_PyErr_SetHandledException()``
* ``_PyException_AddNote()``
* ``_PyImport_AcquireLock()``
* ``_PyImport_FixupBuiltin()``
* ``_PyImport_FixupExtensionObject()``
* ``_PyImport_GetModuleAttr()``
* ``_PyImport_GetModuleAttrString()``
* ``_PyImport_GetModuleId()``
* ``_PyImport_IsInitialized()``
* ``_PyImport_ReleaseLock()``
* ``_PyImport_SetModule()``
* ``_PyImport_SetModuleString()``
* ``_PyInterpreterState_Get()``
* ``_PyInterpreterState_GetConfig()``
* ``_PyInterpreterState_GetConfigCopy()``
* ``_PyInterpreterState_GetMainModule()``
* ``_PyInterpreterState_HasFeature()``
* ``_PyInterpreterState_SetConfig()``
* ``_PyLong_AsTime_t()``
* ``_PyLong_FromTime_t()``
* ``_PyModule_CreateInitialized()``
* ``_PyOS_URandom()``
* ``_PyOS_URandomNonblock()``
* ``_PyObject_CallMethod()``
* ``_PyObject_CallMethodId()``
* ``_PyObject_CallMethodIdNoArgs()``
* ``_PyObject_CallMethodIdObjArgs()``
* ``_PyObject_CallMethodIdOneArg()``
* ``_PyObject_CallMethodNoArgs()``
* ``_PyObject_CallMethodOneArg()``
* ``_PyObject_CallOneArg()``
* ``_PyObject_FastCallDict()``
* ``_PyObject_HasLen()``
* ``_PyObject_MakeTpCall()``
* ``_PyObject_RealIsInstance()``
* ``_PyObject_RealIsSubclass()``
* ``_PyObject_Vectorcall()``
* ``_PyObject_VectorcallMethod()``
* ``_PyObject_VectorcallMethodId()``
* ``_PySequence_BytesToCharpArray()``
* ``_PySequence_IterSearch()``
* ``_PyStack_AsDict()``
* ``_PyThreadState_GetDict()``
* ``_PyThreadState_Prealloc()``
* ``_PyThread_CurrentExceptions()``
* ``_PyThread_CurrentFrames()``
* ``_PyTime_Add()``
* ``_PyTime_As100Nanoseconds()``
* ``_PyTime_AsMicroseconds()``
* ``_PyTime_AsMilliseconds()``
* ``_PyTime_AsNanoseconds()``
* ``_PyTime_AsNanosecondsObject()``
* ``_PyTime_AsSecondsDouble()``
* ``_PyTime_AsTimespec()``
* ``_PyTime_AsTimespec_clamp()``
* ``_PyTime_AsTimeval()``
* ``_PyTime_AsTimevalTime_t()``
* ``_PyTime_AsTimeval_clamp()``
* ``_PyTime_FromMicrosecondsClamp()``
* ``_PyTime_FromMillisecondsObject()``
* ``_PyTime_FromNanoseconds()``
* ``_PyTime_FromNanosecondsObject()``
* ``_PyTime_FromSeconds()``
* ``_PyTime_FromSecondsObject()``
* ``_PyTime_FromTimespec()``
* ``_PyTime_FromTimeval()``
* ``_PyTime_GetMonotonicClock()``
* ``_PyTime_GetMonotonicClockWithInfo()``
* ``_PyTime_GetPerfCounter()``
* ``_PyTime_GetPerfCounterWithInfo()``
* ``_PyTime_GetSystemClock()``
* ``_PyTime_GetSystemClockWithInfo()``
* ``_PyTime_MulDiv()``
* ``_PyTime_ObjectToTime_t()``
* ``_PyTime_ObjectToTimespec()``
* ``_PyTime_ObjectToTimeval()``
* ``_PyTime_gmtime()``
* ``_PyTime_localtime()``
* ``_PyTraceMalloc_ClearTraces()``
* ``_PyTraceMalloc_GetMemory()``
* ``_PyTraceMalloc_GetObjectTraceback()``
* ``_PyTraceMalloc_GetTraceback()``
* ``_PyTraceMalloc_GetTracebackLimit()``
* ``_PyTraceMalloc_GetTracedMemory()``
* ``_PyTraceMalloc_GetTraces()``
* ``_PyTraceMalloc_Init()``
* ``_PyTraceMalloc_IsTracing()``
* ``_PyTraceMalloc_ResetPeak()``
* ``_PyTraceMalloc_Start()``
* ``_PyTraceMalloc_Stop()``
* ``_PyUnicodeTranslateError_Create()``
* ``_PyUnicodeWriter_Dealloc()``
* ``_PyUnicodeWriter_Finish()``
* ``_PyUnicodeWriter_Init()``
* ``_PyUnicodeWriter_PrepareInternal()``
* ``_PyUnicodeWriter_PrepareKindInternal()``
* ``_PyUnicodeWriter_WriteASCIIString()``
* ``_PyUnicodeWriter_WriteChar()``
* ``_PyUnicodeWriter_WriteLatin1String()``
* ``_PyUnicodeWriter_WriteStr()``
* ``_PyUnicodeWriter_WriteSubstring()``
* ``_PyUnicode_AsASCIIString()``
* ``_PyUnicode_AsLatin1String()``
* ``_PyUnicode_AsUTF8String()``
* ``_PyUnicode_CheckConsistency()``
* ``_PyUnicode_Copy()``
* ``_PyUnicode_DecodeRawUnicodeEscapeStateful()``
* ``_PyUnicode_DecodeUnicodeEscapeInternal()``
* ``_PyUnicode_DecodeUnicodeEscapeStateful()``
* ``_PyUnicode_EQ()``
* ``_PyUnicode_EncodeCharmap()``
* ``_PyUnicode_EncodeUTF16()``
* ``_PyUnicode_EncodeUTF32()``
* ``_PyUnicode_EncodeUTF7()``
* ``_PyUnicode_Equal()``
* ``_PyUnicode_EqualToASCIIId()``
* ``_PyUnicode_EqualToASCIIString()``
* ``_PyUnicode_FastCopyCharacters()``
* ``_PyUnicode_FastFill()``
* ``_PyUnicode_FindMaxChar ()``
* ``_PyUnicode_FormatAdvancedWriter()``
* ``_PyUnicode_FormatLong()``
* ``_PyUnicode_FromASCII()``
* ``_PyUnicode_FromId()``
* ``_PyUnicode_InsertThousandsGrouping()``
* ``_PyUnicode_JoinArray()``
* ``_PyUnicode_ScanIdentifier()``
* ``_PyUnicode_TransformDecimalAndSpaceToASCII()``
* ``_PyUnicode_WideCharString_Converter()``
* ``_PyUnicode_WideCharString_Opt_Converter()``
* ``_PyUnicode_XStrip()``
* ``_PyVectorcall_Function()``
* ``_Py_AtExit()``
* ``_Py_CheckFunctionResult()``
* ``_Py_CoerceLegacyLocale()``
* ``_Py_FatalErrorFormat()``
* ``_Py_FdIsInteractive()``
* ``_Py_FreeCharPArray()``
* ``_Py_GetConfig()``
* ``_Py_IsCoreInitialized()``
* ``_Py_IsFinalizing()``
* ``_Py_IsInterpreterFinalizing()``
* ``_Py_LegacyLocaleDetected()``
* ``_Py_RestoreSignals()``
* ``_Py_SetLocaleFromEnv()``
* ``_Py_VaBuildStack()``
* ``_Py_add_one_to_index_C()``
* ``_Py_add_one_to_index_F()``
* ``_Py_c_abs()``
* ``_Py_c_diff()``
* ``_Py_c_neg()``
* ``_Py_c_pow()``
* ``_Py_c_prod()``
* ``_Py_c_quot()``
* ``_Py_c_sum()``
* ``_Py_gitidentifier()``
* ``_Py_gitversion()``

A discussion was started to propose `treating private functions as public
functions
<https://discuss.python.org/t/pssst-lets-treat-all-api-in-public-headers-as-public/28916>`_.

I'm now working on identifying projects affected by these removals and on
proposing solutions for the most commonly used removed functions like the
``_PyObject_Vectorcall()`` alias.


PEP 594
=======

I removed 19 modules deprecated in Python 3.11 by PEP 594:

* aifc
* audioop
* cgi
* cgitb
* chunk
* crypt
* imghdr
* mailcap
* nis
* nntplib
* ossaudiodev
* pipes
* sndhdr
* spwd
* sunau
* telnetlib
* uu
* xdrlib

Zachary Ware removed msilib, so the PEP 594 was fully implemented in Python
3.13.

I announced the change: `PEP 594 has been implemented: Python 3.13 removes 20
stdlib modules
<https://discuss.python.org/t/pep-594-has-been-implemented-python-3-13-removes-20-stdlib-modules/27124>`_.

Removing imghdr caused me some troubles with building the Python documentation.
Sphinx uses imghdr, but recent Sphinx versions no longer use it. I updated
the Sphinx version to workaround this issue.


Remove
======

I removed locale.resetlocale() function, but I failed to remove
locale.getdefaultlocale() in Python 3.13: INADA-san asked me to keep it.

I removed the untested and not documented logging.Logger.warn() method.

Oh, I forgot to remove cafile, capath and cadefault parameters of the
urllib.request.urlopen() function: it's now also done in Python 3.13. I removed
similar parameters in many other modules in Python 3.12.


Cleanup
=======

As usual, I removed a bunch of unused imports (in the stdlib, tests and tools).

I reimplemented xmlrpc.client ``_iso8601_format()`` function with
``datetime.datetime.isoformat()``. The function ignores the timezone on
purpose: the XML-RPC specification doesn't explain how to handle it, many
implementations ignore it.

Port imp code to importlib
==========================

The importlib module was added to Python 3.1 and it became the default
in Python 3.3. The imp module was deprecated in Python 3.4 but was only removed
in Python 3.12. Replacing imp code with importlib is not trivial: importlib
has a different design and API.

I wrote documentation on how to port imp code to importlib in `What's New in
Python 3.12 <https://docs.python.org/dev/whatsnew/3.12.html#removed>`_.

I proposed `adding importlib.util.load_source_path() function
<https://github.com/python/cpython/pull/105755>`_, but I understood that the
devil is in details: it's hard to decide how to handle the ``sys.modules``
cache. I gave up and instead proposed a recipe in the What's New in Python 3.12
documentation::

    import importlib.util
    import importlib.machinery

    def load_source(modname, filename):
        loader = importlib.machinery.SourceFileLoader(modname, filename)
        spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
        module = importlib.util.module_from_spec(spec)
        # The module is always executed and not cached in sys.modules.
        # Uncomment the following line to cache the module.
        # sys.modules[module.__name__] = module
        loader.exec_module(module)
        return module

There are many projects affected by the imp removal and porting them is not
easy. See `How do I migrate from imp?
<https://discuss.python.org/t/how-do-i-migrate-from-imp/27885>`_ discussion.
