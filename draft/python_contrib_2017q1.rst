++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q1
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-07-05 12:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q1
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q1
(january, februrary, march).

Previous report: `My contributions to CPython during 2016 Q4
<{filename}/python_contrib_2016q4.rst>`_.

Statistics
==========

::

    # All commits
    $ git log --after=2016-12-31 --before=2017-04-01 --reverse --branches='*' --author=Stinner > 2017Q1
    $ grep '^commit ' 2017Q1|wc -l
    121

    # Exclude merges
    $ git log --no-merges --after=2016-12-31 --before=2017-04-01 --reverse --branches='*' --author=Stinner|grep '^commit '|wc -l
    105

    # master branch (excluding merges)
    $ git log --no-merges --after=2016-12-31 --before=2017-04-01 --reverse --author=Stinner origin/master|grep '^commit '|wc -l
    98

    # Only merges
    $ git log --merges --after=2016-12-31 --before=2017-04-01 --reverse --branches='*' --author=Stinner|grep '^commit '|wc -l
    16

Statistics: **98** commits in the master branch, 16 merge commits (done using
Mercurial before the migration to GitHub, and then converted to Git), and 7
other commits (likely backports), total: **121** commits.

Optimization
============

With the work done in 2016 on FASTCALL, it became much easier to optimize code
by using the new FASTCALL API.

Python slots
------------

Issue #29507: I worked with **INADA Naoki** to continue the work he did with
**Yury Selivanov** on optimizing method calls. We optimized "slots" implemented
in Python. Slots is an internal optimization to call "dunder" methods like
``__getitem__()``.

For Python methods, get the unbound Python function and prepend arguments with
*self*, rather than calling the descriptor which creates a temporary
PyMethodObject.

Add a new _PyObject_FastCall_Prepend() function used to call the unbound Python
method with *self*. It avoids the creation of a temporary tuple to pass
positional arguments.

Avoiding a temporary PyMethodObject and a temporary tuple makes Python slots up
to **1.46x faster**. Microbenchmark on a ``__getitem__()`` method implemented
in Python::

    Median +- std dev: 121 ns +- 5 ns -> 82.8 ns +- 1.0 ns: 1.46x faster (-31%)

struct module
-------------

In the issue #29300, **Serhiy Storchaka** and me converted most methods in the
C ``_struct`` module to Argument Clinic to make them use the FASTCALL calling
convention. Using METH_FASTCALL avoids the creation of temporary tuple to pass
positional arguments and so is faster. For example, ``struct.pack("i", 1)``
becomes **1.56x faster** (-36%)::

    $ ./python -m perf timeit \
        -s 'import struct; pack=struct.pack' 'pack("i", 1)' \
        --compare-to=../default-ref/python
    Median +- std dev: 119 ns +- 1 ns -> 76.8 ns +- 0.4 ns: 1.56x faster (-36%)
    Significant (t=295.91)

The difference is only ``42.2 ns``, but since the function only takes ``76.8
ns``, the difference is significant. The speedup can also be explained by more
efficient functions used to parse arguments. The new functions now use a cache
on the format string.

deque module
------------

Similar change in the deque module, I modified the index(), insert() and
rotate() methods to use METH_FASTCALL. Speedup:

* d.index(): **1.24x faster**
* d.rotate(1): 1.24x faster
* d.insert(): 1.18x faster
* d.rotate(): 1.10x faster

Tricky bug
==========

test_exceptions.test_unraisable()
---------------------------------

