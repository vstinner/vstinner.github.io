++++++++++++++++++++++++++++++
Remove private C API functions
++++++++++++++++++++++++++++++

:date: 2023-12-15 23:00
:tags: c-api, cpython
:category: cpython
:slug: remove-c-api-funcs-313
:authors: Victor Stinner

In Python 3.13 alpha 1, I removed more than 300 private C API functions. Even
if I announced my plan early in July, users didn't "embrace" my plan and didn't
agree with the rationale. I reverted 50 functions in the alpha 2 release to
calm down the situation and have more time to replace private functions with
public functions.

.. image:: {static}/images/mucha_seasons.jpg
   :alt: Mucha paintaing: the 4 seasons
   :target: https://en.wikipedia.org/wiki/The_Seasons_(Mucha)

*Painting: The Seasons by Czech visual artist Alphonse Mucha (1900)*

Remove private functions
========================

On June 25th, I created `issue gh-106084
<https://github.com/python/cpython/issues/106084>`_: "Remove private C API
functions from abstract.h".

    Over the years, we accumulated many **private** functions as part of the
    **public** C API in abstract.h header file. I propose to remove them: move
    them to the **internal** C API.

On July 1st, I created the meta `issue gh-106320
<https://github.com/python/cpython/issues/106320>`_: "Remove private C API
functions". The issue has 63 pull requests (a lot!), 53 comments and more than
300 events (created by commits and pull requests) which make the issue hard
to navigate.

On July 3rd, **Petr Viktorin** shared his concerns:

    Please be careful about assuming that the **underscore** means a function
    is **private**. AFAIK, that rule first appears for `3.10
    <https://docs.python.org/3.10/c-api/stable.html#stable>`_, and was only
    properly formalized in `PEP 689 <https://peps.python.org/pep-0689/>`_, for
    Python 3.12.

    For older functions, please consider if they should be added to the
    unstable API. IMO it's better to call them “underscored” than “private”.

    See also: historical note in the `devguide <https://devguide.python.org/developer-workflow/c-api/index.html#private-names>`_.

On July 4th, **Petr** posted on Discourse: `(pssst) Let's treat all API in
public headers as public
<https://discuss.python.org/t/pssst-lets-treat-all-api-in-public-headers-as-public/28916>`_.

Remove more private functions
=============================

On July 4th, I removed `181 private functions
<https://github.com/python/cpython/issues/106320#issuecomment-1620749616>`_ so
far.

On July 4th, I identified that `34 projects
<https://github.com/python/cpython/issues/106320#issuecomment-1620773057>`_ on
PyPI top 5,000 are affected by these removals.

On July 7th, I `added PyObject_Vectorcall()
<https://github.com/python/pythoncapi-compat/pull/62>`_ to the
pythoncapi-compat project.

On July 9th, I started the discussion:
`C API: How much private is the private _Py_IDENTIFIER() API?
<https://discuss.python.org/t/c-api-how-much-private-is-the-private-py-identifier-api/29190>`_

On July 13th, I asked if `the PyComplex API
<https://github.com/python/cpython/issues/106320#issuecomment-1633302147>`_
should be made private or not. Petr noticed that this API was documented.

On July 23th, I tried to build numpy, but I was blocked by Cython which was broken by my
changes. I created the `issue gh-107076
<https://github.com/python/cpython/issues/107076>`_: "C API: Cython 3.0 uses
private functions removed in Python 3.13 (numpy 1.25.1 fails to build)".

On July 23th, I found that the private ``_PyTuple_Resize()`` function is documented. I
proposed `adding a new internal _PyTupleBuilder API
<https://github.com/python/cpython/pull/107139>`_ to replace
``_PyTuple_Resize()``.

