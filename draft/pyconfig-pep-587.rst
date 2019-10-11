+++++++++++++++++
PyConfig: PEP 587
+++++++++++++++++

Changing the Python default encoding to UTF-8 is an old idea. After I
saw enough bug reports, I decided to implement it as the PEP 540 in
Python 3.7: ``python3.7 -X utf8`` ignores your locale and forces the
usage of the UTF-8 encoding in Python.

Python Configuration
====================

It's a huge bag of unrelated problems:

* What is the exhaustive list of ways to configuration Python?
* Python Configuration had zero test and zero documentation
* Path Configuration had zero test and zero documentation
* Extend the existing C API to accept byte strings
* Bootstrap problem of configurating the LC_CTYPE locale, UTF-8 Mode,
  filesystem encoding; but also decode byte strings from an unknown
  encoding; etc.
* Rewrite the Path Configuration in pure Python
* Multiphase initialization
* What are the use cases?
* How is the current C API used to embed Python?
* PyInstaller, PyOxyder, py2app, etc. use case
* etc.

Main milestones
===============

* PEP 540 implemented, Python 3.7.0 released with it
* Preinitialization
* Reading the config has no longer side effects
* PyPreConfig no longer uses strings: no more bootstrap issue with
  memory allocators
* PEP 587 accepted

Main development constraint: push small atomic changes without breaking
the master branch, nor breaking backward compatibility.

API constraint: when passing a configuration to a function, the input
config must not be modified. Functions have to duplicate the
configuration and work on their local copy.

What is the authority in term of configuration? Before preinit? During
core init? Once Python is fully initialized?

Problem 1: Encoding used to parse command line arguments
========================================================

To implement my PEP 540, there was a corner case. The UTF-8 Mode can be
enabled by the ``-X utf8`` command line. But the C code parsing command
line arguments works on Unicode (``wchar_t``), whereas the ``main()``
function gets them as bytes: ``int argc, char **argv``. The exception is
Windows where we get them directly as Unicode. Pseudo-code:

* Decode command line arguments (``char **argv``) from the locale
  encoding
* Parse command line arguments as Unicode
* If ``-X utf8`` is found, enable the UTF-8

The first problem is that parsing the command line arguments stores
string which are decoded from the locale encoding. If the UTF-8 mode is
enabled, already parsed strings use a different encoding (except if the
locale encoding is UTF-8).

One solution could be to throw away the parsed configuration, and
restart parsing the command line with UTF-8 mode enabled.

Problem 2: Scatted configuration
================================

The second problem is that the "Python configuration" is scattered all
around the C code in different files. Some files use static buffers to
store strings, like ``Modules/getpath.c``::

    static wchar_t prefix[MAXPATHLEN+1];
    static wchar_t exec_prefix[MAXPATHLEN+1];
    static wchar_t progpath[MAXPATHLEN+1];
    static wchar_t *module_search_path = NULL;

There are many ways to configure Python:

* Command line arguments like ``-E``
* Environment variable like ``PYTHONPATH``
* Configuration files like ``pyvenv.cfg``
* Global configuration variables like ``Py_IgnoreEnvironmentFlag``
* Function call like ``Py_SetPath()``

Each configures different options.

Some configuration parameters are not accessible from the C API, or not
easily. For example, there is no API to override the default values of
``sys.executable``.


Rework Py_Main()
================

I started by reworking functions around ``Py_Main()`` in
``Modules/main.c``. I splitted long functions into smaller functions.  I
added structures to replace global variables. I tried to work step by
step.

The main risk was to introduce a regression. By the way, there was
basically zero test on the "Python configuration".


_PyInitError API
================

In Python 3.6, Py_Main() calls ``Py_FatalError()`` when something goes
wrong. This function not only exits the process, but it can also create
a coredump because it calls ``abort()``. I wanted to provide a better
way to report errors. I create a new ``_PyInitError`` API. Each function
returns ``_PyInitError`` which is basically either "ok" or an error (an
error message). The goal is to let the caller decides how to handle the
error and never exit the process. When Python is embedded in an
application, it's a bad practice to exit the whole process!

