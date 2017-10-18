++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2016 Q1
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-02-09 17:00
:tags: cpython
:category: python
:slug: contrib-cpython-2016q1
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2016 Q1
(january, februrary, march)::

    hg log -r 'date("2016-01-01"):date("2016-03-31")' --no-merges -u Stinner

Statistics: 196 non-merge commits + 33 merge commits (total: 229 commits).

Previous report: `My contributions to CPython during 2015 Q4
<{filename}/python_contrib_2015q4.rst>`_. Next report: `My contributions to
CPython during 2016 Q2 <{filename}/python_contrib_2016q2.rst>`_.


Summary
=======

Since this report is much longer than I expected, here are the highlights:

* Python 8: no pep8, no chocolate!
* AST enhancements coming from FAT Python
* faulthandler now catchs Windows fatal exceptions
* New PYTHONMALLOC environment variable
* tracemalloc: new C API and support multiple address spaces
* ResourceWarning warnings now come with a traceback
* PyMem_Malloc() now fails if the GIL is not held
* Interesting bug: reentrant flag in tracemalloc


Python 8: no pep8, no chocolate!
================================

I prepared an April Fool: `[Python-Dev] The next major Python version will be
Python 8
<https://mail.python.org/pipermail/python-dev/2016-March/143603.html>`_ :-)

I increased Python version to 8, added the ``pep8`` module and modified
``importlib`` to raise an ``ImportError`` if a module is not PEP8-compliant!


AST enhancements coming from FAT Python
=======================================

Changes coming from my `FAT Python
<http://faster-cpython.readthedocs.io/fat_python.html>`_ (AST optimizer, run
ahead of time):

