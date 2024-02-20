++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
C API: My plan to clarify private vs public functions in Python 3.13
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2024-02-20 10:00
:tags: c-api, cpython
:category: cpython
:slug: convert-private-public-c-api-python-3-13
:authors: Victor Stinner

C API: My plan to clarify private vs public functions in Python 3.13
====================================================================

On June 22th, 2023, the main Python branch was forked to become Python 3.13:
the 3.12 branch was created to stabilize Python 3.12. I made immediately
incompatible changes like removing most deprecated functions scheduled for
removal in Python 3.13, to collect user feedback as soon as possible, to have
most time to decide how to deal with complicated cases.

On June 25th, I created the issue `C API: Remove private functions from abstract.h
<https://github.com/python/cpython/issues/106084>`_ to remove private functions
like ``_PySequence_BytesToCharpArray()``, ``_PyObject_HasLen()``,
``_PyObject_RealIsInstance()`` and ``_PyObject_CallMethod()``.

    Over the years, we accumulated many private functions as part of the public
    C API in abstract.h header file. I propose to remove them: move them to the
    internal C API.

**Petr Viktorin** asked to keep functions like `_PyObject_Vectorcall()` since
`PEP 590 – Vectorcall: a fast calling protocol for CPython
<https://peps.python.org/pep-0590/>`_ explicitly keeps these private aliases
for backward compatibility. I didn't know that.

On July 1st, I created a way more global issue `C API: Remove private C API
functions (move them to the internal C API)
<https://github.com/python/cpython/issues/106320>`_.

On July 23th, I posted `C API: My plan to clarify private vs public functions in Python 3.13
<https://discuss.python.org/t/c-api-my-plan-to-clarify-private-vs-public-functions-in-python-3-13/30131>`_.

Is private API supported or not?
================================

The `C API doc <https://docs.python.org/dev/c-api/stable.html>`_ says:

    Names prefixed by an underscore, such as _Py_InternalState, are private API
    that **can change without notice even in patch releases**. If you need to
    use this API, consider reaching out to CPython developers to discuss adding
    public API for your use case.

On July 4th, Petr posted `(pssst) Let’s treat all API in public headers as public
<https://discuss.python.org/t/pssst-lets-treat-all-api-in-public-headers-as-public/28916>`_.

On August 25th, Petr posted `C API: What should the leading underscore (_Py) mean?
<https://discuss.python.org/t/c-api-what-should-the-leading-underscore-py-mean/18486>`_.

On October 31th, Petr asked the Steering Council:
`Is it OK to remove _PyObject_Vectorcall? <https://github.com/python/steering-council/issues/212>`_.
This specific issue was solved by reverting removed aliases in alpha 2.


Rationale
=========

* Private API has no backward compatibility.
* Private API has usually no documentation and no tests.
* Python devs don't know who consumes its API.
* Smaller API means better trust between Python and API consumer, better
  support, more tests.


Removals
========

300 functions removed.

On September 4th, I `declared that the Python 3.13 season of "removing as many
private C API as possible" ended
<https://github.com/python/cpython/issues/106320#issuecomment-1705704935>`_! I
stop here until Python 3.14.

    I will now focus on **testing as many C extensions as possible** on Python
    3.13.

    And as I wrote, I consider **moving back some _Py private functions** from
    the internal C API to the public C API if I don't have enough time to fix
    enough C extensions. Especially functions which affect most C extensions.

    In the current main branch (**Python 3.13**), there are **86 private
    functions** (in Include/cpython/) exported with PyAPI_FUNC(). IMO 86
    private functions is way better than the **385 private functions** exported
    by **Python 3.12**. It's easier to manage.

    Some of them can be moved to the internal C API, but the remaining ones are
    the most complicated to move for various reasons.

    For example, in 2020 I failed to remove _Py_NewReference() since it's used
    by 3rd party C extensions (and by Python itself, by the way) to implement
    nice free list optimizations. There is no good replacement for that, and
    designing a public API to implement a free list is not trivial. Such API
    stays in the gray area: it should not be used, but I will not blame you if
    you continue using it.

    I didn't count internal functions (Include/internal/), I don't care about
    these ones. See the complete statistics of the C API.

    Using the internal C API is fine, but in exchange you are on your own.
    There is no documentation, usually the API is not tested, no or incomplete
    error checking, etc. Most of the internal C API remains usable outside
    CPython itself because they are usages for that, like debuggers and
    profilers which need to inspect Python internals without modifying its
    state. Usually, it means reading memory without calling functions (if
    possible).

Affected Projects
=================

PEP 590 old API, 8 projects: https://github.com/python/cpython/issues/106084#issuecomment-1614440847

July 4, affected projects: https://github.com/python/cpython/issues/106320#issuecomment-1620773057

