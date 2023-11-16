+++++++++++++++++++
PyDict_GetItemRef()
+++++++++++++++++++

:date: 2023-11-16 20:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-abstract-pyobject
:authors: Victor Stinner

https://github.com/python/cpython/issues/106004
https://github.com/python/cpython/pull/106005

The PyDict C API has a bad history. PyDict_GetItem() ignores all exception:
error on hash(), error on "key == key2", KeyboardInterrupt, etc.
PyDict_GetItemWithError() was added to fix this design. Moreover, Python 3.9
and older allowed to call PyDict_GetItem() with the GIL released.

PyDict_GetItem() returns a borrowed reference which is usually safe since the
dictionary still contains a strong reference to the request value. But in
general, borrowed references are error prone and can likely lead to complex
race conditions causing crashes:

While PyDict_GetItem() calls can be quite easily replaced with
PyObject_GetItem() which has a better API (return a new stong reference),
developers usually prefer to still use the specialized PyDict API for best
performance: avoid the minor overhead of type dispatching,
Py_TYPE(obj)->tp_as_mapping->mp_subscript.

I propose adding PyDict_GetItemRef() and PyDict_GetItemStringRef() functions to
the limited C API (version 3.13): replacements for PyDict_GetItem(),
PyDict_GetItemWithError() and PyDict_GetItemString().

API::

    int PyDict_GetItemRef(PyObject *mp, PyObject *key, PyObject **pvalue);
    int PyDict_GetItemStringRef(PyObject *mp, const char *key, PyObject **pvalue);

PyDict_GetItemWithError() has another API issue: when it returns NULL, it can
mean two things. It returns NULL if the key is missing, but it also returns
NULL on error. The caller has to check PyErr_Occurred() to distinguish the two
cases (to write correct code). See capi-workgroup/problems#1 Proposed API
avoids this by returning an int: return -1 on error, or return 0 otherwise
(present or missing key). Checking PyErr_Occurred() is no longer needed.

By the way, the public C API has no PyDict_GetItemStringWithError() function:
using PyDict_GetItemWithError() with a char* key is not convenient. The
_PyDict_GetItemStringWithError() function exists but it's a private C API.

PyErr_Occurred() and Py_INCREF() calls can be removed.

See also my previous attempt in 2020: issue #86460 "Add new C functions with
more regular reference counting like PyTuple_GetItemRef()".

Gregory Smith:

    I'm in favor of this because I don't think we should have public APIs that
    (a) require a value check + PyErr_Occurred() call pattern - a frequent
    source of lurking bugs - or (b) return borrowed references. Yes I know we
    already have them, that's missing the point. The point is that with these
    in place, we can promote their use over the others because these are better
    in all respects.

    One possible long term future would have us deprecate the messy borrowing
    APIs. Having these already in place sooner rather than later smooths that
    potential transition.

    There is no foreseeable future in which we'd go the other way towards
    all-borrowing-only APIs.

Mark Shannon:

    What's the rationale for not distinguishing between found and not found in
    the return value?
    See python/devguide#1121

Serhiy Storchaka:

    The only problem is that functions with so similar names have completely
    different interface. It is pretty confusing. Would not be better to name it
    PyDict_LookupItem or like? It may be worth to add also PyMapping_LookupItem
    for convenience. BTW, I think it is time to make _PyObject_LookupAttr
    public (if we agree about the name).

    Can we come up with a better name than PyDict_GetItemRef?

    I see why you are adding Ref to the end, but all API functions should
    return new references, so it is a bit like calling the function
    PyDict_GetItemNotWrong.

    Obviously, the ideal name [PyDict_GetItem()] is already taken. Anyone have
    any suggestions for a better name?

Sure, if you think that it's useful, I can return 1 if the key is present.

API version 2::

    PyObject *value;
    int res = PyDict_GetItemRef(dict, key, &value);
    if (res < 0) ... error ...
    else if (res == 0) ... missing key ...
    else ... present key

Mark Shannon:

    We made python/devguide#1121 to avoid having to repeat this discussion for
    every new API function.
    https://github.com/python/devguide/issues/1121

I created capi-workgroup/problems#52 to discuss C API naming convention (when
adding new functions).
https://github.com/capi-workgroup/problems/issues/52

