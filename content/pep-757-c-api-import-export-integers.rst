************************************************
PEP 757 – C API to import-export Python integers
************************************************

:date: 2025-09-11 16:00
:tags: c-api, cpython
:category: cpython
:slug: pep-757-c-api-import-export-integers
:authors: Victor Stinner

.. image:: {static}/images/ponyo.jpg
   :alt: Ponyo movie
   :target: https://en.wikipedia.org/wiki/Ponyo

Design an API can take time. This article describes the design of the
C API to import and export Python integers. It takes place between
August 2023 and December 2024. In total, the discussions got more than
448 messages!

The API is a thin abstraction on top of CPython implementation details
to access integer internals. The API has an O(1) complexity: in
practice, no memory is copied (at least, in the current CPython
implementation).

Picture: *Ponyo movie by Hayao Miyazaki*.

Python 3.13 alpha 1 removes _PyLong_New()
=========================================

In August 2023, I `removed
<https://github.com/python/cpython/pull/108604>`__ the ``_PyLong_New()``
function as part of `My plan to clarify private vs public C API
functions in Python 3.13
<https://discuss.python.org/t/c-api-my-plan-to-clarify-private-vs-public-functions-in-python-3-13/30131>`__.

In October, Python 3.13.0 alpha 1 was released without this function.
**Sergey B Kirpichev** reported that the gmpy2 project uses
``_PyLong_New()`` and asked how to replace the removed function. He
created `issue gh-111415
<https://github.com/python/cpython/issues/111415>`_: Consider restoring
_PyLong_New() function as public.

Python 3.13 alpha 2 restores _PyLong_New()
==========================================

In November, the private ``_PyLong_New()`` function has been restored in
Python 3.13 alpha 2 which was released at November 22.

Add public function PyLong_GetDigits()
======================================

In June 2024, **Sergey B Kirpichev** opened the `[C API Working Group] decision issue #31
<https://github.com/capi-workgroup/decisions/issues/31>`__: Add public
function ``PyLong_GetDigits()``. API::

    const digits* PyLong_GetDigits(PyObject* obj, Py_ssize_t *ndigits)

I disliked this API since it's too close to the exact implementation.
The API cannot be implemented in an efficient way if implementation
details change.

For example, in the future, CPython might adopt tagged pointers for
small integers and so don't have a concrete array of digits.

There was a call for a different API to address these issues.

PyLong_Export() and PyLong_Import() functions
=============================================

First API
---------

In July, I created `gh-121339
<https://github.com/python/cpython/pull/121339>`__ pull request to propose a
different API. Later, I opened the `[C API Working Group] decision issue
#35 <https://github.com/capi-workgroup/decisions/issues/35>`__
(which got 51 messages): Add import-export API for Python int objects. API::

    // Layout API
    typedef struct PyLongLayout {
        uint8_t bits_per_digit;
        uint8_t digit_size;
        int8_t word_endian;
        int8_t array_endian;
    } PyLongLayout;

    const PyLongLayout PyLong_LAYOUT;

    // Export API
    typedef struct PyLong_DigitArray {
        PyObject *obj;
        int negative;
        Py_ssize_t ndigits;
        const Py_digit *digits;
    } PyLong_DigitArray;

    int PyLong_AsDigitArray(PyObject *obj, PyLong_DigitArray *array)
    void PyLong_FreeDigitArray(PyLong_DigitArray *array)

    // Import API
    PyLongWriter* PyLongWriter_Create(int negative, Py_ssize_t ndigits, Py_digit **digits)
    PyObject* PyLongWriter_Finish(PyLongWriter *writer)

API changes
-----------

The `pull request <https://github.com/python/cpython/pull/121339>`__ got
277 messages (!) between July 2024 and February 2025. The API names were
discussed in length, and better names have been proposed.

The ``PyLong_LAYOUT`` constant was replaced with the
``PyLong_GetNativeLayout()`` function to have a better ABI.

The dependency to the ``Py_digit`` type has been removed. The
``Py_digit*`` type was replaced with ``void*`` to support digit of
arbitrary size.

``PyLong_Export.obj`` became private: ``obj`` was renamed to
``reserved``, and its specific type ``PyObject*`` became the opaque
``Py_uintptr_t`` type.

``PyLongWriter_Discard()`` function was added to handle errors.

PEP 757
=======

In September, **Sergey** and me wrote `PEP 757 – C API to import-export
Python integers <https://peps.python.org/pep-0757/>`__: the `discussion
<https://discuss.python.org/t/pep-757-c-api-to-import-export-python-integers/63895>`__
got 80 messages.

It was proposed to use an union for PyLongExport with a ``kind`` member
to select the format (small integer or digit array). The idea was
abandonned in the meanwhile.

For small integers, there is no warranty that they will be stored as a
digit array in the future. The ``PyLongExport.value`` member
(``int64_t``) was added to store the value of small integers.

There were two open questions:

* Should we add ``digits_order`` and ``endian`` members to
  ``sys.int_info`` and remove ``PyLong_GetNativeLayout()``? The
  ``PyLong_GetNativeLayout()`` function returns a C structure which is
  more convenient to use in C than
  ``sys.int_info`` which uses Python objects.
* Should we use anonymous union.

It was decided to leave ``sys.int_info`` unchanged and keep
``PyLong_GetNativeLayout()``.

It was also decided to avoid anonymous union to avoid any risk of
compatibility issue with old C versions.

`Benchmarks <https://peps.python.org/pep-0757/#benchmarks>`__ measured
the abstraction cost: it is between 1.04x slower and 1.27x faster. It
means that the abstraction has no significant impact on the performance.
In short (geometric mean):

* Export: 1.05x faster
* Import: 1.03x slower



Overwhelmed
===========

After months of discussions and many back and forth on the API,
`I got overwhelmed
<https://discuss.python.org/t/pep-757-c-api-to-import-export-python-integers/63895/66>`_
and close to give up. Hopefully, I didn't give up.


C API Working Group and Steering Council
========================================

In October, I opened a C API Working Group vote on PEP 757:
`decision issue #45
<https://github.com/capi-workgroup/decisions/issues/45>`__
which got 40 messages.

At November 28, 2024, the C API WG accepted the PEP and I `submitted the
PEP <https://github.com/python/steering-council/issues/264>`_ to the
Steering Council.

One week later, at December 8, the Steering Council accepted PEP 757 as
well!


Final API
=========

After many iterations, the final API is::

    // Layout API
    typedef struct PyLongLayout {
        uint8_t bits_per_digit;
        uint8_t digit_size;
        int8_t digits_order;
        int8_t digit_endianness;
    } PyLongLayout;

    const PyLongLayout* PyLong_GetNativeLayout(void)

    // Export API
    typedef struct PyLongExport {
        int64_t value;
        uint8_t negative;
        Py_ssize_t ndigits;
        const void *digits;
        Py_uintptr_t _reserved;
    } PyLongExport;

    int PyLong_Export(PyObject *obj, PyLongExport *export_long)
    void PyLong_FreeExport(PyLongExport *export_long)

    // Import API
    PyLongWriter* PyLongWriter_Create(int negative, Py_ssize_t ndigits, void **digits)
    PyObject* PyLongWriter_Finish(PyLongWriter *writer)
    void PyLongWriter_Discard(PyLongWriter *writer)

The ``decimal`` extension and ``Python/marshal.c`` have been modified to
use this API.
