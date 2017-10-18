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
<{filename}/python_contrib_2016q2.rst>`_. Next report: `My contributions to
CPython during 2016 Q4 <{filename}/python_contrib_2016q4.rst>`_.

Table of Contents:

* Two new core developers
* CPython sprint, September, in California
* PEP 524: Make os.urandom() blocking on Linux
* PEP 509: private dictionary version
* FASTCALL: optimization avoiding temporary tuple to call functions
* More efficient CALL_FUNCTION bytecode
* Work on optimization
* Interesting bug: hidden resource warnings
* Contributions
* Bugfixes
* regrtest changes
* Tests changes
* Other changes


Two new core developers
=======================

New core developers is the result of the productive third 2016 quarter.

At september 25, 2016, Yury Selivanov proposed to give `commit privileges for
INADA Naoki
<https://mail.python.org/pipermail/python-committers/2016-September/004013.html>`_.
Naoki became a core developer the day after!

At november 14, 2016, I proposed to `promote Xiang Zhang as a core developer
<https://mail.python.org/pipermail/python-committers/2016-November/004045.html>`_.
One week later, he also became a core developer! I mentored him during one
month, and later let him push directly changes.

Most Python core developers are men coming from North America and Europe.
INADA Naoki comes from Japan and Xiang Zhang comes from China: more core
developers from Asia, we increased the diversity of Python core developers!


CPython sprint, September, in California
========================================

I was invited at my first CPython sprint in September! Five days, September
5-9, at Instagram office in California, USA. I reviewed a lot of changes and
pushed many new features! Read my previous blog post: `CPython sprint,
september 2016 <{filename}/cpython_sprint_2016.rst>`_.


PEP 524: Make os.urandom() blocking on Linux
============================================

I pushed the implementation my PEP 524: read my previous blog post: `PEP 524:
os.urandom() now blocks on Linux in Python 3.6
<{filename}/pep_524_os_urandom_blocking.rst>`_.


PEP 509: private dictionary version
===================================

Another enhancement from my `FAT Python
<http://faster-cpython.readthedocs.io/fat_python.html>`_ project: my `PEP 509:
Add a private version to dict <https://www.python.org/dev/peps/pep-0509/>`_ was
approved at the CPython sprint by Guido van Rossum.

The dictionary version is used by FAT Python to check quickly if a variable was
modified in a Python namespace. Technically, a Python namespace is a regular
dictionary.

Using the feedback from the python-ideas mailing list on the first version of
my PEP, I made further changes:

* Use 64-bit unsigned integers on 32-bit system: "A risk of an integer overflow
  every 584 years is acceptable." Using 32-bit, an overflow occurs every 4
  seconds!
* Don't expose the version at Python level to prevent users writing
  optimizations based on it in Python. Reading the dictionary version in Python
  is as slow as a dictionary lookup, wheras the version is usually used to
  avoid a "slow" dictionary lookup. The version is only accessible at the C
  level.

While my experimental FAT Python static optimizer didn't convince Guido, Yury
Selivanov wrote yet another cache for global variables using the dictionary
version: `Implement LOAD_GLOBAL opcode cache
<http://bugs.python.org/issue28158>`_ (sadly, not merged yet).

I added the private version to the builtin dict type with the issue #26058. The
global dictionary version is incremented at each dictionary creation and at
each dictionary change, and each dictionary has its own version as well.


FASTCALL: optimization avoiding temporary tuple to call functions
=================================================================

Thanks to my work on making Python benchmarks more stable, I confirmed that my
FASTCALL patches don't introduce performance regressions, and make Python
faster in some specific cases.

I started to push FASTCALL changes. It will take me 6 months to push most
changes to enable fully FASTCALL "everywhere" in the code base and to finish
the implementation.

Following blog posts will describe FASTCALL changes, its history and
performance enhancements. Spoiler: Python 3.6 is fast!


More efficient CALL_FUNCTION bytecode
=====================================

I reviewed and merged Demur Rumed's patch to make the CALL_FUNCTION opcodes
more efficient. Demur implemented the design proposed by Serhiy Storchaka.
Serhiy Storchaka also reviewied the implementation with me.

Issue #27213: Rework CALL_FUNCTION* opcodes to produce shorter and more
efficient bytecode:

* ``CALL_FUNCTION`` now only accepts positional arguments
* ``CALL_FUNCTION_KW`` accepts positional arguments and keyword arguments,
  keys of keyword arguments are packed into a constant tuple.
* ``CALL_FUNCTION_EX`` is the most generic opcode: it expects a tuple and a
  dict for positional and keyword arguments.

``CALL_FUNCTION_VAR`` and ``CALL_FUNCTION_VAR_KW`` opcodes have been removed.