The optimization on Python slots (issue #29507) caused a regression in the
test_unraisable() unit test of test_exceptions.

The ``test_unraisable()`` method expects that ``PyErr_WriteUnraisable(method)``
fails on ``repr(method)``.

Before the change, ``slot_tp_finalize()`` called
``PyErr_WriteUnraisable()`` with a PyMethodObject. In this case,
``repr(method)`` calls ``repr(self)`` which is ``BrokenRepr.__repr__()`` and
the calls raises a new exception.

After the change, ``slot_tp_finalize()`` uses an unbound method:
``repr()`` is called on a regular ``__del__()`` method which doesn't call
``repr(self)`` and so ``repr()`` doesn't fail anymore.

The fix is to remove the BrokenRepr unit test, since
``PyErr_WriteUnraisable()`` doesn't call ``__repr__()`` anymore.

The removed test was really implementation specific, and my optimization
"fixed" the bug or "broke" the test. It's hard to say :-)

unittest assertRaises() reference cycle
---------------------------------------

At April 2015, **Vjacheslav Fyodorov** reported a reference cycle in the
assertRaises() method of the unittest module: bpo-23890.

When the context manager API of the ``assertRaises()`` method is used, the
context manager returns an object which contains the exception. So the
exception is kept alive longer than usual.

Python 3 exceptions now store traceback objects which contain local variables.
If a function stores the current exception in a local variable and the frame of
this function is part of the traceback, we get a reference cycle:

    exception -> traceback > frame -> variable -> exception

I fixed the reference cycle by manually clearing local variables. Example of
change of my commit::

    try:
        return context.handle('assertRaises', args, kwargs)
    finally:
        # bpo-23890: manually break a reference cycle
        context = None

It's not the first time that I fixed such reference cycle in the unit test
module. My previous fix was the issue #19880. Fix a reference leak in
unittest.TestCase. Explicitly break reference cycles between frames and the
``_Outcome`` instance: commit `031bd532
<https://github.com/python/cpython/commit/031bd532c48cf20a9cbf438bdae75dde49e36c51>`_.


FASTCALL
========

Recursion depth
---------------

In the issue #29306, I fixed the usage of Py_EnterRecursiveCall() to account
correctly the recursion depth, to fix the code responsible to prevent C stack
overflow:

* ``*PyCFunction_*Call*()`` functions now call ``Py_EnterRecursiveCall()``.
* ``PyObject_Call()`` now calls directly ``_PyFunction_FastCallDict()`` and
  ``PyCFunction_Call()`` to avoid calling ``Py_EnterRecursiveCall()`` twice per
  function call

Support position arguments
--------------------------

The issue #29286 enhanced Argument Clinic to use FASTCALL for functions which
only accept positional arguments:

* Rename _PyArg_ParseStack to _PyArg_ParseStackAndKeywords
* Add _PyArg_ParseStack() helper function
* Add _PyArg_NoStackKeywords() helper function.
* Add _PyArg_UnpackStack() function helper
* Argument Clinic: Use METH_FASTCALL calling convention instead of METH_VARARGS
  to parse position arguments and to parse "boring" position arguments.

Functions converted to FASTCALL
-------------------------------

* _hashopenssl module
* collections.OrderedDict methods (some of them, not all)
* __build_class__(), getattr(), next() and sorted() builtin functions
* type_prepare() C function, used in type constructor
* dict.get() and dict.setdefault() now use Argument Clinic. The signature of
  docstrings is also enhanced. For example, ``get(...)`` becomes
  ``get(self, key, default=None, /)``. Add also a note explaining why
  dict_update() doesn't use METH_FASTCALL.

Optimizations
-------------

* Issue #28839: Optimize function_call(), now simply calls
  _PyFunction_FastCallDict() which is more efficient (fast paths for the common
  case, optimized code object and no keyword argument).
* Issue #28839: Optimize _PyFunction_FastCallDict() when kwargs is an empty
  dictionary, avoid the creation of an useless empty tuple.
* Issue #29259: Write fast path in _PyCFunction_FastCallKeywords() for
  METH_FASTCALL, avoid the creation of a temporary dictionary for keyword
  arguments.
* Issue #29259, #29263. methoddescr_call() creates a PyCFunction object, call
  it and the destroy it. Add a new _PyMethodDef_RawFastCallDict() method to
  avoid the temporary PyCFunction object.
* PyCFunction_Call() now calls _PyCFunction_FastCallDict()
* bpo-29735: Optimize partial_call(): avoid tuple. Add _PyObject_HasFastCall().
  Fix also a performance regression in partial_call() if the callable doesn't
  support FASTCALL.

Bugfixes
--------

* Issue #29286: _PyStack_UnpackDict() now returns -1 on error. Change
  _PyStack_UnpackDict() prototype to be able to notify of failure when args is
  NULL.
* Fix PyCFunction_Call() performance issue. Issue #29259, #29465:
  PyCFunction_Call() doesn't create anymore a redundant tuple to pass
  positional arguments for METH_VARARGS. Add a new cfunction_call()
  subfunction.

Objects/call.c file
-------------------

The issue #29465 moved all C functions "calling functions" to a new
Objects/call.c file. Moving all functions at the same place should help to keep
the code consistent. It might also help the compiler to inline code more
easily, or maybe help to cache more machine code in CPU instruction cache.

This change was made during the GitHub migration. Since the change is big
(modify many ``.c`` files), I got many conflicts and it was annoying to rebase
it. I am not happy to get this ``call.c`` file, it already helped me :-)

