++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q4
++++++++++++++++++++++++++++++++++++++++++

:date: 2018-03-06 20:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q4
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q4
(octobre, november, december).

Previous report: `My contributions to CPython during 2017 Q3 (part3)
<{filename}/python_contrib_2017q3_part3.rst>`_.

Big enhancements: a new development mode (-X dev) enabling debug checks at
runtime and PEP 564 adding time.time_ns() and others to get time with
nanosecond resolution.

Summary:

* Statistics
* XXX

Extra articles:

* `Split Py_Main() <{filename}/split_pymain.rst>`_
* `Python 3.7 New UTF-8 Mode <{filename}/utf8_mode.rst>`_
* `Python 3.7 New Development Mode (-X dev) <{filename}/dev_mode.rst>`_
* `The Python 3.7 GIL change <{filename}/gil_change.rst>`_
* `Python 3.7 perf_counter() nanoseconds <{filename}/perf_counter_nanoseconds.rst>`_
* `Python 3.7 nanoseconds <{filename}/nanoseconds.rst>`_


Statistics
==========

::

    # All branches
    $ git log --after=2017-09-31 --before=2018-01-01 --reverse --branches='*' --author=Stinner|grep '^commit ' -c
    157

    # Master branch only
    $ git log --after=2017-09-31 --before=2018-01-01 --reverse --author=Stinner ref/upstream/master|grep '^commit ' -c
    124

Statistics: I pushed **124** commits in the master branch on a **total of 157
commits**, remaining: 33 commits in the other branches (backports, fixes
specific to Python 2.7 or 3.6, security fixes)


Optimizations
=============

bpo-31835: **Anselm Kruis** reported a performance issue: Python has "fast path"
taken under certain conditions, but it was not taken for functions defined in
modules using ``from __future__ import ...`` imports (which is quite common for
code compatible with Python 2.7 and Python 3). A check was just too strict with
no good reason.

I just "fixed" the code to also optimize these functions: optimize also
FASTCALL using __future__.  ``_PyFunction_FastCallDict()`` and
``_PyFunction_FastCallKeywords()`` now also takes the fast path if the code
object uses ``__future__`` (``CO_FUTURE_xxx`` code flags).

bpo-27535: Optimize warnings.warn(). Optimize warnings.filterwarnings():
replace re.compile('') with None to avoid the cost of calling a regex.match()
method, whereas it always matchs. Optimize ``get_warnings_attr()``: replace
``PyObject_GetAttrString()`` with ``_PyObject_GetAttrId()``.

bpo-31324, ``test.bisect``: Optimize ``support._match_test()``: use the most
efficient pattern matching code depending on the kind of patterns. Change
co-authored by: **Serhiy Storchaka**.

bpo-27535: Fix memory leak with warnings ignore. The warnings module doesn't
leak memory anymore in the hidden warnings registry for the "ignore" action
of warnings filters. The warn_explicit() function doesn't add the warning
key to the registry anymore for the "ignore" action.

    "As a result, on the first pass, the memory consumption is constant and is
    about 3.9 Mb for my environment. For the second pass, the memory consumption
    constantly grows up to 246 Mb for 1 million files. I.e. memory leak is about
    254 bytes for every opened file."

Enhancements
============

make smelly
-----------

Recently, a new ``cell_set_contents()`` public symbol was added by mistake: see
bpo-30486. It was quickly noticed by doko, and fixed by me (commit
0ad05c32cc41d4c21bfd78b9ffead519ead475a2). It wasn't the first time that such
mistake is made, so I worked on an automated check on our CI.

bpo-31810: Add ``Tools/scripts/smelly.py`` script to check if all symbols
exported by libpython start with "Py" or "_Py". Modify ``make smelly`` to run
smelly.py: the command now fails with a non-zero exit code if libpython leaks a
"smelly" symbol. Travis CI now runs ``make smelly``.

Other changes
-------------

* bpo-31683: ``Py_FatalError()`` now supports long error messages, this
  function is called to exit immediately Python with an error message. On
  Windows, ``Py_FatalError()`` now limits the size to 256 bytes of the buffer
  used to call ``OutputDebugStringW()``. Previously, the size depended on the
  length of the error message.
* bpo-30807: ``signal.setitimer()`` now uses the ``_PyTime`` API. The
  ``_PyTime`` API handles detects overflow and is well tested. Document also
  that the signal will only be sent once if the *internal* argument is equal to
  zero.
