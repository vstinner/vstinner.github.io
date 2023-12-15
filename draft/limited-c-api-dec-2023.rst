++++++++++++++++++++++++++++++++++++++++++++++
Status of Python limited C API - December 2023
++++++++++++++++++++++++++++++++++++++++++++++

:date: 2023-12-15 22:00
:tags: c-api, cpython
:category: cpython
:slug: limited-c-api-dec-2023
:authors: Victor Stinner


Functions added to the limited C API
====================================

Python 3.13 adds the following functions to the limited C API:

* ``PyMem_RawMalloc()``, ``PyMem_RawCalloc()``,
  ``PyMem_RawRealloc()`` and ``PyMem_RawFree()``
* ``PySys_Audit()``
* ``PySys_AuditTuple()``
* ``Py_IsFinalizing()``

Changes
=======

``Py_SET_REFCNT()`` is now implemented as an opaque function call.

In the limited C API version 3.12 and newer, ``Py_INCREF()`` and
``Py_DECREF()`` were already modified to be implemented as opaque function
calls.

Talk at Core Dev Sprint at Brno
===============================

In October, I was at Brno (Czech Republic) for 1 week, October 9-13, for the annual
Python Core Dev sprint. The first day, Monday, I gave a talk about the progress
of the C API and my agenda for the C API:
`Python C API
<https://github.com/vstinner/talks/blob/main/2023-CoreDevSprint-Brno/c-api.pdf>`__
(PDF slides). The discussion was constructive.

Argument Clinic
===============

In August, I created `issue gh-108494
<https://github.com/python/cpython/issues/108494>`_ to add support for the
limited C API in Argument Clinic. I had two goals:

* Use Argument Clinic in stdlib C extensions built with the limited C API;
* Prepare Argument Clinic to make it more usable outside CPython code base.

I started with a minimum change to avoid the internal C API in the most simple
case. Slowly, I made more changes to cover more cases.


Stdlib C extensions
===================

In 20202, I created `issue gh-85283
<https://github.com/python/cpython/issues/85283>`_ to convert a few stdlib
extensions to the limited C API. But I had some technical issues such as
Argument Clinic which uses private functions and the internal C API.

In August 2023, I started the discussion: `Use the limited C API for some of our
stdlib C extensions
<https://discuss.python.org/t/use-the-limited-c-api-for-some-of-our-stdlib-c-extensions/32465>`_.

In October, I modified the following C extensions to be built with the limited
C API:

* ``_ctypes_test``
* ``_multiprocessing.posixshmem``
* ``_scproxy``
* ``_stat``,
* ``_testimportmultiple``
* ``_uuid``
* ``errno``
* ``md5``
* ``resource``
* ``winsound``

Some projects

Creation of PEP 733
===================

In May, after Pycon US, Irit created a new C API Workgroup organization on
GitHub with a first project: the `Problems project
<https://github.com/capi-workgroup/problems/>`_ where developers were invited
to report C API problems.

In July, Irit wrote a `first PEP draft
<https://github.com/capi-workgroup/problems/pull/63>`_ summarizing all issues.

In October, Irit created a `pull request
<https://github.com/python/peps/pull/3491>`_ of the draft of the PEP 733 – An
Evaluation of Python’s Public C API. The first version had an impressive of
list of 33 authors. After a long review with 274 messages and 49 commits (!),
the PR was merged with 28 authors (5 persons asked to not be liste as authors).
The PEP was `announced on Discourse
<https://discuss.python.org/t/pep-733-an-evaluation-of-python-s-public-c-api/37618>`_.
Irit added:

    As an informational PEP, it does not require SC approval

See `PEP 733 – An Evaluation of Python’s Public C API <https://peps.python.org/pep-0733/>`_.

Authors (28) of the PEP 733:

* Erlend Egeberg Aasland
* Domenico Andreoli
* Stefan Behnel
* Carl Friedrich Bolz-Tereick
* Simon Cross
* Steve Dower
* Tim Felgentreff
* David Hewitt
* Shantanu Jain
* Wenzel Jakob
* Irit Katriel
* Marc-Andre Lemburg
* Donghee Na
* Karl Nelson
* Ronald Oussoren
* Antoine Pitrou
* Neil Schemenauer
* Mark Shannon
* Stepan Sindelar
* Gregory P. Smith
* Eric Snow
* Victor Stinner
* Guido van Rossum
* Petr Viktorin
* Carol Willing
* William Woodruff
* David Woods
* Jelle Zijlstra


C API Working Group
===================

During the Core Dev Sprint, Guido `created a PR
<https://github.com/python/peps/pull/3476>`_ for PEP 731: "C API Working Group
Charter" with 5 initial members:

* Steve Dower
* Irit Katriel
* Guido van Rossum
* Victor Stinner
* Petr Viktorin

At the end of November, the Steering Council `accepted the PEP
<https://github.com/python/steering-council/issues/210#issuecomment-1819668621>`_.

Three projects were created to organize the work:

* `API Evolution <https://github.com/capi-workgroup/api-evolution/>`_,
* `API Revolution <https://github.com/capi-workgroup/api-revolution/>`_,
* `Decisions <https://github.com/capi-workgroup/decisions/>`_.

For example, last week, the first decison was taken by approving my proposed
``Py_HashPointer()`` API::

    Py_hash_t Py_HashPointer(const void *ptr)

See `Py_HashPointer() documentation
<https://docs.python.org/dev/c-api/hash.html#c.Py_HashPointer>`_
in Python 3.13.
