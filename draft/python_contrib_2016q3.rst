++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2016 Q3
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-02-14 19:00
:tags: cpython
:category: python
:slug: contrib-cpython-2016q3
:authors: Victor Stinner
:summary: My contributions to CPython during 2016 Q3

My contributions to `CPython <https://www.python.org/>`_ during 2016 Q3
(july, august, september)::

    hg log -r 'date("2016-07-01"):date("2016-09-30")' --no-merges -u Stinner

Statistics: 161 non-merge commits + 29 merge commits (total: 190 commits).

Previous report: `My contributions to CPython during 2016 Q2
<{filename}/python_contrib_2016q2.rst>`_.


CPython sprint
==============

Read my previous blog post: `CPython sprint, september 2016
<{filename}/cpython_sprint_2016.rst>`_.


PEP 524: os.urandom() now blocks on Linux
=========================================

Read my previous blog post: `PEP 524: os.urandom() now blocks on Linux
<{filename}/pep_524_os_urandom_blocking.rst>`_.


PEP 509: private dictionary version
===================================

Another enhancement from my `FAT Python
<http://faster-cpython.readthedocs.io/fat_python.html>`_ project, my `PEP 509:
Add a private version to dict <https://www.python.org/dev/peps/pep-0509/>`_ was
approved at the CPython sprint by Guido.

The dictionary version is used by FAT Python to check quickly if a variable was
modified in a Python namespace. Technically, a Python namespace is a regular
dictionary.

While my experimental FAT Python didn't convince Guido, Yury Selivanov wrote
yet another cache for global variables using the dictionary version: `Implement
LOAD_GLOBAL opcode cache <http://bugs.python.org/issue28158>`_.

After I published the first version of my PEP, I made changes:

* Use 64-bit unsigned integer on 32-bit system: "A risk of an integer overflow
  every 584 years is acceptable." Using 32-bit, an overflow occurs every 4
  seconds.
* Don't expose the version at Python level to prevent users writing
  optimizations based on it. Reading the dictionary version in Python is as
  slow as a dictionary lookup, wheras the version is usually used to avoid a
  "slow" dictionary lookup.

I added the private version to the builtin dict type with the ussue #26058. The
global dictionary version is incremented at each dictionary creation and at
each dictionary change.


FASTCALL
========

Thanks to my work on marking Python benchmarks more stable.

* Issue #27128: Add _PyObject_FastCall(), a new calling convention avoiding a
  temporary tuple to pass positional parameters in most cases, but create a
  temporary tuple if needed (ex: for the tp_call slot).

  The API is prepared to support keyword parameters, but the full
  implementation will come later (_PyFunction_FastCall() doesn't support
  keyword parameters yet).

  Add also:

  - _PyStack_AsTuple() helper function: convert a "stack" of parameters to
    a tuple.
  - _PyCFunction_FastCall(): fast call implementation for C functions
  - _PyFunction_FastCall(): fast call implementation for Python functions

Following by a lot of changes to use FASTCALL "everywhere".

Issue #27128. Fix a reference leak if creating the tuple to pass positional
parameters fails.

Issue #27128: _pickle uses fast call. Use _PyObject_FastCall() to avoid the
creation of temporary tuple.

Issue #27128. When a Python function is called with no arguments, but all
parameters have a default value: use default values as arguments for the fast
path.

Issue #27809: Rename _PyObject_FastCall() to _PyObject_FastCallDict()

Issue #27809: _PyFunction_FastCallDict() supports keyword args

Issue #27809: PyEval_CallObjectWithKeywords() doesn't increment temporary the
reference counter of the args tuple (positional arguments). The caller already
holds a strong reference to it.

Issue #27809: PyObject_CallMethodObjArgs() now uses fast call

Backed out changeset 70f88b097f60 (map_next)
Backed out changeset 0e4f26083bbb (PyObject_CallMethodObjArgs)

Issue #27809: PyObject_CallMethodObjArgs() now uses fast call

Issue #27848: use Py_ssize_t rather than C int for the number of function
positional and keyword arguments.

Issue #27830: Add _PyObject_FastCallKeywords(). Similar to
_PyObject_FastCallDict(), but keyword arguments are also passed in the same C
array than positional arguments, rather than being passed as a Python dict.

_pickle: remove outdated comment. _Pickle_FastCall() is now fast again! The
optimization was introduced in Python 3.2, removed in Python 3.4 and
reintroduced in Python 3.6 (thanks to the new generic fastcall functions).

Issue #27830: Revert, remove _PyFunction_FastCallKeywords()

Avoid inefficient way to call functions without argument. Don't pass "()"
format to PyObject_CallXXX() to call a function without argument: pass NULL as
the format string instead. It avoids to have to parse a string to produce 0
argument.

