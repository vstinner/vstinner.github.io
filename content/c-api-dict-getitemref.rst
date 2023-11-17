+++++++++++++++++++
PyDict_GetItemRef()
+++++++++++++++++++

:date: 2023-11-16 20:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-abstract-pyobject
:authors: Victor Stinner

This article is about the intense API design discussion when I proposed adding
the ``PyDict_GetItemRef()`` function to Python 3.13 C API, between June and
July 2023.

.. image:: {static}/images/amour_psychee.jpg
   :alt: Psyche Revived by Cupid's Kiss

Photo: *Psyche Revived by Cupid's Kiss* sculpture by Antonio Canova.



Add PyImport_AddModuleRef() function
====================================

In June, while reading a change, I found surprising code: the
``PyImport_AddModuleObject()`` creates a weak reference on the module returned
by ``import_add_module()``, call ``Py_DECREF()`` on the module, and then try to
get the module back from the weak reference: it can be NULL if the reference
count was 1. I expected to have just ``Py_DECREF()``, but no, complicated code
involving a weak reference is needed to prevent a crash.

So I `added <https://github.com/python/cpython/issues/105922>`_ the new
`PyImport_AddModuleRef() function
<https://docs.python.org/dev/c-api/import.html#c.PyImport_AddModuleRef>`_ to
return directly the strong reference, and avoid having to create a temporary
weak reference.

Note: The API of the new PyImport_AddModuleObject() function is `still being
discussed and may change in the near future
<https://github.com/python/cpython/issues/106915>`_.


Add PyWeakref_GetRef() function
===============================

Shortly after, I `added <https://github.com/python/cpython/issues/105927>`_ the
new `PyWeakref_GetRef() function
<https://docs.python.org/dev/c-api/weakref.html#c.PyWeakref_GetRef>`_. It is
similar to ``PyWeakref_GetObject()``, but returns a strong reference instead of
a borrowed reference.

Since I listed `Bad C API
<https://pythoncapi.readthedocs.io/bad_api.html#borrowed-references>`_ in 2018,
I am now fighting against borrowed references since they cause multiple issues
such as:

* Subtle crashes in C extensions.
* Make the C API implementation in PyPy more complicated:
  `Inside cpyext: Why emulating CPython C API is so Hard
  <https://www.pypy.org/posts/2018/09/inside-cpyext-why-emulating-cpython-c-8083064623681286567.html>`_
  (2018) by Antonio Cuni.
* Unknown objects lifetime preventing optimization opportunities.
* Make the C API less regular and harder to use: some functions return a new
  reference, others return borrowed reference.

In 2020, my first attempt to `add a new PyTuple_GetItemRef() function
<https://github.com/python/cpython/issues/86460>`_ was rejected.


PyDict_GetItemRef(): easy!
==========================

Since it went well (quick discussion, no major disagreement) to add
``PyImport_AddModuleRef()`` and ``PyWeakref_GetRef()`` functions, I felt lucky and
proposed `adding a new PyDict_GetItemRef() function
<https://github.com/python/cpython/issues/106004>`_. It should be easy as well,
right? The discussion started and the issue and continued in the associated
`pull request <https://github.com/python/cpython/pull/106005>`_.

The idea to replace the ``PyDict_GetItem()`` function which returns a borrowed reference
and ignore all errors: ``hash(key)`` error, ``key == key2`` comparison error,
``KeyboardInterrupt``, etc.

There is also the ``PyDict_GetItemWithError()`` function which reports errors.
But this API has a different API: when it returns ``NULL``, the caller must
check ``PyErr_Occurred()`` to know if an exception is set, or if the key is
missing. This problem was the `very first issue
<https://github.com/capi-workgroup/problems/issues/1>`_ created in the Problems
project of the C API Working Group.

This Problems project is a collaborative work to collect C API issues. By the
way, the `PEP 733 – An Evaluation of Python’s Public C API
<https://peps.python.org/pep-0733/>`_ was published at October 16: summary of
these problems.


PyDict_GetItemRef(): API version 1
==================================

I proposed the API::

    int PyDict_GetItemRef(PyObject *mp, PyObject *key, PyObject **pvalue);
    int PyDict_GetItemStringRef(PyObject *mp, const char *key, PyObject **pvalue);

Return 0 on success, or -1 on error.

**Gregory Smith** was supportive:

    I'm in favor of this because I don't think we should have public APIs that
    (a) require a value check + ``PyErr_Occurred()`` call pattern - a frequent
    source of lurking bugs - or (b) return borrowed references. Yes I know we
    already have them, that's missing the point. The point is that with these
    in place, we can promote their use over the others because these are better
    in all respects.

