+++++++++++++++++++++++++++++++++++++++++++++++++
Painful history of the Python filesystem encoding
+++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2018-03-15 17:00
:tags: cpython
:category: python
:slug: painful-history-python-filesystem-encoding
:authors: Victor Stinner

Between Python 3.0 released in 2008 and Python 3.7 scheduled for summer 2018,
the Python filesystem encoding changed many times. **I took at least 10 years
to choose the Python best filesystem encoding.**

At January 2010, I was officially `promoted as a core developer
<https://devguide.python.org/developers/>` by Martin von Loewis. I spent the
whole year to fix dozens of encoding issues during the development Python 3.2,
following my previous work on Unicode starting in 2008.  This article explains
the long discussions which occurred that year to choose the best "filesystem"
encoding for Python on each platform.

**This article is the third in a series of articles telling the history and
rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() bug on undecodable filenames <{filename}/python30_listdir.rst>`_.
* 2. PEP 383
* 3. Painful history of the Python filesystem encoding

Operating system
================

When Python 3.0 was released, it was unclear to Python core developers which
encodings should be used for each kind of data:

* File content: open().read()
* Filenames: os.listdir(), open(), etc.
* Command line arguments: sys.argv and subprocess.Popen arguments
* Environment variables: os.environ
* etc.

In many cases, the UTF-8 encoding was only used accidentally because Python 2
code was modified to use Unicode with the "default encoding" which is UTF-8 in
Python 3. While UTF-8 is a good choice is *most* cases, it is not the best
choice in *all* cases. Python 3.1, Python 3.2 and Python 3.3 will get a lot of
changes to adjust encodings in all corners of the standard library.

The article would be very boring if I start to give the full list of *all*
changes I made to fix encodings. This article is restricted to the main design
changes made between 2008 and 2012 on the filesystem encoding which is one of
the most important encoding in Python 3.

Add sys.setfilesystemencoding()
===============================

`bpo-3187 <https://bugs.python.org/issue3187>`__: In the middle of the
discussion how to fix the ``os.listdir()`` bug, **Martin v.  Löwis** `proposed
a new function to change the filesystem encoding
<https://bugs.python.org/issue3187#msg74080>`_:

    Here is a patch that solves the issue in a different way: it introduces
    sys.setfilesystemencoding. **If applications invoke
    sys.setfilesystemencoding("iso-8859-1"), all file names can be successfully
    converted into a character string.**

The ISO-8859-1 encoding has a very interesting property for bytes: it maps
exactly the ``0x00 - 0xff`` byte range to the U+0000 - U+00ff Unicode range,
the decoder cannot fail::

    $ python3.6 -q
    >>> all(ord((b'%c' % byte).decode('iso-8859-1')) == byte for byte in range(256))
    True
    >>> all(ord(('%c' % char).encode('iso-8859-1')) == char for char in range(256))
    True

Guido van Rossum `commented <https://bugs.python.org/issue3187#msg74173>`__:

    I will check in Victor's changes (with some edits).

    Together this means that the various suggested higher-level solutions
    (like returning path-like objects, or some kind of roudtripping
    almost-but-not-quite-utf-8 encoding) can be implemented in pure Python.

At 2008-10-03, **Martin v. Löwis** pushed his `commit 04dc25c5
<https://github.com/python/cpython/commit/04dc25c53728f5c2fe66d9e66af67da0c9b8959d>`__::

    Issue #3187: Add sys.setfilesystemencoding.

Extract of the new function::

    +int
    +_Py_SetFileSystemEncoding(PyObject *s)
    +{
    +       PyObject *defenc;
            (...)
    +       Py_FileSystemDefaultEncoding = strdup(PyBytes_AsString(defenc));
    +       Py_HasFileSystemDefaultEncoding = 0;
    +       return 0;
    +}

``sys.setfilesystemencoding()`` only sets the ``Py_FileSystemDefaultEncoding``
variable. It doesn't try to change the encoding of existing filenames.

In retrospective, I see this function has asking developers and users to be
smart and choose the encoding themself, since CPython core developers were
unable to agree on which encoding was the good one.

While the ISO-8859-1 encoding trick is tempting, we will see later that
``setfilesystemencoding()`` is broken by design and so cannot be used in
practice.