Having ``call.c`` also helps to keep helper functions need their callers, and
prevent to expose them in the C API, even if they are exposed as private
functions.

Don't optimize keywords
-----------------------

* Document that _PyFunction_FastCallDict() must copy kwargs. Issue #29318:
  Caller and callee functions must not share the dictionary: kwargs must be
  copied.
* Document why functools.partial() must copy kwargs. Add a comment to prevent
  further attempts to avoid a copy for optimization.


Stack consumption
=================

A FASTCALL micro-optimization was blocked by Serhiy Storchaka because it
increased the C stack consumption. In the past, I never analyzed the C stack
consumption. Since I wanted to get this micro-optimization merged, I tried to
reduce the consumption.

At the beginning, I wrote a function to **measure** the C stack consumption in
a reliable way. It took me a few iterations.

Table showing the C stack consumption in bytes, and the difference compared to
Python 3.5 (last release before I started working on FASTCALL):

====================  ================  =====  ================  ================
Function                      2.7         3.5          3.6           3.7
====================  ================  =====  ================  ================
test_python_call      1,360 (**+352**)  1,008  1,120 (**+112**)    960 (**-48**)
test_python_getitem   1,408 (**+288**)  1,120  1,168 (**+48**)     880 (**-240**)
test_python_iterator  1,424 (**+192**)  1,232  1,200 (**-32**)   1,024 (**-208**)
Total                 4,192 (**+832**)  3,360  3,488 (**+128**)  2,864 (**-496**)
====================  ================  =====  ================  ================

Table showing the number of function calls before a stack overflow,
and the difference compared to Python 3.5:

====================  ===================  ======  ===================  ===================
Function                       2.7            3.5           3.6           3.7
====================  ===================  ======  ===================  ===================
test_python_call       6,161 (**-2,153**)   8,314   7,482 (**-832**)     8,729 (**+415**)
test_python_getitem    5,951 (**-1,531**)   7,482   7,174 (**-308**)     9,522 (**+2,040**)
test_python_iterator   5,885 (**-916**)     6,801   6,983 (**+182**)     8,184 (**+1,383**)
Total                  17,997 (**-4600**)  22,597  21,639 (**-958**)    26,435 (**+3,838**)
====================  ===================  ======  ===================  ===================

Changes:

* call_method() now uses _PyObject_FastCall(). Issue #29233: Replace the
  inefficient _PyObject_VaCallFunctionObjArgs() with _PyObject_FastCall() in
  call_method() and call_maybe().

* Issue #29227: Inline call_function() into _PyEval_EvalFrameDefault() using
  Py_LOCAL_INLINE to reduce the stack consumption.

* Issue #29234: Inlining _PyStack_AsTuple() into callers increases their stack
  consumption, Disable inlining to optimize the stack consumption. Add
  _Py_NO_INLINE: use __attribute__((noinline)) of GCC and Clang.


Contributions
=============

* Issue #28961: Fix unittest.mock._Call helper: don't ignore the name parameter
  anymore. Patch written by **Jiajun Huang**.
* Prohibit implicit C function declarations. Issue #27659: use
  -Werror=implicit-function-declaration when possible (GCC and Clang, but it
  depends on the compiler version). Patch written by **Chi Hsuan Yen**.


os.urandom() and getrandom()
============================

Issue #29157: Prefer getrandom() over getentropy()

* dev_urandom() now calls py_getentropy(). Prepare the fallback to support
  getentropy() failure and falls back on reading from /dev/urandom.
* Simplify dev_urandom(). pyurandom() is now responsible to call getentropy()
  or getrandom(). Enhance also dev_urandom() and pyurandom() documentation.