Demur Rumed also implemented "Wordcode", a new bytecode format using fixed
units of 16-bit: 8-bit opcode with 8-bit argument. Wordcode was merged in May
2016, see `issue #26647: ceval: use Wordcode, 16-bit bytecode
<http://bugs.python.org/issue26647>`_.

All instructions have an argument: opcodes without argument use the argument
``0``. It allowed to remove the following conditional code in the very hot code
of ``Python/ceval.c``::

    if (HAS_ARG(opcode))
        oparg = NEXTARG();

The bytecode is now fetched using 16-bit words, instead of loading one or two
8-bit words per instruction.


Work on optimization
====================

I continued with work on the `performance
<https://github.com/python/performance>`_ Python benchmark suite. The suite
works on CPython and PyPy, but it's maybe not fine tuned for PyPy yet.

* Issue #27938: Add a fast-path for us-ascii encoding

* Issue #15369: Remove the (old version of) pybench microbenchmark. Please use
  the new "performance" benchmark suite which includes a more recent version of
  pybench.

* Issue #15369. Remove old and unreliable pystone microbenchmark. Please use
  the new "performance" benchmark suite which is much more reliable.


Interesting bug: hidden resource warnings
=========================================

At 2016-08-22, I started to investigate why "Warning -- xxx was modfied by
test_xxx" warnings were not logged on some buildbots (issue #27829).

I modified the code logging the warning to flush immediatly stderr:
``print(..., flush=True)``.

19 days later, I tried to remove a quiet flag ``-q`` on the Windows build...
but it was a mistake, this flag doesn't mean quiet in the modified batch script
:-)

13 days later, I finally understood that the ``-W`` option of regrtest was
eating stderr if the test pass but the environment was modified.

I fixed regrtest to log stderr in all cases, except if the test pass! It should
now be easier to fix "environment changed" warnings emitted by regrtest.


Contributions
=============

As usual, I reviewed and pushed changes written by other contributors:

* Issue #27350: I reviewed and pushed the implementation of compact
  dictionaries preserving insertion order. This resulted in dictionaries using
  20% to 25% less memory when compared to Python 3.5. The implementation was
  written by **INADA Naoki**, based on the PyPy implementation, with a design
  by Raymond Hettinger.

* "make tags": remove ``-t`` option of ``ctags``. The option was kept for
  backward compatibility, but it was completly removed recently. Patch written
  by **Stéphane Wirtel**.

* Issue #27558: Fix a ``SystemError`` in the implementation of "raise" statement.
  In a brand new thread, raise a RuntimeError since there is no active
  exception to reraise. Patch written by **Xiang Zhang**.

* Issue #28120: Fix ``dict.pop()`` for splitted dictionary when trying to remove a
  "pending key": a key not yet inserted in split-table. Patch by **Xiang
  Zhang**.


Bugfixes
========

* socket: Fix ``internal_select()`` function. Bug found by **Pavel Belikov**
  ("Fragment N1"): http://www.viva64.com/en/b/0414/#ID0ECDAE

* socket: use INVALID_SOCKET.

  - Replace ``fd = -1`` with ``fd = INVALID_SOCKET``
  - Replace ``fd < 0`` with ``fd == INVALID_SOCKET``:
    SOCKET_T is unsigned on Windows

  Bug found by Pavel Belikov ("Fragment N1"):
  http://www.viva64.com/en/b/0414/#ID0ECDAE

* Issue #11048: ctypes, fix ``CThunkObject_new()``

  - Initialize restype and flags fields to fix a crash when Python runs on a
    read-only file system
  - Use ``Py_ssize_t`` type rather than ``int`` for the ``i`` iterator variable
  - Reorder assignements to be able to more easily check if all fields are
    initialized

  Initial patch written by **Marcin Bachry**.

* Issue #27744: socket: Fix memory leak in ``sendmsg()`` and
  ``sendmsg_afalg()``.  Release ``msg.msg_iov`` memory block. Release memory
  on ``PyMem_Malloc(controllen)`` failure

* Issue #27866: ssl: Fix refleak in ``cipher_to_dict()``.

* Issue #28077: Fix dict type, ``find_empty_slot()`` only supports combined
  dictionaries.

* Issue #28200: Fix memory leak in ``path_converter()``. Replace
  ``PyUnicode_AsWideCharString()`` ``with PyUnicode_AsUnicodeAndSize()``.

* Issue #27955: Catch permission error (``EPERM``) in ``py_getrandom()``.
  Fallback on reading from the ``/dev/urandom`` device when the ``getrandom()``
  syscall fails with ``EPERM``, for example if blocked by SECCOMP.