@erlend-aasland added some guidelines related to proposed API in the Devguide.
https://devguide.python.org/developer-workflow/c-api/index.html#guidelines-for-expanding-changing-the-public-api

@erlend-aasland @markshannon: About the function name, I created
capi-workgroup/problems#52 but it's unclear to me what's the outcome of this
naming convention discussion.
https://github.com/capi-workgroup/problems/issues/52

Mark:

    Using `PyObject*` is needlessly throwing away type information, and we
    haven't established naming conventions yet.

By the way, draft PEP 703 – Making the Global Interpreter Lock Optional in
CPython proposes PyDict_FetchItem() which returns a strong reference, to
replace PyDict_GetItem()
https://peps.python.org/pep-0703/

The PEP has a section explaining why PyDict_GetItem() is not deprecated: Why
Not Deprecate PyDict_GetItem in Favor of PyDict_FetchItem?. I understand that
the proposed API is: `PyObject* PyDict_FetchItem(PyObject *dict, PyObject *key)`.
https://peps.python.org/pep-0703/#why-not-deprecate-pydict-getitem-in-favor-of-pydict-fetchitem

Erlend Aasland:

    Why not strongly typed, since it is a PyDict_ API?

::

    -PyDict_GetItemRef(PyObject *op, PyObject *key, PyObject **pvalue)
    +PyDict_GetItemRef(PyDictObject *op, PyObject *key, PyObject **pvalue)

    I created python/devguide#1127 to try to find a consensus regarding
    guidelines for weakly/stronly typed APIs.
    https://github.com/python/devguide/issues/1127

If the argument type is changed to PyDictObject*, it means that all existing
calls to PyDict_GetItem() and PyDict_GetItemWithError() will also have to cast
their argument to PyDictObject* when the code is updated to use
PyDict_GetItemRef().

Just one example: PyDict_New() returns a PyObject*. It sounds wrong to me that
the caller has more knowledge about the expected type than the official
PyDict_New() API.

::

    PyObject *obj = PyDict_New():
    PyDictObject *dict_for_getitemref = (PyDictObject*)obj;  // why??
    (...)
    PyObject *value;
    if (PyDict_GetItemStringRef(dict_for_getitemref, "key", &value) < 0) ... errror ...


Changing the parameter type would better fit into the idea of a brand new C
API: https://github.com/capi-workgroup/problems/issues/55

At June 29, Erlend and Gregory Smith approved the PR.

As I explained earlier, IMO it's better to have a similar name to ease the
migration and to ease the discovery of the newer "correct" API. @erlend-aasland
and @gpshead are fine with it.

For me, "Get" is the obvious name. For example, the Python API uses
__getitem__() method name, the Python dict type has get() and setdefault()
methods.

Serhiy Storchaka:

    The "Ref" suffix is not informative. In different functions it have
    different meaning (Py_IncRef(), PyWeakref_CheckRef() -- nothing in common).
    But comparing with PyModule_AddObjectRef() and PyImport_AddModuleRef() I
    would expect that PyDict_GetItemRef() has the same signature as
    PyDict_GetItem() -- takes two PyObject* arguments, returns PyObject*, the
    only difference is in refcounts here or there. It is not, and you should
    completely rewrite the code which uses it.

July 4. @gpshead created python/steering-council#201 to ask the Steering Council
opinion about PyDict_GetItemRef(), and adding similar APIs (to avoid borrowed
references) in general.
https://github.com/python/steering-council/issues/201

     Q1: Should we add non-borrowed-reference public C APIs where only
     borrowed-reference ones exist.

     Q2: if yes to Q1, is there a preferred naming convention to use for new
     public C APIs that return a strong reference when the earlier APIs these
     would be parallel versions of only returned a borrowed reference.

July 20. Petr Viktorin.

    Anecdotal evidence against solving a single problem (borrowed refs) en
    masse:

    The new PyImport_AddModuleRef works like PyImport_AddModule, it just
    returns a strong reference.
    But both have questionable behaviour: they either return an already
    imported module (from sys.modules), or a freshly created (empty) one -- and
    they don't indicate which of those cases happened.
    We will want to yet another function to fix that wart, and if no one gets
    to it in time, the *Ref iteration will be hard to get rid of.

