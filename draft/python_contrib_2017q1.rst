++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q1
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-07-05 12:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q1
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q1
(january, februrary, march)::

    # Exclude merges
    $ git log --no-merges --after=2016-12-31 --before=2017-04-01 --reverse --branches='*' --author=Stinner > 2017Q1
    $ grep '^commit ' 2017Q1|wc -l
    105

    # All commits
    $ git log --after=2016-12-31 --before=2017-04-01 --reverse --branches='*' --author=Stinner|grep '^commit '|wc -l
    121

Statistics: 105 non-merge commits + 16 merge commits (total: 121 commits).

Previous report: `My contributions to CPython during 2016 Q4
<{filename}/python_contrib_2016q4.rst>`_.

Optimization
============

::

    Issue #29300: Convert _struct module to Argument Clinic

    * The struct module now requires contiguous buffers.
    * Convert most functions and methods of the _struct module to Argument Clinic
    * Use "Py_buffer" type for the "buffer" argument. Argument Clinic is
      responsible to create and release the Py_buffer object.
    * Use "PyStructObject *" type for self to avoid explicit conversions.
    * Add an unit test on the _struct.Struct.unpack_from() method to test passing
      arguments as keywords.
    * Rephrase docstrings.
    * Rename "fmt" argument to "format" in docstrings and the documentation.

    As a side effect, functions and methods which used METH_VARARGS calling
    convention like struct.pack() now use the METH_FASTCALL calling convention
    which avoids the creation of temporary tuple to pass positional arguments and
    so is faster. For example, struct.pack("i", 1) becomes 1.56x faster (-36%)::

        $ ./python -m perf timeit \
            -s 'import struct; pack=struct.pack' 'pack("i", 1)' \
            --compare-to=../default-ref/python
        Median +- std dev: 119 ns +- 1 ns -> 76.8 ns +- 0.4 ns: 1.56x faster (-36%)
        Significant (t=295.91)

    Patch co-written with Serhiy Storchaka.

::

    Optimize deque index, insert and rotate() methods

    Issue #29452: Use METH_FASTCALL calling convention for index(), insert() and
    rotate() methods of collections.deque to avoid the creation a temporary tuple
    to pass position arguments. Speedup on deque methods:

    * d.rotate(): 1.10x faster
    * d.rotate(1): 1.24x faster
    * d.insert(): 1.18x faster
    * d.index(): 1.24x faster

slots::

    Optimize slots: avoid temporary PyMethodObject

    Issue #29507: Optimize slots calling Python methods. For Python methods, get
    the unbound Python function and prepend arguments with self, rather than
    calling the descriptor which creates a temporary PyMethodObject.

    Add a new _PyObject_FastCall_Prepend() function used to call the unbound Python
    method with self. It avoids the creation of a temporary tuple to pass
    positional arguments.

    Avoiding temporary PyMethodObject and avoiding temporary tuple makes Python
    slots up to 1.46x faster. Microbenchmark on a __getitem__() method implemented
    in Python:

    Median +- std dev: 121 ns +- 5 ns -> 82.8 ns +- 1.0 ns: 1.46x faster (-31%)

    Co-Authored-by: INADA Naoki <songofacandy@gmail.com>

Tricky bug
==========

::

    Issue #29507: Update test_exceptions

    test_unraisable() of test_exceptions expects that PyErr_WriteUnraisable(method)
    fails on repr(method).

    Before the previous change (7b8df4a5d81d), slot_tp_finalize() called
    PyErr_WriteUnraisable() with a PyMethodObject. In this case, repr(method) calls
    repr(self) which is BrokenRepr.__repr__() and the calls raises a new exception.

    After the previous change, slot_tp_finalize() uses an unbound method: repr() is
    called on a regular __del__() method which doesn't call repr(self). repr()
    doesn't fail anymore.

    PyErr_WriteUnraisable() doesn't call __repr__() anymore, so remove BrokenRepr
    unit test.