Later, I discovered that the draft `PEP 703 – Making the Global Interpreter
Lock Optional in CPython <https://peps.python.org/pep-0703/>`__ proposed adding
a ``PyDict_FetchItem()`` similar to my proposed ``PyDict_GetItemRef()``
function.


API version 2: Change the Return Value
======================================

**Mark Shannon** asked:

    What's the rationale for not distinguishing between found and not found in
    the return value? See `Document the preferred style for API functions with
    three, four or five-way returns
    <https://github.com/python/devguide/issues/1121>`_.

I modified the API to return 1 if the key is present. API version 2::

    PyObject *value;
    int res = PyDict_GetItemRef(dict, key, &value);
    if (res < 0) ... error ...
    else if (res == 0) ... missing key ...
    else ... present key

By the way, **Erlend Aasland** added `C API guidelines
<https://devguide.python.org/developer-workflow/c-api/index.html#guidelines-for-expanding-changing-the-public-api>`_
in the Python Developer Guide (devguide) about function return value.


Naming
======

**Serhiy Storchaka** had concerns about the name:

    The only problem is that functions with so similar names have completely
    different interface. It is pretty confusing. Would not be better to name it
    ``PyDict_LookupItem`` or like? It may be worth to add also ``PyMapping_LookupItem``
    for convenience.

**Mark Shannon** added:

    Can we come up with a better name than ``PyDict_GetItemRef``?
    I see why you are adding ``Ref`` to the end, but all API functions should
    return new references, so it is a bit like calling the function
    PyDict_GetItemNotWrong.

    Obviously, the ideal name [``PyDict_GetItem()``] is already taken. Anyone
    have any suggestions for a better name?

I created `Naming convention for new C API functions
<https://github.com/capi-workgroup/problems/issues/52>`_ to discuss the ``Ref``
suffix for new functions returning a strong refererence.

PEP 703 proposes ``PyDict_FetchItem()`` name.


First Argument Type
===================

**Mark Shannon** had concerned about the type of the first argument:

    Using ``PyObject*`` is needlessly throwing away type information.

**Erlend Aasland** added:

    Why not strongly typed, since it is a ``PyDict_`` API?

**Sam Gross** wrote:

    In the context of PEP 703, I think it would be better to have variations
    that only change one axis of the semantics (e.g., new vs. borrowed, error
    vs. no error) and have the naming reflect that. For example, PEP 703
    proposes:

    ``PyDict_FetchItem`` for ``PyDict_GetItem`` and
    ``PyDict_FetchItemWIthError`` for ``PyDict_GetItemWithError``.


Pull Request Approvals and Naming Strikes Back
==============================================

**Erlend** and **Gregory** approved my pull request.

**Erlend** wrote:

    I'm approving this. A new naming scheme makes sense for a new API; I'm not
    sure it makes sense to try and enforce a new scheme in the current API. For
    now, there is already precedence of the ``Ref`` suffix in the current API;
    I'm ok with that. Also, the current API uses ``PyObject *`` all over the
    place. If we are to change this, we practically will end up with a
    completely new API; AFAICS, there is no problem with sticking to the
    current practice.

Then the discussion about the function name came back. So **Gregory** asked the
Steering Council: `decision: Should we add non-borrowed-ref public C APIs, if
so, is there a naming convention?
<https://github.com/python/steering-council/issues/201>`_. He asked two
questions:

* Q1: Should we add non-borrowed-reference public C APIs where only
  borrowed-reference ones exist.
* Q2: if yes to Q1, is there a preferred naming convention to use for new
  public C APIs that return a strong reference when the earlier APIs these
  would be parallel versions of only returned a borrowed reference.

Later, **Serhiy Storchaka** also approved the pull request:

    In general, I support adding this function. The benefits:

    * Returns a strong reference. It will save from some errors and may be
      better for PyPy.
    * Save CPU time for calling PyErr Occurred().

The PR had a total of 3 approvals.


API version 3: use PyDictObject
===============================

When I asked again **Mark** his opinion on the API, he wrote:

    I'm opposed because making ad-hoc changes like this is going to make the
    C-API worse, not better.

I ended by changing my pull request to propose an API version 3::

    int PyDict_GetItemRef(PyDictObject *op, PyObject *key, PyObject **pvalue)

Change the first parameter type from ``PyObject*`` to ``PyDictObject*``, as
asked by **Mark**.


