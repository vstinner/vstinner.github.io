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


UTF-8 Mode
==========

PEP 540 -- Add a new UTF-8 Mode
https://www.python.org/dev/peps/pep-0540/

BDFL-Delegate: INADA Naoki

Abstract
--------

Add a new "UTF-8 Mode" to enhance Python's use of UTF-8.  When UTF-8 Mode
is active, Python will:

* use the ``utf-8`` encoding, irregardless of the locale currently set by
  the current platform, and
* change the ``stdin`` and ``stdout`` error handlers to
  ``surrogateescape``.

This mode is off by default, but is automatically activated when using
the "POSIX" locale.

Add the ``-X utf8`` command line option and ``PYTHONUTF8`` environment
variable to control UTF-8 Mode.

Version History
---------------

* Version 4: ``locale.getpreferredencoding()`` now returns ``'UTF-8'``
  in the UTF-8 Mode.
* Version 3: The UTF-8 Mode does not change the ``open()`` default error
  handler (``strict``) anymore, and the Strict UTF-8 Mode has been
  removed.
* Version 2: Rewrite the PEP from scratch to make it much shorter and
  easier to understand.
* Version 1: First version posted to python-dev.

Post History
------------

* 2017-12: `[Python-Dev] PEP 540: Add a new UTF-8 Mode
  <https://mail.python.org/pipermail/python-dev/2017-December/151054.html>`_
* 2017-04: `[Python-Dev] Proposed BDFL Delegate update for PEPs 538 &
  540 (assuming UTF-8 for *nix system boundaries)
  <https://mail.python.org/pipermail/python-dev/2017-April/147795.html>`_
* 2017-01: `[Python-ideas] PEP 540: Add a new UTF-8 Mode
  <https://mail.python.org/pipermail/python-ideas/2017-January/044089.html>`_
* 2017-01: `bpo-28180: Implementation of the PEP 538: coerce C locale to
  C.utf-8 (msg284764) <https://bugs.python.org/issue28180#msg284764>`_
* 2016-08-17: `bpo-27781: Change sys.getfilesystemencoding() on Windows
  to UTF-8 (msg272916) <https://bugs.python.org/issue27781#msg272916>`_
  -- Victor proposed ``-X utf8`` for the :pep:`529` (Change Windows
  filesystem encoding to UTF-8)

Implementation
--------------