* getrandom() is now preferred over getentropy(). The glibc 2.24 now implements
  getentropy() on Linux using the getrandom() syscall.  But getentropy()
  doesn't support non-blocking mode. Since getrandom() is tried first, it's not
  more needed to explicitly exclude getentropy() on Solaris. Replace:
  "if defined(HAVE_GETENTROPY) && !defined(sun)"
  with "if defined(HAVE_GETENTROPY)"
* Enhance py_getrandom() documentation. py_getentropy() now supports ENOSYS,
  EPERM & EINTR


regrtest
========

* regrtest: don't fail immediately if a child does crash. Issue #29362: Catch a
  crash of a worker process as a normal failure and continue to run next tests.
  It allows to get the usual test summary: single line result (OK/FAIL), total
  duration, etc.
* Fix regrtest -j0 -R output: write also dots into stderr, instead of stdout.

Migration to GitHub
===================

* Rename README to README.rst and enhance formatting
* bpo-29527: Don't treat warnings as error in Travis docs job
* Travis CI: run rstlint.py in the docs job. Currently,
  http://buildbot.python.org/all/buildslaves/ware-docs buildbot is only run as
  post-commit. For example, bpo-29521 (PR#41) introduced two warnings,
  unnotified by the Travis CI docs job. Modify the docs job to run
  toosl/rstlint.py. Fix also the two minor warnings which causes the buildbot
  slave to fail. Doc/Makefile: set PYTHON to python3.
* Add Travis CI and Codecov badges to README.
* Exclude myself from mention-bot. I made changes in almost all CPython files
  last 5 years, so mention-bot asks me to review basically all pull requests. I
  simply don't have the bandwidth to review everything, sorry! I prefer to
  select myself which PR I want to follow.
* bpo-27425: Add .gitattributes, fix Windows tests. Mark binary files as binay
  in .gitattributes to not translate newline characters in Git repositories on
  Windows.

Enhancements
============

* Issue #29259: python-gdb.py now also checks for PyCFunction in the current
  frame, not only in the older frame. python-gdb.py now also supports
  method-wrapper (wrapperobject) objects (Issue #29367).
* Issue #26273: Document TCP_USER_TIMEOUT and TCP_CONGESTION
* bpo-29919: Remove unused imports found by pyflakes. Make also minor PEP8
  coding style fixes on modified imports.
* bpo-29887: Test normalization now fails if download fails; fix also a
  ResourceWarning.

Security
========

* Backport for Python 3.4. Issues #27850 and #27766: Remove 3DES from ssl
  default cipher list and add ChaCha20 Poly1305. See the `CVE-2016-2183:
  Sweet32 attack (DES, 3DES)
  <http://python-security.readthedocs.io/vuln/cve-2016-2183_sweet32_attack_des_3des.html>`_
  vulnerability.

Bugfixes
========

* Issue #29140: Fix hash(datetime.time). Fix time_hash() function: replace
  DATE_xxx() macros with TIME_xxx() macros. Before, the hash function used a
  wrong value for microseconds if fold is set (equal to 1).
* Issue #29174, #26741: Fix subprocess.Popen.__del__() fox Python shutdown.
  subprocess.Popen.__del__() now keeps a strong reference to warnings.warn()
  function.
* Issue #25591: Fix test_imaplib if ssl miss
* Fix script_helper.run_python_until_end(): copy the ``SYSTEMROOT`` environment
  variable.  Windows requires at least the SYSTEMROOT environment variable to
  start Python. If run_python_until_end() doesn't copy SYSTEMROOT, the
  function always fail on Windows.
* Fix datetime.fromtimestamp(): check bounds. Issue #29100: Fix
  datetime.fromtimestamp() regression introduced in Python 3.6.0: check minimum
  and maximum years.
* Fix test_datetime on system with 32-bit time_t. Issue #29100: Catch
  OverflowError in the new test_timestamp_limits() test.
* Fix test_datetime on Windows. Issue #29100: On Windows,
  datetime.datetime.fromtimestamp(min_ts) fails with an OSError in
  test_timestamp_limits().
* bpo-29176: Fix name of the _curses.window class. Set name to "_curses.window"
  instead of "_curses.curses window" (with a space!?).
* bpo-29619: os.stat() and os.DirEntry.inodeo() now convert inode (st_ino)
  using unsigned integers.
