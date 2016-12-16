++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Fast call: A new calling convention for the Python C API
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-12-15 16:00
:tags: optimization, python
:category: python
:slug: python-fast-call
:authors: Victor Stinner


pickle (1997)
=============

Caching a tuple for arguments is a very old optimization technic. It was first
used in 1997, Python 1.5, by Guido van Rossum in the newly created cPickle
module (`commit fd3626511dad
<https://hg.python.org/cpython/rev/fd3626511dad>`_).

The tuple is cached in a pickler object::

    typedef struct
    {
      PyObject_HEAD
      ...
      PyObject *arg;
      ...
    } Picklerobject;

Example showing how *arg* is used in ``write_other()`` (simplified code)::

  UNLESS(self->arg)
    UNLESS(self->arg = PyTuple_New(1))
    { ... }

  if (PyTuple_SetItem(self->arg, 0, py_str) == -1)
  { ... }

  Py_INCREF(py_str);
  UNLESS(junk = PyObject_CallObject(self->write, self->arg))
  { ...  }

where ``UNLESS()`` is the following macro::

    #define UNLESS(E) if (!(E))

A tuple of 1 element is created if ``self->arg`` is not set yet (``NULL``).
Then, the element of the tuple is replaced. The tuple is used to pass arguments
when calling the ``self->write`` function.


3.0 comment
-----------

In Python 3.0, the code was deeply refactored (`commit 0ae50aa7d97c
<https://hg.python.org/cpython/rev/0ae50aa7d97c>`_). A new helper function was
added with an interesting comment::

    /* A temporary cleaner API for fast single argument function call.

       XXX: Does caching the argument tuple provides any real performance benefits?

       A quick benchmark, on a 2.0GHz Athlon64 3200+ running Linux 2.6.24 with
       glibc 2.7, tells me that it takes roughly 20,000,000 PyTuple_New(1) calls
       when the tuple is retrieved from the freelist (i.e, call PyTuple_New() then
       immediately DECREF it) and 1,200,000 calls when allocating brand new tuples
       (i.e, call PyTuple_New() and store the returned value in an array), to save
       one second (wall clock time). Either ways, the loading time a pickle stream
       large enough to generate this number of calls would be massively
       overwhelmed by other factors, like I/O throughput, the GC traversal and
       object allocation overhead. So, I really doubt these functions provide any
       real benefits.

       On the other hand, oprofile reports that pickle spends a lot of time in
       these functions. But, that is probably more related to the function call
       overhead, than the argument tuple allocation.

       XXX: And, what is the reference behavior of these? Steal, borrow? At first
       glance, it seems to steal the reference of 'arg' and borrow the reference
       of 'func'. */
    static PyObject *
    _Pickler_FastCall(PicklerObject *self, PyObject *func, PyObject *arg)
    { ... }


Removed from Python 3.4
-----------------------

The optimization was removed from Python 3.4 by the `commit dd51b72cfb52
<https://hg.python.org/cpython/rev/dd51b72cfb52>`_. Commit message::

    Remove the tuple reuse optimization in _Pickle_FastCall.

    I have noticed a race-condition occurring on one of the buildbots because of
    this optimization. The function called may release the GIL which means
    multiple threads may end up accessing the shared tuple. I could fix it up by
    storing the tuple to the Pickler and Unipickler object again, but honestly it
    really not worth the trouble.

    I ran many benchmarks and the only time the optimization helps is when using a
    fin-memory file, like io.BytesIO on which reads are super cheap, combined with
    pickle protocol less than 4. Even in this contrived case, the speedup is a
    about 5%. For everything else, this optimization does not provide any
    noticable improvements.


itertools (2003)
================

In Python 2.3.0 (released in 2003), Raymond Hettinger added a new new itertools
module. The implementation of the module used a cached tuple for the
itertools.izip() generator. The optimization was also added to the enumerate()
generator.

When the itertools module was merged into Python 2.3, in the development
branch, it used a cached tuple for itertools.imap() generator, but the cache
was removed before 2.3.0 in the `commit 59ae41e04ffb
<https://hg.python.org/cpython/rev/59ae41e04ffb>`_: "Eliminated tuple re-use in
imap(). Doing it correctly made the code too hard to read."

In Python 2.7, the itertools uses a cached tuple for the following generators:

* itertools.combinations()
* itertools.combinations_with_replacement()
* itertools.izip()
* itertools.permutations()
* itertools.product()


Pycon US 2014
=============

In 2014 during a lunch at Pycon, Larry Hasting told me that he would like to
get rid of temporary tuples to call functions in Python. In Python, positional
arguments are passed as a tuple to C functions: ``PyObject *args``.

Larry wrote `Argument Clinic <https://docs.python.org/dev/howto/clinic.html>`_
which gives more control on how C functions are called. But I guess that Larry
didn't have time to finish his implementation, since he didn't publish a patch.


Tuple creation is slow
======================

Creating temporary tuples is known to be slow, at least by a few developers.

Changes in 2015
===============

Tuple creation is too slow
---------------------------

At 2015-02-24, Serhiy Storchaka opened the `issue #23507: Tuple creation is too
slow <http://bugs.python.org/issue23507>`_. He proposed changes to filter(),
map() and list.sort() to reuse a tuple in a loop or cache a tuple in a C
structure.

His patch checks the reference counter to decide if it is ok to keep the cached
tuple or not: if there is more than 1 reference to the tuple, the cache is
invalidated.


property get
------------

At the end of 2014, Joe Jevnik created the `cnamedtuple
<https://pypi.python.org/pypi/cnamedtuple>`_ project: collections.namedtuple
implemented in C. At 2015-04-10, he opened the issue `C implementation of
namedtuple (WIP) <http://bugs.python.org/issue23910>`_ to propose to merge his
C code into the stdlib.

Raymond Hettinger moved the discussion to the performance of getting an
attribute from a namedtuple. The discussion moved to optimizing
property_descr_get(), and then it became even more specific about the tuple
used to pass arguments to PyObject_CallFunctionObjArgs().

Raymond proposed to cache a tuple of one element before calls to avoid the cost
of the tuple creation (and then destruction).

Raymond suggested to ensure that the reference counter is 1.

At 2015-04-10, Joe Jevnik proposed to optimize property_descr_get() by caching
the tuple of 1 item in a static C variable: issue: `property_descr_get reuse
argument tuple <http://bugs.python.org/issue23910>`_, `commit 661cdbd617b8
<https://hg.python.org/cpython/rev/661cdbd617b8>`_.

2015-05-24: `Correct reuse argument tuple in property descriptor
<http://bugs.python.org/issue24276>`_. Bug found while working on the C
implementation of functools.lru_cache. First fix.

2016-04-21: `Crash when iterating on gc.get_objects()
<http://bugs.python.org/issue26811>`_. Second fix.


Proof of Concept (PoC)
======================

First API::

   PyObject* _PyObject_CallStack(PyObject *func,
                                 PyObject **stack,
                                 int na, int nk);

* [WIP] Add a new _PyObject_FastCall() function which avoids the creation of a tuple or dict for arguments
  http://bugs.python.org/issue26814
  Date: 2016-04-21 08:57
* Date: 2016-04-21 10:42: getting an attribute of namedtuple becomes 31% faster
  and function calls become 2x as fast!

Larry Hastings mentions a private experiment project modifying Argument Clinic
to use a new calling convention.
http://bugs.python.org/issue26814#msg263920

Date: 2016-04-22 11:40

`Python 3.6 FASTCALL compared to Python 3.6
<http://bugs.python.org/issue26814#msg263999>`_:

+-----------------------------------+--------------+----------------+
| Tests                             | /tmp/default |  /tmp/fastcall |
+===================================+==============+================+
| filter                            |   241 us (*) |  166 us (-31%) |
+-----------------------------------+--------------+----------------+
| map                               |   205 us (*) |  168 us (-18%) |
+-----------------------------------+--------------+----------------+
| sorted(list, key=lambda x: x)     |   242 us (*) |  162 us (-33%) |
+-----------------------------------+--------------+----------------+
| sorted(list)                      |  27.7 us (*) |        27.8 us |
+-----------------------------------+--------------+----------------+
| b=MyBytes(); bytes(b)             |   549 ns (*) |         533 ns |
+-----------------------------------+--------------+----------------+
| namedtuple.attr                   |  2.03 us (*) | 1.56 us (-23%) |
+-----------------------------------+--------------+----------------+
| object.__setattr__(obj, "x", 1)   |   347 ns (*) |  218 ns (-37%) |
+-----------------------------------+--------------+----------------+
| object.__getattribute__(obj, "x") |   331 ns (*) |  200 ns (-40%) |
+-----------------------------------+--------------+----------------+
| getattr(1, "real")                |   267 ns (*) |  150 ns (-44%) |
+-----------------------------------+--------------+----------------+
| bounded_pymethod(1, 2)            |   193 ns (*) |         190 ns |
+-----------------------------------+--------------+----------------+
| unbound_pymethod(obj, 1, 2        |   195 ns (*) |         192 ns |
+-----------------------------------+--------------+----------------+
| Total                             |   719 us (*) |  526 us (-27%) |
+-----------------------------------+--------------+----------------+

Python 3.4 / 3.6 / 3.6 FASTCALL compared to Python 2.7:
http://bugs.python.org/issue26814#msg264003

+------------------------------------+-------------+----------------+----------------+----------------+
|  Tests                             |        py27 |           py34 |           py36 |           fast |
+====================================+=============+================+================+================+
|  filter                            |  165 us (*) |  318 us (+93%) |  237 us (+43%) |         165 us |
+------------------------------------+-------------+----------------+----------------+----------------+
|  map                               |  209 us (*) |  258 us (+24%) |         202 us |  171 us (-18%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  sorted(list, key=lambda x: x)     |  272 us (*) |  348 us (+28%) |  237 us (-13%) |  163 us (-40%) |
+------------------------------------+-------------+----------------+----------------+----------------+
| 2sorted(list)                      | 33.7 us (*) | 47.8 us (+42%) | 27.3 us (-19%) | 27.7 us (-18%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  b=MyBytes(); bytes(b)             | 3.31 us (*) |  835 ns (-75%) |  510 ns (-85%) |  561 ns (-83%) |
+------------------------------------+-------------+----------------+----------------+----------------+
| 1namedtuple.attr                   | 4.63 us (*) |        4.51 us | 1.98 us (-57%) | 1.57 us (-66%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  object.__setattr__(obj, "x", 1)   |  463 ns (*) |         440 ns |  343 ns (-26%) |  222 ns (-52%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  object.__getattribute__(obj, "x") |  323 ns (*) |  396 ns (+23%) |         316 ns |  196 ns (-39%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  getattr(1, "real")                |  218 ns (*) |   237 ns (+8%) |  264 ns (+21%) |  147 ns (-33%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  bounded_pymethod(1, 2)            |  213 ns (*) |  244 ns (+14%) |   194 ns (-9%) |  188 ns (-12%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  unbound_pymethod(obj, 1, 2)       |  345 ns (*) |  247 ns (-29%) |  196 ns (-43%) |  191 ns (-45%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  func()                            |  161 ns (*) |  211 ns (+31%) |         161 ns |         157 ns |
+------------------------------------+-------------+----------------+----------------+----------------+
|  func(1, 2, 3)                     |  219 ns (*) |  247 ns (+13%) |  196 ns (-10%) |  190 ns (-13%) |
+------------------------------------+-------------+----------------+----------------+----------------+
|  Total                             |  689 us (*) |  980 us (+42%) |         707 us |  531 us (-23%) |
+------------------------------------+-------------+----------------+----------------+----------------+


Benchmarks
==========

2016-04-29.

Then I started to run the Grand Unified Python Benchmark Suite.


Serhiy Storchaka: "Could you repeat benchmarks on different computer? Better with different CPU or compiler."

Serhiy: "Results look as a noise. Some tests become slower, others become faster. If
results on different machine will show the same sets of slowing down and
speeding up tests, this likely is not a noise."

2016-05-19. "I removed tp_fastnew, tp_fastinit and tp_fastnew fields from
PyTypeObject to replace them with new type flags (ex: Py_TPFLAGS_FASTNEW) to
avoid code duplication and reduce the memory footprint.  Before, each function
was simply duplicated. This change introduces a backward incompatibility change"
http://bugs.python.org/issue26814#msg265856

"I spent a lot of ot time on the CPython benchmark suite to check for
performance regression. In fact, I spent most of my time to try to understand
why most benchmarks looked completly unstable. I now tuned correctly my system
and patched perf.py to get reliable benchmarks."

Date: 2016-05-19 13:38

* Add METH_FASTCALL calling convention to C functions, similar
  to METH_VARARGS|METH_KEYWORDS
* Argument Clinic uses METH_FASTCALL when possible (it may use METH_FASTCALL
  for all cases in the future)
* Add new type flags changing the calling conventions of tp_new, tp_init and
  tp_call:

  - Py_TPFLAGS_FASTNEW
  - Py_TPFLAGS_FASTINIT
  - Py_TPFLAGS_FASTCALL

Date: 2016-05-25 14:05
http://bugs.python.org/issue26814#msg266359

"I fixed even more issues with my setup to run benchmark. Results should be
even more reliable. Moreover, I fixed multiple reference leaks in the code
which introduced performance regressions. I started to write articles to
explain how to run stable benchmarks:"

Simpler patch
=============

2016-05-26: `Add _PyObject_FastCall() <http://bugs.python.org/issue27128>`_.

First benchmark: "everything is slower".

Black hole: fix benchmarks to make them stable
==============================================

* isolcpus
* write perf module
* fork benchmarks project, renamed to performance, moved to GitHub
* use multiple processes
* use average (median) rather than the minimum
* system tuning
* builtin feature: warmup samples
* drop all benchmark results from speed.python.org, upload again to
  speed.python.org


August 2016: Back on simpler patch
==================================

`Python-Dev: New calling convention to avoid temporarily tuples when calling
functions
<https://mail.python.org/pipermail/python-dev/2016-August/145793.html>`_.

2016-08-08: "I spent the last 3 months on making the CPython benchmark suite
more stable and enhance my procedure to run benchmarks to ensure that
benchmarks are more stable."

2016-08-19: `First commit: Add _PyObject_FastCall()
<https://hg.python.org/cpython/rev/a1a29d20f52d>`_::

     PyAPI_FUNC(PyObject *) _PyObject_FastCall(PyObject *func,
                                               PyObject **args, int nargs,
                                               PyObject *kwargs);

The *kwargs* parameter is unused and must be ``NULL``.


Next
====

_PyFunction_FastCallDict()
--------------------------

2016-08-20: Add _PyFunction_FastCallDict(): fast call with keyword arguments as a dict
http://bugs.python.org/issue27809

Add::

    _PyObject_FastCallDict(PyObject **args, int nargs, PyObject *kwargs)

where *kwargs* is a Python dictionary. Changes:

* Rename _PyObject_FastCall() to _PyObject_FastCallDict()
* Add _PyObject_FastCall(func, args, nargs) macro
* Add _PyObject_CallArg1(func, arg) macro
* Add _PyObject_CallNoArg(func) macro

tp_new, tp_init and tp_call slots expect a Python dictionary for keyword
arguments. Many C functions pass keyword arguments (Python dict) unchanged
to another function: see http://bugs.python.org/msg273370.


METH_FASTCALL
-------------

2016-08-20: Add METH_FASTCALL: new calling convention for C functions
http://bugs.python.org/issue27810


_PyObject_FastCallKeywords()
----------------------------

2016-08-22: Add _PyObject_FastCallKeywords(): avoid the creation of a temporary
dictionary for keyword arguments
http://bugs.python.org/issue27830

(XXXXXXXXXXXXXXXXXXXXX ... XXXXXXXXXXXX)

Use FastCall
------------


Then I patched a lot of call sites calling PyObject_Call(),
PyObject_CallObject(), PyEval_CallObject(), etc. with a temporary
tuple. Just one example::

    -            args = PyTuple_Pack(1, match);
    -            if (!args) {
    -                Py_DECREF(match);
    -                goto error;
    -            }
    -            item = PyObject_CallObject(filter, args);
    -            Py_DECREF(args);
    +            item = _PyObject_FastCall(filter, &match, 1, NULL);


Cleanup
-------

Inefficient 1::

    -    res = _PyObject_CallMethodId(fut->fut_loop, &PyId_get_debug, "()", NULL);
    +    res = _PyObject_CallMethodId(fut->fut_loop, &PyId_get_debug, NULL);

Issue #28799: Remove CALL_PROFILE special build,

* PyObject_CallFunctionObjArgs(func, NULL) => _PyObject_CallNoArg(func)
* PyObject_CallFunctionObjArgs(func, arg, NULL) => _PyObject_CallArg1(func, arg)

Replace
    PyObject_CallFunction(func, "O", arg)
and
    PyObject_CallFunction(func, "O", arg, NULL)
with
    _PyObject_CallArg1(func, arg)

Replace
    PyObject_CallFunction(func, NULL)
with
    _PyObject_CallNoArg(func)

Replace:
    PyObject_CallObject(callable, NULL)
with:
    _PyObject_CallNoArg(callable)

Replace:
    PyObject_CallFunctionObjArgs(callable, NULL)
with:
    _PyObject_CallNoArg(callable)

* PyObject_CallFunctionObjArgs(func, NULL) => _PyObject_CallNoArg(func)
* PyObject_CallFunctionObjArgs(func, arg, NULL) => _PyObject_CallArg1(func, arg)

=> Issue #28858: stack usage.

Issue #28858: Remove _PyObject_CallArg1() macro

Issue #28915: Replace _PyObject_CallMethodId() with
_PyObject_CallMethodIdObjArgs() when the format string only use the format 'O'
for objects, like "(O)".

Issue #28915: Avoid calling _PyObject_CallMethodId() with "(...)" format to
avoid the creation of a temporary tuple: use Py_BuildValue() with
_PyObject_CallMethodIdObjArgs().

Replace PyObject_CallFunction(func, NULL) with _PyObject_CallNoArg(func).

Issue #28915: Replace _PyObject_CallMethodId() with
_PyObject_CallMethodIdObjArgs() in unpickle()

Issue #28915: Replace _PyObject_CallMethodId() with
_PyObject_CallMethodIdObjArgs() in various modules when the format string was
only made of "O" formats, PyObject* arguments.


Argument Clinic
---------------

change::

    changeset:   105559:c62352ec21bc
    user:        Victor Stinner <victor.stinner@gmail.com>
    date:        Fri Dec 09 18:08:18 2016 +0100
    files:       Python/_warnings.c Python/clinic/_warnings.c.h
    description:
    Issue #20185: Convert _warnings.warn() to Argument Clinic

    Fix warn_explicit(): interpret source=None as source=NULL.





Stack
-----

Issue #28915: Add _PyObject_FastCallVa() helper to factorize code of functions:
Issue #28915: Add _PyObject_CallFunctionVa() helper to factorize code of
functions:
Add _Py_VaBuildStack() function
_PyObject_CallFunctionVa() uses fast call




December 2016
-------------

Python 3.7.

http://bugs.python.org/issue28915
__getitem__ slot becomes 1.23x faster

Reduce stack consumption of PyObject_CallFunctionObjArgs() and like
http://bugs.python.org/issue28870



Annex: API to call objects
==========================

Python 3.5: the main function is PyObject_Call().

* Arguments tuple and Keyword arguments dict:

  - PyObject_Call(func, args: tuple, kwargs: dict)
  - PyEval_CallObjectWithKeywords(func, args: tuple, kwargs: dict)

* Arguments as a tuple

  - PyObject_CallObject(func, args: tuple)
  - PyEval_CallObject(func, args: tuple): *macro*

* Format string:

  - PyObject_CallFunction(func, format: char*, ...)
  - PyObject_CallMethod(func, method: char*, format: char*, ...)
  - _PyObject_CallMethodId(func, method: _Py_Identifier, format: char*, ...)
  - PyEval_CallFunction(func, format, ...)
  - PyEval_CallMethod(func, method: char*, format: char*, ...)


* Arguments as ``...``:

  - PyObject_CallFunctionObjArgs(func, ...)
  - PyObject_CallMethodObjArgs(obj, attr: str, ...)
  - _PyObject_CallMethodIdObjArgs(obj, attr: _Py_Identifier, ...)

Python 3.6 has new functions. The main fastcall function is
_PyObject_FastCallKeywords():

* _PyObject_FastCallKeywords(func, args: C array, nargs: Py_ssize_t, kwnames: Tuple[str])
* _PyObject_CallNoArg(func): *macro*
* _PyObject_CallArg1(func, arg): *macro*
* _PyObject_FastCall(func, args: C array, nargs: Py_ssize_t): *macro*
* _PyObject_FastCallDict(func, args: C array, nargs: Py_ssize_t, kwargs: dict)
* _PyObject_Call_Prepend(func, arg0, args, kwargs)