Commit::

    commit 91106cd9ff2f321c0f60fbaa09fd46c80aa5c266
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Dec 13 12:29:09 2017 +0100

        bpo-29240: PEP 540: Add a new UTF-8 Mode (#855)

        * Add -X utf8 command line option, PYTHONUTF8 environment variable
          and a new sys.flags.utf8_mode flag.
        * If the LC_CTYPE locale is "C" at startup: enable automatically the
          UTF-8 mode.
        * Add _winapi.GetACP(). encodings._alias_mbcs() now calls
          _winapi.GetACP() to get the ANSI code page
        * locale.getpreferredencoding() now returns 'UTF-8' in the UTF-8
          mode. As a side effect, open() now uses the UTF-8 encoding by
          default in this mode.
        * Py_DecodeLocale() and Py_EncodeLocale() now use the UTF-8 encoding
          in the UTF-8 Mode.
        * Update subprocess._args_from_interpreter_flags() to handle -X utf8
        * Skip some tests relying on the current locale if the UTF-8 mode is
          enabled.
        * Add test_utf8mode.py.
        * _Py_DecodeUTF8_surrogateescape() gets a new optional parameter to
          return also the length (number of wide characters).
        * pymain_get_global_config() and pymain_set_global_config() now
          always copy flag values, rather than only copying if the new value
          is greater than the old value.


GIL change
==========

In March 2014, Steve Dower reported a bug when a "C thread" uses the Python C
API: "In Python 3.4rc3, calling PyGILState_Ensure() from a thread that was not
created by Python and without any calls to PyEval_InitThreads() will cause a
fatal exit: (...)".

I commented "IMO it's a bug in PyEval_InitThreads()."

In March 2016, I wrote a short C program to reproduce the bug and a fix.

In november 2017, Marcin Kasperski asked "Is this fix released? I can't find it
in the changelog…". Oops, I forgot to apply my fix.

Not only I applied my fix, but I also wrote an unit test.

    Ok, the bug is now fixed in Python 2.7, 3.6 and master (future 3.7). On 3.6
    and master, the fix comes with an unit test.

The fix::

    bpo-20891: Fix PyGILState_Ensure() (#4650)

    When PyGILState_Ensure() is called in a non-Python thread before
    PyEval_InitThreads(), only call PyEval_InitThreads() after calling
    PyThreadState_New() to fix a crash.

    Add an unit test in test_embed.

Everything was fine... until december 2017, when **random** failures were
spotted on macOS buildbots::

    macbook:master haypo$ while true; do ./Programs/_testembed bpo20891 ||break; date; done
    Lun  4 déc 2017 12:46:34 CET
    Lun  4 déc 2017 12:46:34 CET
    Lun  4 déc 2017 12:46:34 CET
    Fatal Python error: PyEval_SaveThread: NULL tstate

    Current thread 0x00007fffa5dff3c0 (most recent call first):
    Abort trap: 6

My analysis:

    I found a working fix: call PyEval_InitThreads() in
    PyThread_start_new_thread(). So the GIL is created as soon as a second
    thread is spawned. The GIL cannot be created anymore while two threads are
    running. At least, with the "python" binary. It doesn't fix the issue if a
    thread is not spawned by Python, but this thread calls PyGILState_Ensure().

Antoine Pitrou commented:

    Why not *always* call PyEval_InitThreads() at interpreter initialization?
    Are there any downsides?

I found the origin of the code creating the GIL "on demand"::

    commit 1984f1e1c6306d4e8073c28d2395638f80ea509b
    Author: Guido van Rossum <guido@python.org>
    Date:   Tue Aug 4 12:41:02 1992 +0000

        * Makefile adapted to changes below.
        * split pythonmain.c in two: most stuff goes to pythonrun.c, in the library.
        * new optional built-in threadmodule.c, build upon Sjoerd's thread.{c,h}.
        * new module from Sjoerd: mmmodule.c (dynamically loaded).
        * new module from Sjoerd: sv (svgen.py, svmodule.c.proto).
        * new files thread.{c,h} (from Sjoerd).
        * new xxmodule.c (example only).
        * myselect.h: bzero -> memset
        * select.c: bzero -> memset; removed global variable

    (...)

    +void
    +init_save_thread()
    +{
    +#ifdef USE_THREAD
    +       if (interpreter_lock)
    +               fatal("2nd call to init_save_thread");
    +       interpreter_lock = allocate_lock();
    +       acquire_lock(interpreter_lock, 1);
    +#endif
    +}
    +#endif

"I guess that the intent of dynamically created GIL is to reduce the "overhead"
of the GIL when 100% of the code is run in single thread."

Guido van Rossum:

    Yeah, the original reasoning was that threads were something esoteric and
    not used by most code, and at the time we definitely felt that always using
    the GIL would cause a (tiny) slowdown and increase the risk of crashes due
    to bugs in the GIL code. I'd be happy to learn that we no longer need to
    worry about this and can just always initialize it.

    (Note: I haven't read the entire thread, just the first and last message.)

Nick Coghlan:

    Victor, could you run your patch through the performance benchmarks?

I ran pyperformance on my PR 4700. Differences of at least 5%::

    haypo@speed-python$ python3 -m perf compare_to ~/json/uploaded/2017-12-18_12-29-master-bd6ec4d79e85.json.gz /home/haypo/json/patch/2017-12-18_12-29-master-bd6ec4d79e85-patch-4700.json.gz --table --min-speed=5

    +----------------------+--------------------------------------+-------------------------------------------------+
    | Benchmark            | 2017-12-18_12-29-master-bd6ec4d79e85 | 2017-12-18_12-29-master-bd6ec4d79e85-patch-4700 |
    +======================+======================================+=================================================+
    | pathlib              | 41.8 ms                              | 44.3 ms: 1.06x slower (+6%)                     |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | scimark_monte_carlo  | 197 ms                               | 210 ms: 1.07x slower (+7%)                      |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | spectral_norm        | 243 ms                               | 269 ms: 1.11x slower (+11%)                     |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | sqlite_synth         | 7.30 us                              | 8.13 us: 1.11x slower (+11%)                    |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | unpickle_pure_python | 707 us                               | 796 us: 1.13x slower (+13%)                     |
    +----------------------+--------------------------------------+-------------------------------------------------+

    Not significant (55): 2to3; chameleon; chaos; (...)

I decided to skip the test which was failing randomly before going to holiday,
I didn't want to stress myself with having to take such major decision before
leaving. Modifying one of the most important key feature of Python (GIL) before
leaving is not a good idea.

At the end of january 2018, "I tested again these 5 benchmarks were Python was
slower with my PR. I ran these benchmarks manually on my laptop using CPU
isolation. Result::

    vstinner@apu$ python3 -m perf compare_to ref.json patch.json --table
    Not significant (5): unpickle_pure_python; sqlite_synth; spectral_norm; pathlib; scimark_monte_carlo

Ok, that was expected: no significant difference.

So I pushed the fix to master::

    New changeset 2914bb32e2adf8dff77c0ca58b33201bc94e398c by Victor Stinner in branch 'master':
    bpo-20891: Py_Initialize() now creates the GIL (#4700)
    https://github.com/python/cpython/commit/2914bb32e2adf8dff77c0ca58b33201bc94e398c

Antoine Pitrou considers that my PR 5421 for Python 3.6 should not be merged:

    I don't think so. People can already call PyEval_InitThreads.

I reenabled test_embed.test_bpo20891() on master but removed it from Python
3.6.

::

    bpo-20891: Skip test_embed.test_bpo20891() (#4967)

    Skip the test failing randomly because of known race condition.

    Skip the test to fix macOS buildbots until a decision is made on the
    proper fix for the race condition.

Note: Python 2.7 doesn't have test_embed.test_bpo20891() since it was more
complex to write such test for Python 2.7.


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

commit 21c7730761e2a768e33b89b063a095d007dcfd2c
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 27 12:11:55 2017 +0100

    bpo-32089: Use default action for ResourceWarning (#4584)

    In development and debug mode, use the "default" action, rather than
    the "always" action, for ResourceWarning in the default warnings
    filters.

::

    bpo-32101: Add PYTHONDEVMODE environment variable (#4624)

    * bpo-32101: Add sys.flags.dev_mode flag
      Rename also the "Developer mode" to the "Development mode".
    * bpo-32101: Add PYTHONDEVMODE environment variable
      Mention it in the development chapiter.

::

    bpo-32230: Set sys.warnoptions with -X dev (#4820)

    Rather than supporting dev mode directly in the warnings module, this
    instead adjusts the initialisation code to add an extra 'default'
    entry to sys.warnoptions when dev mode is enabled.

    This ensures that dev mode behaves *exactly* as if `-Wdefault` had
    been passed on the command line, including in the way it interacts
    with `sys.warnoptions`, and with other command line flags like `-bb`.

    Fix also bpo-20361: have -b & -bb options take precedence over any
    other warnings options.

    Patch written by Nick Coghlan, with minor modifications of Victor Stinner.

::

    bpo-32101: Fix tests for PYTHONDEVMODE=1 (#4821)

    test_asycio: remove also aio_path which was used when asyncio was
    developed outside the stdlib.



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

Before Py_Initialize and memory allocators
------------------------------------------

* bpo-32124: Document C functions safe before init. Explicitly document C
  functions and C variables that can be set before Py_Initialize().

Follow-up of bpo-32086, bpo-32096 and "[Python-Dev] Python initialization and embedded Python" thread:
https://mail.python.org/pipermail/python-dev/2017-November/150605.html

[Python-Dev] Python initialization and embedded Python
https://mail.python.org/pipermail/python-dev/2017-November/150605.html

"The CPython internals evolved during Python 3.7 cycle. I would like to know if
we broke the C API or not."

https://bugs.python.org/issue32096
https://bugs.python.org/issue32086
https://bugs.python.org/issue32124

::

    bpo-32030: Rework memory allocators (#4625)

    * Fix _PyMem_SetupAllocators("debug"): always restore allocators to
      the defaults, rather than only caling _PyMem_SetupDebugHooks().
    * Add _PyMem_SetDefaultAllocator() helper to set the "default"
      allocator.
    * Add _PyMem_GetAllocatorsName(): get the name of the allocators
    * main() now uses debug hooks on memory allocators if Py_DEBUG is
      defined, rather than calling directly malloc()
    * Document default memory allocators in C API documentation
    * _Py_InitializeCore() now fails with a fatal user error if
      PYTHONMALLOC value is an unknown memory allocator, instead of
      failing with a fatal internal error.
    * Add new tests on the PYTHONMALLOC environment variable
    * Add support.with_pymalloc()
    * Add the _testcapi.WITH_PYMALLOC constant and expose it as
       support.with_pymalloc().
    * sysconfig.get_config_var('WITH_PYMALLOC') doesn't work on Windows, so
       replace it with support.with_pymalloc().
    * pythoninfo: add _testcapi collector for pymem


Next
----

::

    bpo-32030: Add _PyMainInterpreterConfig_ReadEnv() (#4542)

    Py_GetPath() and Py_Main() now call
    _PyMainInterpreterConfig_ReadEnv() to share the same code to get
    environment variables.

    Changes:

    * Add _PyMainInterpreterConfig_ReadEnv()
    * Add _PyMainInterpreterConfig_Clear()
    * Add _PyMem_RawWcsdup()
    * _PyMainInterpreterConfig: rename pythonhome to home
    * Rename _Py_ReadMainInterpreterConfig() to
      _PyMainInterpreterConfig_Read()
    * Use _Py_INIT_USER_ERR(), instead of _Py_INIT_ERR(), for decoding
      errors: the user is able to fix the issue, it's not a bug in
      Python. Same change was made in _Py_INIT_NO_MEMORY().
    * Remove _Py_GetPythonHomeWithConfig()

::

    bpo-32030: Add _PyMainInterpreterConfig.program_name (#4548)

    * Py_Main() now calls Py_SetProgramName() earlier to be able to get
      the program name in _PyMainInterpreterConfig_ReadEnv().
    * Rename prog to program_name
    * Rename progpath to program_name

::

    bpo-32030: Add _PyPathConfig_Init() (#4551)

    * Add _PyPathConfig_Init() and _PyPathConfig_Fini()
    * Remove _Py_GetPathWithConfig()
    * _PyPathConfig_Init() returns _PyInitError to allow to handle errors
      properly
    * Add pathconfig_clear()
    * Windows calculate_path_impl(): replace Py_FatalError() with
      _PyInitError
    * Py_FinalizeEx() now calls _PyPathConfig_Fini() to release memory
    * Fix _Py_InitializeMainInterpreter() regression: don't initialize
      path config if _disable_importlib is false
    * PyPathConfig now uses dynamically allocated memory

::

    bpo-32030: Fix _Py_InitializeEx_Private() (#4649)

    _Py_InitializeEx_Private() now calls
    _PyMainInterpreterConfig_ReadEnv() to read environment variables
    PYTHONHOME and PYTHONPATH, and set the program name.

::

    bpo-32030: Cleanup "path config" code (#4663)

    * Rename PyPathConfig structure to _PyPathConfig and move it to
      Include/internal/pystate.h
    * Rename path_config to _Py_path_config
    * _PyPathConfig: Rename program_name field to program_full_path
    * Add assert(str != NULL); to _PyMem_RawWcsdup(), _PyMem_RawStrdup()
      and _PyMem_Strdup().
    * Rename calculate_path() to pathconfig_global_init(). The function
      now does nothing if it's already initiallized.

::

    bpo-32030: Fix Py_GetPath(): init program_name (#4665)

    * _PyMainInterpreterConfig_ReadEnv() now sets program_name from
      environment variables and pymain_parse_envvars() implements the
      falls back on argv[0].
    * Remove _PyMain.program_name: use the program_name from
      _PyMainInterpreterConfig
    * Move the Py_SetProgramName() call back to pymain_init_python(),
      just before _Py_InitializeCore().
    * pathconfig_global_init() now also calls
      _PyMainInterpreterConfig_Read() to set program_name if it isn't set
      yet
    * Cleanup PyCalculatePath: pass main_config to subfunctions to get
      directly fields from main_config (home, module_search_path_env and
      program_name)

::

    bpo-32030: Don't call _PyPathConfig_Fini() in Py_FinalizeEx() (#4667)

    Changes:

    * _PyPathConfig_Fini() cannot be called in Py_FinalizeEx().
      Py_Initialize() and Py_Finalize() can be called multiple times, but
      it must not "forget" parameters set by Py_SetProgramName(),
      Py_SetPath() or Py_SetPythonHome(), whereas _PyPathConfig_Fini()
      clear all these parameters.
    * config_get_program_name() and calculate_program_full_path() now
      also decode paths using Py_DecodeLocale() to use the
      surrogateescape error handler, rather than decoding using
      mbstowcs() which is strict.
    * Change _Py_CheckPython3() prototype: () => (void)
    * Truncate a few lines which were too long

::

    bpo-32030: Add Python/pathconfig.c (#4668)

    * Factorize code from PC/getpathp.c and Modules/getpath.c to remove
      duplicated code
    * rename pathconfig_clear() to _PyPathConfig_Clear()
    * Inline _PyPathConfig_Fini() in pymain_impl() and then remove it,
      since it's a oneliner

::

    bpo-32030: Fix config_get_program_name() on macOS (#4669)

::

    bpo-32030: _PyPathConfig_Init() sets home and program_name (#4673)

    _PyPathConfig_Init() now also initialize home and program_name:

    * Rename existing _PyPathConfig_Init() to _PyPathConfig_Calculate().
      Add a new _PyPathConfig_Init() function in pathconfig.c which
      handles the _Py_path_config variable and call
      _PyPathConfig_Calculate().
    * Add home and program_name fields to _PyPathConfig.home
    * _PyPathConfig_Init() now initialize home and program_name
      from main_config
    * Py_SetProgramName(), Py_SetPythonHome() and Py_GetPythonHome() now
      calls Py_FatalError() on failure, instead of silently ignoring
      failures.
    * config_init_home() now gets directly _Py_path_config.home to only
      get the value set by Py_SetPythonHome(), or NULL if
      Py_SetPythonHome() was not called.
    * config_get_program_name() now gets directly
      _Py_path_config.program_name to only get the value set by
      Py_SetProgramName(), or NULL if Py_SetProgramName() was not called.
    * pymain_init_python() doesn't call Py_SetProgramName() anymore,
      _PyPathConfig_Init() now always sets the program name
    * Call _PyMainInterpreterConfig_Read() in
      pymain_parse_cmdline_envvars_impl() to control the memory allocator
    * C API documentation: it's no more safe to call Py_GetProgramName()
      before Py_Initialize().

::

    Revert "bpo-32197: Try to fix a compiler error on OS X introduced in bpo-32030. (#4681)" (#4694)

    * Revert "bpo-32197: Try to fix a compiler error on OS X introduced in bpo-32030. (#4681)"

    This reverts commit 13badcbc60cdbfae1dba1683fd2fae9d70717143.

    Re-apply commits:

    * "bpo-32030: _PyPathConfig_Init() sets home and program_name (#4673)"
      commit af5a895073c24637c094772b27526b94a12ec897.
    * "bpo-32030: Fix config_get_program_name() on macOS (#4669)"
      commit e23c06e2b03452c9aaf0dae52296c85e572f9bcd.
    * "bpo-32030: Add Python/pathconfig.c (#4668)"
      commit 0ea395ae964c9cd0f499e2ef0d0030c971201220.
    * "bpo-32030: Don't call _PyPathConfig_Fini() in Py_FinalizeEx() (#4667)"
      commit ebac19dad6263141d5db0a2c923efe049dba99d2.
    * "bpo-32030: Fix Py_GetPath(): init program_name (#4665)"
      commit 9ac3d8882712c9675c3d2f9f84af6b5729575cde.

    * Fix compilation error on macOS

::

    bpo-32030: Simplify _PyCoreConfig_INIT macro (#4728)

    * Simplify _PyCoreConfig_INIT, _PyMainInterpreterConfig_INIT,
      _PyPathConfig_INIT macros: no need to set fields to 0/NULL, it's
      redundant (the C language sets them to 0/NULL for us).
    * Fix typo: pymain_run_statup() => pymain_run_startup()
    * Remove a few XXX/TODO

::

    bpo-32030: Add pymain_get_global_config() (#4735)

    * Py_Main() now starts by reading Py_xxx configuration variables to
      only work on its own private structure, and then later writes back
      the configuration into these variables.
    * Replace Py_GETENV() with pymain_get_env_var() which ignores empty
      variables.
    * Add _PyCoreConfig.dump_refs
    * Add _PyCoreConfig.malloc_stats
    * _PyObject_DebugMallocStats() is now responsible to check if debug
      hooks are installed. The function returns 1 if stats were written,
      or 0 if the hooks are disabled. Mark _PyMem_PymallocEnabled() as
      static.

::

    bpo-32030: Add _PyImport_Fini2() (#4737)

    PyImport_ExtendInittab() now uses PyMem_RawRealloc() rather than
    PyMem_Realloc(). PyImport_ExtendInittab() can be called before
    Py_Initialize() whereas only the PyMem_Raw allocator is supposed to
    be used before Py_Initialize().

    Add _PyImport_Fini2() to release the memory allocated by
    PyImport_ExtendInittab() at exit. PyImport_ExtendInittab() now forces
    the usage of the default raw allocator, to be able to release memory
    in _PyImport_Fini2().

    Don't export these functions anymore to be C API, only to
    Py_BUILD_CORE:

    * _PyExc_Fini()
    * _PyImport_Fini()
    * _PyGC_DumpShutdownStats()
    * _PyGC_Fini()
    * _PyType_Fini()
    * _Py_HashRandomization_Fini()

::

    pymain_set_sys_argv() now copies argv (#4838)

    bpo-29240, bpo-32030:

    * Rename pymain_set_argv() to pymain_set_sys_argv()
    * pymain_set_sys_argv() now creates of copy of argv and modify the
      copy, rather than modifying pymain->argv
    * Call pymain_set_sys_argv() earlier: before pymain_run_python(), but
      after pymain_get_importer().
    * Add _PySys_SetArgvWithError() to handle errors

::

    bpo-32030: Add _PyPathConfig_ComputeArgv0() (#4845)

    Changes:

    * Split _PySys_SetArgvWithError() into subfunctions for Py_Main():

      * Create the Python list object
      * Set sys.argv to the list
      * Compute argv0
      * Prepend argv0 to sys.path

    * Add _PyPathConfig_ComputeArgv0()
    * Remove _PySys_SetArgvWithError()
    * Py_Main() now splits the code to compute sys.argv/path0 and the
      code to update the sys module: add pymain_compute_argv()
      subfunction.

::

    bpo-32030: Rewrite _PyMainInterpreterConfig (#4854)

    _PyMainInterpreterConfig now contains Python objects, whereas
    _PyCoreConfig contains wchar_t* strings.

    Core config:

    * Rename _PyMainInterpreterConfig_ReadEnv() to _PyCoreConfig_ReadEnv()
    * Move 3 strings from _PyMainInterpreterConfig to _PyCoreConfig:
      module_search_path_env, home, program_name.
    * Add _PyCoreConfig_Clear()
    * _PyPathConfig_Calculate() now takes core config rather than main
      config
    * _PyMainInterpreterConfig_Read() now requires also a core config

    Main config:

    * Add _PyMainInterpreterConfig.module_search_path: sys.path list
    * Add _PyMainInterpreterConfig.argv: sys.argv list
    * _PyMainInterpreterConfig_Read() now computes module_search_path

::

    bpo-32030: Add _PyMainInterpreterConfig.warnoptions (#4855)

    Add warnoptions and xoptions fields to _PyMainInterpreterConfig.

::

    bpo-32329: Fix -R option for hash randomization (#4873)

    bpo-32329, bpo-32030:

    * The -R option now turns on hash randomization when the
      PYTHONHASHSEED environment variable is set to 0 Previously, the
      option was ignored.
    * sys.flags.hash_randomization is now properly set to 0 when hash
      randomization is turned off by PYTHONHASHSEED=0.
    * _PyCoreConfig_ReadEnv() now reads the PYTHONHASHSEED environment
      variable. _Py_HashRandomization_Init() now only apply the
      configuration, it doesn't read PYTHONHASHSEED anymore.

::

    bpo-32329: Add versionchanged to -R option doc (#4884)

::

    bpo-32030: Add _PyCoreConfig_Copy() (#4874)

    Each interpreter now has its core_config and main_config copy:

    * Add _PyCoreConfig_Copy() and _PyMainInterpreterConfig_Copy()
    * Move _PyCoreConfig_Read(), _PyCoreConfig_Clear() and
      _PyMainInterpreterConfig_Clear() from Python/pylifecycle.c to
      Modules/main.c
    * Fix _Py_InitializeEx_Private(): call _PyCoreConfig_ReadEnv() before
      _Py_InitializeCore()

::

    bpo-32030: Add _PyMainInterpreterConfig.executable (#4876)

    * Add new fields to _PyMainInterpreterConfig:

      * executable
      * prefix
      * base_prefix
      * exec_prefix
      * base_exec_prefix

    * _PySys_EndInit() now sets sys attributes from
      _PyMainInterpreterConfig

::

    bpo-29240: Don't define decode_locale() on macOS (#4895)

    Don't define decode_locale() nor encode_locale() on macOS or Android.

::

    bpo-29240, bpo-32030: Py_Main() re-reads config if encoding changes (#4899)

    bpo-29240, bpo-32030: If the encoding change (C locale coerced or
    UTF-8 Mode changed), Py_Main() now reads again the configuration with
    the new encoding.

    Changes:

    * Add _Py_UnixMain() called by main().
    * Rename pymain_free_pymain() to pymain_clear_pymain(), it can now be
      called multipled times.
    * Rename pymain_parse_cmdline_envvars() to pymain_read_conf().
    * Py_Main() now clears orig_argc and orig_argv at exit.
    * Remove argv_copy2, Py_Main() doesn't modify argv anymore. There is
      no need anymore to get two copies of the wchar_t** argv.
    * _PyCoreConfig: add coerce_c_locale and coerce_c_locale_warn.
    * Py_UTF8Mode is now initialized to -1.
    * Locale coercion (PEP 538) now respects -I and -E options.

::

    bpo-32030: Fix compilation on FreeBSD, #include <fenv.h> (#4919)

    * main.c: add missing #include <fenv.h> on FreeBSD
    * indent also other #ifdef in main.c
    * cleanup Programs/python.c

::

    bpo-32030: Fix compiler warnings (#4921)

    Fix compiler warnings in Py_FinalizeEx(): only define variables if
    they are needed, add #ifdef.

    Other cleanup changes:

    * _PyWarnings_InitWithConfig() is no more needed: call
      _PyWarnings_Init() instead.
    * Inline pymain_init_main_interpreter() in its caller. This
      subfunction is no more justifed.

::

    bpo-32030: Add _PyCoreConfig.argv (#4934)

    * Add argc and argv to _PyCoreConfig
    * _PyMainInterpreterConfig_Read() now builds its argv from
      _PyCoreConfig.arg
    * Move _PyMain.env_warning_options into _Py_CommandLineDetails
    * Reorder pymain_free()

::

    bpo-32030: Cleanup pymain_main() (#4935)

    * Reorganize pymain_main() to make the code more flat
    * Clear configurations before pymain_update_sys_path()
    * Mark Py_FatalError() and _Py_FatalInitError() with _Py_NO_RETURN
    * Replace _PyMain.run_code variable with a new RUN_CODE() macro
    * Move _PyMain.cf into a local variable in pymain_run_python()

::

    bpo-32030: Add _PyCoreConfig.warnoptions (#4936)

    Merge _PyCoreConfig_ReadEnv() into _PyCoreConfig_Read(), and
    _Py_CommandLineDetails usage is now restricted to pymain_cmdline().

    Changes:

    * _PyCoreConfig: Add nxoption, xoptions, nwarnoption and warnoptions
    * Add _PyCoreConfig.program: argv[0] or ""
    * Move filename, command, module and xoptions from
      _Py_CommandLineDetails to _PyMain. xoptions _Py_OptList becomes
      (int, wchar_t**) list.
    * Add pymain_cmdline() function
    * Rename copy_argv() to copy_wstrlist(). Rename clear_argv() to
      clear_wstrlist(). Remove _Py_OptList structure: use (int,
      wchar_t**) list instead.
    * Rename pymain_set_flag_from_env() to pymain_get_env_flag()
    * Rename pymain_set_flags_from_env() to pymain_get_env_flags()
    * _PyMainInterpreterConfig_Read() now creates the warnoptions from
      _PyCoreConfig.warnoptions
    * Inline pymain_add_warning_dev_mode() and
      pymain_add_warning_bytes_flag() into config_init_warnoptions()
    * Inline pymain_get_program_name() into _PyCoreConfig_Read()
    * _Py_CommandLineDetails: Replace warning_options with nwarnoption
      and warnoptions. Replace env_warning_options with nenv_warnoption
      and env_warnoptions.
    * pymain_warnings_envvar() now has a single implementation for
      Windows and Unix: use config_get_env_var_dup() to also get the
      variable as wchar_t* on Unix.

::

    bpo-32030: Complete _PyCoreConfig_Read() (#4946)

    * Add _PyCoreConfig.install_signal_handlers
    * Remove _PyMain.config: _PyMainInterpreterConfig usage is now
      restricted to pymain_init_python_main().
    * Rename _PyMain.core_config to _PyMain.config
    * _PyMainInterpreterConfig_Read() now creates the xoptions dictionary
       from the core config
    * Fix _PyMainInterpreterConfig_Read(): don't replace xoptions and
      argv if they are already set.

::

    bpo-32030: Fix usage of memory allocators (#4953)

    * _Py_InitializeCore() doesn't call _PyMem_SetupAllocators() anymore
      if the PYTHONMALLOC environment variable is not set.
    * pymain_cmdline() now sets the allocator to the default, instead of
      setting the allocator in subfunctions.
    * Py_SetStandardStreamEncoding() now calls
      _PyMem_SetDefaultAllocator() to get a known allocator, to be able
      to release the memory with the same allocator.

::

    bpo-32030: Add _Py_EncodeUTF8_surrogateescape() (#4960)

    Py_EncodeLocale() now uses _Py_EncodeUTF8_surrogateescape(), instead
    of using temporary unicode and bytes objects. So Py_EncodeLocale()
    doesn't use the Python C API anymore.

::

    bpo-32030: Add _Py_EncodeLocaleRaw() (#4961)

    Replace Py_EncodeLocale() with _Py_EncodeLocaleRaw() in:

    * _Py_wfopen()
    * _Py_wreadlink()
    * _Py_wrealpath()
    * _Py_wstat()
    * pymain_open_filename()

    These functions are called early during Python intialization, only
    the RAW memory allocator must be used.

::

    bpo-32030: Add _Py_FindEnvConfigValue() (#4963)

    Add a new _Py_FindEnvConfigValue() function: code shared between
    Windows and Unix implementations of _PyPathConfig_Calculate() to read
    the pyenv.cfg file.

    _Py_FindEnvConfigValue() now uses _Py_DecodeUTF8_surrogateescape()
    instead of using a Python Unicode string, the Python API must not be
    used early during Python initialization. Same change in Unix
    search_for_exec_prefix(): use _Py_DecodeUTF8_surrogateescape().

    Cleanup also encode_current_locale(): PyMem_RawFree/PyMem_Free can be
    called with NULL.

    Fix also "NUL byte" => "NULL byte" typo.

::

    bpo-29240: Skip test_readline.test_nonascii() (#4968)

    Skip the test which fails on FreeBSD with POSIX locale.

    Skip the test to fix FreeBSD buildbots, until a fix can be found, so
    the buildbots can catch other regressions.


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