* bpo-31917: Add 3 new clock identifiers to the ``time`` module:
  ``CLOCK_BOOTTIME``, ``CLOCK_PROF``, ``CLOCK_UPTIME``.
* test.pythoninfo: Collect more info from builtins, resource, test.test_socket
  and test.support modules. Co-Authored-By: **Christian Heimes**.

PyMem_AlignedAlloc()
====================

In August 2013, Raymond Hettinger suggested memory allocator variants such as
``PyMem_Alloc32(n)`` and ``PyMem_Alloc64(n)`` to return suitably aligned data
blocks.

bpo-20064: Document the following functions:

* ``PyObject_Malloc()``
* ``PyObject_Calloc()``
* ``PyObject_Realloc()``
* ``PyObject_Free()``

Fix also ``PyMem_RawFree()`` documentation.

bpo-18835: Cleanup pymalloc:

* Rename _PyObject_Alloc() to pymalloc_alloc()
* Rename _PyObject_FreeImpl() to pymalloc_free()
* Rename _PyObject_Realloc() to pymalloc_realloc()
* pymalloc_alloc() and pymalloc_realloc() don't fallback on the raw
  allocator anymore, it now must be done by the caller
* Add "success" and "failed" labels to pymalloc_alloc() and
  pymalloc_free()
* pymalloc_alloc() and pymalloc_free() don't update
  num_allocated_blocks anymore: it should be done in the caller
* _PyObject_Calloc() is now responsible to fill the memory block
  allocated by pymalloc with zeros
* Simplify pymalloc_alloc() prototype
* _PyObject_Realloc() now calls _PyObject_Malloc() rather than
  calling directly pymalloc_alloc()

_PyMem_DebugRawAlloc() and _PyMem_DebugRawRealloc():

* document the layout of a memory block
* don't increase the serial number if the allocation failed
* check for integer overflow before computing the total size
* add a 'data' variable to make the code easiler to follow

test_setallocators() of _testcapimodule.c now test also the context.

... At the end, it was decided to **not** add ``PyMem_AlignedMalloc()``

Security
========

I am a member of the Python Securirty Response Team (PSRT). We got multiple
reports about "DLL injection" on Windows: see `Python security on Windows
<http://python-security.readthedocs.io/security.html#windows>`_. I audited the
Python source code to check if there are other vulnerable Python functions and
found a ``LoadLibrary("SHELL32")`` call in ``os.startfile()``. But this exact
call is **not vulnerable** to *DLL hijacking* thanks to the "KnownDLLs" Windows
feature, so I added a comment for future security audits::

    /* Security note: this call is not vulnerable to "DLL hijacking".
       SHELL32 is part of "KnownDLLs" and so Windows always load
       the system SHELL32.DLL, even if there is another SHELL32.DLL
       in the DLL search path. */

Coverity alarms
---------------

bpo-31653, commit 828ca59208af0b1b52a328676c5cc0c5e2e999b0: Remove deadcode in
semlock_acquire(), fix the following Coverity warning::

    >>>  CID 1420038:  Control flow issues  (DEADCODE)
    >>>  Execution cannot reach this statement: "res = sem_trywait(self->han...".
    321                  res = sem_trywait(self->handle);

The deadcode was introduced by the commit
c872d39d324cd6f1a71b73e10406bbaed192d35f.

Coverity
--------

