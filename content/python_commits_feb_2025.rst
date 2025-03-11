++++++++++++++++++++++++++++++++
My Python commits: February 2025
++++++++++++++++++++++++++++++++

:date: 2025-03-11 15:00
:tags: cpython
:category: cpython
:slug: python-commits-february-2025
:authors: Victor Stinner

Here is a report on my 18 commits merged into Python in February 2025:

* Reorganize C API tests
* Use PyErr_FormatUnraisable()
* Reorganize includes
* C API: Remove PySequence_Fast()
* C API: Fix function signatures
* C API: Deprecate private _PyUnicodeWriter
* Documentation
* Misc changes

.. image:: {static}/images/dejeuner_canotiers.jpg
   :alt: Le Déjeuner des Canotiers by Auguste Renoir
   :target: https://en.wikipedia.org/wiki/Luncheon_of_the_Boating_Party

Painting: *Le Déjeuner des Canotiers* (1881) by *Auguste Renoir*.

gh-93649: Reorganize C API tests
================================

Tests on the C API are written in Python and C. The C part is made of a big
file ``Modules/_testcapimodule.c`` (4,410 lines) and 37 C files in the
``Modules/_testcapi/`` directory. At the beginning, ``_testcapimodule.c`` was
the only file and there is a work-in-progress to split it into smaller files.

I moved more codes from ``_testcapimodule.c`` into sub-files:

* Add ``Modules/_testcapi/frame.c`` file.
* Add ``Modules/_testcapi/type.c`` file.
* Add ``Modules/_testcapi/function.c`` file.
* Move ``_testcapi`` tests to specific files.

``_testcapimodule.c`` size before/after my changes:

* Before: **4,410** lines
* After: **3,375 lines** (-1,035 lines: 23% smaller)

gh-129354: Use PyErr_FormatUnraisable()
=======================================

When an error occurs, Python usually raises an exception to let the developer
decides how to handle the error. In some rare cases, exceptions cannot be
raised and `sys.unraisablehook
<https://docs.python.org/dev/library/sys.html#sys.unraisablehook>`_ is called
instead.

Before, many of these "unraisable exceptions" were logged with limited or no
context. I modified these functions to explain why these errors were logged.

Example of change::

    -            PyErr_WriteUnraisable(self);
    +            PyErr_FormatUnraisable("Exception ignored "
    +                                   "while finalizing file %R", self);

Before, only the *self* object was logged with a generic error message. Now
the "Exception ignored while finalizing file" specific message is logged which
explains where the error comes from.

I replaced ``PyErr_FormatUnraisable()`` with ``PyErr_FormatUnraisable()`` in
20 C files. And I had to update 7 related Python test files.


gh-129539: Reorganize includes
==============================

The `posixmodule.c
<https://github.com/python/cpython/blob/052cb717f5f97d08d2074f4118fd2c21224d3015/Modules/posixmodule.c>`_
file is the biggest C file of the Python project: it is made of 18,206 lines
of C code.

It starts with 600 lines of code to include 103 header files. These lines were
not well organized leading to `a bug (EX_OK symbol)
<https://github.com/python/cpython/issues/129539>`_.

I `reorganized these 600 lines
<https://github.com/python/cpython/commit/df4a2f5bd74fc582d99e6a82e070058d7765f44d>`_
to add sections, group similar includes, and add a comment explaining why each
include is needed. For example, the ``<unistd.h>`` header is needed to get the
``symlink()`` function::

    #ifdef HAVE_UNISTD_H
    #  include <unistd.h>             // symlink()
    #endif


gh-91417, C API: Remove PySequence_Fast()
=========================================

While digging into `open C API issues
<https://github.com/python/cpython/issues?q=state%3Aopen%20label%3A%22topic-C-API%22>`_,
I found an `old bug <https://github.com/python/cpython/issues/91417>`_ (2022)
about the ``PySequence_Fast()`` function in the limited C API.

The ``PySequence_Fast()`` function should be used with
``PySequence_Fast_GET_SIZE()`` and ``PySequence_Fast_GET_ITEM()`` macros, but
these macros don't work in the limited C API.

