+++++++++++++++
Split Py_Main()
+++++++++++++++

:date: 2018-03-06 14:00
:tags: cpython
:category: python
:slug: split-pymain
:authors: Victor Stinner


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


