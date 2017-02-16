++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2016 Q4
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-02-16 11:00
:tags: cpython
:category: python
:slug: contrib-cpython-2016q4
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2016 Q4
(october, november, december)::

    hg log -r 'date("2016-10-01"):date("2016-12-31")' --no-merges -u Stinner

Statistics: 105 non-merge commits + 31 merge commits (total: 136 commits).

Previous report: `My contributions to CPython during 2016 Q3
<{filename}/python_contrib_2016q3.rst>`_.

Table of Contents:


Python startup performance regression
=====================================

Timeline of Python startup performance on speed.python.org:

.. image:: {filename}/images/python_startup_regression.png
   :alt: Timeline of Python startup performance
   :target: https://speed.python.org/timeline/#/?exe=5&ben=python_startup&env=1&revs=50&equid=off&quarts=on&extr=on

Nov 08 2016: Issue #28637: Revert issue #28082, don't import enum in re.
Importing the enum module in the re module slows down Python startup by 34%
when Python is run from a virtual environment, or more generally when the re
module is imported at startup but not the enum module.

Nov 14 2016. Issue #28637: Reapply changeset 223731925d06. "issue28082: use
IntFlag for re constants" by Ethan Furman. The re module is not more used in
the site module and so adding "import enum" to re.py doesn't impact
python_startup benchmark anymore.


Contributions
=============

* Issue #27896: Allow passing sphinx options to Doc/Makefile. Patch written by **Julien Palard**.

* Issue #28476: Reuse math.factorial() in test_random.
  Patch written by **Francisco Couzo**.

* Issue #28479: Fix reST syntax in windows.rst. Patch written by **Julien Palard**.

* Issue #26273: Add new constants: ``socket.TCP_CONGESTION`` (Linux 2.6.13) and
   ``socket.TCP_USER_TIMEOUT`` (Linux 2.6.37).
   Patch written by **Omar Sandoval**.

* Issue #28979: Fix What's New in Python 3.6: compact dict is not faster, but
  only more compact. Patch written by **Brendan Donegan**.

* Issue #28147: Fix a memory leak in split-table dictionaries: ``setattr()``
  must not convert combined table into split table.
  Patch written by **INADA Naoki**.

* Issue #29109: Enhance tracemalloc documentation:

  - Wrong parameter name, 'group_by' instead of 'key_type'
  - Don't round up numbers when explaining the examples. If they exactly match
    what can be read in the script output, it is to easier to understand
    (4.8 MiB vs 4855 KiB)
  - Fix incorrect method link that was pointing to another module

  Patch written by Loic Pefferkorn.

Micro optimizations
===================

* Issue #28544: Fix inefficient call to _PyObject_CallMethodId(). The ``()``
  format string creates an empty tuple for arguments: it requires extra work to
  parse the format string.

* Use ``PyThreadState_GET()`` macro in performance critical code.
  ``_PyThreadState_UncheckedGet()`` calls are not inlined as expected, even
  when using ``gcc -O3``.

* Modify ``type_setattro()`` to call directly
  ``_PyObject_GenericSetAttrWithDict()`` instead of
  ``PyObject_GenericSetAttr()``. ``PyObject_GenericSetAttr()`` is a thin
  wrapper to ``_PyObject_GenericSetAttrWithDict()``.


FASTCALL optimizations
======================

Same than 2016 Q3: *lot* of changes for FASTCALL optimizations, but I will
write instead a dedicated article.


Code placement
==============

XXX read blog post.

Issue #28618: Make hot functions using __attribute__((hot))

When Python is not compiled with PGO, the performance of Python on call_simple
and call_method microbenchmarks depend highly on the code placement. In the
worst case, the performance slowdown can be up to 70%.

The GCC __attribute__((hot)) attribute helps to keep hot code close to reduce
the risk of such major slowdown. This attribute is ignored when Python is
compiled with PGO.

The following functions are considered as hot according to statistics collected
by perf record/perf report:

* _PyEval_EvalFrameDefault()
* call_function()
* _PyFunction_FastCall()
* PyFrame_New()
* frame_dealloc()
* PyErr_Occurred()

DATE XXX, Issue #28618: Mark dict lookup functions as hot. It's common to see
these functions in the top 3 of "perf report".


Optimization
============

After 2 years of benchmarks and a huge effort of making Python benchmarks more
reliable and stable, I decided to close the issue #21955 "ceval.c: implement
fast path for integers with a single digit" as REJECTED.  I added a comment in
the C code to prevent further optimizations attempt::

    /* NOTE(haypo): Please don't try to micro-optimize int+int on
       CPython using bytecode, it is simply worthless.
       See http://bugs.python.org/issue21955 and
       http://bugs.python.org/issue10044 for the discussion. In short,
       no patch shown any impact on a realistic benchmark, only a minor
       speedup on microbenchmarks. */

Issue #28240, ``timeit`` benchmark module:

* Autorange now uses a single loop iteration instead of 10. For example,
  ``python3 -m timeit -s 'import time' 'time.sleep(1)'`` now takes 4 seconds
  instead of 40 seconds.

* Repeat the benchmarks 5 times by default, instead of only 3, to make
  benchmarks more reliable.

* Remove ``-c/--clock`` and ``-t/--time`` command line options which were
  deprecated since Python 3.3.

* Enhance formatting of raw timings in verbose mode

* Add ``nsec`` (nanosecond) unit for format timings

* Add newlines to the output for readability.


Interesting bug: duplicated warnings filters when tests reload the module
=========================================================================

Issue #28727: Implement rich comparison for _sre.SRE_Pattern. Regular
expression patterns, _sre.SRE_Pattern objects created by re.compile(), become
comparable (only x==y and x!=y operators). This change should fix the issue
#18383: don't duplicate warning filters when the warnings module is reloaded
(thing usually only done in unit tests).