nl_langinfo(CODESET) missing or fails
=====================================

2010-05-04, `bpo-8610 <https://bugs.python.org/issue8610>`__: Python3/POSIX:
errors if file system encoding is None.

Quote:

    On POSIX (but not on Mac OS X), Python3 calls get_codeset() to get the file
    system encoding. If this function fails, sys.getfilesystemencoding()
    returns None.

    (...)

    We have two choices: raise a fatal error if get_codeset() failed, or
    fallback to utf-8.

First option:

    Here is a patch for the first solution: display a fatal error if we are
    unable to get the locale encoding.

    (...)

    I don't think it's a good idea to display an fatal error at runtime. If
    nl_langinfo(CODESET) is not available, configure should fail or we should
    fallback to an hardcoded encoding (ok but which one?).

Second option:

    Patch for the second solution (fallback to utf-8 on get_codeset() failure)
    (...)

MaL:

    If nl_langinfo(CODESET) fails, Python should assume the default
    locale, which is "C" on POSIX platforms. The "C" locale uses
    ASCII as encoding, so Python should use that as well.

Change::

    commit b744ba1d14c5487576c95d0311e357b707600b47
    Author: Victor Stinner <victor.stinner@haypocalc.com>
    Date:   Sat May 15 12:27:16 2010 +0000

        Issue #8610: Load file system codec at startup, and display a fatal error on
        failure. Set the file system encoding to utf-8 (instead of None) if getting
        the locale encoding failed, or if nl_langinfo(CODESET) function is missing.


Support locale encodings different than UTF-8
=============================================

2010-05-04: `bpo-8611 <https://bugs.python.org/issue8611>`__: Python3 doesn't
support locale different than utf8 and an non-ASCII path (POSIX)

Quote:

    Python3 is unable to start (bootstrap failure) on a POSIX system if the
    locale encoding is different than utf8 and the Python path (standard
    library path where the encoding module is stored) contains a non-ASCII
    character. (Windows and Mac OS X are not affected by this issue because the
    file system encoding is hardcoded.)

For example, `bpo-8242 <https://bugs.python.org/issue8242>`__ "Improve support
of PEP 383 (surrogates) in Python3" meta issue tracked multiple issues:

* `bpo-7606 <https://bugs.python.org/issue7606>`__:
  test_xmlrpc fails with non-ascii path
* `bpo-8092 <https://bugs.python.org/issue8092>`__:
  utf8, backslashreplace and surrogates
* `bpo-8383 <https://bugs.python.org/issue8383>`__:
  pickle is unable to encode unicode surrogates
* `bpo-8390 <https://bugs.python.org/issue8390>`__:
  tarfile: use surrogates for undecode fields
* `bpo-8391 <https://bugs.python.org/issue8391>`__:
  os.execvpe() doesn't support surrogates in env
* `bpo-8393 <https://bugs.python.org/issue8393>`__:
  subprocess: support undecodable current working directory on POSIX OS
* `bpo-8394 <https://bugs.python.org/issue8394>`__:
  ctypes.dlopen() doesn't support surrogates
* `bpo-8412 <https://bugs.python.org/issue8412>`__:
  os.system() doesn't support surrogates nor bytes
* `bpo-8467 <https://bugs.python.org/issue8467>`__:
  subprocess: surrogates of the error message (Python implementation on non-Windows)
* `bpo-8468 <https://bugs.python.org/issue8468>`__:
  bz2: support surrogates in filename, and bytes/bytearray filename
* `bpo-8477 <https://bugs.python.org/issue8477>`__:
  _ssl: support surrogates in filenames, and bytes/bytearray filenames
* `bpo-8485 <https://bugs.python.org/issue8485>`__:
  Don't accept bytearray as filenames, or simplify the API

2010-10-19, five months later, I closed the issue:

    Starting at r85691, the full test suite of Python 3.2 pass with ASCII,
    ISO-8859-1 and UTF-8 locale encodings in a non-ascii directory.
    **The work on this issue is done.**


Add PYTHONFSENCODING environment variable
=========================================