On July 23th, I proposed:
`C API: My plan to clarify private vs public functions in Python 3.13
<https://discuss.python.org/t/c-api-my-plan-to-clarify-private-vs-public-functions-in-python-3-13/30131>`_.

    Private API has multiple issues: they are usually **not documented**, **not
    tested**, and so their **behavior may change** without any warning or
    anything.  Also, they can be **removed anytime** without any notice.

* Phase 1: Remove as many private API as possible
* Phase 2 (Python 3.13 alpha 1): revert removals if needed to make sure that Cython, numpy and pip
  work.
* Phase 3 (Python 3.13 beta 1): consider reverting more removals if needed.

On July 24th, I created the PR `Remove private _PyCrossInterpreterData API
<https://github.com/python/cpython/pull/107068>`_. **Eric Snow** asked me
to keep this private API since it's used by 3rd party C extensions.

On August 24th, I created `issue gh-108444
<https://github.com/python/cpython/issues/108444>`_ to add ``PyLong_AsInt()``
public function, replacing the removed ``_PyLong_AsInt()`` function.

On September 4th, I looked at the ``_PyArg`` API. I started the discussion:
`Use the limited C API for some of our stdlib C extensions
<https://discuss.python.org/t/use-the-limited-c-api-for-some-of-our-stdlib-c-extensions/32465>`_.

On September 4th, `I declared
<https://discuss.python.org/t/c-api-my-plan-to-clarify-private-vs-public-functions-in-python-3-13/30131/8>`_:

    I declare that the Python 3.13 **season of “removing as many private C API
    as possible” ended**! I stop here until Python 3.14.

Python 3.12 exports **385** private functions. After the cleanup, Python 3.13
only exported **86** private functions: I removed 299 functions. I closed the
issue.


Python 3.13 alpha 1 negative feedback
=====================================

On October 13th, **Python 3.13 alpha 1 was released** with my changes
removing around 300 private C API functions.

On October 14th, **Guido van Rossum** `asked
<https://github.com/python/cpython/issues/106320#issuecomment-1762755146>`_:

    Thanks for the list. Should we **encourage** various **projects to test
    3.13a1**, which just came out? Is there a way we can encourage them more?

On October 30th, **Stefan Behnel**, Cython creator, posted the message:
`Python 3.13 alpha 1 contains breaking changes, what's the plan?
<https://discuss.python.org/t/python-3-13-alpha-1-contains-breaking-changes-whats-the-plan/37490>`_.
He also `commented the issue <https://github.com/python/cpython/issues/106320#issuecomment-1772735064>`_.
Extract:

    I just came across this issue. Let me express my general disapproval
    regarding deliberate breakage, which this issue appears to be entirely
    about. As far as I can see, none of these removals was motivated. The mere
    idea of removing existing API "because we can" is entirely foreign to me.

On October 31th, **Petr** asked the Steering Council:
`Is it OK to remove _PyObject_Vectorcall? <https://github.com/python/steering-council/issues/212>`_
about the removal of old aliases with underscore, such as
``_PyObject_Vectorcall``.
I didn't know that these names were part of `PEP 590 – Vectorcall: a fast
calling protocol for CPython <https://peps.python.org/pep-0590/>`_, nothing was
written about that in the header files.

On November 2nd, **Guido** `wrote
<https://github.com/python/cpython/issues/106320#issuecomment-1790832433>`_
(where WG stands for C API Working Group):

    We can talk till we’re blue in the face but please no more action (i.e., no
    more moving/removing APIs) until the full WG has had a chance to discuss
    this and make a decision.

    (Restoring removed APIs at users’ requests is fine.)

On November 3rd, **Gregory P. Smith** `wrote
<https://github.com/python/cpython/issues/111481#issuecomment-1794211126>`__:

    I'd much prefer 'revert' for any API anyone is found using in 3.13.

    We need to treat 3.13 as a more special than usual release and aim to
    minimize compatibility headaches for existing project code. That way more
    things that build and run on 3.12 build can run on 3.13 as is or with
    minimal work.

    This will enable ecosystem code owners to focus on the bigger picture task
    of enabling existing code to be built and tested on an experimental pep703
    free-threading build rather than having a pile of unrelated cleanup trivia
    blocking that.

