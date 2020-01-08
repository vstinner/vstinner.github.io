++++++++++++++++++++++++++++++++++
Early work on Python configuration
++++++++++++++++++++++++++++++++++

:date: 2020-01-08 18:00
:tags: cpython
:category: python
:slug: early-work-python-configuration
:authors: Victor Stinner

Python Configuration
====================

Python is highly configurable but its configuration evolved organically. The
initialization configuration is scattered all around the code using different
ways to set them:

* command line arguments (ex: ``python3 -b``);
* environment variables (ex: ``PYTHONPATH``);
* configuration files (ex: ``pyvenv.cfg`` used by virtual environments);
* global configuration variables of the C API (ex: ``Py_IsolatedFlag``);
* function calls of the C API (ex: ``Py_SetProgramName()``).

2012, PEP 432: Simplifying the CPython startup sequence
========================================================

In December 2012, Nick Coghlan started proposed a new PEP on the python-ideas
list, `PEP 432: Simplifying the CPython startup sequence
<https://mail.python.org/archives/list/python-ideas@python.org/thread/A57LOY7CPBQWE7NLDV3YQTIPN7RVFXFM/#TLFTYGIQXNEGY5YWM4AYSOPYK25QA3EF>`_:

    After helping Brett with the migration to importlib in 3.3, and
    looking at some of the ideas kicking around for additional CPython
    features that would affect the startup sequence, I've come to the
    conclusion that what we have now simply isn't sustainable long term.

    It's already the case that if you use certain options (specifically -W
    or -X), the interpreter will start accessing the C API before it has
    called Py_Initialize(). It's not cool when other people do that (we'd
    never accept code that behaved that way as a valid reproducer for a
    bug report), and it's *definitely* not cool that we're doing it (even
    though we seem to be getting away with it for the moment, and have
    been for a long time).

Christian Heimes commented::


    Hello Nick, we could use the opportunity and move more settings to
    Py_CoreConfig. At the moment several settings are stored in static
    variables:

    Python/pythonrun.c:

    static wchar_t *progname
    static wchar_t *default_home
    static wchar_t env_home[PATH_MAX+1]

One month later, January 2013, Nick posted `Updated `PEP 432 "Restructuring the CPython startup sequence" <https://www.python.org/dev/peps/pep-0432/>`__: Simplifying the
CPython update sequence
<https://mail.python.org/pipermail/python-ideas/2013-January/018511.html>`_:

    The biggest change in the new version is moving from a Python dictionary to
    a **C struct as the storage** for the full low level interpreter
    configuration as Antoine suggested.

Daniel Shahaf asked:

    Quick question, do you plan to **expose the C argv values** as part of this
    work?

Terry Reedy commented:

    IE, **you prefer positive flags**, with some on by default, over having all
    flags indicate a non-default condition. I would too, but I don't hack on
    the C code base. 'dont_write_bytecode' is especially ugly.

2014: new pylifecycle.c file
============================

November 2014, Nick Coghlan started to implement his PEP in `bpo-22869
<https://bugs.python.org/issue22869>`_ with `commit d6009517
<https://github.com/python/cpython/commit/d600951748d7a19cdb3e58a376c51ed804b630e6>`__::

    Issue #22869: Split pythonrun into two modules

    - interpreter startup and shutdown code moved to a new
      pylifecycle.c module
    - Py_OptimizeFlag moved into the new module with the other
      global flags

2017
----

`PEP 432 "Restructuring the CPython startup sequence" <https://www.python.org/dev/peps/pep-0432/>`__: Redesign the interpreter startup sequence
https://bugs.python.org/issue22257
Nick Coghlan
2014-08-23 but first commit at 2017-05-23

referred at:
https://github.com/python/cpython/commit/d7ac06126db86f76ba92cbca4cb702852a321f78
https://bugs.python.org/issue31845

At 2017-05-23, commit c7ec9985bbd added _PyMainInterpreterConfig with 1
field.