Avoid calling functions with an empty string as format string. Directly pass
NULL rather than an empty string.

(...)

Issue #27830: Add _PyObject_FastCallKeywords(): avoid the creation of a
temporary dictionary for keyword arguments.


Issue #27810: Add a new METH_FASTCALL calling convention for C functions::

    PyObject* func(PyObject *self, PyObject **args,
                   Py_ssize_t nargs, PyObject *kwnames);

Where args is a C array of positional arguments followed by values of keyword
arguments. nargs is the number of positional arguments, kwnames are keys of
keyword arguments. kwnames can be NULL.

Issue #27810: Emit METH_FASTCALL code in Argument Clinic

Issue #27810: Exclude METH_FASTCALL from the stable API.


CALL_FUNCTION
=============

XXX wordcode?

Issue #27213: Rework CALL_FUNCTION* opcodes to produce shorter and more
efficient bytecode:

* CALL_FUNCTION now only accepts position arguments
* CALL_FUNCTION_KW accepts position arguments and keyword arguments, but keys
  of keyword arguments are packed into a constant tuple.
* CALL_FUNCTION_EX is the most generic, it expects a tuple and a dict for
  positional and keyword arguments.

CALL_FUNCTION_VAR and CALL_FUNCTION_VAR_KW opcodes have been removed.

2 tests of test_traceback are currently broken: skip test, the issue #28050 was
created to track the issue.

Patch by Demur Rumed, design by Serhiy Storchaka, reviewed by Serhiy Storchaka
and Victor Stinner.


Interesting bug: hidden warnings
================================

* regrtest: add Python ``-u`` command line option to child processes to get
  unbuffered stdout and stderr. It should help to get more information on
  a crash.

* Issue #27829: regrtest -W displays stderr if env changed. regrtest -W hides
  output if a test pass, but also when env changed and so the env changed
  warning is hidden. So it's hard to debug. With this change, stderr is now
  always displayed when a test doesn't pass.


Changes
=======

* Issue #22624: Python 3 requires clock() to build


* socket: Fix internal_select(). Bug found by Pavel Belikov ("Fragment N1"):
  http://www.viva64.com/en/b/0414/#ID0ECDAE

* socket: use INVALID_SOCKET.

  - Replace "fd = -1" with "fd = INVALID_SOCKET"
  - Replace "fd < 0" with "fd == INVALID_SOCKET": SOCKET_T is unsigned on Windows

  Bug found by Pavel Belikov ("Fragment N1"): http://www.viva64.com/en/b/0414/#ID0ECDAE

* Issue #11048: ctypes, fix CThunkObject_new()

  - Initialize restype and flags fields to fix a crash when Python runs on a
    read-only file system
  - Use Py_ssize_t type rather than int for the "i" iterator variable
  - Reorder assignements to be able to more easily check if all fields are
    initialized

  Initial patch written by Marcin Bachry.

* Issue #27404: tag security related changes with [Security] prefix in the
  changelog Misc/NEWS.

* Issue #27776: dev_urandom(raise=0) now closes the file descriptor on error

* Issue #27181: Skip test_statistics tests known to fail until a fix is found.

* Issue #27128, #18295: Use Py_ssize_t in _PyEval_EvalCodeWithName(). Replace
  int type with Py_ssize_t for index variables used for positional arguments.
  It should help to avoid integer overflow and help to emit better machine code
  for "i++" (no trap needed for overflow). Make also the total_args variable
  constant.

* regrtest: rename --slow option to --slowest. Thanks to optparse, --slow
  syntax still works ;-) Add --slowest option to buildbots. Display the top 10
  slowest tests.

* regrtest: nicer output for durations. Use milliseconds and minutes units, not
  only seconds.

* script_helper: kill the subprocess on error. If Popen.communicate() raises an
  exception, kill the child process to not leave a running child process in
  background and maybe create a zombi process. This change fixes a
  ResourceWarning in Python 3.6 when unit tests are interrupted by CTRL+c.

* Fix "make tags": set locale to C to call sort. vim expects that the tags file
  is sorted using english collation, so it fails if the locale is french for
  example. Use LC_ALL=C to force english sorting order. Issue #27726.

* Issue #27698: Add socketpair to socket.__all__ on Windows

* regrtest: Add a summary of the summary, "Tests result: xxx". It's sometimes hard to
  check quickly if tests succeeded, failed or something bad happened. I added a
  final "Result: xxx" line which summarizes all outputs into a single line,
  written at the end (it should always be the last line of the output).

* Issue #27786: Simplify x_sub(). The z variable is known to be a fresh number
  which cannot be shared, Py_SIZE() can be used directly to negate the number.

* Fix a clang warning in grammar.c. Clang is smarter than GCC and emits a
  warning for dead code after a function declared with
  __attribute__((__noreturn__)) (Py_FatalError).