Issue #28688: Remove warnings.filters check from regrtest. Reloading the
warnings module duplicates filters in warnings.filters. Fixing the issue is
tricky. It was decided to simply remove the check from Python 3.5, since the
bug only impacts Python unit tests, not real applications. The check is kept in
Python 3.6 and newer.

Issue #28727: Fix typo in pattern_richcompare(). Typo catched by Serhiy
Storchaka, thanks!

::

    -           && left->codesize && right->codesize);
    +           && left->codesize == right->codesize);

Issue #28727: Optimize pattern_richcompare() for a==a. A pattern is equal to
itself::

    +    if (lefto == righto) {
    +        /* a pattern is equal to itself */
    +        return PyBool_FromLong(op == Py_EQ);
    +    }


regrtest
========

* Issue #28409: regrtest: fix the parser of command line arguments.

* regrtest ``--fromfile`` now accepts a list of filenames, not only a list of
  *test* names.

Other changes
=============

* Fix ``_Py_normalize_encoding()`` function: It's not exactly the same than
  Python ``encodings.normalize_encoding()``: the C function also converts to
  lowercase.

* Issue #28256: Cleanup ``_math.c``: only define fallback implementations when
  needed. It avoids producing deadcode when the system provides required math
  functions, and so enhance the code coverage.

* _csv: use ``_PyLong_AsInt()`` to simplify the code, the function checks for
  the limits of the C ``int`` type.

* Issue #28544: Fix ``_asynciomodule.c`` on Windows. ``PyType_Ready()`` sets
  the reference to ``&PyType_Type``. ``&PyType_Type`` address cannot be
  resolved at compilation time (not on Windows?).

* Issue #28082: Add basic unit tests on the new ``re`` enums.

* Issue #28691: Fix ``warn_invalid_escape_sequence()``: handle correctly
  ``DeprecationWarning`` raised as an exception. First clear the current
  exception to replace the ``DeprecationWarning`` exception with a
  ``SyntaxError`` exception. Unit test written by **Serhiy Storchaka**.

* Issue #28023: Fix python-gdb.py on old GDB versions. Replace
  ``int(value.address)+offset`` with ``value.cast(unsigned char*)+offset``.
  It seems like ``int(value.address)`` fails on old versions of GDB.

* Issue #28765: _sre.compile() now checks the type of groupindex and
  indexgroup. groupindex must a dictionary and indexgroup must be a tuple.
  Previously, indexgroup was a list. Use a tuple to reduce the memory usage.

* Issue #28782: Fix a bug in the implementation ``yield from``
  (``_PyGen_yf()``), fix the test checking if the next instruction is
  ``YIELD_FROM``.  Regression introduced by the new "WordCode" bytecode (issue
  #26647). Reviewed by **Serhiy Storchaka** and **Yury Selivanov**.

* Issue #28792: Remove aliases from ``_bisect``. Remove aliases from the C
  module.  Always implement ``bisect()`` and ``insort()`` aliases in bisect.py.
  Remove also the ``# backward compatibility`` command: there is no plan to
  deprecate nor remove these aliases. When keys are equal, it makes sense to
  use ``bisect.bisect()`` and ``bisect.insort()``.

* Fix a ResourceWarning in ``generate_opcode_h.py``. Use a context manager to
  close the Python file. Replace also ``open()`` with ``tokenize.open()`` to
  handle coding cookie if any in ``Lib/opcode.py``.

* Issue #28740: Add sys.getandroidapilevel() function: return the build time
  API version of Android as an integer. Function only available on Android.

* Issue #28152: Fix ``-Wunreachable-code`` warnings on Clang. Don't declare
  dead code when the code is declared with Clang.

* Issue #28152: Fix -Wunreachable-code warning on clang.

  - Replace C ``if()`` with precompiler ``#if`` to fix a warning on dead code
    when using Clang.

  - Replace ``0`` with ``(0)`` to ignore a compiler warning about dead code on
    ``((int)(SEM_VALUE_MAX) < 0)``: ``SEM_VALUE_MAX`` is not negative on Linux.

* Issue #28835: Fix a regression introduced in ``warnings.catch_warnings()``:
  call ``warnings.showwarning()`` if it was overriden inside the context
  manager.

* Issue #28915: Replace ``int`` with ``Py_ssize_t`` in modsupport.
  ``Py_ssize_t`` type is better for indexes. The compiler might emit more
  efficient code for ``i++``. ``Py_ssize_t`` is the type of a PyTuple index for
  example. Replace also ``int endchar`` with ``char endchar``.

* Initialize variables to fix compiler warnings. Warnings seen on the "AMD64
  Debian PGO 3.x" buildbot. Warnings are false positive, but variable
  initialization should not harm performances.

* Remove useless variable initialization. Don't initialize variables which are
  not used before they are assigned.


* Issue #28838: Cleanup abstract.h. Rewrite all comments to use the same style
  than other Python header files: comment functions *before* their declaration,
  no newline between the comment and the declaration. Reformat some comments,
  add newlines, to make them easier to read. Quote argument like 'arg' to
  mention an argument in a comment.

* Issue #28838: abstract.h: remove long outdated comment. The documentation is
  of the Python C API is more complete and more up to date than this old
  comment. Removal suggested by **Antoine Pitrou**.

* python-gdb.py: catch ``gdb.error`` on ``gdb.selected_frame()``.

* Issue #28383: __hash__ documentation recommends naive XOR to combine, but
  this is suboptimal. Update the doc to suggest to reuse the hash() method
  using a tuple, with an example.