I decided to `remove PySequence_Fast()
<https://github.com/python/cpython/commit/2ad069d906c6952250dabbffbcb882676011b310>`_
and these macros from the limited C API.
The function never worked with the limited C API. It was added by mistake.

Sadly, one month later, my colleague Karolina Surma `discovered
<https://bugzilla.redhat.com/show_bug.cgi?id=2345504>`_ that `PyQt6 is broken
by Python 3.14a5 <https://github.com/python/cpython/issues/130947>`_: PyQt6
uses the removed ``PySequence_Fast()``! I'm `working on adding the function
back <https://github.com/python/cpython/pull/130948>`_.


gh-111178, C API: Fix function signatures
=========================================

When Python is built with ``clang -fsanitize=undefined``, Python fails quickly
on calling functions with the wrong ABI. For example, the ``tp_dealloc`` ABI
is::

    void tp_dealloc(PyObject *self)

whereas the built-in ``list`` type used the ABI::

    void list_dealloc(PyListObject *op)

``PyObject*`` and ``PyListObject*`` are not the same type causing an
`undefined behavior <https://en.wikipedia.org/wiki/Undefined_behavior>`_.

The correct function signature is::

    void list_dealloc(PyObject *op)

In February, I fixed the function signature in 4 files:

* ``symtable.c``
* ``namespaceobject.c``
* ``instruction_sequence.c``
* ``sliceobject.c``

Since October 2023, there is a `long on-going work-in-progress
<https://github.com/python/cpython/issues/111178>`_ to fix all function
signatures. It's a lot of work. At the end of February 2025, 97 pull requests
have already been merged to fix signatures.


gh-128863, C API: Deprecate private _PyUnicodeWriter
====================================================

I added a `new public PyUnicodeWriter C API
<https://docs.python.org/dev/c-api/unicode.html#pyunicodewriter>`_ to Python
3.14. So I deprecated the old private ``_PyUnicodeWriter`` C API:

* ``_PyUnicodeWriter_Init()``
* ``_PyUnicodeWriter_Finish()``
* ``_PyUnicodeWriter_Dealloc()``
* ``_PyUnicodeWriter_WriteChar()``
* ``_PyUnicodeWriter_WriteStr()``
* ``_PyUnicodeWriter_WriteSubstring()``
* ``_PyUnicodeWriter_WriteASCIIString()``
* ``_PyUnicodeWriter_WriteLatin1String()``

This deprecation was controversial and has to go through a `C API Working
Group decision <https://github.com/capi-workgroup/decisions/issues/57>`_.


Documentation
=============

* gh-129342: `Explain how to replace Py_GetProgramName() in C
  <https://github.com/python/cpython/commit/632ca568219f86679661bc288f46fa5838102ede>`_
* gh-101944: `Clarify PyModule_AddObjectRef() documentation
  <https://github.com/python/cpython/commit/04264a286e5ddfe8ac7423f7376ca34a2ca8b7ba>`_


Misc changes
============

* gh-128911: Use the new `PyImport_ImportModuleAttr()
  <https://docs.python.org/dev/c-api/import.html#c.PyImport_ImportModuleAttr>`_
  function:

  * Replace ``PyImport_ImportModule()`` + ``PyObject_GetAttr()`` with
    ``PyImport_ImportModuleAttr()``.
  * Replace ``PyImport_ImportModule()`` + ``PyObject_GetAttrString()`` with
    ``PyImport_ImportModuleAttrString()``.

* gh-129363: `Add colors to tests run in sequentially mode
  <https://github.com/python/cpython/commit/f1b81c408fb83beeee519ae4fb9d3a36dd4522b3>`_.
  First, write the test name without color. Then, write the test name
  and the result with color. Each test is displayed twice.

* gh-109959: Remove ``test_glob.test_selflink()`` test.
  The test is not reliable, `it fails randomly on Linux
  <https://github.com/python/cpython/issues/109959#issuecomment-2577550700>`_.