Disagreement on using PyDictObject type
=======================================

**Serhiy** was against the change:

    I am dislike using concrete struct types instead of ``PyObject*`` in API,
    especially in public API. Isn't there a rule forbidding this?

In May, **Mark** created `The C API is weakly typed
<https://github.com/capi-workgroup/problems/issues/31>`_ discussion in the
Problems project.

During the discussion, **Erlend** created `Document guidelines for when to use
dynamically typed APIs <https://github.com/python/devguide/issues/1127>`_ in
the devguide to try to find a consensus regarding guidelines for weakly/stronly
typed APIs.

There are two questions:

* Use ``PyObject*`` or ``PyDictObject*`` type for the parameter.
* Check the type at runtime, or don't check for best performance (use an
  assertion in debug mode).

**Serhiy** wrote:

    It is not about runtime checking.

    It is about requiring to cast the argument to ``PyDictObject*`` every time
    you use the function: ``PyDict_GetItemRef((PyDictObject*)foo, bar, &baz)``.

    It is tiresome, and it is unsafe, because the compiler will not reject the
    code if ``foo`` is ``int`` or ``const char*``.

**Gregory** added:

    Our C API only accepts plain ``PyObject *`` as input to all our public
    APIs. Otherwise user code will be littered with typecasts all over the
    place.

**Gregory** also removed his approval.


Revert to API version 2 with PyObject type
==========================================

Since **Serhiy** and **Gregory** were against the change, I reverted it to move
back to the ``PyObject*`` type. **Serhiy** and **Erlend** confirmed their
approval.

I created the issue `Design a brand new C API with new PyCAPI_ prefix where all
functions respect new guidelines
<https://github.com/capi-workgroup/problems/issues/55>`_ in the Problems
project to discuss the creation of a branch new API. I suggested **Mark** to
only consider changing "weakly type" ``PyObject*`` type to strongly typed
``PyDictObject*`` in such new API.


More changes? API version 4
===========================

**Petr Viktorin** joined the discussion and proposed a late change:

    FWIW, here's a possible new variant: you could set result to ``NULL`` in
    which case the result isn't stored/incref'd. And that would start a
    convention of how to turn a get operation into a membership test. (And the
    Lookup name would fit that better.)

**Mark Shannon**:

    If this function is to take ``PyObject *``, as **Erlend** seems to insist,
    then it shouldn't raise a ``SystemError`` when passed something other than
    a dict. It should raise a ``TypeError``.

I modified the API (version 4) to raise ``SystemError`` if the first argument
is not a dictionary instead of ``TypeError``.


Merge The Change
================

After around 1 month of intense discussions, I merged my change adding the
``PyDict_GetItemRef()`` function (`commit
<https://github.com/python/cpython/commit/41ca16455188db806bfc7037058e8ecff2755e6c>`_)
with `a summary of the discussion
<https://github.com/python/cpython/pull/106005#issuecomment-1646249360>`_.

I also `added the function to pythoncapi-compat project
<https://github.com/python/pythoncapi-compat/commit/eaff3c172f94ed32ac38860c38d7a8fa27483e57>`_.


How To Take Decisions?
======================

The discussions occurred at many multiple places:

* My Python issue
* My Python pull request
* Multiple Problems issues
* Multiple devguide issues
* Steering Council issue

The discussion was heated. **Erlend** decided to take a break:

    I'm taking a break from the C API discussions; I'm removing myself from
    this PR for now

While the change was approved by 3 core developers, there was not strictly a
consensus since **Mark** did not formally approve the change. Multiple persons
asked to first define some general guidelines for new APIs **before** making
further C API changes.

**Gregory** opened an Steering Council issue at July 2. I asked for an update
at July 17. Three meetings later, they didn't have the opportunity to visit the
question. They were busy on discussing the heavy `PEP 703 – Making the Global
Interpreter Lock Optional in CPython <https://peps.python.org/pep-0703/>`__. At July 25,
**Gregory** replied in the name of the Steering Council:

    The steering council chatted about non-borrowed-ref and naming conventions
    today. We want to **delegate** this to the **C API working group** to come
    back with a broader recommendation. **Irit Katriel** has put together the
    initial draft of `An Evaluation of Python's Public C API
    <https://github.com/capi-workgroup/problems/blob/main/capi_problems.rst>`_
    for example.

The problem was that the C API Working Group was just a GitHub organization, it
was not an organized group with designated members.

`Stay tuned for the creation a formal C API Working Group
<https://github.com/python/steering-council/issues/210>`_.