The compiler now ignores constant statements like ``b'bytes'`` (issue #26204).
I had to replace constant statement with expressions to prepare the change (ex:
replace ``b'bytes'`` with ``x = b'bytes'``). First, the compiler emited a
``SyntaxWarning``, but it was quickly decided to let linters to emit such
warnings to not annoy users: `read the thread on python-dev
<https://mail.python.org/pipermail/python-dev/2016-February/143163.html>`_.

Example, Python 3.5::

    >>> def f():
    ...  b'bytes'
    ...
    >>> import dis; dis.dis(f)
      2           0 LOAD_CONST               1 (b'bytes')
                  3 POP_TOP
                  4 LOAD_CONST               0 (None)
                  7 RETURN_VALUE

Python 3.6::

    >>> def f():
    ...  b'bytes'
    ...
    >>> import dis; dis.dis(f)
      1           0 LOAD_CONST               0 (None)
                  2 RETURN_VALUE

Other changes:

* Issue #26107: The format of the co_lnotab attribute of code objects changes
  to support negative line number delta. It allows AST optimizers to move
  instructions without breaking Python tracebacks. Change needed by the loop
  unrolling optimization of FAT Python.
* Issue #26146: Add a new kind of AST node: ``ast.Constant``. It can be used by
  external AST optimizers like FAT Python, but the compiler does not emit
  directly such node. Update code to accept ast.Constant instead of ast.Num
  and/or ast.Str.
* Issue #26146: ``marshal.loads()`` now uses the empty frozenset singleton. It
  fixes a test failure in FAT Python and reduces the memory footprint.


faulthandler now catchs Windows fatal exceptions
================================================

I enhanced the faulthandler.enable() function on Windows to set a
handler for Windows fatal exceptions using ``AddVectoredExceptionHandler()``
(issue #23848).

Windows exceptions are the native way to handle fatal errors on Windows,
whereas UNIX signals SIGSEGV, SIGFPE and SIGABRT are "emulated" on top of that.


New PYTHONMALLOC environment variable
=====================================

I added a new ``PYTHONMALLOC`` environment variable (issue #26516) to set the
Python memory allocators.

``PYTHONMALLOC=debug`` enables debug hooks on a Python compiled in release
mode, whereas Python 3.5 requires to recompile Python in debug mode. These
hooks implements various checks:

* Detect **buffer underflow**: write before the start of the buffer
* Detect **buffer overflow**: write after the end of the buffer
* Detect API violations, ex: ``PyObject_Free()`` called on a buffer
  allocated by ``PyMem_Malloc()``
* Check if the GIL is held when allocator functions of PYMEM_DOMAIN_OBJ (ex:
  ``PyObject_Malloc()``) and PYMEM_DOMAIN_MEM (ex: ``PyMem_Malloc()``) domains
  are called

Moreover, logging a fatal memory error now uses the tracemalloc module to get
the traceback where a memory block was allocated. Example of a buffer overflow
using ``python3.6 -X tracemalloc=5`` (store 5 frames in traces)::

    Debug memory block at address p=0x7fbcd41666f8: API 'o'
        4 bytes originally requested
        The 7 pad bytes at p-7 are FORBIDDENBYTE, as expected.
        The 8 pad bytes at tail=0x7fbcd41666fc are not all FORBIDDENBYTE (0xfb):
            at tail+0: 0x02 *** OUCH
            at tail+1: 0xfb
            at tail+2: 0xfb
            ...
        The block was made by call #1233329 to debug malloc/realloc.
        Data at p: 1a 2b 30 00

    Memory block allocated at (most recent call first):
      File "test/test_bytes.py", line 323
      File "unittest/case.py", line 600
      ...

    Fatal Python error: bad trailing pad byte

    Current thread 0x00007fbcdbd32700 (most recent call first):
      File "test/test_bytes.py", line 323 in test_hex
      File "unittest/case.py", line 600 in run
      ...

``PYTHONMALLOC=malloc`` forces the usage of the system ``malloc()`` allocator.
This option can be used with Valgrind. Without this option, Valgrind emits tons
of false alarms in the Python ``pymalloc`` memory allocator.


tracemalloc: new C API and support multiple address spaces
==========================================================

Antoine Pitrou and Nathaniel Smith asked me to enhance the tracemalloc module:

* Add a C API to be able to manually track/untrack memory blocks, to track
  the memory allocated by custom memory allocators. For example, numpy uses
  allocators with a specific memory alignment for SIMD instructions.
* Support tracking memory of different address spaces. For example, central
  (CPU) memory and GPU memory for numpy.

Support multiple address spaces
-------------------------------

I made deep changes in the ``hashtable.c`` code (simple C implementation of an
hash table used by ``_tracemalloc``) to support keys of a variable size (issue
#26588), instead of using an hardcoded ``void *`` size. It allows to support
keys larger than ``sizeof(void*)``, but also to use *less* memory for keys
smaller than ``sizeof(void*)`` (ex: ``int`` keys).

Then I extended the C ``_tracemalloc`` module and the Python ``tracemalloc`` to
add a new ``domain`` attribute to traces: add ``Trace.domain`` attribute and
``tracemalloc.DomainFilter`` class.

The final step was to optimize the memory footprint of _tracemalloc. Start with
compact keys (``Py_uintptr_t`` type) and only switch to ``pointer_t`` keys when
the first memory block with a non-zero domain is tracked (when one more one
address space is used). So the ``_tracemalloc`` memory usage doesn't change by
default in Python 3.6!

C API
-----

I added a private C API (issue #26530)::

  int _PyTraceMalloc_Track(_PyTraceMalloc_domain_t domain, Py_uintptr_t ptr, size_t size);
  int _PyTraceMalloc_Untrack(_PyTraceMalloc_domain_t domain, Py_uintptr_t ptr);

I waited for Antoine and Nathaniel feedback on this API, but the API remains
private in Python 3.6 since none reviewed it.


ResourceWarning warnings now come with a traceback
==================================================

Final result
------------

Before going to explain the long development of the feature, let's see an
example of the final result! Example with the script ``example.py``::

    import warnings

    def func():
        return open(__file__)

    f = func()
    f = None

Output of the command ``python3.6 -Wd -X tracemalloc=5 example.py``::

    example.py:7: ResourceWarning: unclosed file <_io.TextIOWrapper name='example.py' mode='r' encoding='UTF-8'>
      f = None
    Object allocated at (most recent call first):
      File "example.py", lineno 4
        return open(__file__)
      File "example.py", lineno 6
        f = func()

The ``Object allocated at (...)`` part is the new feature ;-)

Add source parameter to warnings
--------------------------------

Python 3 logs ``ResourceWarning`` warnings when a resource is not closed
properly to help developers to handle resources correctly. The problem is that
the warning is only logged when the object is destroy, which can occur far from
the object creation and can occur on a line unrelated to the object because of
the garbage collector.

I added a new ``tracemalloc`` module to Python 3.4 which has an interesting
``tracemalloc.get_object_traceback()`` function. If tracemalloc traced the
allocation of an object, it is able to provide later the traceback where the
object was allocated.

I wanted to modify the ``warnings`` module to call
``get_object_traceback()``, but I noticed that it wasn't possible
to easily extend the ``warnings`` API because this module allows to override
``showwarning()`` and ``formatwarning()`` functions and these
functions have a fixed number of parameters. Example::

    def showwarning(message, category, filename, lineno, file=None, line=None):
        ...

With the issue #26568, I added new  ``_showwarnmsg()`` and ``_formatwarnmsg()``
functions to the warnings module which get a ``warnings.WarningMessage`` object
instead of a list of parameters::

    def _showwarnmsg(msg):
        ...

I added a ``source`` attribute to ``warnings.WarningMessage`` (issue #26567)
and a new optional ``source`` parameter to ``warnings.warn()`` (issue #26604):
the leaked resource object. I modified ``_formatwarnmsg()`` to log the
traceback where resource was allocated, if available.

The tricky part was to fix corner cases when the following functions of the
``warnings`` module are overriden:

* ``formatwarning()``, ``showwarning()``
* ``_formatwarnmsg()``, ``_showwarnmsg()``


Set the source parameter
------------------------

I started to modify modules to set the source parameter when logging
``ResourceWarning`` warnings.

The easy part was to modify ``asyncore``, ``asyncio`` and ``_pyio`` modules to
set the ``source`` parameter. These modules are implemented in Python, the
change was just to add ``source=self``. Example of ``asyncio`` destructor::

    def __del__(self):
        if not self.is_closed():
            warnings.warn("unclosed event loop %r" % self, ResourceWarning,
                          source=self)
            if not self.is_running():
                self.close()

Note: The warning is logged before the resource is closed to provide more
information in ``repr()``. Many objects clear most information in their
``close()`` method.

Modifying C modules was more tricky than expected. I had to implement
"finalizers" (`PEP 432: Safe object finalization
<https://www.python.org/dev/peps/pep-0442/>`_) for the ``_socket.socket`` type
(issue #26590) and for the ``os.scandir()`` iterator (issue #26603).

More reliable warnings
----------------------

The Python shutdown process is complex, and some Python functions are broken
during the shutdown. I enhanced the warnings module to handle nicely these
failures and try to log warnings anyway.

I modified ``warnings.formatwarning()`` to catch ``linecache.getline()``
failures on formatting the traceback.

Logging the resource traceback is complex, so I only implemented it in Python.
Python tries to use the Python ``warnings`` module if it was imported, or falls
back on the C ``_warnings`` module. To get the resource traceback at Python
shutdown, I modified the C module to try to import the Python warning:
``_warnings.warn_explicit()`` now tries to import the Python warnings module if
the source parameter is set to be able to log the traceback where the source
was allocated (issue #26592).

Fix ResourceWarning warnings
----------------------------

Since it became easy to debug these warnings, I fixed some of them in the
Python test suite:

* Issue #26620: Fix ResourceWarning in test_urllib2_localnet. Use context
  manager on urllib objects and use self.addCleanup() to cleanup resources even
  if a test is interrupted with CTRL+c
* Issue #25654: multiprocessing: open file with ``closefd=False`` to avoid
  ResourceWarning. _test_multiprocessing: open file with ``O_EXCL`` to detect
  bugs in tests (if a previous test forgot to remove TESTFN).
  ``test_sys_exit()``: remove TESTFN after each loop iteration
* Fix ``ResourceWarning`` in test_unittest when interrupted


PyMem_Malloc() now fails if the GIL is not held
===============================================

Since using the mall object allocator (``pymalloc)``) for dictionary key
storage showed speedup for the dict type (issue #23601), I proposed to
generalize the change, use ``pymalloc`` for ``PyMem_Malloc()``: `[Python-Dev]
Modify PyMem_Malloc to use pymalloc for performance
<https://mail.python.org/pipermail/python-dev/2016-February/143084.html>`_.

The main issue was that the change means that ``PyMem_Malloc()`` now requires
to hold the GIL, whereas it didn't before since it called directly
``malloc()``.

Check if the GIL is held
------------------------

CPython has a ``PyGILState_Check()`` function to check if the GIL is held.
Problem: the function doesn't work with subinterpreters: see issues #10915 and
#15751.

I added an internal flag to ``PyGILState_Check()`` (issue #26558) to skip the
test. The flag value is false at startup, set to true once the GIL is fully
initialized (Python initialization), set to false again when the GIL is
destroyed (Python finalization). The flag is also set to false when the first
subinterpreter is created.

This hack works around ``PyGILState_Check()`` limitations allowing to call
`PyGILState_Check()`` anytime to debug more bugs earlier.

``_Py_dup()``, ``_Py_fstat()``, ``_Py_read()`` and ``_Py_write()`` are
low-level helper functions for system functions, but these functions require
the GIL to be held.  Thanks to the ``PyGILState_Check()`` enhancement, it
became possible to check the GIL using an assertion.

PyMem_Malloc() and GIL
----------------------

Issue #26563: Debug hooks on Python memory allocators now raise a fatal error
if memory allocator functions like PyMem_Malloc() and PyMem_Malloc() are called
without holding the GIL.

The change spotted two bugs which I fixed:

* Issue #26563: Replace PyMem_Malloc() with PyMem_RawMalloc() in the Windows
  implementation of os.stat(), the code is called without holding the
  GIL.
* Issue #26563: Fix usage of PyMem_Malloc() in overlapped.c. Replace
  PyMem_Malloc() with PyMem_RawFree() since PostToQueueCallback() calls
  PyMem_Free() in a new C thread which doesn't hold the GIL.

I wasn't able to switch ``PyMem_Malloc()`` to ``pymalloc`` in this quarter,
since it took more a lot of time to implement requested checks and test third
party modules.

Fatal error and faulthandler
----------------------------

I enhanced the faulthandler module to work in non-Python threads (issue
#26563). I fixed ``Py_FatalError()`` if called without holding the GIL: don't
try to print the current exception, nor try to flush stdout and stderr: only
dump the traceback of Python threads.


Interesting bug: reentrant flag in tracemalloc
==============================================

A bug annoyed me a lot: a random assertion error related to a reentrant flag in
the _tracemalloc module.

Story starting in the `middle of the issue #26588 (2016-03-21)
<http://bugs.python.org/issue26588#msg262125>`_. While working on issue #26588,
"_tracemalloc: add support for multiple address spaces (domains)", I noticed an
assertion failure in set_reentrant(), a helper function to set a *Thread Local
Storage* (TLS), on a buildbot::

    python: ./Modules/_tracemalloc.c:195: set_reentrant:
        Assertion `PyThread_get_key_value(tracemalloc_reentrant_key) == ((PyObject *) &_Py_TrueStruct)' failed.

I was unable to reproduce the bug on my Fedora 23 (AMD64). After changes on my
patch, I pushed it the day after, but the assertion failed again. I added
assertions and debug informations. More failures, an interesting one on Windows
which uses a single process.

I added an assertion in tracemalloc_init() to ensure that the reeentrant flag
is set at the end of the function. The reentrant flag was no more set at
tracemalloc_start() entry for an unknown reason. I changed the module
initialization to no call tracemalloc_init() anymore, it's only called on
tracemalloc.start().

"The bug was seen on 5 buildbots yet: PPC Fedora, AMD64 Debian, s390x RHEL,
AMD64 Windows, x86 Ubuntu."

I finally understood and fixed the bug with the `change af1c1149784a
<https://hg.python.org/cpython/rev/af1c1149784a>`_: tracemalloc_start() and
tracemalloc_stop() don't clear/set the reentrant flag anymore.

The problem was that I expected that tracemalloc_init() and tracemalloc_start()
functions would always be called in the same thread, whereas it occurred that
tracemalloc_init() was called in thread A when the tracemalloc module is
imported, whereas tracemalloc_start() was called in thread B.


Other commits
=============

Enhancements
------------

The developers of the ``vmprof`` profiler asked me to expose the atomic
variable ``_PyThreadState_Current``. The private variable was removed from
Python 3.5.1 API because the implementation of atomic variables depends on the
compiler, compiler options, etc. and so caused compilation issues. I added a
new private ``_PyThreadState_UncheckedGet()`` function (issue #26154) which
gets the value of the variable without exposing its implementation.

Other enhancements:

* Issue #26099: The site module now writes an error into stderr if
  sitecustomize module can be imported but executing the module raise an
  ImportError. Same change for usercustomize.
* Issue #26516: Enhance Python memory allocators documentation. Add link to
  PYTHONMALLOCSTATS environment variable. Add parameters to PyMem macros like
  PyMem_MALLOC().
* Issue #26569: Fix pyclbr.readmodule() and pyclbr.readmodule_ex() to support
  importing packages.
* Issue #26564, #26516, #26563: Enhance documentation on memory allocator debug
  hooks.
* doctest now supports packages. Issue #26641: doctest.DocFileTest and
  doctest.testfile() now support packages (module splitted into multiple
  directories) for the package parameter.


Bugfixes
--------

Issue #25843: When compiling code, don't merge constants if they are equal but
have a different types. For example, ``f1, f2 = lambda: 1, lambda: 1.0`` is now
correctly compiled to two different functions: ``f1()`` returns ``1`` (int) and
``f2()`` returns ``1.0`` (int), even if 1 and 1.0 are equal.

Other fixes:

* Issue #26101: Fix test_compilepath() of test_compileall. Exclude Lib/test/
  from sys.path in test_compilepath(). The directory contains invalid Python
  files like Lib/test/badsyntax_pep3120.py, whereas the test ensures that all
  files can be compiled.
* Issue #24520: Replace fpgetmask() with fedisableexcept(). On FreeBSD,
  fpgetmask() was deprecated long time ago.  fedisableexcept() is now
  preferred.
* Issue #26161: Use Py_uintptr_t instead of void* for atomic pointers in
  pyatomic.h. Use atomic_uintptr_t when <stdatomic.h> is used. Using void*
  causes compilation warnings depending on which implementation of atomic types
  is used.
* Issue #26637: The importlib module now emits an ImportError rather than a
  TypeError if __import__() is tried during the Python shutdown process but
  sys.path is already cleared (set to None).
* doctest: fix _module_relative_path() error message. Write the module name
  rather than <module> in the error message, if module has no __file__
  attribute (ex: package).


Fix type downcasts on Windows 64-bit
------------------------------------

In my spare time, I'm trying to fix a few compiler warnings on Windows 64-bit
where the C ``long`` type is only 32-bit, whereas pointers are ``64-bit`` long:

* posix_getcwd(): limit to INT_MAX on Windows. It's more to fix a compiler
  warning during compilation, I don't think that Windows support current
  working directories larger than 2 GB :-)
* _pickle: Fix load_counted_tuple(), use Py_ssize_t for size. Fix a warning on
  Windows 64-bit.
* getpathp.c: fix compiler warning, wcsnlen_s() result type is size_t.
* compiler.c: fix compiler warnings on Windows
* _msi.c: try to fix compiler warnings
* longobject.c: fix compilation warning on Windows 64-bit. We know that
  Py_SIZE(b) is -1 or 1 an so fits into the sdigit type.
* On Windows, socket.setsockopt() now raises an OverflowError if the socket
  option is larger than INT_MAX bytes.


Unicode bugfixes
----------------

* Issue #26227: On Windows, getnameinfo(), gethostbyaddr() and
  gethostbyname_ex() functions of the socket module now decode the hostname
  from the ANSI code page rather than UTF-8.
* Issue #26217: Unicode resize_compact() must set wstr_length to 0 after
  freeing the wstr string. Otherwise, an assertion fails in
  _PyUnicode_CheckConsistency().
* Issue #26464: Fix str.translate() when string is ASCII and first replacements
  removes characters, but next replacements use a non-ASCII character or a
  string longer than 1 character. Regression introduced in Python 3.5.0.


Buildbot, tests
---------------

Just to give you an idea of the work required to keep a working CI, here is the
list of changes I maded in a single quarter to make tests and Python buildbots
more reliable.

* Issue #26610: Skip test_venv.test_with_pip() if ctypes miss
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


Contributions
-------------

I also pushed a few changes written by other contributors:

* Issue #25907: Use {% trans %} tags in HTML templates to ease the translation
  of the documentation. The tag comes from Jinja templating system, used by
  Sphinx. Patch written by **Julien Palard**.
* Issue #26248: Enhance os.scandir() doc, patch written by Ben Hoyt:
* Fix error message in asyncio.selector_events. Patch written by **Carlo
  Beccarini**.
* Issue #16851: Fix inspect.ismethod() doc, return also True if object is an
  unbound method. Patch written by **Anna Koroliuk**.
* Issue #26574: Optimize bytes.replace(b'', b'.') and bytearray.replace(b'', b'.'):
  up to 80% faster. Patch written by **Josh Snider**.
