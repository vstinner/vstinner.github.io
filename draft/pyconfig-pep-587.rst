+++++++++++++++++
PyConfig: PEP 587
+++++++++++++++++

Changing the Python default encoding to UTF-8 is an old idea. After I
saw enough bug reports, I decided to implement it as the PEP 540 in
Python 3.7: ``python3.7 -X utf8`` ignores your locale and forces the
usage of the UTF-8 encoding in Python.

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


PEP 587
=======

* Thomas Wouters accepted my PEP 587!
  https://mail.python.org/pipermail/python-dev/2019-May/157721.html
  5th PEP version
