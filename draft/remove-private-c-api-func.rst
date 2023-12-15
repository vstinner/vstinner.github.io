++++++++++++++++++++++++++++++
Remove private C API functions
++++++++++++++++++++++++++++++

:date: 2023-12-15 23:00
:tags: c-api, cpython
:category: cpython
:slug: limited-c-api-dec-2023
:authors: Victor Stinner


Remove private C API functions
==============================

At the end of June, I created `issue gh-106084
<https://github.com/python/cpython/issues/106084>`_: "Remove private C API
functions from abstract.h". Soon after that, I created a more generic `issue
gh-106320 <https://github.com/python/cpython/issues/106320>`_: "Remove private
C API functions".

On Discourse, Petr proposed `(pssst) Let's treat all API in public headers as public
<https://discuss.python.org/t/pssst-lets-treat-all-api-in-public-headers-as-public/28916>`_.

I proposed the opposite: `C API: My plan to clarify private vs public functions
in Python 3.13
<https://discuss.python.org/t/c-api-my-plan-to-clarify-private-vs-public-functions-in-python-3-13/30131>`_.

At the beginning of September, `I declared
<https://discuss.python.org/t/c-api-my-plan-to-clarify-private-vs-public-functions-in-python-3-13/30131/8>`_:

    I declare that the Python 3.13 season of “removing as many private C API as
    possible” ended! I stop here until Python 3.14.

Python 3.12 exports 385 private functions. After the cleanup, Python 3.13
only exported 86 private functions: I removed 299 functions.

Python 3.13 alpha1 and revert
=============================

At October 13, Python 3.13 alpha1 was released with my changes removed many
private C API functions.

At October 30, Stefan Behnel creator and maintainer of Cython posted the
message: `Python 3.13 alpha 1 contains breaking changes, what's the plan?
<https://discuss.python.org/t/python-3-13-alpha-1-contains-breaking-changes-whats-the-plan/37490>`_.

My colleague Karolina did a great bug triage work on counting build failures
per C API issue by recompiling 4000+ Python packages in Fedora with Python
3.13.  At November 7, she posted a report:
`Ongoing packages' rebuild with Python 3.13 in Fedora
<https://discuss.python.org/t/ongoing-packages-rebuild-with-python-3-13-in-fedora/38134>`_.


Restore removed functions causing most problems
===============================================

At November 13, I created `issue gh-112026
<https://github.com/python/cpython/issues/112026>`_: "[C API] Revert of private
functions removed in Python 3.13 causing most problems". I made 4 changes:

* Add again ``<unistd.h>`` include in Python.h
* Restore removed private C API
* Restore removed _PyDict_GetItemStringWithError()
* Add again _PyThreadState_UncheckedGet() function

I selected functions by looking at bug reports, Karolina's report, and by
trying to build numpy and cffi. With my reverts, numpy successfully, and
cffi built successfully with a minor change that I reported upstream:
`cffi: Use PyErr_FormatUnraisable() on Python 3.13
<https://github.com/python-cffi/cffi/pull/34>`_.

In total, I restored `50 private functions
<https://github.com/python/cpython/issues/112026#issuecomment-1813191948>`_.
At November 22, Python 3.13 alpha2 was released with these restored functions.
It seems like the situation is more quiet now.

Reverting was part of my initial plan, it was clearly announced. But I didn't
expect that so many people would test Python 3.13 alpha1! I `posted a message
to apologize
<https://discuss.python.org/t/python-3-13-alpha-1-contains-breaking-changes-whats-the-plan/37490/29>`_
and to give the context of this work. Extract:

    Following the announced plan 22, I reverted 50 private APIs 20 which were
    removed in Python 3.13 alpha1. These APIs will be available again in the
    incoming Python 3.13 alpha2 (scheduled next Tuesday).

    I planned to make Cython, numpy and cffi compatible with Python 3.13
    alpha1. Well, I missed this release. With reverted changes, numpy 1.26.2
    can be built successfully, and cffi 1.16.0 just requires a single change
    13. So we should be good (or almost good) for Python 3.13 alpha2.

    (...)

    I’m sorry if some people felt that this C API work was forced on them and
    their opinion was not taken in account. We heard you and we took your
    feedback in account. It took me time to adjust my plan according to early
    received feedback. I expected to have 6 months to work step by step. Well,
    I had 2 weeks instead 🙂


Add public functions
====================

At the end of October, I created `issue gh-111481
<https://github.com/python/cpython/issues/111481>`_: "[C API] Meta issue: add
new public functions with doc+tests to replace removed private functions".

So far, I added the following functions to Python 3.13:

* ``PyDict_Pop()``
* ``PyDict_PopString()``
* ``PyList_Clear()``
* ``PyList_Extend()``
* ``PyLong_AsInt()``
* ``Py_HashPointer()``
* ``Py_IsFinalizing()``

I have many open pull requests to add more public functions.

Adding new functions is slower than what I expected. The good part is that many
people review the API and the new API is way better than the old one. At least,
it is moving steadily, functions are added one by one.