At 2017-09-07, `commit 2ebc5ce4 <https://github.com/python/cpython/commit/2ebc5ce42a8a9e047e790aefbf9a94811569b2b6>`__:

* _PyCoreConfig: 5 fields
* _PyMainInterpreterConfig: 1 field

Commits::

    commit 6b4be195cd8868b76eb6fbe166acc39beee8ce36
    Author: Eric Snow <ericsnowcurrently@gmail.com>
    Date:   Mon May 22 21:36:03 2017 -0700

        bpo-22257: Small changes for `PEP 432 "Restructuring the CPython startup sequence" <https://www.python.org/dev/peps/pep-0432/>`__. (#1728)

        `PEP 432 "Restructuring the CPython startup sequence" <https://www.python.org/dev/peps/pep-0432/>`__ specifies a number of large changes to interpreter startup code, including exposing a cleaner C-API. The major changes depend on a number of smaller changes. This patch includes all those smaller changes.

        +typedef struct {
        +    wchar_t *filename;           /* Trailing arg without -c or -m */
        +    wchar_t *command;            /* -c argument */
        +    wchar_t *module;             /* -m argument */
        +    PyObject *warning_options;   /* -W options */
        +    PyObject *extra_options;     /* -X options */
        +    int print_help;              /* -h, -? options */
        +    int print_version;           /* -V option */
        +    int bytes_warning;           /* Py_BytesWarningFlag */
        +    int debug;                   /* Py_DebugFlag */
        +    int inspect;                 /* Py_InspectFlag */
        +    int interactive;             /* Py_InteractiveFlag */
        +    int isolated;                /* Py_IsolatedFlag */
        +    int optimization_level;      /* Py_OptimizeFlag */
        +    int dont_write_bytecode;     /* Py_DontWriteBytecodeFlag */
        +    int no_user_site_directory;  /* Py_NoUserSiteDirectory */
        +    int no_site_import;          /* Py_NoSiteFlag */
        +    int use_unbuffered_io;       /* Py_UnbufferedStdioFlag */
        +    int verbosity;               /* Py_VerboseFlag */
        +    int quiet_flag;              /* Py_QuietFlag */
        +    int skip_first_line;         /* -x option */
        +} _Py_CommandLineDetails;

        _PySys_BeginInit()
        _PySys_EndInit()

    commit 1abcf6700b4da6207fe859de40c6c1bada6b4fec
    Author: Eric Snow <ericsnowcurrently@gmail.com>
    Date:   Tue May 23 21:46:51 2017 -0700

        bpo-22257: Private C-API for core runtime initialization (`PEP 432 "Restructuring the CPython startup sequence" <https://www.python.org/dev/peps/pep-0432/>`__). (#1772)

        (patch by Nick Coghlan)

        +typedef struct {
        +    int ignore_environment;
        +    int use_hash_seed;
        +    unsigned long hash_seed;
        +    int _disable_importlib; /* Needed by freeze_importlib */
        +} _PyCoreConfig;

2017-10-23
PYTHONDONTWRITEBYTECODE and PYTHONOPTIMIZE have no effect
https://bugs.python.org/issue31845
(Python 3.7 regression)

Somehow related, 2017
---------------------

2017-07-05 .. 2017-11-24
Consolidate stateful C globals under a single struct.
https://bugs.python.org/issue30860
Eric Snow

Commit::

    commit 2ebc5ce42a8a9e047e790aefbf9a94811569b2b6 (HEAD)
    Author: Eric Snow <ericsnowcurrently@gmail.com>
    Date:   Thu Sep 7 23:51:28 2017 -0600

        bpo-30860: Consolidate stateful runtime globals. (#3397)

        * group the (stateful) runtime globals into various topical structs
        * consolidate the topical structs under a single top-level _PyRuntimeState struct
        * add a check-c-globals.py script that helps identify runtime globals

        Other globals are excluded (see globals.txt and check-c-globals.py).

        _PyCoreConfig:

        +    char *allocator;