Example::

    static _PyInitError
    wstrlist_append(int *len, wchar_t ***list, const wchar_t *str)
    {
        ...
        wchar_t **list2 = (wchar_t **)PyMem_RawRealloc(*list, size);
        if (list2 == NULL) {
            PyMem_RawFree(str2);
            return _Py_INIT_NO_MEMORY();
        }
        ...
        return _Py_INIT_OK();
    }


_PyCoreConfig
=============

I create a C structure to store the "Python configuration" using C
types. I started with 3 fields. In Python 3.7, the ``_PyCoreConfig``
structure has not less than 34 fields!

Extract::

    typedef struct {
        int install_signal_handlers;  /* Install signal handlers? -1 means unset */
        int ignore_environment; /* -E, Py_IgnoreEnvironmentFlag */
        int use_hash_seed;      /* PYTHONHASHSEED=x */
        ...
    } _PyCoreConfig;

My goal was to be able to read all the Python configuration at once
with no side effect. **Reading** the configuration must not modify
any Python state. **Writing** the configuration must be a separated
and explicit action.

It took me several months to achieve this goal. I moved configuration
options one by one with a lot of care.

_PyMainInterpreterConfig
========================

Nick Coghlan? Eric Snow?

Python 3.7 ::

    typedef struct {
        int install_signal_handlers;   /* Install signal handlers? -1 means unset */
        PyObject *argv;                /* sys.argv list, can be NULL */
        PyObject *executable;          /* sys.executable str */
        PyObject *prefix;              /* sys.prefix str */
        PyObject *base_prefix;         /* sys.base_prefix str, can be NULL */
        PyObject *exec_prefix;         /* sys.exec_prefix str */
        PyObject *base_exec_prefix;    /* sys.base_exec_prefix str, can be NULL */
        PyObject *warnoptions;         /* sys.warnoptions list, can be NULL */
        PyObject *xoptions;            /* sys._xoptions dict, can be NULL */
        PyObject *module_search_path;  /* sys.path list */
    } _PyMainInterpreterConfig;


_PyMain
=======

To split the giant ``Py_Main()`` function into subfunctions, I started
to move variables into a new ``_PyMain`` structure::

    /* Structure used by Py_Main() to pass data to subfunctions */
    typedef struct {
        int argc;
        int use_bytes_argv;
        char **bytes_argv;
        wchar_t **wchar_argv;

        /* Exit status or "exit code": result of pymain_main() */
        int status;
        /* Error message if a function failed */
        _PyInitError err;

        ...
    } _PyMain;

I knew that it was ugly, but it was a simple way to refactor the code.

At the beginning, some options were stored in ``_PyMain`` and some
others in ``_PyCoreConfig`` as a transition period, to be able to
rework the code incrementally. They are some very special and complex
options.


Test suite
==========

When Python 3.7.0 has been released, we got multiple bug reports about
regressions that I introduced. I felt ashame but there was basically
no test...

I decided to start writing some basic tests. At the beginning, I only
tested a few ``_PyCoreConfig`` fields. I tested the different ways
to configuration Python:

* "Legacy" ``Py_Initialize()`` function
* Global configuration variables
* Environment variables
* The new private ``_PyCoreConfig`` API

I decided to not test the "Path Configuration" which is the most complex
part of the Python configuration. Untested options:

* Global configuration variable: ``Py_HasFileSystemDefaultEncoding``
* Core config: ``dll_path``, ``executable``, ``module_search_paths``
* Main config: ``module_search_path``


Preinitialization: first failed attempt
=======================================

First failed attempt:

2018-11-16: https://bugs.python.org/issue35266
Add _PyPreConfig and rework _PyCoreConfig and _PyMainInterpreterConfig

    When I looked again at this issue, I'm not sure how what should be
    done, what is the proper design, what should stay after Python
    initialization, etc. I prefer to abandon this change and maybe retry
    to write it later.

    I have a more advanced version in this branch of my fork:
    https://github.com/vstinner/cpython/commits/pre_config_next

Abandonned idea:

    I created bpo-35265 "Internal C API: pass the memory allocator in a
    context" to pass a "context" to a lot of functions, context which
    contains the memory allocator but can contain more things later.


Memory allocator, context, different structures for configuration...
it's really not an easy topic :-( There are so many constraints put into
a single API!

The conservation option at this point is to keep the API private.