July 4, used APIs: https://github.com/python/cpython/issues/106320#issuecomment-1620773776

Cython: https://github.com/python/cpython/issues/107076

On October 14th, Guido `wrote
<https://github.com/python/cpython/issues/106320#issuecomment-1762755146>_:

    Should we encourage various projects to test 3.13a1, which just came out?
    Is there a way we can encourage them more?


Documented removed API?
=======================

https://github.com/python/cpython/issues/106320#issuecomment-1794684601

_PyTuple_Resize() and _PyBytes_Resize():

... and PyComplex such as _Py_c_sum().


Keep old API?
=============

**Petr** `wrote <https://github.com/python/cpython/issues/106084#issuecomment-1614258496>`__ (emphasis is mine):

    The ``#define`` is not a big maintenance burden, and there's no reason to
    **punish** early adopters or people who want easier compatibility with 3.8.

On November 6th, **Guido van Rossum** `wrote
<https://github.com/python/cpython/issues/106320#issuecomment-1794240140>`__
(emphasis is mine):

    Note there is a **moratorium** on removing APIs until the term “private”
    has been **clarified by the C API WG**.

I would like to reduce the size of the C API. Aliases are causing a maintenance burden:

* Users have to decide which API is the "good one"
* Old APIs may have to be documented and tested ([these aliases are in the docs](https://docs.python.org/dev/c-api/call.html#PY_VECTORCALL_ARGUMENTS_OFFSET))
* Other Python implementations have to implement it just because some C extensions use them: not all Python implementations can implement aliases with ``#define``.
* Macros are not available in C extensions which don't use the header file but use directly symbols: macros are bad, see https://peps.python.org/pep-0670/

Petr:




Unhappy users
=============

xxx Stefan

xxx Petr

xxx Guido

On November 6th, **Gregory Smith** `wrote <https://github.com/python/cpython/issues/111481#issuecomment-1794211126>`__:

    I'd much prefer 'revert' for any API anyone is found using in 3.13.

    We need to treat 3.13 as a more special than usual release and aim to
    minimize compatibility headaches for existing project code. That way more
    things that build and run on 3.12 build can run on 3.13 as is or with
    minimal work.

    This will enable ecosystem code owners to focus on the bigger picture task
    of enabling existing code to be built and tested on an experimental pep703
    free-threading build rather than having a pile of unrelated cleanup trivia
    blocking that.


The Big Revert in Alpha 2
=========================

https://discuss.python.org/t/revert-python-3-13-c-api-incompatible-changes-causing-most-troubles/38214

Revert immediately C API changes impacting at least 5 projects.

My colleague **Karolina Surma** did a `great bug triage work on couting build
failures per C API issue
<https://discuss.python.org/t/ongoing-packages-rebuild-with-python-3-13-in-fedora/38134>`_
20 by recompiling 4000+ Python packages in Fedora with Python 3.13.

reverted: xxx

still removed: xxx

New public API in Python 3.13
=============================

New public API in Python 3.13 replacing private APIs:

====================================  ================================  =============
Public                                Private                           Comment
====================================  ================================  =============
``PyCFunctionFastWithKeywords`` type  ``_PyCFunctionFastWithKeywords``
``PyCFunctionFast`` type              ``_PyCFunctionFast``
``PyErr_FormatUnraisable()``          ``_PyErr_WriteUnraisableMsg()``   Better API
``PyLong_AsNativeBytes()``            ``_PyLong_FromByteArray()``
``PyLong_FromNativeBytes()``          ``_PyLong_FromByteArray()``
``PyTime_t`` type                     ``_PyTime_t``
``PyTime_MIN``                        ``_PyTime_MIN``
``PyTime_MAX``                        ``_PyTime_MAX``
``PyTime_AsSecondsDouble()``          ``_PyTime_AsSecondsDouble()``
``PyTime_Monotonic()``                ``_PyTime_GetMonotonicClock()``   Can fail
``PyTime_PerfCounter()``              ``_PyTime_GetPerfCounter()``      Can fail
``PyTime_Time()``                     ``_PyTime_GetSystemClock()``      Can fail
====================================  ================================  =============

Keeping the old API or not is still an on-going discussion. For example,
``_PyCFunctionFast`` type was kept, but ``_PyErr_WriteUnraisableMsg()`` was
removed.

* decision: `Should we make it hard for 3rd parties to use private functions? <https://github.com/capi-workgroup/decisions/issues/7>`_
* decision: `Keep alias or not when replacing a private API with a public API? Action: add guidance in the devguide <https://github.com/capi-workgroup/decisions/issues/14>`_
* api-evolution: `Macro to hide deprecated functions <https://github.com/capi-workgroup/api-evolution/issues/24>`_