On November 7th, my colleague **Karolina Surma** posted a report: `Ongoing packages'
rebuild with Python 3.13 in Fedora
<https://discuss.python.org/t/ongoing-packages-rebuild-with-python-3-13-in-fedora/38134>`_.
She did a great bug triage work on counting build failures per C API issue by
recompiling 4000+ Python packages in Fedora with Python 3.13.

On November 13th, **Petr** also identified that the private PyComplex API, such as
``_Py_c_sum()`` function, was documented. Moreover, the `issue gh-112019
<https://github.com/python/cpython/issues/112019>`_ was created to ask to
revert these APIs.


Revert in Python 3.13 alpha 2
=============================

On November 13th, I created `issue gh-112026
<https://github.com/python/cpython/issues/112026>`_: "[C API] Revert of private
functions removed in Python 3.13 causing most problems". I made 4 changes:

* Add again ``<unistd.h>`` include in Python.h
* Restore removed private C API
* Restore removed _PyDict_GetItemStringWithError()
* Add again _PyThreadState_UncheckedGet() function

I selected functions by looking at bug reports, **Karolina**'s report, and by
trying to build numpy and cffi. With my reverts, numpy built successfully, and
cffi built successfully with a minor change that I reported upstream
(`cffi: Use PyErr_FormatUnraisable() on Python 3.13
<https://github.com/python-cffi/cffi/pull/34>`_).

In total, I restored `50 private functions
<https://github.com/python/cpython/issues/112026#issuecomment-1813191948>`_.

On November 22th, **Python 3.13 alpha 2 was released** with these restored
functions.  It seems like the situation is calmer now.

Reverting was part of my initial plan, it was clearly announced since the
beginning. But I didn't expect that so many people would test Python 3.13 alpha
1 as soon as it was released (October)! Usually, we only start to get feedback
around beta 1 (May). I had like **2 weeks to fix most issues instead of 7
months**. It was really stressful for me.

I `posted a message to apologize
<https://discuss.python.org/t/python-3-13-alpha-1-contains-breaking-changes-whats-the-plan/37490/29>`_
and to give the context of this work. Extract:

    Following the announced plan 22, I reverted 50 private APIs 20 which were
    removed in Python 3.13 alpha 1. These APIs will be available again in the
    incoming Python 3.13 alpha 2 (scheduled next Tuesday).

    I **planned to make Cython, numpy and cffi compatible**  with Python 3.13
    **alpha 1**. Well, I missed this release. With reverted changes, numpy
    1.26.2 can be built successfully, and cffi 1.16.0 just requires a single
    change 13. So we should be good (or almost good) for Python 3.13
    **alpha 2**.

    (...)

    I’m sorry if some people felt that this C API work was forced on them and
    their opinion was not taken in account. We heard you and we took your
    feedback in account. It took me time to adjust my plan according to early
    received feedback. I expected to have 6 months to work step by step. Well,
    I had 2 weeks instead 🙂


Add public functions
====================

On October 30th, I created `issue gh-111481
<https://github.com/python/cpython/issues/111481>`_: "[C API] Meta issue: add
new public functions with doc+tests to replace removed private functions".

So far, I added 7 public functions to Python 3.13:

* ``PyDict_Pop()``
* ``PyDict_PopString()``
* ``PyList_Clear()``
* ``PyList_Extend()``
* ``PyLong_AsInt()``
* ``Py_HashPointer()``
* ``Py_IsFinalizing()``

More functions are coming soon, I have many open pull requests.

Adding new functions is slower than what I expected. The good part is that many
people are reviewing the APIs, and that the new public APIs are way better than
the old private ones: less error prone, can be more efficient, etc. At least,
the conversion of private to public is moving steadily, functions are added one
by one.