Preinitialization: second attempt
=================================

https://bugs.python.org/issue36142#msg336791

I added a _PyCoreConfig structure to Python 3.7 which contains almost
all parameters used to configure Python. Problems: _PyCoreConfig uses
bytes and Unicode strings (char* and wchar_t*) whereas it is also used
to setup the memory allocator and (filesystem, locale and stdio)
encodings.

I propose to add a new _PyPreConfig which is the "strict minimum"
configuration to setup encodings and the memory allocator. In practice,
it also contains parameters which directly or indirectly impacts the
allocator and encodings. For example, isolated impacts use_environment
which impacts the allocator (PYTHONMALLOC environment variable). Another
example: dev_mode=1 sets the allocator to "debug".

The command line arguments are now parsed twice. _PyPreConfig only
parses a few parameters like -E, -I and -X. A temporary _PyPreCmdline is
used to store command line arguments like -X options.

I moved structures closer to where they are used. "Global" _PyMain
structure has been removed. _PyCmdline now lives way shorter than
previously and is moved from main.c to coreconfig.c. The idea is to
better control when and how memory is allocated.


_Py_PreInitialize(): step 3
===========================

https://github.com/python/cpython/commit/f29084d611a6ca504c99a0967371374febf0ccc3

bpo-36301: Add _PyRuntimeState.preconfig (GH-12506)

bpo-36301: Remove _PyCoreConfig.preconfig (GH-12546)

    Note for myself: PYTHONDEVMODE=1, PreConfig isolated=1, CoreConfig
    isolated=0: is the dev mode enabled or not? IMHO it should not.
    Maybe add a specific unit test?


C types vs PyObject*
====================

https://bugs.python.org/issue36142#msg336989

Agreed - I think the biggest thing we learned from the
pre-implementation in Python 3.7 is that the "Let's move as much config
as we can to Python C API data types" fell down in a couple of areas:

1. The embedding application is likely to speak char* and/or wchar_*
natively, not PyObject*, and this applies even for CPython's own current
`Py_Main` implementation.

2. There's some core system libc interaction scaffolding that we need in
place first, giving 3 phases, not two:

(...)

Second Py_Main() rework
=======================

https://github.com/python/cpython/commit/dfe884759d1f4441c889695f8985bc9feb9f37eb
https://github.com/python/cpython/commit/95e2cbf32f8156c239b27dae558ba058d0f2d496

* Move code parsing command line arguments from main.c to coreconfig.c
* Modify _PyInitError to return an "exitcode" rather than an error
* Remove _PyMain.err (_PyInitError) and modify functions to return
  _PyInitError instead
* Remove _PyMain structure: add run_command, run_module, run_filename
  and skip_source_first_line from _PyMain to _PyCoreConfig. This change
  doesn't fit well with PEP 432 design, but it was more a practical
  compromise to be able to move on.


Prepare implementation for the PEP
==================================

Preinitialization
-----------------

There were a few major pain points to solve before being to propose
a public API. One of them was the blurry "preinitialization".

There was also the question of enabling or not PEP 538 and PEP 540
(UTF-8 Mode) when the legacy Py_Initialize() function is used.

https://bugs.python.org/issue36202#msg337915
    Calling Py_DecodeLocale() before _PyPreConfig_Write() can produce mojibake

https://bugs.python.org/issue36301
    Add _Py_PreInitialize() function

XXX INADA-san started a thread
XXX Steve Dower XXX

First implementation: _PyConfig.preconfig. isolated and use_environment
moved to _PyPreConfig to avoid redundancy.

* _PyCoreConfig_Read() calls _PyPreConfig_Read()

I moved more and more fields to _PyPreConfig:

* utf8_mode, coerce_c_locale, coerce_c_locale_warn, legacy_windows_stdio
* allocator, dev_mode

_PyPreConfig also parses command line arguments: -E and -I.

_PyCoreConfig_Read gets a second parameter::

    PyAPI_FUNC(_PyInitError) _PyCoreConfig_Read(_PyCoreConfig *config,
        const _PyPreConfig *preconfig);

_PyPreConfig_Write() sets the memory allocator.

    "_PyPreConfig_Write() now reallocates the pre-configuration with the
    new memory allocator."