* Issue #27829: libregrtest.save_env: flush stderr. Use flush=True to try to
  get a warning which is missing in buildbots. Use also f-string to make the
  code shorter.

* Issue #27938: Add a fast-path for us-ascii encoding

* Issue #18401: Fix test_pdb if $HOME is not set. HOME is not set on Windows
  for example.

* test_eintr: Fix ResourceWarning warnings

* regrtest: accept options after test names. For example, ``./python -m test
  test_os -v`` runs ``test_os`` in verbose mode. Before, regrtest tried to run
  a test called ``-v``...

* Issue #27744: socket: Fix memory leak in sendmsg() and sendmsg_afalg().
  Release msg.msg_iov memory block.
  Release memory on PyMem_Malloc(controllen) failure

* Issue #27866: ssl: Fix refleak in cipher_to_dict()

* Buildbot: give 20 minute per test file. It seems like at least 2 buildbots
  need more than 15 minutes per test file.  Example with "AMD64 Snow Leop 3.x"::

    10 slowest tests:
    - test_tools: 14 min 40 sec
    - test_tokenize: 11 min 57 sec
    - test_datetime: 11 min 25 sec
    - ...

* Issue #28077: Fix dict type, find_empty_slot() only supports combined
  dictionaries.

* Issue #27350: What's New in Python 3.6: Document compact dict memory usage

* Issue #15369: Remove the (old version of) pybench microbenchmark. Please use
  the new "performance" benchmark suite which includes a more recent version of
  pybench.

* Issue #15369. Remove old and unreliable pystone microbenchmark. Please use
  the new "performance" benchmark suite which is much more reliable.

* Issue #28114: Add unit tests on os.spawn*() to prepare to fix a crash
  with bytes environment.

* Issue #28127: Add _PyDict_CheckConsistency(), function checking that a
  dictionary remains consistent after any change. By default, only basic
  attributes are tested, table content is not checked because the impact on
  Python performance is too important. Define ``DEBUG_PYDICT``
  (ex: ``gcc -D DEBUG_PYDICT``) to check also dictionaries content.

* Issue #28195: Fix test_huntrleaks_fd_leak() of test_regrtest. Don't expect
  the fd leak message to be on a specific line number, just make sure that the
  line is present in the output.

* Issue #28200: Fix memory leak in ``path_converter()``. Replace
  ``PyUnicode_AsWideCharString()`` ``with PyUnicode_AsUnicodeAndSize()``.

* Issue #27955: Catch permission error (``EPERM``) in py_getrandom(). Fallback
  on reading from the ``/dev/urandom`` device when the ``getrandom()`` syscall
  fails with ``EPERM``, for example if blocked by SECCOMP.


* Issue #27778: Fix a memory leak in os.getrandom() when the getrandom() is
  interrupted by a signal and a signal handler raises a Python exception.

* Issue #28176: test_asynico: fix test_sock_connect_sock_write_race(), increase
  the timeout from 10 seconds to 60 seconds.

* Issue #28233: Fix PyUnicode_FromFormatV() error handling. Fix a memory leak
  if the format string contains a non-ASCII character, destroy the unicode
  writer.


Contributions
=============

* Issue #27350: Implement compact dict. `dict` implementation is changed like
  PyPy. It is more compact and preserves insertion order. _PyDict_Dummy()
  function has been removed. Disable test_gdb: python-gdb.py is not updated yet
  to the new structure of compact dictionaries (issue #28023). Patch written by
  INADA Naoki.

* "make tags": remove -t option of ctags. The option was kept for backward
  compatibility, but it was completly removed recently. Patch written by
  Stéphane Wirtel.

* Issue #27558: Fix SystemError in "raise" statement. Fix a SystemError in the
  implementation of "raise" statement.  In a brand new thread, raise a
  RuntimeError since there is no active exception to reraise. Patch written by
  Xiang Zhang.

* Issue #28120: Fix _PyDict_Pop() on pending key. Fix dict.pop() for splitted
  dictionary when trying to remove a "pending key" (Not yet inserted in
  split-table). Patch by Xiang Zhang.


New core developers
===================

At september 25, 2016, Yury Selivanov proposed to give `commit privileges for
INADA Naoki
<https://mail.python.org/pipermail/python-committers/2016-September/004013.html>`_

At november 14, 2016, I proposed to `promote Xiang Zhang as a core developer
<https://mail.python.org/pipermail/python-committers/2016-November/004045.html>`_.
At november 22, 2016, he became a new Python core developer! I mentored him
during one month, and later let him push directly changes.

Most Python core developers are men coming from North America and Europe.
INADA Naoki comes from Japan and Xiang Zhang comes from China: more core
developers from Asia! We increased the diversity of Python core developers!
