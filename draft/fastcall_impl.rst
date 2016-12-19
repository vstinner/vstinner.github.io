+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Fast call: A new calling convention for the Python C API (implementation)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-12-19 22:00
:tags: optimization, python
:category: python
:slug: python-fast-call-implementation
:authors: Victor Stinner

The first article `Fast call: A new calling convention for the Python C API
(history) <{filename}/fastcall_history.rst>`_ explained the long history of
fast calls in CPython. This article described the new private C API that I
wrote in CPython 3.6 to avoid cached tuple and all their subtle issues.


Use cached tuples in filter(), map() and more
=============================================

At 2015-02-24, Serhiy Storchaka opened the `issue #23507: Tuple creation is too
slow <http://bugs.python.org/issue23507>`_. He proposed changes to filter(),
map() and list.sort() to reuse a tuple in a loop or cache a tuple in a C
structure.

His patch checks the reference counter to decide if it is ok to keep the cached
tuple or not: if there is more than 1 reference to the tuple, the cache is
invalidated.

But a few months later (2015-05-24), a bug was found in a similar optimization
implemented in property_descr_get(): `Correct reuse argument tuple in property
descriptor <http://bugs.python.org/issue24276>`_. Bug found while working on
the C implementation of functools.lru_cache. Next year, another bug was found:
`Crash when iterating on gc.get_objects()
<http://bugs.python.org/issue26811>`_.


Proof of Concept (PoC)
======================

Because of the two ``property_descr_get()``  bugs, I decided to try a very
different approach: avoid completely tuples, and use a C array of (pointers to)
Python objects.

I wrote a first proof of concept (PoC) to have an idea of the performance.
First API::

   PyObject* _PyObject_CallStack(PyObject *func,
                                 PyObject **stack,
                                 int na, int nk);

Benchmark results were surprisingely good!

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
