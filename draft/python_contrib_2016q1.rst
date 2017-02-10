++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2016 Q1
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-02-09 17:00
:tags: cpython
:category: python
:slug: contrib-cpython-2016q1
:authors: Victor Stinner

My contributions to CPython during 2016 Q1 (january, februrary, march)::

    hg log -r 'date("2016-01-01"):date("2016-03-31")' --no-merges -u Stinner

Statistics: 196 non-merge commits + 33 merge commits (total: 229 commits).

Quick:

* On ResourceWarning, log traceback where the object was allocated using tracemalloc.
* New PYTHONMALLOC environment variable: allow to use Python builtin debug
  hooks or to use Valgrind on a Python compiled in release mode. It's no
  more needed to recompile Python in debug mode.
* Upstream some FAT Python work
* Enhance debug tools: faulthandler, tracemalloc and Py_FatalError().
* _tracemalloc: add domain to trace keys
* Issue #23848: On Windows, faulthandler.enable() now also installs an
  exception handler to dump the traceback of all Python threads on fatal
  Windows exceptions, not only on UNIX signals (SIGSEGV, SIGFPE, SIGABRT).
* regrtest: better output.
* Python 8: PEP 8 enforced.

Interesting bug
===============

* Issue #26588: Fix _tracemalloc start/stop: don't play with the reentrant flag.
  set_reentrant(1) fails with an assertion error if tracemalloc_init() is
  called first in a thread A and tracemalloc_start() is called second in a
  thread B. The tracemalloc is imported in a thread A. Importing the module
  calls tracemalloc_init(). tracemalloc.start() is called in a thread B.

faulthandler
============

* Issue #23848: On Windows, faulthandler.enable() now also installs an
  exception handler to dump the traceback of all Python threads on fatal
  Windows exceptions, not only on UNIX signals (SIGSEGV, SIGFPE, SIGABRT).

FAT Python
==========

* Issue #26107: The format of the co_lnotab attribute of code objects changes
  to support negative line number delta. It allows AST optmizers to move
  instructions without breaking Python tracebacks. Change needed by the loop
  unrolling optimization of FAT Python.
* Issue #26146: Add a new kind of AST node: ast.Constant. It can be used by
  external AST optimizers like FAT Python, but the compiler does not emit
  directly such node. Update code to accept ast.Constant instead of ast.Num
  and/or ast.Str.
* Issue #26146: marshal.loads() now uses the empty frozenset singleton. It
  fixes a test failure in FAT Python and reduces the memory footprint.
* Issue #26204: Replace constant statement with expression to prepare a
  following change which will ignore constant statements. For example,
  replace ``1`` with ``x = 1``.
* Issue #26204: compiler now ignores constant statements like ``1``. First,
  the compiler emited a ``SyntaxWarning``, but it was decided to let linters
  to emit such warnings to not annoy users.


Enhancements
============

* Issue #26154: Add a new private _PyThreadState_UncheckedGet() function which
  gets the current thread state, but don't call Py_FatalError() if it is NULL.
  Python 3.5.1 removed the _PyThreadState_Current symbol from the Python C API
  to no more expose complex and private atomic types. Atomic types depends on
  the compiler or can even depend on compiler options. The new function
  _PyThreadState_UncheckedGet() allows to get the variable value without having
  to care of the exact implementation of atomic types. Change requested by
  vmprof developers.
* Issue #26099: The site module now writes an error into stderr if
  sitecustomize module can be imported but executing the module raise an
  ImportError. Same change for usercustomize.
* Issue #26516: Enhance Python memory allocators documentation. Add link to
  PYTHONMALLOCSTATS environment variable. Add parameters to PyMem macros like
  PyMem_MALLOC(). Fix PyMem_SetupDebugHooks(): add Calloc functions. Add some
  newlines for readability.
* Issue #26516: Add PYTHONMALLOC environment variable to set the Python memory
  allocators. It allows to enable debug hooks on a Python compiled in debug
  mode.  It also allows to force ``malloc()`` allocator to debug Python in
  Valgrind. By default, Python uses pymalloc allocator which emits a lot of
  false alarms in Valgrind.
* Issue #26569: Fix pyclbr.readmodule() and pyclbr.readmodule_ex() to support
  importing packages.
* Issue #26564, #26516, #26563: Enhance documentation on memory allocator debug
  hooks.
