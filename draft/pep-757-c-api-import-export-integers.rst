************************************************
PEP 757 – C API to import-export Python integers
************************************************

:date: 2025-06-20 14:00
:tags: c-api, cpython
:category: cpython
:slug: pep-757-c-api-import-export-integers
:authors: Victor Stinner

Python 3.13 alpha 1 removes _PyLong_New()
=========================================

In August 2023, I `removed
<https://github.com/python/cpython/pull/108604>`__ the ``_PyLong_New()``
function as part of `My plan to clarify private vs public C API
functions in Python 3.13
<https://discuss.python.org/t/c-api-my-plan-to-clarify-private-vs-public-functions-in-python-3-13/30131>`__.
Python 3.13.0 alpha 1 released at October 13 includes this change.

gmpy2 uses _PyLong_New()
========================

In October, two months later, after the alpha 1 release, Sergey B
Kirpichev reported that the gmpy2 project uses ``_PyLong_New()`` and
asked how to replace the removed function. He created `issue gh-111415
<https://github.com/python/cpython/issues/111415>`_: Consider restoring
_PyLong_New() function as public.

Python 3.13 alpha 2 restores _PyLong_New()
==========================================

In November, the private ``_PyLong_New()`` function has been restored in
Python 3.13 alpha 2 which was released at November 22.

Add public function PyLong_GetDigits()
======================================

In June 2024, Sergey B Kirpichev opened the `decision issue #31
<https://github.com/capi-workgroup/decisions/issues/31>`__: Add public
function ``PyLong_GetDigits()``.

PyLong_Export() and PyLong_Import() functions
=============================================

In July, I created `gh-121339
<https://github.com/python/cpython/pull/121339>`__: Add PyLong_Export()
and PyLong_Import() functions and PyLong_LAYOUT structure.

Later, I opened the `decision issue 35
<https://github.com/capi-workgroup/decisions/issues/35>`__: Add
import-export API for Python int objects.

PEP 757
=======

In September, Sergey and me wrote `PEP 757 – C API to import-export
Python integers <https://peps.python.org/pep-0757/>`__.

Discussion: `PEP 757 – C API to import-export Python integers
<https://discuss.python.org/t/pep-757-c-api-to-import-export-python-integers/63895>`__.

There are two open questions:

* Should we add ``digits_order`` and ``endian`` members to
  ``sys.int_info`` and remove ``PyLong_GetNativeLayout()``? The
  ``PyLong_GetNativeLayout()`` function returns a C structure which is
  more convenient to use in C than
  ``sys.int_info`` which uses Python objects.
* Should we use anonymous union.

C API Working Group and Steering Council
========================================

In October, I opened a C API Working Group vote on PEP 757: `decision issue 45
<https://github.com/capi-workgroup/decisions/issues/45>`__.

At November 28, 2024, the C API WG accepted the PEP and I `submitted the
PEP <https://github.com/python/steering-council/issues/264>`_ to the
Steering Council.

One week later, at December 8, the steering council accepted PEP 757 as
well!