_PyPreConfig_Read() now sets temporarily LC_CTYPE to the user preferred
locale, as _PyPreConfig_Write() will do permanentely.

The pre-configuration is designed to be as small as possible, it
configures:

* memory allocators
* LC_CTYPE locale and set the UTF-8 mode

The _PyPreConfig structure has 8 fields:

* allocator
* coerce_c_locale
* coerce_c_locale_warn
* dev_mode
* isolated
* (Windows only) legacy_windows_fs_encoding
* use_environment
* utf8_mode

I had to include fields which have an impact on other fields. Examples:

* dev_mode=1 sets allocator to "default";
* isolated=1 sets use_environment to 0;
* legacy_windows_fs_encoding=1 sets utf8_mode to 0.

I removed the last side effects of _PyCoreConfig_Read(): it no longer
modify the locale. Same for the new _PyPreConfig_Read(): zero size
effect.

The new _PyPreConfig_Write() and _PyCoreConfig_Write() are now
responsible to write the new configurations.

Mojibake
--------

I created bpo-36202: "Calling Py_DecodeLocale() before _PyPreConfig_Write() can produce mojibake".

Step 4
-------

bpo-36763: Fix Py_SetStandardStreamEncoding() (GH-13028)
bpo-36763: Add _PyCoreConfig_SetArgv() (GH-13030)
bpo-36763: Rework _PyInitError API (GH-13031)
bpo-36763: Add _PyCoreConfig_SetString() (GH-13035)
bpo-36763: Make _PyCoreConfig.check_hash_pycs_mode public (GH-13052)
bpo-36763: Add _PyCoreConfig._config_version (GH-13065)
bpo-36763: _PyCoreConfig_SetPyArgv() preinitializes Python (GH-13037)
bpo-36763: Remove _PyCoreConfig._init_main (GH-13066)

I updated my PEP 587:
[Python-Dev] RFC: PEP 587 "Python Initialization Configuration": 2nd version
https://mail.python.org/pipermail/python-dev/2019-May/157290.html

bpo-36763: Add _PyCoreConfig.parse_argv (GH-13361)
bpo-36763: Add _PyCoreConfig.configure_c_stdio (GH-13363)

    XXX tweet + email to capi-sig

bpo-36763: Remove _PyCoreConfig.program (GH-13373)
bpo-36763: _Py_RunMain() doesn't call Py_Exit() anymore (GH-13390)
bpo-36763: Remove _PyCoreConfig.dll_path (GH-13402)
bpo-36763: Fix Python preinitialization (GH-13432)

    * Add _PyPreConfig.parse_argv
    * Add _PyCoreConfig._config_init field and _PyCoreConfigInitEnum enum
      type

bpo-36763: Add _PyPreConfig._config_init (GH-13481)

wchar_t* only
-------------

https://bugs.python.org/issue36775

bpo-36775: Add _PyUnicode_InitEncodings() (GH-13057)
bpo-36775: _PyCoreConfig only uses wchar_t* (GH-13062)

    _PyCoreConfig: Change filesystem_encoding, filesystem_errors,
    stdio_encoding and stdio_errors fields type from char* to wchar_t*.


Implement the PEP
=================

https://github.com/python/cpython/commit/331a6a56e9a9c72f3e4605987fabdaec72677702

    XXX diffstat

February 2019
=============

INADA Naoki: Adding char* based APIs for Unix
https://discuss.python.org/t/adding-char-based-apis-for-unix/916

Py_Main() expects argv as an array of wchar_t* strings.

Python has several high-level C API which accept or return wchar_t* string.
It is OK on Windows, but I don’t want to use wchar_t* on Unix.

Victor added ``_Py_UnixMain(int argc, char **argv)`` which is char* version
of ``Py_Main(int argc, wchar_t **argv)``.  Can we make it public API? Is the
name looks good?