While discussing how to fix `bpo-8610 <https://bugs.python.org/issue8610>`__
"Python3/POSIX: errors if file system encoding is None", I asked what is the
best encoding to use if the operating system fails to report its encoding (if
``nl_langinfo(CODESET)`` fails). At 2010-05-05, **Marc-Andre Lemburg** created
`bpo-8622 <https://bugs.python.org/issue8622>`__:

    As discussed on issue8610, we need a way to override the automatic
    detection of the file system encoding - for much the same reasons we also
    do for the I/O encoding: the detection mechanism isn't fail-safe.

    We should add a new environment variable with the same functionality as
    PYTHONIOENCODING::

        PYTHONFSENCODING: Encoding[:errors] used for file system.

I liked the idea of the variable, so I implemented it. At Aug 18 2010, I pushed
my `commit 94908bbc
<https://github.com/python/cpython/commit/94908bbc1503df830d1d615e7b57744ae1b41079>`__:

    Issue #8622: Add PYTHONFSENCODING environment variable to override the
    filesystem encoding.

    initfsencoding() displays also a better error message if get_codeset()
    failed.


Remove sys.setfilesystemencoding()
==================================

2010-08-18, just after adding PYTHONFSENCODING, I opened `bpo-9632
<https://bugs.python.org/issue9632>`__ to remove the
``sys.setfilesystemencoding()`` function:

    The ``sys.setfilesystemencoding()`` function is dangerous because it
    introduces a lot of inconsistencies: this function is unable to reencode
    all filenames in all objects (eg. Python is unable to find filenames in
    user objects or 3rd party libraries). Eg. if you change the filesystem from
    utf8 to ascii, it will not be possible to use existing non-ascii (unicode)
    filenames: they will raise UnicodeEncodeError.

    As ``sys.setdefaultencoding()`` in Python2, I think that
    sys.setfilesystemencoding() is the root of evil :-) ``PYTHONFSENCODING``
    (issue #8622) is the right solution to set the filesysteme encoding.

**Marc-Andre Lemburg** complained that applications embedding Python may want
to set the encoding used by Python. I proposed to use the ``PYTHONFSENCODING``
environment variable as a workaround, even if it was not the best option.

One month later, I pushed `commit 5b519e02
<https://github.com/python/cpython/commit/5b519e02016ea3a51f784dee70eead3be4ab1aff>`__:

    Issue #9632: Remove sys.setfilesystemencoding() function: use
    PYTHONFSENCODING environment variable to set the filesystem encoding at
    Python startup.  sys.setfilesystemencoding() creates inconsistencies
    because it is unable to reencode all filenames in all objects.


Reencode filenames when setting the filesystem encoding
=======================================================

At 2010-08-17, I created `bpo-9630 <https://bugs.python.org/issue9630>`__:
"Reencode filenames when setting the filesystem encoding".

Since the beginning of 2010, I identified a design flaw in Python
initialization. Python starts by decoding strings from the default encoding
UTF-8. Later, Python reads the locale encoding and loads the Python codec of
this encoding. Then Python starts to use this new encoding. Problem: if the
locale encoding is not UTF-8, encoding strings decoded from UTF-8 to the new
encoding can fail in different ways.

I wrote a patch to "reencode" filenames of all module and code objects in
initfsencoding(), once the locale encoding is known.

When I wrote the patch, I knew that it was an ugly hack and not the proper
design. I proposed to try to avoid importing any Python module before the Python
codec of the locale encoding is loaded, but there is a pratical issue. Python
only has builtin implementation (written in C) of the most popular encodings
like ASCII and UTF-8. Some encodings like ISO-8859-15 are only implemented in
Python.

I also proposed to "unload all modules, clear all caches and delete all code
objects" after setting the filesystem encoding. This option would be very
inefficient and make Python startup slower, whereas Python 3 startup was also
way slower than Python 2 startup.

At Sep 29, 2010, I pushed my `commit c39211f5
<https://github.com/python/cpython/commit/c39211f51e377919952b139c46e295800cbc2a8d>`__:

    Issue #9630: Redecode filenames when setting the filesystem encoding

    Redecode the filenames of:

     - all modules: __file__ and __path__ attributes
     - all code objects: co_filename attribute
     - sys.path
     - sys.meta_path
     - sys.executable
     - sys.path_importer_cache (keys)

    Keep weak references to all code objects until ``initfsencoding()`` is
    called, to be able to redecode co_filename attribute of all code objects.

The list of weak references to code objects really looks like a hack and I
disliked it, but I failed to find a better way to fix Python startup.


PYTHONFSENCODING dead end
=========================

Even with my latest big and ugly "redecode filenames when setting the
filesystem encoding" fix, there were issues when the filesystem encoding was
set to an encoding different than the locale encoding. I identified 4 bugs:

* `bpo-9992 <https://bugs.python.org/issue9992>`__, ``sys.argv``: decoded from the **locale** encoding, but subprocess encodes process arguments to the **filesystem** encoding
* `bpo-10014 <https://bugs.python.org/issue10014>`__, ``sys.path``: decoded from the **locale** encoding, but import encodes paths to the **filesystem** encoding
* `bpo-10039 <https://bugs.python.org/issue10039>`__, the script name: read on the command line
  (ex: ``python script.py``) which is decoded from the locale encoding, whereas
  it is used to fill ``sys.path[0]`` and import encodes paths to the
  **filesystem** encoding.
* `bpo-9988 <https://bugs.python.org/issue9988>`__, ``PYTHONWARNINGS`` environment variable: decoded from the
  **locale** encoding, but ``subprocess`` encodes environment variables to the
  **filesystem** encoding.

At Oct 7 2010, I wrote an email to the python-dev list: `Inconsistencies if
locale and filesystem encodings are different
<https://mail.python.org/pipermail/python-dev/2010-October/104509.html>`_. I proposed two solutions:

* (a) use the same encoding to encode and decode values (it can be different
  for each issue).
* (b) remove PYTHONFSENCODING variable and raise an error if locale and
  filesystem encodings are different (ensure that both encodings are the same).

**Marc-Andre Lemburg** `replied
<https://mail.python.org/pipermail/python-dev/2010-October/104511.html>`__:

    You have to differentiate between the meaning of a file system
    encoding and the locale:

    A file system encoding defines how the applications interact
    with the file system.

    A locale defines how the user expects to interact with the
    application.

    It is well possible that the two are different. Mac OS X is
    just one example. Another common example is having a Unix
    account using the C locale (=ASCII) while working on a UTF-8
    file system.

"G_FILENAME_ENCODING env var to guide GTK2/GLib"


Remove PYTHONFSENCODING
=======================

2010-09-29: I reported `bpo-9992 <https://bugs.python.org/issue9992>`__:
Command-line arguments are not correctly decoded if locale and fileystem
encodings are different.

I proposed a patch to use the **locale** encoding to decode and encode command
line arguments, rather than using the **filesystem** encoding.

**Martin v. Löwis** proposed to use the locale encoding for the command line
arguments, environment variables and all filenames.

Martin v. Löwis
Antoine Pitrou
Marc-Andre Lemburg

https://bugs.python.org/issue9992#msg118352:

    You mean that we should use the following encoding :

    - Mac OS X: UTF-8
    - Windows: unicode for command line/env, mbcs to decode filenames
    - others OSes: locale encoding

    To do that, we have to:

    - "others OSes": delete the ``PYTHONFSENCODING`` variable
    - Mac OS X: use UTF-8 to decode the command line arguments (we can use
      ``PyUnicode_DecodeUTF8()`` + ``PyUnicode_AsWideCharString()`` before
      Python is initialized)


2010-09-29: `bpo-9992 <https://bugs.python.org/issue9992>`__: Command-line
arguments are not correctly decoded if locale and fileystem encodings are
different.

At Oct 13 2010, I pushed `commit 8f6b6b0c
<https://github.com/python/cpython/commit/8f6b6b0cc3febd15e33a96bd31dcb3cbef2ad1ac>`__:

    Issue #9992: Remove PYTHONFSENCODING environment variable.

At Oct 15, 2010, I pushed an important change to **use the locale encoding**
and remove the ugly ``redecode_filenames()`` hack, `commit f3170cce
<https://github.com/python/cpython/commit/f3170ccef8809e4a3f82fe9f82dc7a4a486c28c1>`__:

    Use locale encoding if Py_FileSystemDefaultEncoding is not set

    * PyUnicode_EncodeFSDefault(), PyUnicode_DecodeFSDefaultAndSize() and
      PyUnicode_DecodeFSDefault() use the locale encoding instead of UTF-8 if
      Py_FileSystemDefaultEncoding is NULL
    * redecode_filenames() functions and _Py_code_object_list (issue #9630)
      are no more needed: remove them

Python 3.2: February 2011
=========================

February 2011: Python 3.2.0 released.

Python 3.3: September 2012
==========================

Python 3.3: September 2012

Lying FreeBSD: force ASCII encoding
===================================

Fixed in Python 3.3, fix backported to Python 3.2.

2012-11-11, `bpo-16455 <https://bugs.python.org/issue16455>`__: Decode command
line arguments from ASCII on FreeBSD and Solaris if the locale is C.

At Dec 4 2012, I pushed the `commit d45c7f8d <https://github.com/python/cpython/commit/d45c7f8d74d30de0a558b10e04541b861428b7c1>`__:

    Issue #16455: On FreeBSD and Solaris, if the locale is C, the
    ASCII/surrogateescape codec is now used, instead of the locale encoding, to
    decode the command line arguments. This change fixes inconsistencies with
    os.fsencode() and os.fsdecode() because these operating systems announces
    an ASCII locale encoding, whereas the ISO-8859-1 encoding is used in
    practice.

Full comment::

    /* Workaround FreeBSD and OpenIndiana locale encoding issue with the C locale.
       On these operating systems, nl_langinfo(CODESET) announces an alias of the
       ASCII encoding, whereas mbstowcs() and wcstombs() functions use the
       ISO-8859-1 encoding. The problem is that os.fsencode() and os.fsdecode() use
       locale.getpreferredencoding() codec. For example, if command line arguments
       are decoded by mbstowcs() and encoded back by os.fsencode(), we get a
       UnicodeEncodeError instead of retrieving the original byte string.

       The workaround is enabled if setlocale(LC_CTYPE, NULL) returns "C",
       nl_langinfo(CODESET) announces "ascii" (or an alias to ASCII), and at least
       one byte in range 0x80-0xff can be decoded from the locale encoding. The
       workaround is also enabled on error, for example if getting the locale
       failed.

       Values of locale_is_ascii:

           1: the workaround is used: _Py_wchar2char() uses
              encode_ascii_surrogateescape() and _Py_char2wchar() uses
              decode_ascii_surrogateescape()
           0: the workaround is not used: _Py_wchar2char() uses wcstombs() and
              _Py_char2wchar() uses mbstowcs()
          -1: unknown, need to call check_force_ascii() to get the value
    */
    static int force_ascii = -1;

Core of the check::

    for (i=0x80; i<0xff; i++) {
        unsigned char ch;
        wchar_t wch;
        size_t res;

        ch = (unsigned char)i;
        res = mbstowcs(&wch, (char*)&ch, 1);
        if (res != (size_t)-1) {
            /* decoding a non-ASCII character from the locale encoding succeed:
               the locale encoding is not ASCII, force ASCII */
            return 1;
        }
    }


Python 3.4: March 2014
======================

Python 3.4: March 2014.

Summary
=======

Filesystem encoding
-------------------

Python filesystem encoding:

* ANSI code page on Windows
* UTF-8 on macOS
* UTF-8 if nl_langinfo(CODESET) is not available
* locale encoding otherwise.

``initfsencoding()`` fails with a fatal error on nl_langinfo(CODESET) failure,
importing the Python codec failure or memory allocatore failure.

Command line arguments
----------------------

``main()`` decodecs ``int argc, char **argv`` from the locale encoding using ``_Py_char2wchar()``.

``_Py_char2wchar()``:

* Decode from UTF-8/surrogateescape on macOS
* Decode from ASCII/surrogateescape if nl_langinfo(CODESET) announces an alias
  of the ASCII encoding, whereas mbstowcs() and wcstombs() functions use the
  ISO-8859-1 encoding.
* Decode from the locale encoding using surrogateescape otherwise.

On Windows, ``wmain()`` is used instead of ``main()`` and command line
arguments are directly passed as Unicode::

    #ifdef MS_WINDOWS
    int
    wmain(int argc, wchar_t **argv)
    {
        return Py_Main(argc, argv);
    }
    #else
    (...)
    #endif


Conclusion
==========

XXX
