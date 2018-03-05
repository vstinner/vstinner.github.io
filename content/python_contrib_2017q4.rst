++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q4
++++++++++++++++++++++++++++++++++++++++++

:date: 2018-01-29 17:00
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


Development mode, -X dev
========================

bpo-32043: New "developer mode": "-X dev" option (#4413)

Add a new "developer mode": new "-X dev" command line option to
enable debug checks at runtime.

Changes:

* Add unit tests for -X dev
* test_cmd_line: replace test.support with support.
* Fix _PyRuntimeState_Fini(): Use the same memory allocator
   than _PyRuntimeState_Init().
* Fix _PyMem_GetDefaultRawAllocator()

bpo-32047: -X dev enables asyncio debug mode (#4418)

The new -X dev command line option now also enables asyncio debug
mode.

commit 895862aa01793a26e74512befb0c66a1da2587d6
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 09:47:03 2017 -0800

    bpo-32088: Display Deprecation in debug mode (#4474)

    When Python is build is debug mode (Py_DEBUG), DeprecationWarning,
    PendingDeprecationWarning and ImportWarning warnings are now
    displayed by default.

    test_venv: run "-m pip" and "-m ensurepip._uninstall" with -W
    ignore::DeprecationWarning since pip code is not part of Python.

commit f39b674876d2bd47ec7fc106d673b60ff24092ca
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 15:24:56 2017 -0800

    bpo-32094: Update subprocess for -X dev (#4480)

    Modify subprocess._args_from_interpreter_flags() to handle -X dev
    option.

    Add also unit tests for test.support.args_from_interpreter_flags()
    and test.support.optim_args_from_interpreter_flags().


I worked with Nick Coghlan to polish how warnings filters are created during
Python startup to get a straighforward behaviour and implement properly
Nick's PEP xxx (show deprecation warnings by default in the __main__ module).

commit 09f3a8a1249308a104a89041d82fe99e6c087043
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 17:32:40 2017 -0800

    bpo-32089: Fix warnings filters in dev mode (#4482)

    The developer mode (-X dev) now creates all default warnings filters
    to order filters in the correct order to always show ResourceWarning
    and make BytesWarning depend on the -b option.

    Write a functional test to make sure that ResourceWarning is logged
    twice at the same location in the developer mode.

    Add a new 'dev_mode' field to _PyCoreConfig.

commit bc9b6e29cb52f8da15613f9174af2f603131b56d
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 18:59:50 2017 -0800

    bpo-32043: Rephrase -X dev documentation (#4478)

    * should not be more verbose if the code is correct
    * enabled checks can be "expensive"



PyMem revert
============

XXX explain

::

    bpo-32096: Remove obj and mem from _PyRuntime (#4532)

    bpo-32096, bpo-30860:  Partially revert the commit
    2ebc5ce42a8a9e047e790aefbf9a94811569b2b6:

    * Move structures back from Include/internal/mem.h to
      Objects/obmalloc.c
    * Remove _PyObject_Initialize() and _PyMem_Initialize()
    * Remove Include/internal/pymalloc.h
    * Add test_capi.test_pre_initialization_api():
       Make sure that it's possible to call Py_DecodeLocale(), and then call
       Py_SetProgramName() with the decoded string, before Py_Initialize().

    PyMem_RawMalloc() and Py_DecodeLocale() can be called again before
    _PyRuntimeState_Init().

    Co-Authored-By: Eric Snow <ericsnowcurrently@gmail.com>

XXX bugs with memory allocators.


Split Py_Main(), PEP 432
========================

In XXX, Nick Coghlan wrote the PEP 432: a big plan to rework Python
initialization to better support embedded Python, more easily customize Python,
etc.

XXX python-dev reports.

Changes
-------

::

    bpo-32030: Split Py_Main() into subfunctions (#4399)

    * Don't use "Python runtime" anymore to parse command line options or
      to get environment variables: pymain_init() is now a strict
      separation.
    * Use an error message rather than "crashing" directly with
      Py_FatalError(). Limit the number of calls to Py_FatalError(). It
      prepares the code to handle errors more nicely later.
    * Warnings options (-W, PYTHONWARNINGS) and "XOptions" (-X) are now
      only added to the sys module once Python core is properly
      initialized.
    * _PyMain is now the well identified owner of some important strings
      like: warnings options, XOptions, and the "program name". The
      program name string is now properly freed at exit.
      pymain_free() is now responsible to free the "command" string.
    * Rename most methods in Modules/main.c to use a "pymain_" prefix to
      avoid conflits and ease debug.
    * Replace _Py_CommandLineDetails_INIT with memset(0)
    * Reorder a lot of code to fix the initialization ordering. For
      example, initializing standard streams now comes before parsing
      PYTHONWARNINGS.
    * Py_Main() now handles errors when adding warnings options and
      XOptions.
    * Add _PyMem_GetDefaultRawAllocator() private function.
    * Cleanup _PyMem_Initialize(): remove useless global constants: move
      them into _PyMem_Initialize().
    * Call _PyRuntime_Initialize() as soon as possible:
      _PyRuntime_Initialize() now returns an error message on failure.
    * Add _PyInitError structure and following macros:

      * _Py_INIT_OK()
      * _Py_INIT_ERR(msg)
      * _Py_INIT_USER_ERR(msg): "user" error, don't abort() in that case
      * _Py_INIT_FAILED(err)

::

    bpo-32030: Enhance Py_Main() (#4412)

    Parse more env vars in Py_Main():

    * Add more options to _PyCoreConfig:

      * faulthandler
      * tracemalloc
      * importtime

    * Move code to parse environment variables from _Py_InitializeCore()
      to Py_Main(). This change fixes a regression from Python 3.6:
      PYTHONUNBUFFERED is now read before calling pymain_init_stdio().
    * _PyFaulthandler_Init() and _PyTraceMalloc_Init() now take an
      argument to decide if the module has to be enabled at startup.
    * tracemalloc_start() is now responsible to check the maximum number
      of frames.

    Other changes:

    * Cleanup Py_Main():

      * Rename some pymain_xxx() subfunctions
      * Add pymain_run_python() subfunction

    * Cleanup Py_NewInterpreter()
    * _PyInterpreterState_Enable() now reports failure
    * init_hash_secret() now considers pyurandom() failure as an "user
      error": don't fail with abort().
    * pymain_optlist_append() and pymain_strdup() now sets err on memory
      allocation failure.

::

    bpo-32030: Add more options to _PyCoreConfig (#4485)

    Py_Main() now handles two more -X options:

    * -X showrefcount: new _PyCoreConfig.show_ref_count field
    * -X showalloccount: new _PyCoreConfig.show_alloc_count field

::

    bpo-32030: Add _PyCoreConfig.module_search_path_env (#4504)

    Changes:

    * Py_Main() initializes _PyCoreConfig.module_search_path_env from
      the PYTHONPATH environment variable.
    * PyInterpreterState_New() now initializes core_config and config
      fields
    * Compute sys.path a little bit ealier in
      _Py_InitializeMainInterpreter() and new_interpreter()
    * Add _Py_GetPathWithConfig() private function.

::

    bpo-32030: Move PYTHONPATH to _PyMainInterpreterConfig (#4511)

    Move _PyCoreConfig.module_search_path_env to _PyMainInterpreterConfig
    structure.

::

    bpo-32030: Add _PyMainInterpreterConfig.pythonhome (#4513)

    * Py_Main() now reads the PYTHONHOME environment variable
    * Add _Py_GetPythonHomeWithConfig() private function
    * Add _PyWarnings_InitWithConfig()
    * init_filters() doesn't get the current core configuration from the
      current interpreter or Python thread anymore. Pass explicitly the
      configuration to _PyWarnings_InitWithConfig().
    * _Py_InitializeCore() now fails on _PyWarnings_InitWithConfig()
      failure.
    * Pass configuration as constant

::

    bpo-32030: Rewrite calculate_path() (#4521)

    * calculate_path() rewritten in Modules/getpath.c and PC/getpathp.c
    * Move global variables into a new PyPathConfig structure.
    * calculate_path():

      * Split the huge calculate_path() function into subfunctions.
      * Add PyCalculatePath structure to pass data between subfunctions.
      * Document PyCalculatePath fields.
      * Move cleanup code into a new calculate_free() subfunction
      * calculate_init() now handles Py_DecodeLocale() failures properly
      * calculate_path() is now atomic: only replace PyPathConfig
        (path_config) at once on success.

    * _Py_GetPythonHomeWithConfig() now returns an error on failure
    * Add _Py_INIT_NO_MEMORY() helper: report a memory allocation failure
    * Coding style fixes (PEP 7)



Nanoseconds, PEP 564
====================

Part 1: Add _PyTime_GetPerfCounter()
------------------------------------

bpo-31415: Add ``_PyTime_GetPerfCounter()`` function and use it for `-X
importtime <https://docs.python.org/dev/using/cmdline.html#id5>`_, previously a
monotonic clock was used which has a bad resolution on Windows: usually 15.6
ms, whereas most Python imports take less than 10 ms.

The new ``-X importtime`` command line option is a great enhacement of Python
3.7 written by INADA Naoki to analyze the performance of Python imports to
optimize the startup time of your application.  Read also `How to speed up
Python application startup time
<https://dev.to/methane/how-to-speed-up-python-application-startup-time-nkf>`_
by INADA Naoki (Jan 19, 2018).

Part 2: Add _PyTime_GetPerfCounterDoubleWithInfo()
--------------------------------------------------

The commit a997c7b434631f51e00191acea2ba6097691e859 of bpo-31415 moved the
implementation of time.perf_counter() from Modules/timemodule.c to
Python/pytime.c. The change not only moved the code, but also changed the
internal type storing time from floatting point number (C double) to integer
number (_PyTyime_t = int64_t).

The drawback of this change is that time.perf_counter() now converts
QueryPerformanceCounter() / QueryPerformanceFrequency() double into a _PyTime_t
(integer) and then back to double. Two useless conversions required by the
_PyTime_t format used in Python/pytime.c. These conversions introduced a loss
of precision.

Try attached round.py script which implements the double <=> _PyTime_t
conversions and checks to check for precision loss. The script shows that we
loose precision even with a single second for QueryPerformanceFrequency() ==
3579545.

It seems like QueryPerformanceFrequency() now returns 10 ** 7 (10_000_000,
resolution of 100 ns) on Windows 8 and newer, but returns 3,579,545 (3.6 MHz,
resolution of 279 ns) on Windows 7. It depends maybe on the hardware clock, I
don't know. Anyway, whenever possible, we should avoid precision loss of a
clock.

bpo-31773: time.perf_counter() uses again double. time.clock() and
time.perf_counter() now use again C double internally. Remove also
_PyTime_GetWinPerfCounterWithInfo(): use _PyTime_GetPerfCounterDoubleWithInfo()
instead on Windows.

Part 3
------

The day after, I reopened the issue since I found a solution to only use
integer in pytime.c for QueryPerformanceCounter() / QueryPerformanceFrequency()
*and* prevent integer overflow.

Commit::

    bpo-31773: _PyTime_GetPerfCounter() uses _PyTime_t (GH-3983)

    * Rewrite win_perf_counter() to only use integers internally.
    * Add _PyTime_MulDiv() which compute "ticks * mul / div"
      in two parts (int part and remaining) to prevent integer overflow.
    * Clock frequency is checked at initialization for integer overflow.
    * Enhance also pymonotonic() to reduce the precision loss on macOS
      (mach_absolute_time() clock).

Since 6 years (2012), I'm trying to only use integer numbers to store time.

PyTime_t: 2014, Python 3.5

I'm working on pytime.c since xxx

I looked at the Linux kernel source code: clock sources only use integers. I'm
always impressed by the quality of the Linux kernel source code.

Using a pencil and a sheet of paper, I found a solution for my problem.

The "trick" is implemented in this function::

    Py_LOCAL_INLINE(_PyTime_t)
    _PyTime_MulDiv(_PyTime_t ticks, _PyTime_t mul, _PyTime_t div)
    {
        _PyTime_t intpart, remaining;
        /* Compute (ticks * mul / div) in two parts to prevent integer overflow:
           compute integer part, and then the remaining part.

           (ticks * mul) / div == (ticks / div) * mul + (ticks % div) * mul / div

           The caller must ensure that "(div - 1) * mul" cannot overflow. */
        intpart = ticks / div;
        ticks %= div;
        remaining = ticks * mul;
        remaining /= div;
        return intpart * mul + remaining;
    }

On Windows, I added the following sanity checks::

    /* Check that frequency can be casted to _PyTime_t.

       Make also sure that (ticks * SEC_TO_NS) cannot overflow in
       _PyTime_MulDiv(), with ticks < frequency.

       Known QueryPerformanceFrequency() values:

       * 10,000,000 (10 MHz): 100 ns resolution
       * 3,579,545 Hz (3.6 MHz): 279 ns resolution

       None of these frequencies can overflow with 64-bit _PyTime_t, but
       check for overflow, just in case. */
    if (frequency > _PyTime_MAX
        || frequency > (LONGLONG)_PyTime_MAX / (LONGLONG)SEC_TO_NS) {
        PyErr_SetString(PyExc_OverflowError,
                        "QueryPerformanceFrequency is too large");
        return -1;
    }

with _PyTime_MAX = 2**63-1 (currently, _PyTime_t uses a resolution of 1
nanosecond, so 2**63-1 nanoseconds).

macOS check, added later::

    /* Make sure that (ticks * timebase.numer) cannot overflow in
       _PyTime_MulDiv(), with ticks < timebase.denom.

       Known time bases:

       * always (1, 1) on Intel
       * (1000000000, 33333335) or (1000000000, 25000000) on PowerPC

       None of these time bases can overflow with 64-bit _PyTime_t, but
       check for overflow, just in case. */
    if ((_PyTime_t)timebase.numer > _PyTime_MAX / (_PyTime_t)timebase.denom) {
        PyErr_SetString(PyExc_OverflowError,
                        "mach_timebase_info is too large");
        return -1;
    }

time.clock()
------------

bpo-31803: ``time.clock()`` and ``time.get_clock_info('clock')`` now emit a
DeprecationWarning warning. Replace ``time.clock()`` with
``time.perf_counter()`` in tests and demos.

Remove also ``hasattr(time, 'monotonic')`` in ``test_time`` since
``time.monotonic()`` is always available since Python 3.5.

os.stat_float_times()
---------------------

os.stat_float_times() was introduced in Python 2.3 to get file modification
times with sub-second resolution. The default remains to get time as seconds
(integer). See commit f607bdaa77475ec8c94614414dc2cecf8fd1ca0a.

The function was introduced to get a smooth transition to time as floating
point number, to keep the backward compatibility with Python 2.2.

In Python 2.5, os.stat() returns time as float by default: commit
fe33d0ba87f5468b50f939724b303969711f3be5.

Python 2.5 was released 11 years ago. I consider that people had enough time to
migrate their code to float time :-)

I modified os.stat_float_times() to emit a DeprecationWarning in Python 3.1:
commit 034d0aa2171688c40cee1a723ddcdb85bbce31e8 (bpo-14711).

bpo-31827: Remove os.stat_float_times().

Serhiy: "stat_result is a named 10-tuple, containing several additional
attributes. The last three items are st_atime, st_mtime and st_ctime as
integers. Accessing them by name returns floats. Isn't a time to make them
floats when access stat_result as a tuple?"

I tried to remove the backward compatibility layer: I modified
stat_result[ST_MTIME] to return float rather than int. Problem: it broke
test_logging, the code deciding if a log file should be rotated or not.

While I'm not strongly opposed to modify stat_result[ST_MTIME], I prefer to do
it in a separated PR. Moreover, we need maybe to emit a DeprecationWarning, or
at least deprecate the feature in the doc, before changing the type, no?"

Serhiy: "I agree, it should be done in a separate issue. It needs a
special discussion. And maybe this can't be changed."

faulthandler timeout
--------------------

faulthandler now uses the _PyTime_t C type rather than double for timeout. Use
the _PyTime_t type rather than double for the faulthandler timeout in
the ``dump_traceback_later()`` function.

This change should fix the following Coverity warning::

    CID 1420311:  Incorrect expression  (UNINTENDED_INTEGER_DIVISION)
    Dividing integer expressions "9223372036854775807LL" and "1000LL",
    and then converting the integer quotient to type "double". Any
    remainder, or fractional part of the quotient, is ignored.

        if ((timeout * 1e6) >= (double) PY_TIMEOUT_MAX) {

The warning comes from ``(double)PY_TIMEOUT_MAX`` with::

    #define PY_TIMEOUT_MAX (PY_LLONG_MAX / 1000)

PEP 564
-------

Six years ago (2012), I wrote PEP 410 which proposes a large and complex change
in all Python functions returning time to support nanosecond resolution using
the decimal.Decimal type. The PEP was rejected for different reasons.

Since all Python clock now use internally _PyTime_t, I wrote the PEP 564
to propose to add ``_ns()`` clock variants like ``time.time_ns()``: return
time as an integer number of nanoseconds.

People were now convinced by the need for nanosecond resolution, so I
added a "Issues caused by precision loss" section with 2 examples:

* Example 1: measure time delta in long-running process
* Example 2: compare times with different resolution

As for my previous PEP 410, many people proposed many alternatives recorded in
the PEP: sub-nanosecond resolution, modifying time.time() result type,
different types, different API, a new module, etc.

Implementaton of the PEP 564
----------------------------

bpo-31784, commit c29b585fd4b5a91d17fc5dd41d86edff28a30da3: Implement PEP 564:
add ``time.time_ns()``.

Add new time functions:

* ``time.clock_gettime_ns()``
* ``time.clock_settime_ns()``
* ``time.monotonic_ns()``
* ``time.perf_counter_ns()``
* ``time.process_time_ns()``
* ``time.time_ns()``

Add new _PyTime functions:

* ``_PyTime_FromTimespec()``
* ``_PyTime_FromNanosecondsObject()``
* ``_PyTime_FromTimeval()``

Other changes:

* Add ``os.times()`` tests to ``test_os``.
* ``pytime_fromtimeval()`` and ``pytime_fromtimeval()`` now return
  ``_PyTime_MAX`` or ``_PyTime_MIN`` on overflow, rather than undefined
  behaviour
* ``_PyTime_FromNanoseconds()`` parameter type changes from ``long long`` to
  ``_PyTime_t``

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

Bugfixes
========

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


Misc changes
============

* Replace KB unit with KiB (#4293). kB (*kilo* byte) unit means 1000 bytes,
  whereas KiB ("kibibyte") means 1024 bytes. KB was misused: replace kB or KB
  with KiB when appropriate. Same change for MB and GB which become MiB and
  GiB.  Change the output of Tools/iobench/iobench.py. Round also the size of
  the documentation from 5.5 MB to 5 MiB.

* ``tokenizer``: Remove unused tabs options. Remove the following fields from
  ``tok_state`` structure which are now used unused:

  * ``altwarning``: "Issue warning if alternate tabs don't match"
  * ``alterror``: "Issue error if alternate tabs don't match"
  * ``alttabsize``: "Alternate tab spacing"

  Replace ``alttabsize`` variable with the ``ALTTABSIZE`` define.

* bpo-31979: Remove unused ``align_maxchar()`` function.