And there are some other wchar_t* APIs. Can we add char* version for
them? ::

    Doc/c-api/sys.rst
    218:.. c:function:: void PySys_AddWarnOption(const wchar_t *s)
    233:.. c:function:: void PySys_SetPath(const wchar_t *path)
    275:.. c:function:: void PySys_AddXOption(const wchar_t *s)

    Doc/c-api/init.rst
    344:.. c:function:: void Py_SetProgramName(const wchar_t *name)
    375:.. c:function:: wchar_t* Py_GetPrefix()
    388:.. c:function:: wchar_t* Py_GetExecPrefix()
    423:.. c:function:: wchar_t* Py_GetProgramFullPath()
    436:.. c:function:: wchar_t* Py_GetPath()
    456:.. c:function::  void Py_SetPath(const wchar_t *)
    551:.. c:function:: void PySys_SetArgvEx(int argc, wchar_t **argv, int updatepath)
    599:.. c:function:: void PySys_SetArgv(int argc, wchar_t **argv)
    611:.. c:function:: void Py_SetPythonHome(const wchar_t *home)

Make pyvenv style virtual environments easier to configure when embedding Python
https://bugs.python.org/issue22213

2014-08-17: Graham Dumpleton

2019-02-06: Nick Coghlan

Similar issue: https://bugs.python.org/issue35706


Well, it's a strange story. At the beginning, I had a very simple use case... it took me more or less one year to implement it :-) My use case was to add... a new -X utf8 command line option:

* parsing the command line requires to decode bytes using an encoding
* the encoding depends on the locale, environment variable and options on the command line
* environment variables depend on the command line (-E option)

If the utf8 mode is enabled (PEP 540), the encoding must be set to UTF-8, all configuration must be removed and the whole configuration (env vars, cmdline, etc.) must be read again from scratch :-)

To be able to do that, I had to collect *every single* thing which has an impact on the Python initialization: all things that I moved into _PyCoreConfig.

... but I didn't want to break the backward compatibility, so I had to keep support for Py_xxx global configuration variables... and also the few initialization functions like Py_SetPath() or Py_SetStandardStreamEncoding().

Later it becomes very dark, my goal became very unclear and I looked at the PEP 432 :-)


If a _PyCoreConfig field is set: it has the priority over any other way to initialize the field. _PyCoreConfig has the highest prioririty.

For example, _PyCoreConfig allows to completely ignore the code which computes sys.path (and related variables) by setting directly the "path configuration":

Nick:
https://bugs.python.org/issue22213#msg335688

    Steve, you're describing the goals of PEP 432 - design the desired
    API, then write the code to implement it. So while Victor's goal was
    specifically to get PEP 540 implemented, mine was just to make it so
    working on the startup sequence was less awful (and in particular,
    to make it possible to rewrite getpath.c in Python at some point).

    Unfortunately, it turns out that redesigning a
    going-on-thirty-year-old startup sequence takes a while, as we first
    have to discover what all the global settings actually *are* :)

INADA-san: "Thank you for adding bytes based APIs, and congrats for your
PEP 587. It looks very tough job."


Updating the PEP 432?
=====================

> I like where you're going with this, but would be willing to write an update to PEP 432 to sketch out in advance what you now think the end state is going to look like?

Sadly, I'm unable to design in advance what will be the final state.

Python initialization is a giant beast, full of traps, with many practical issues.

I'm moving slowly, step by step.

https://bugs.python.org/issue35266#msg330069


Deprecate calling Py_Main() after Py_Initialize()? Add Py_InitializeFromArgv()?
===============================================================================

https://bugs.python.org/issue36204

See bpo-34008: "Do we support calling Py_Main() after Py_Initialize()?".
I had to fix a regression in Python 3.7 to fix the application called
"fontforge".

Pseudo-code of fontforge::

    Py_Initialize()
    for file in files:
       PyRun_SimpleFileEx(file)
    Py_Main(arg, argv)
    Py_Finalize()

PySys_SetArgvEx() can be called before Py_Initialize(), but arguments
passed to this function are not parsed.


PEP 540 UTF-8 Mode
==================

November 2017, I created bpo-32030 to split the big Py_Main() function into smaller subfunctions. My motivation was to be able to properly implement my PEP 540.

It will take me 3 months of work and 45 commits to completely cleanup Py_Main() and put almost all Python configuration options into the private C _PyCoreConfig structure.

December 2017, bpo-32030, thanks to the Py_Main() refactoring, I was able to finish the implementation of my PEP.

I pushed my commit 9454060e:

    Py_Main() re-reads config if encoding changes

    If the encoding change (C locale coerced or UTF-8 Mode changed), Py_Main() now reads again the configuration with the new encoding.