::

    Fix CID-1414686: PyInit_readline() handles errors (#4647)

    Handle PyModule_AddIntConstant() and PyModule_AddStringConstant()
    failures. Add also constants before calling setup_readline(), since
    setup_readline() registers callbacks which uses a reference to the
    module, whereas the module is destroyed if adding constants fails.

    Fix Coverity warning:

    CID 1414686: Unchecked return value (CHECKED_RETURN)
    2. check_return: Calling PyModule_AddStringConstant without checking
    return value (as is done elsewhere 45 out of 55 times).

Coverity
--------

::

    Fix CID-1420310: cast PY_TIMEOUT_MAX to _Py_time_t (#4646)

    Fix the following false-alarm Coverity warning:

        Result is not floating-point
        (UNINTENDED_INTEGER_DIVISION)integer_division: Dividing integer
        expressions 9223372036854775807LL and 1000LL, and then converting
        the integer quotient to type double. Any remainder, or fractional
        part of the quotient, is ignored.

        To compute and use a non-integer quotient, change or cast either
        operand to type double. If integer division is intended, consider
        indicating that by casting the result to type long long .

``Modules/_threadmodule.c`` change::

    -    timeout_max = (double)PY_TIMEOUT_MAX * 1e-6;
    +    timeout_max = (_PyTime_t)PY_TIMEOUT_MAX * 1e-6;

Coverity
--------

::

    PyLong_FromString(): fix Coverity CID 1424951 (#4738)

    Explicitly cast digits (Py_ssize_t) to double to fix the following
    false-alarm warning from Coverity:

    "fsize_z = digits * log_base_BASE[base] + 1;"

    CID 1424951: Incorrect expression (UNINTENDED_INTEGER_DIVISION)
    Dividing integer expressions "9223372036854775783UL" and "4UL", and
    then converting the integer quotient to type "double". Any remainder,
    or fractional part of the quotient, is ignored.

``Objects/longobject.c`` change::

    -        fsize_z = digits * log_base_BASE[base] + 1;
    -        if (fsize_z > MAX_LONG_DIGITS) {
    +        double fsize_z = (double)digits * log_base_BASE[base] + 1.0;
    +        if (fsize_z > (double)MAX_LONG_DIGITS) {


Bugfixes
========

faulthandler core dumps
-----------------------

Xavier de Gaye: "After running test_regrtest in the source tree on linux, the
build/ subdirectory (i.e. test.libregrtest.main.TEMPDIR) contains a new
test_python_* directory that contains a core file when the core file size is
unlimited."

Victor: "I'm unable to reproduce the issue on Fedora 27"

Victor: "Ah! I misunderstood the bug report. I was looking for a ENV_FAILED
failure, but no, regrtest fails to remove its temporary directory but no
warning is emitted in this case."

* bpo-32252: Fix faulthandler_suppress_crash_report(). Fix
  faulthandler_suppress_crash_report() used to prevent core dump files when
  testing crashes. getrlimit() returns zero on success.

``Modules/faulthandler.c`` change::

    -    if (getrlimit(RLIMIT_CORE, &rl) != 0) {
    +    if (getrlimit(RLIMIT_CORE, &rl) == 0) {

Changes
-------

* bpo-11063: Fix the ``_uuid module`` on macOS. On macOS, use
  ``uuid_generate_time()`` instead of ``uuid_generate_time_safe()`` of
  ``libuuid``, since ``uuid_generate_time_safe()`` is not available.
* bpo-31701: On Windows, ``faulthandler.enable()`` now ignores MSC and COM
  exceptions.
* bpo-30768: Recompute timeout on interrupted lock. Fix the "pthread+semaphore" implementation of
  ``PyThread_acquire_lock_timed()`` when called with timeout > 0 and
  intr_flag=0: recompute the timeout if sem_timedwait() is interrupted by a
  signal (EINTR). See also the :pep:`475`. The pthread implementation of
  ``PyThread_acquire_lock()`` now fails with a fatal error if the timeout is
  larger than ``PY_TIMEOUT_MAX``, as done in the Windows implementation;
  the check prevents any risk of overflow in ``PyThread_acquire_lock()``.
  Add also ``PY_DWORD_MAX`` constant.
* bpo-32050: Fix -x option documentation. The line number in correct when using
  the ``-x option``: Py_Main() uses ``ungetc()`` to not skip the first newline
  character.
* asyncio: Fix BaseSelectorEventLoopTests. Currently, two tests fail with
  PYTHONASYNCIODEBUG=1 (or using -X dev).
* bpo-32155: Bugfixes found by flake8 F841 warnings

  * distutils.config: Use the PyPIRCCommand.realm attribute if set
  * turtledemo: wait until macOS osascript command completes to not
    create a zombie process
  * Tools/scripts/treesync.py: declare 'default_answer' and
    'create_files' as globals to modify them with the command line
    arguments. Previously, -y, -n, -f and -a options had no effect.

  flake8 warning: "F841 local variable 'p' is assigned to but never
  used".

  The distutils.config change was reverted later, but the realm variable was
  removed (to fix the flake8 warning).

* bpo-32302: Fix distutils bdist_wininst for CRT v142. CRT v142 is binary
  compatible with CRT v140.
  "test_distutils: test_get_exe_bytes() failure on AppVeyor"

Tests
=====

curses and signal handlers
--------------------------

Three months after **Antoine Pitrou** added the ``test_many_processes()``
multiprocessing test (in bpo-30589), **Serhiy Storchaka** reported bpo-31629:
"test_multiprocessing_fork fails only if run all tests on FreeBSD. It is passed
successfully if run it separately."

I confirm that test_multiprocessing_fork fails with "./python -m test -vuall"
on FreeBSD CURRENT (I tested on Koobs's buildbot worker). I'm currently trying
to bisect the issue. It's not easy since test_curses does randomly crash and
running +200 tests sequentially is slow.

After 4 hours, using my cool ``test.bisect`` tool, I succeeded to isolate the
problem to only two test methods::

    test.test_curses.TestCurses.test_new_curses_panel
    test.test_multiprocessing_fork.WithProcessesTestProcess.test_many_processes

Command::

    CURRENT-amd64% ./python -m test -v -uall \
        -m test.test_curses.TestCurses.test_new_curses_panel \
        test_curses \
        -m test.test_multiprocessing_fork.WithProcessesTestProcess.test_many_processes \
        test_multiprocessing_fork

One hour later, I simplified the bug to a single Python script ``bug.py``::

    import curses
    import multiprocessing
    import signal
    import time

    multiprocessing.set_start_method('fork', force=True)

    def sleep_some():
        time.sleep(100)

    if 1:
        curses.initscr()
        curses.endwin()

    procs = [multiprocessing.Process(target=sleep_some) for i in range(3)]
    for p in procs:
        p.start()
    time.sleep(0.001)  # let the children start...
    for p in procs:
        p.terminate()
    for p in procs:
        p.join()
    for p in procs:
        print(p.exitcode, -signal.SIGTERM)

**Pablo Galindo Salgado**: "I have tracked the issue down to the call inside the
call to initscr in _cursesmodule.c."

Add support.SaveSignals. ``test_curses`` now saves/restores
signals. On FreeBSD, the curses module sets handlers of some signals, but
don't restore old handlers when the module is deinitialized.

Changes:

* bpo-31510: Fix multiprocessing test_many_processes() on macOS. On macOS, a
  process can exit with -SIGKILL if it is killed "early" with SIGTERM.
* bpo-31178: Fix ``test_exception_errpipe_bad_data()`` and
  ``test_exception_errpipe_normal()`` of ``test_subprocess``: mock
  ``os.waitpid()`` to avoid calling the real ``os.waitpid(0, 0)`` which is an
  unexpected side effect of the test and can hang forever in some cases.
* bpo-25588: Fix regrtest when run inside IDLE. When regrtest in run inside
  IDLE, ``sys.stdout`` and ``sys.stderr`` are not ``TextIOWrapper`` objects and
  have no file descriptor associated: ``sys.stderr.fileno()`` raises
  ``io.UnsupportedOperation``. Disable ``faulthandler`` and don't replace
  ``sys.stdout`` (to change the error handler) in that case.
* bpo-31676: Fix ``test_imp.test_load_source()`` side effect,
  ``test_load_source()`` now replaces the current ``__name__`` module with a
  temporary module to prevent side effects.
* bpo-31174: Fix ``test_unparse.DirectoryTestCase`` of ``test_tools``, it now
  stores the names sample to always test the same files. It prevents false
  alarms when hunting reference leaks.
* test_capi.test__testcapi() becomes more verbose. Write the name of each
  subtest on a new line to help debugging when a test does crash Python.
* ``test.pythoninfo``: add ``Py_DEBUG`` entry to more easily check if Python
  was compiled in debug mode or not.
* bpo-31910: ``test_socket.test_create_connection()`` now catchs also
  ``EADDRNOTAVAIL`` to fix the test on Travis CI.
* bpo-32128: Skip test_nntplib.test_article_head_body(). The NNTP server
  currently has troubles with SSL, whereas we don't have the control on this
  server. This test blocks all CIs, so disable it until a fix can be found.
* bpo-32107: Revert commit 9522a218f7dff95c490ff359cc60e8c2af35f5c8 "UUID1 MAC
  address calculation". It broke Travis CI and buildbots like "s390x SLES 3.x".
* bpo-31705: Skip test_socket.test_sha256() on linux < 4.5. It took 2 months
  to fix this bug, time to collect enough information about impacted Linux
  kernels and impacted architectures.

  * FAIL: ppc64le on Linux 3.10
  * PASS: ppc64le on Linux 4.11

  Victor: "Ah, I think that I found the bugfix (8 Jan 2016): https://github.com/torvalds/linux/commit/6de62f15b581
  So it was fixed in the kernel 4.5."

  I found also https://access.redhat.com/errata/RHSA-2017:2437 :

  "The lrw_crypt() function in 'crypto/lrw.c' in the Linux kernel before 4.5
  allows local users to cause a system crash and a denial of service by the
  NULL pointer dereference via accept(2) system call for AF_ALG socket without
  calling setkey() first to set a cipher key. (CVE-2015-8970, Moderate)"

* bpo-32294: Fix multiprocessing ``test_semaphore_tracker()``. Run the child
  process with -E option to ignore the ``PYTHONWARNINGS`` environment variable.

Code removal
============

* ``tokenizer``: Remove unused tabs options. Remove the following fields from
  ``tok_state`` structure which are now used unused:

  * ``altwarning``: "Issue warning if alternate tabs don't match"
  * ``alterror``: "Issue error if alternate tabs don't match"
  * ``alttabsize``: "Alternate tab spacing"

  Replace ``alttabsize`` variable with the ``ALTTABSIZE`` define.

* bpo-31979: Remove unused ``align_maxchar()`` function.
* bpo-32125: Remove Py_UseClassExceptionsFlag flag. This flag was deprecated
  and wasn't used anymore since Python 2.0.
* asyncio: Remove unused Future._tb_logger attribute. It was only used on
  Python 3.3, now only Future._log_traceback is used.
* asyncio: Remove asyncio/compat.py file. The asyncio/compat.py file was
  written to support Python < 3.5 and Python < 3.5.2. But Python 3.5 doesn't
  accept bugfixes anymore, only security fixes. There is no more need to
  backport bugfixes to Python 3.5, and so no need to have a single code base
  for Python 3.5, 3.6 and 3.7.
* bpo-32154: Remove asyncio.selectors.

  * Remove asyncio.selectors and asyncio._overlapped symbols from the
    namespace of the asyncio module
  * Replace "from asyncio import selectors" with "import selectors"
  * Replace "from asyncio import _overlapped" with "import _overlapped"

  asyncio.selectors was added to support Python 3.3, which doesn't have
  selectors in its standard library, and Python 3.4 in the same code
  base. Same rationale for asyncio._overlapped. Python 3.3 reached its
  end of life, and asyncio is no more maintained as a third party
  module on PyPI.

* bpo-32154: asyncio: use directly socket.socketpair() and remove
  asyncio.windows_utils.socketpair(). Since Python 3.5, socket.socketpair() is
  also available on Windows, and so can be used directly, rather than using
  asyncio.windows_utils.socketpair(). test_socket: socket.socketpair() is
  always available.
* bpo-32159: Remove tools for CVS and Subversion. CPython migrated from CVS to
  Subversion, to Mercurial, and then to Git. CVS and Subversion are not more
  used to develop CPython.

  * platform module: drop support for sys.subversion. The
    sys.subversion attribute has been removed in Python 3.3.
  * Remove Misc/svnmap.txt
  * Remove Tools/scripts/svneol.py
  * Remove Tools/scripts/treesync.py

  Later, Misc/svnmap.txt was reverted. Clarify the usage of this file in
  Misc/README.

* bpo-32030: Remove the initstr variable, unused since the commit
  e69f0df45b709c25ac80617c41bbae16f56870fb pushed in 2012 "bpo-13959:
  Re-implement imp.find_module() in Lib/imp.py". Pass also the *interp*
  variable to ``_PyImport_Init()``.

Misc changes
============

* Replace KB unit with KiB (#4293). kB (*kilo* byte) unit means 1000 bytes,
  whereas KiB ("kibibyte") means 1024 bytes. KB was misused: replace kB or KB
  with KiB when appropriate. Same change for MB and GB which become MiB and
  GiB.  Change the output of Tools/iobench/iobench.py. Round also the size of
  the documentation from 5.5 MB to 5 MiB.
* bpo-31245: asyncio: Fix typo, isistance => isinstance. The code wasn't tested
  :-(
* ``make tags``: index also Modules/_ctypes/. Avoid also "cd $(srcdir)" to not
  change the current directory.
* import.c: Fix a GCC warning. Fix the warning::

    Python/import.c: warning: comparison between signed and unsigned integer expressions
         if ((i + n + 1) <= PY_SSIZE_T_MAX / sizeof(struct _inittab)) {