::

    Fix ref cycles in TestCase.assertRaises() (#193)

    bpo-23890: unittest.TestCase.assertRaises() now manually breaks a
    reference cycle to not keep objects alive longer than expected.


FASTCALL
========

Major bug:

* Issue #29286: _PyStack_UnpackDict() now returns -1 on error. Change
  _PyStack_UnpackDict() prototype to be able to notify of failure when args is
  NULL.

Issue #29306: Fix usage of Py_EnterRecursiveCall()

* ``*PyCFunction_*Call*()`` functions now call Py_EnterRecursiveCall().
* PyObject_Call() now calls directly _PyFunction_FastCallDict() and
  PyCFunction_Call() to avoid calling Py_EnterRecursiveCall() twice per
  function call

Changes:

* Issue #28839: Optimize function_call(), now simply calls
  _PyFunction_FastCallDict() which is more efficient (fast paths for the common
  case, optimized code object and no keyword argument).
* Issue #28839: Optimize _PyFunction_FastCallDict() when kwargs is an empty
  dictionary, avoid the creation of an useless empty tuple.
* Issue #29259: Write fast path in _PyCFunction_FastCallKeywords() for
  METH_FASTCALL, avoid the creation of a temporary dictionary for keyword
  arguments.
* __build_class__() builtin uses METH_FASTCALL
* type_prepare() now uses fast call (METH_FASTCALL)
* Convert some OrderedDict methods to Argument Clinic
* getattr() uses METH_FASTCALL
* next() uses FASTCALL
* sorted() uses METH_FASTCALL
* _hashopenssl uses METH_FASTCALL
* Issue #29259, #29263. methoddescr_call() creates a PyCFunction object, call
  it and the destroy it. Add a new _PyMethodDef_RawFastCallDict() method to
  avoid the temporary PyCFunction object.
* PyCFunction_Call() now calls _PyCFunction_FastCallDict()
* dict.get() and dict.setdefault() now use Argument Clinic. The signature of
  docstrings is also enhanced. For example, ``get(...)`` becomes
  ``get(self, key, default=None, /)``. Add also a note explaining why
  dict_update() doesn't use METH_FASTCALL.
* Document that _PyFunction_FastCallDict() must copy kwargs. Issue #29318:
  Caller and callee functions must not share the dictionary: kwargs must be
  copied.
* Fix PyCFunction_Call() performance issue. Issue #29259, #29465:
  PyCFunction_Call() doesn't create anymore a redundant tuple to pass
  positional arguments for METH_VARARGS. Add a new cfunction_call()
  subfunction.
* Issue #29465: Add Objects/call.c file
* Document why functools.partial() must copy kwargs. Add a comment to prevent
  further attempts to avoid a copy for optimization.
* bpo-29735: Optimize partial_call(): avoid tuple. Add _PyObject_HasFastCall().
  Fix also a performance regression in partial_call() if the callable doesn't
  support FASTCALL.

Issue #29286, Support positional arguments for fastcall:

* Rename _PyArg_ParseStack to _PyArg_ParseStackAndKeywords
* Add _PyArg_ParseStack() helper function
* Add _PyArg_NoStackKeywords() helper function.
* Argument Clinic: Use METH_FASTCALL calling convention instead of METH_VARARGS
  to parse position arguments and to parse "boring" position arguments.
* Add _PyArg_UnpackStack() function helper


Stack consumption
=================

::

    call_method() now uses _PyObject_FastCall()

    Issue #29233: Replace the inefficient _PyObject_VaCallFunctionObjArgs() with
    _PyObject_FastCall() in call_method() and call_maybe().

    Only a few functions call call_method() and call it with a fixed number of
    arguments. Avoid the complex and expensive _PyObject_VaCallFunctionObjArgs()
    function, replace it with an array allocated on the stack with the exact number
    of argumlents.

    It reduces the stack consumption, bytes per call, before => after:

    test_python_call: 1168 => 1152 (-16 B)
    test_python_getitem: 1344 => 1008 (-336 B)
    test_python_iterator: 1568 => 1232 (-336 B)

    Remove the _PyObject_VaCallFunctionObjArgs() function which became useless.
    Rename it to object_vacall() and make it private.

::

    Inline call_function()

    Issue #29227: Inline call_function() into _PyEval_EvalFrameDefault() using
    Py_LOCAL_INLINE to reduce the stack consumption.

    It reduces the stack consumption, bytes per call, before => after:

    test_python_call: 1152 => 1040 (-112 B)
    test_python_getitem: 1008 => 976 (-32 B)
    test_python_iterator: 1232 => 1120 (-112 B)

    => total: 3392 => 3136 (- 256 B)

::

    Disable _PyStack_AsTuple() inlining

    Issue #29234: Inlining _PyStack_AsTuple() into callers increases their stack
    consumption, Disable inlining to optimize the stack consumption.

    Add _Py_NO_INLINE: use __attribute__((noinline)) of GCC and Clang.

    It reduces the stack consumption, bytes per call, before => after:

    test_python_call: 1040 => 976 (-64 B)
    test_python_getitem: 976 => 912 (-64 B)
    test_python_iterator: 1120 => 1056 (-64 B)

    => total: 3136 => 2944 (- 192 B)




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