If the encoding changed after reading the Python configuration, cleanup the configuration and read again the configuration with the new encoding. The key feature here allowed by the refactoring is to be able to cleanup properly all the configuration.



PRs rewritten at least 6 times from scratch
===========================================

When I started to change the implementation, it was common that I had to
make changes which I didn't expect, then more changes, then even more
changes. At the end, the overall change was giant.

In this case, I tried to rewrite the change from scratch step by step.
By merging small "atomic" changes. I proposed a PR. And merged the PR
before writing the second change. GitHub doesn't support a serie of
multiple PRs, and conflicts were too likely anyway.

Sometimes, I failed to find the right approach to write small changes.
I had to iterate up to 6 times over a few days to find the real starting
point and be able to start pushing public changes one by one.

Most changes had to modify at least 3 files because the implementation
is scattered into multiple files. Many simple changes had to modify 10
files or more, to update an API for example.


PEP 587 History
===============

Version 1 (March 28, 2019)
--------------------------

I designed the first version of the PEP to minimize the size of the API:
provide the bare minimum just to configure Python.

"Since Steve Dower asked me to write a formal PEP for my proposal of a
new C API to initialize Python, here you have!"

https://mail.python.org/archives/list/python-dev@python.org/thread/C6JQ6NHTB3BP6RWD4PA3FSL3T46N3FBG/

Version 2 (May 2, 2019)
-----------------------

The bare minimum was too minimum. I added ``PyConfig_Read()`` which
is a key feature to override the configure read by Python.

Version 3 (May 15, 2019)
------------------------

Strings are now in Unicode by default (``wchar_t**``), bytes strings
become second class citizen.

Version 4 (May 20, 2019)
------------------------

Steve Dower and me had a strong disagreement on the default
configuration. So I changed my PEP to add not one but two default
configurations!

* "Python Configuration" behaves as the regular Python
* "Isolated Configuration" ignores the environment, designed to embed
  Python into an application

I have been asked to get ride of macros, since they don't work well with
programming languages other than C. Or even in C, it's not convenient.
For example, ``PyConfig_INIT`` macro for static initialization has been
replaced with ``PyConfig_InitIsolatedConfig()`` and
``PyConfig_InitPythonConfig()`` functions.

I also removed the special case of PyConfig which uses only static
data, no dynamically allocated memory.

Version 5 (May 24, 2019)
------------------------

Add "Multi-Phase Initialization Private Provisional API".

PEP Accepted!
-------------

Thomas Wouters was selected as the BDFL-delegate for my PEP. He didn't
like PyInitError name. We agreed on the "PyStatus" name. He didn't like
PyStatus_Exception() name, but we failed to find a better name.

`Thomas Wouters accepted my PEP 587 on May 26, 2019
<https://mail.python.org/pipermail/python-dev/2019-May/157721.html>`_.

Enhancements of the PEP discussion
----------------------------------

One great enhancement was that PyPreConfig stopped to use dynamically
allocated strings, only integers. The problem is that PyPreConfig is
used to setup the memory allocators. Having to allocate memory to
initialize the memory allocator caused me a lot of troubles in the
implementation. Avoiding strings made the code way simpler!

I also added Py_RunMain() which is a nice enhancement.

I explained how PyImport_FrozenModules, PyImport_AppendInittab() and
PyImport_ExtendInittab() interact with the new API. I didn't know them
before I wrote the PEP :-)

The ratione is now quite good to list problems solved by the new API.

Nick Coghlan helped me to clarify the interactions with his PEP 432.


Updating the implementation while updating the PEP
==================================================

The first versions of the PEP had some "suboptimum" APIs because of
implementation issues.

One major pain point was that almost all strings of PyConfig were
Unicode strings (``wchar_t*``) except of ``filesystem_encoding``
and ``filesystem_errors``. Not only the implementation used bytes
strings internally, but XXX

XXX

_PyMainInterpreterConfig removed
================================

While I like the idea of the PEP 432, the implementation was far from
being usable. The expected API itself wasn't well defined. I decided
to remove _PyMainInterpreterConfig structure until we reopen the
discussion of "Multi-Phase Initialization".