July 21.

    It seems like the Steering Council is busy with the nogil PEP. I decided to
    move on and merge python/cpython#106005 since my PR was approved (well, it
    had 3 approvals, but it lost 2 in the bumpy discussion). If the Steering
    Council is in disagreement, the function can be reverted before Python 3.13
    final: we have plently of time to consider such revert.

Gregory Smith. July 25

    The steering council chatted about non-borrowed-ref and naming conventions
    today. We want to delegate this to the C API working group to come back
    with a broader recommendation. @iritkatriel has put together the initial
    draft of
    https://github.com/capi-workgroup/problems/blob/main/capi_problems.rst for
    example.

PyDict_GetItemRef() now returns 1 if the item is found, and 0 if the item is
not found.

By the way, I recently modified PyWeakref_GetRef() to return 1 if the reference
is alive, and return 0 if it's dead.

@markshannon raised different questions.

Change the first parameter type to PyDictObject* and use assertions rather than
runtime checks on the object type. I propose to keep PyObject* to make the new
API closer to existing APIs, knowing that most PyDict API use PyObject*,
especially PyDict_New(). -- I'm open to reconsider this. See
capi-workgroup/problems#31 and python/devguide#1127 onging discussions.

Concern about the lack of naming convention when adding new functions to the C
API: I created capi-workgroup/problems#52 for that.

@markshannon: would you approve this change if I change the parameter type to
PyDictObject* and convert runtime type check to an assertion?

July 12. Serhiy Storchaka approved the PR.

    In general, I support adding this function. The benefits:

    * Returns a strong reference. It will save from some errors and may be better for PyPy.
    * Save CPU time for calling PyErr Occurred().

This PR is connected to multiple Problems issues, references in comments above.

Sam Gross:

    In the context of PEP 703, I think it would be better to have variations
    that only change one axis of the semantics (e.g., new vs. borrowed, error
    vs. no error) and have the naming reflect that. For example, PEP 703
    proposes:

    PyDict_FetchItem for PyDict_GetItem and
    PyDict_FetchItemWIthError for PyDict_GetItemWithError.

July 12. API 3.

    Change first argument type to PyDictObject*

    Replace runtime type check with an assertion: assert(PyDict_Check(mp));

Serhiy:

    I am dislike using concrete struct types instead of PyObject* in API,
    especially in public API. Isn't there a rule forbidding this?

There is a discussion to change this: capi-workgroup/problems#31 and
python/devguide#1127. It sounds like a good idea to avoid a runtime type check
by expecting a specific type. I wrote it in the What's New in Python 3.13 entry
of this PR:
    https://github.com/capi-workgroup/problems/issues/31
    https://github.com/python/devguide/issues/1127

Serhiy:

    It is about requiring to cast the argument to PyDictObject* every time you
    use the function: `PyDict_GetItemRef((PyDictObject*)foo, bar, &baz)`. It is
    tiresome, and it is unsafe, because the compiler will not reject the code
    if `foo is int` or `const char*`.

Gregory:

    Our C API only accepts plain PyObject * as input to all our public APIs.
    Otherwise user code will be littered with typecasts all over the place.

Oh. @serhiy-storchaka and @gpshead seem to be strongly against it, so I
reverted the change to go back to the initial plan: PyObject* type.

> @serhiy-storchaka @gpshead @erlend-aasland: Are you ok with the API using
PyDictObject* type? Or should I revert this 3rd commit?

Oh. @serhiy-storchaka and @gpshead seem to be strongly against it, so I
reverted the change to go back to the initial plan: ``PyObject*`` type.