* doctest now supports packages. Issue #26641: doctest.DocFileTest and
  doctest.testfile() now support packages (module splitted into multiple
  directories) for the package parameter.

ResourceWarning
===============

* Issue #26568: add new  _showwarnmsg() and _formatwarnmsg() functions to the
  warnings module.
* Issue #26567: On ResourceWarning, log traceback where the object was
  allocated. Add a source attribute to warnings.WarningMessage. Add
  warnings._showwarnmsg() which uses tracemalloc to get the traceback where
  source object was allocated.
* Issue #26590: Add socket finalizer. Implement a safe finalizer for the
  _socket.socket type. It now releases the GIL to close the socket. Use
  PyErr_ResourceWarning() to raise the ResourceWarning to pass the socket
  object to the warning logger, to get the traceback where the socket was
  created (allocated).
* Issue #26604: Add a source parameter to warnings.warn(). Add a new optional
  source parameter to _warnings.warn() and warnings.warn(). Modify asyncore,
  asyncio and _pyio modules to set the source parameter when logging a
  ResourceWarning warning.
* Issue #26603: Implement finalizer for os.scandir() iterator.
  Set the source parameter when emitting the ResourceWarning warning.
  Close the iterator before emitting the warning
* Issue #26592: _warnings.warn_explicit() now tries to import the warnings
  module (Python implementation) if the source parameter is set to be able to
  log the traceback where the source was allocated.
* Issue #26620: Fix ResourceWarning in test_urllib2_localnet. Use context
  manager on urllib objects to ensure that they are closed on error.
  Use self.addCleanup() to cleanup resources even if a test is interrupted
  with CTRL+c
* Issue #21925: warnings.formatwarning() now catches exceptions on
  linecache.getline(...) to be able to log ResourceWarning emitted late during
  the Python shutdown process.
* Issue #25654: multiprocessing: open file with closefd=False to avoid
  ResourceWarning. _test_multiprocessing: open file with O_EXCL to detect bugs
  in tests (if a previous test forgot to remove TESTFN). test_sys_exit():
  remove TESTFN after each loop iteration
* Issue #21925: Fix test_warnings for release mode. Use -Wd comment line option
  to log the ResourceWarning. Initial patch written by Serhiy Storchaka.
* Fix ResourceWarning in test_unittest when interrupted

tracemalloc
===========

* Issue #26588: hashtable.h now supports keys of any size, not only
  sizeof(void*). It allows to support key larger than sizeof(void*), but also
  to use less memory for key smaller than sizeof(void*).
* Issue #26588: The _tracemalloc now supports tracing memory allocations of
  multiple address spaces (domains). Add tracemalloc.DomainFilter.
* Issue #26530: Add C functions _PyTraceMalloc_Track() and
  _PyTraceMalloc_Untrack() to track memory blocks using the tracemalloc module.
* Issue #26588: _tracemalloc: use compact key for traces. Optimize memory
  footprint of _tracemalloc before non-zero domain is used. Start with compact
  key (Py_uintptr_t) and also switch to pointer_t key when the first memory
  block with a non-zero domain is tracked.

Memory
======

"use small object allocator for dict key storage" showed speedup for the dict
type by replacing PyMem_Malloc() with PyObject_Malloc() in dictobject.c.
http://bugs.python.org/issue23601

When I worked on the PEP 445, it was discussed to use the Python fast memory
allocator for small memory allocations (<= 512 bytes), but I think that nobody
tested on benchmark.

[Python-Dev] Modify PyMem_Malloc to use pymalloc for performance
https://mail.python.org/pipermail/python-dev/2016-February/143084.html

* Issue #26563: faulthandler now works in non-Python threads
* Issue #26563: Fail if PyMem_Malloc() is called without holding the GIL. Debug
  hooks on Python memory allocators now raise a fatal error if functions of the
  PyMem_Malloc() family are called without holding the GIL.
* Issue #26563: Replace PyMem_Malloc() with PyMem_RawMalloc() in the Windows
  implementation of os.stat(), since the code is called without holding the
  GIL.
* Issue #26563: Fix usage of PyMem_Malloc() in overlapped.c. Replace
  PyMem_Malloc() with PyMem_RawFree() since PostToQueueCallback() calls
  PyMem_RawFree() (previously PyMem_Free()) in a new C thread which doesn't
  hold the GIL.