* Issue #27778: Fix a memory leak in ``os.getrandom()`` when the
  ``getrandom()`` is interrupted by a signal and a signal handler raises a
  Python exception.

* Issue #28233: Fix ``PyUnicode_FromFormatV()`` error handling. Fix a memory
  leak if the format string contains a non-ASCII character: destroy the unicode
  writer.


regrtest changes
================

* regrtest: rename ``--slow`` option to ``--slowest`` (to get same option name
  than the ``testr`` tool). Thanks to optparse, --slow syntax still works ;-)
  Add --slowest option to buildbots. Display the top 10 slowest tests.

* regrtest: nicer output for durations. Use milliseconds and minutes units, not
  only seconds.

* regrtest: Add a summary of the tests at the end of tests output:
  "Tests result: xxx". It was sometimes hard to check quickly if tests
  succeeded, failed or something bad happened.

* regrtest: accept options after test names. For example, ``./python -m test
  test_os -v`` runs ``test_os`` in verbose mode. Before, regrtest tried to run
  a test called "-v"!

* Issue #28195: Fix ``test_huntrleaks_fd_leak()`` of test_regrtest. Don't expect
  the fd leak message to be on a specific line number, just make sure that the
  line is present in the output.

Example of a recent (2017-02-15) successful test run, truncated output::

    ...
    0:08:20 [403/404] test_codecs passed
    0:08:21 [404/404] test_threading passed
    391 tests OK.

    10 slowest tests:
    - test_multiprocessing_spawn: 1 min 24 sec
    - test_concurrent_futures: 1 min 3 sec
    - test_multiprocessing_forkserver: 60 sec
    ...

    13 tests skipped:
        test_devpoll test_ioctl test_kqueue ...

    Total duration: 8 min 22 sec
    Tests result: SUCCESS


Tests changes
=============

* script_helper: kill the subprocess on error. If Popen.communicate() raises an
  exception, kill the child process to not leave a running child process in
  background and maybe create a zombi process. This change fixes a
  ResourceWarning in Python 3.6 when unit tests are interrupted by CTRL+c.

* Issue #27181: Skip test_statistics tests known to fail until a fix is found.

* Issue #18401: Fix test_pdb if $HOME is not set. HOME is not set on Windows
  for example.

* test_eintr: Fix ``ResourceWarning`` warnings

* Buildbot: give 20 minute per test file. It seems like at least 2 buildbots
  need more than 15 minutes per test file.  Example with "AMD64 Snow Leop 3.x"::

    10 slowest tests:
    - test_tools: 14 min 40 sec
    - test_tokenize: 11 min 57 sec
    - test_datetime: 11 min 25 sec
    - ...

* Issue #28176: test_asynico: fix test_sock_connect_sock_write_race(), increase
  the timeout from 10 seconds to 60 seconds.


Other changes
=============

* Issue #22624: Python 3 now requires the ``clock()`` function to build to
  simplify the C code.

* Issue #27404: tag security related changes with the "[Security]" prefix in
  the changelog Misc/NEWS.

* Issue #27776: ``dev_urandom(raise=0)`` now closes the file descriptor on error

* Issue #27128, #18295: Use ``Py_ssize_t`` in ``_PyEval_EvalCodeWithName()``.
  Replace ``int`` type with ``Py_ssize_t`` for index variables used for
  positional arguments.  It should help to avoid integer overflow and help to
  emit better machine code for ``i++`` (no trap needed for overflow). Make also
  the ``total_args`` variable constant.

* Fix "make tags": set locale to C to call sort. vim expects that the tags file
  is sorted using english collation, so it fails if the locale is french for
  example. Use LC_ALL=C to force english sorting order. Issue #27726.

* Issue #27698: Add ``socketpair`` function to ``socket.__all__`` on Windows

* Issue #27786: Simplify (optimize?) PyLongObject private function ``x_sub()``:
  the ``z`` variable is known to be a new object which cannot be shared,
  ``Py_SIZE()`` can be used directly to negate the number.

* Fix a clang warning in grammar.c. Clang is smarter than GCC and emits a
  warning for dead code on a function declared with
  ``__attribute__((__noreturn__))`` (the ``Py_FatalError()`` function in this
  case).

* Issue #28114: Add unit tests on ``os.spawn*()`` to prepare to fix a crash
  with bytes environment.

* Issue #28127: Add ``_PyDict_CheckConsistency()``: function checking that a
  dictionary remains consistent after any change. By default, only basic
  attributes are tested, table content is not checked because the impact on
  Python performance is too important. ``DEBUG_PYDICT`` must be defined (ex:
  ``gcc -D DEBUG_PYDICT``) to check also dictionaries content.