I tried to use a revert, but sadly the Git history became too complicated, so
instead of squashed commits and I rebased my PR. Sorry about that :-(

---

Gregory:
> commenting here to tell github to remove my approval as this PR seems to be
going in exploratory directions and is awaiting various feedback and decisions.

Well, I was requested to set *multiple* guidelines for different aspects of the
API on this single function addition.

* Return 1 if the key is present?

  * My first version returned 0 if the key is present and if the key is missing, both considered as "success".
  * A guideline was added to the devguide: https://github.com/python/devguide/issues/1121
  * I modified my PR to return 1 if the key is present (and return 0 if the key is missing).

* Function name

  * My PR adds **Ref** suffix to the existing function
  * @markshannon dislikes the name and asked to define a naming convention for new functions.
  * I created: "Naming convention" https://github.com/capi-workgroup/problems/issues/52
  * @serhiy-storchaka proposed PyDict_GetOptionalItem() but is ok with PyDict_GetItemRef().
  * PEP 703 proposes ``PyDict_FetchItem()`` name.
  * The majority seems to be fine with the proposed name: **PyDict_GetItemRef**().

* Type of the first parameter

  * My first version used ``PyObject*``
  * @markshannon wants ``PyDictObject*``, he created discussion:
    https://github.com/capi-workgroup/problems/issues/31
  * I changed the parameter type to ``PyDictObject*`` to see the consequences
    of the change: replace runtime check with assertion, remove tests on
    invalid dict type (since it would crash rather than raising a clean
    SystemError exception).
  * @serhiy-storchaka and @gpshead want ``PyObject*``: they are against the
    need for cast between ``PyObject*`` and ``PyDictObject*`` and do prefer
    type checking at runtime, since it's too rare that developers have access
    to a Python binary with assertions enabled
  * After @serhiy-storchaka and @gpshead pushback: I reverted this change, to
    come back to my initial plan: ``PyObject*``.

* @markshannon would prefer to define some guidelines first, before proposing
  adding a concrete function:

  * "I'm opposed because making ad-hoc changes like this is going to make the
    C-API worse, not better."

* Since @markshannon has some disagreements, @gpshead opened a discussion at
the Steering Council https://github.com/python/steering-council/issues/201

---

PR changelog:

* First version
* Return 1 if the key is present
* Change parameter name from *pvalue* to *result* (and simplify
  dictitems_contains() implementation)
* Change first parameter type to ``PyDictObject**``
* Move the comments from C (dictobject.c) to header file (dictobject.h)
* Revert the parameter type change: come back to ``PyObject*``

Petr:

    FWIW, here's a possible new variant: you could set result to NULL in which
    case the result isn't stored/incref'd. And that would start a convention of
    how to turn a get operation into a membership test. (And the Lookup name
    would fit that better.)

Mark:

    If this function is to take PyObject *, as @erlend-aasland seems to insist,
    then it shouldn't raise a SystemError when passed something other than a
    dict.  It should raise a TypeError.

This issue goes in all directions, it's a little bit hard to follow :-(

Erlend:

    I'm taking a break from the C API discussions; I'm removing myself from
    this PR for now

Thanks everyone for the great reviews. I think that the final API is better
than my first version.

The road for that function was more bumpy than for other functions since
PyDict_GetDict() is one of the commonly used function, and as I wrote before,
we took this function as an opportunity to revisit some API design choices.
There are some disagreements which have been discussed in length, especially in
the https://github.com/capi-workgroup/problems/issues/ project. Overall, the
majority seems to be in favor of this change (and I didn't see any concrete
counter-proposal to solve the issue).

Sadly, this PR lost two approvals in the bumpy discussion. IMO it's now time to
move on and see how this function can be used to avoid bugs and how to migrate
users from the cursed PyDict_GetItem() to that better PyDict_GetItemRef()
function.

Supporters of a new API instead of fixing the current API one function by one,
I suggest continuing the discussion in
https://github.com/capi-workgroup/problems/issues/ : there are a few issues
related to that. So far, I didn't see any clear nor complete proposal, so for
me, we are still at the same status quo: we do our best, fixing functions, one
by one, when we agree that there is an issue. Same for the question of using
PyDictObject* type rather than PyObject* for the first parameter: it's still
being discussed and so far, no consensus was reached.

Completely getting rid of PyDict_GetItem() may take time. Maybe we need to
consider capi-workgroup/problems#54 approach for users who want to start a new
C API with a clean C API without known issues like borrowed references. But
well, that's out of the scope of this issue. This issue does not deprecate
PyDict_GetItem() on purpose.

October 13.

https://github.com/capi-workgroup/api-evolution/issues/29

    See python/devguide#1127 issue.
    See also capi-workgroup/problems#31 issue.