Changes
=======

* Issue #26100: Add subprocess._optim_args_from_interpreter_flags(). The test
  suite now pass -O and -OO command line options to subprocesses.
* Issue #25876: test_gdb: use subprocess._args_from_interpreter_flags() to test
  Python with more options.
* Minor refactoring in various parts of the Python and C code: remove unused
  imports, write one import per line, etc.
* Issue #26564: On memory error, dump the traceback where the corrupted
  memory block was allocated. Use the tracemalloc module to get the traceback.

Bugfixes
========

* Issue #26101: Fix test_compilepath() of test_compileall. Exclude Lib/test/
  from sys.path in test_compilepath(). The directory contains invalid Python
  files like Lib/test/badsyntax_pep3120.py, whereas the test ensures that all
  files can be compiled.
* Issue #24520: Replace fpgetmask() with fedisableexcept(). On FreeBSD,
  fpgetmask() was deprecated long time ago.  fedisableexcept() is now
  preferred.
* Issue #25843: When compiling code, don't merge constants if they are equal
  but have a different types. For example, "f1, f2 = lambda: 1, lambda: 1.0" is
  now correctly compiled to two different functions: f1() returns 1 (int) and
  f2() returns 1.0 (int), even if 1 and 1.0 are equal.
* Issue #26161: Use Py_uintptr_t instead of void* for atomic pointers in
  pyatomic.h. Use atomic_uintptr_t when <stdatomic.h> is used. Using void*
  causes compilation warnings depending on which implementation of atomic types
  is used.
* Issue #26558: Fix Py_FatalError() if called without the GIL. If
  Py_FatalError() is called without the GIL, don't try to print the current
  exception, nor try to flush stdout and stderr: only dump the traceback of
  Python threads.
* posix_getcwd(): limit to INT_MAX on Windows. It's more to fix a conversion
  warning during compilation, I don't think that Windows support current
  working paths larger than 2 GB...
* Issue #10915, #15751, #26558: Add more checks on the GIL

  - PyGILState_Check() now returns 1 (success) before the creation of the GIL and
    after the destruction of the GIL. It allows to use the function early in
    Python initialization and late in Python finalization.
  - Add a flag to disable PyGILState_Check(). Disable PyGILState_Check() when
    Py_NewInterpreter() is called
  - Add assert(PyGILState_Check()) to: _Py_dup(), _Py_fstat(), _Py_read()
    and _Py_write()
  - Check the GIL in PyObject_Malloc(). The debug hook of PyObject_Malloc() now
    checks that the GIL is held when the function is called.
* Issue #26637: The importlib module now emits an ImportError rather than a
  TypeError if __import__() is tried during the Python shutdown process but
  sys.path is already cleared (set to None).
* Issue #26610: Skip test_venv.test_with_pip() if ctypes miss
* doctest: fix _module_relative_path() error message. Write the module name
  rather than <module> in the error message, if module has no __file__
  attribute (ex: package).

Windows 64-bit:

* _pickle: Fix load_counted_tuple(), use Py_ssize_t for size. Fix a warning on
  Windows 64-bit.
* getpathp.c: fix compiler warning, wcsnlen_s() result type is size_t.
* compiler.c: fix compiler warnings on Windows
* _msi.c: try to fix compiler warnings
* longobject.c: fix compilation warning on Windows 64-bit. We know that
  Py_SIZE(b) is -1 or 1 an so fits into the sdigit type.
* On Windows, socket.setsockopt() now raises an OverflowError if the socket
  option is larger than INT_MAX bytes.

Unicode:

* Issue #26217: Unicode resize_compact() must set wstr_length to 0 after
  freeing the wstr string. Otherwise, an assertion fails in
  _PyUnicode_CheckConsistency().
* Issue #26227: Windows: Decode hostname from ANSI code page. On Windows,
  getnameinfo(), gethostbyaddr() and gethostbyname_ex() functions of the socket
  module now decode the hostname from the ANSI code page rather than UTF-8.
* Issue #26464: Fix str.translate() when string is ASCII and first replacements
  removes character, but next replacement uses a non-ASCII character or a
  string longer than 1 character. Regression introduced in Python 3.5.0.

Buildbot, tests:

* test_asyncio: fix test_timeout_time(). Accept time delta up to 0.12 second,
  instead of 0.11, for the "AMD64 FreeBSD 9.x" buildbot slave.
* Issue #13305: Always test datetime.datetime.strftime("%4Y") for years < 1900.
  Change quickly reverted, strftime("%4Y") fails on most platforms.
* Issue #17758: Skip test_site if site.USER_SITE directory doesn't exist and
  cannot be created.
* Fix test_venv on FreeBSD buildbot. Ignore pip warning in
  test_venv.test_with_venv().
* Issue #26566: Rewrite test_signal.InterProcessSignalTests. Don't use
  os.fork() with a subprocess to not inherit existing signal handlers or
  threads: start from a fresh process. Use a timeout of 10 seconds to wait for
  the signal instead of 1 second
* Issue #26538: regrtest: Fix module.__path__. libregrtest: Fix setup_tests()
  to keep module.__path__ type (_NamespacePath), don't convert to a list.
  Add _NamespacePath.__setitem__() method to importlib._bootstrap_external.
* regrtest: add time to output. Timestamps should help to debug slow buildbots,
  and timeout and hang on buildbots.
* regrtest: add timeout to main process when using -jN. libregrtest: add a
  watchdog to run_tests_multiprocess() using faulthandler.dump_traceback_later().
* Makefile: change default value of TESTTIMEOUT from 1 hour to 15 min.
  The whole test suite takes 6 minutes on my laptop. It takes less than 30
  minutes on most buildbots. The TESTTIMEOUT is the timeout for a single test
  file.
* Buildbots: change also Windows timeout from 1 hour to 15 min
* regrtest: display test duration in sequential mode. Only display duration if
  a test takes more than 30 seconds.
* Issue #18787: Try to fix test_spwd on OpenIndiana. Try to get the "root"
  entry which should exist on all UNIX instead of "bin" which doesn't exist on
  OpenIndiana.
* regrtest: fix --fromfile feature. Update code for the name regrtest output
  format. Enhance also test_regrtest test on --fromfile
* regrtest: mention if tests run sequentially or in parallel
* regrtest: when parallel tests are interrupted, display progress
* support.temp_dir(): call support.rmtree() instead of shutil.rmtree(). Try
  harder to remove directories on Windows.
* rt.bat: use -m test instead of Lib\test\regrtest.py
* Refactor regrtest.
* Fix test_warnings.test_improper_option(). test_warnings: only run
  test_improper_option() and test_warnings_bootstrap() once. The unit test
  doesn't depend on self.module.
* Fix test_os.test_symlink(): remove created symlink.
* Issue #26643: Add missing shutil resources to regrtest.py
* test_urllibnet: set timeout on test_fileno(). Use the default timeout of 30
  seconds to avoid blocking forever.
* Issue #26295: When using "python3 -m test --testdir=TESTDIR", regrtest
  doesn't add "test." prefix to test module names. regrtest also prepends
  testdir to sys.path.
* Issue #26295: test_regrtest now uses a temporary directory

Misc:

* Fix typo in doc: avoid the french "& cie" :-)

Refactoring
===========

Tons of tiny changes to make the code simpler and safer in subtle ways.

Python 8
========

[Python-Dev] The next major Python version will be Python 8
https://mail.python.org/pipermail/python-dev/2016-March/143603.html

::

    changeset:   100818:9aedec2dbc01
    user:        Victor Stinner <victor.stinner@gmail.com>
    date:        Thu Mar 31 23:30:53 2016 +0200
    files:       Include/patchlevel.h Lib/pep8.py Lib/site.py
    description:
    Python 8: no pep8, no chocolate!

Contributions
=============

* Issue #25907: Use {% trans %} tags in HTML templates to ease the translation
  of the documentation. The tag comes from Jinja templating system, used by
  Sphinx. Patch written by Julien Palard.
* Issue #26248: Enhance os.scandir() doc, patch written by Ben Hoyt:
* Fix error message in asyncio.selector_events. Patch written by Carlo
  Beccarini.
* Issue #16851: Fix inspect.ismethod() doc, return also True if object is an
  unbound method. Patch written by Anna Koroliuk.
* Issue #26574: Optimize bytes.replace(b'', b'.') and bytearray.replace(b'', b'.'):
  up to 80% faster. Patch written by Josh Snider.

