File system and locale encodings
++++++++++++++++++++++++++++++++

:date: 2018-03-14 15:00
:tags: cpython
:category: python
:slug: python-filesystem-locale-encoding
:authors: Victor Stinner

This article describes changes during Python 3.2 development, so before Python
3.2 final.

Previous article: `Python 3.0 listdir() bug on undecodable filenames
<{filename}/python30_listdir.rst>`_.

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

2010-05-05, `MaL proposed PYTHONFSENCODING
<https://bugs.python.org/issue8610#msg105010>`_::

    I think we should also add a new environment variable to override
    the automatic determination of the file system encoding, much like
    what we have for the I/O encoding:

    PYTHONFSENCODING: Encoding[:errors] used for file system.

Change::

    commit b744ba1d14c5487576c95d0311e357b707600b47
    Author: Victor Stinner <victor.stinner@haypocalc.com>
    Date:   Sat May 15 12:27:16 2010 +0000

        Issue #8610: Load file system codec at startup, and display a fatal error on
        failure. Set the file system encoding to utf-8 (instead of None) if getting
        the locale encoding failed, or if nl_langinfo(CODESET) function is missing.

2010-05-05, `bpo-8622 <https://bugs.python.org/issue8622>`__: As a follow-up of
`bpo-8610 <https://bugs.python.org/issue8610>`__, **Marc-Andre Lemburg**
proposed a way to override the automatic detection of the file system
encoding::

    PYTHONFSENCODING: Encoding[:errors] used for file system.

initfsencoding()
================

bpo-8965:

Change::

    commit 7f84ab59523ab7f7d7d288551a459e24718b8c7d
    Author: Victor Stinner <victor.stinner@haypocalc.com>
    Date:   Fri Jun 11 00:36:33 2010 +0000

        Issue #8965: initfsencoding() doesn't change the encoding on Mac OS X

        File system encoding have to be hardcoded to "utf-8" on Mac OS X. r81190
        introduced a regression: the encoding was changed depending on the locale.


Remove sys.setfilesystemencoding()
==================================

At 2010-08-18, I opened `bpo-9632 <https://bugs.python.org/issue9632>`__ to
remove sys.setfilesystemencoding(), `commit 5b519e02
<https://github.com/python/cpython/commit/5b519e02016ea3a51f784dee70eead3be4ab1aff>`__:

    Issue #9632: Remove sys.setfilesystemencoding() function: use
    PYTHONFSENCODING environment variable to set the filesystem encoding at
    Python startup.  sys.setfilesystemencoding() creates inconsistencies
    because it is unable to reencode all filenames in all objects.

The ``sys.setfilesystemencoding()`` function was removed because it had a
flawed design.


Support locale encodings different than UTF-8
=============================================

https://bugs.python.org/issue8611
Python3 doesn't support locale different than utf8 and an non-ASCII path (POSIX)

Quote:

    Python3 is unable to start (bootstrap failure) on a POSIX system if the
    locale encoding is different than utf8 and the Python path (standard
    library path where the encoding module is stored) contains a non-ASCII
    character. (Windows and Mac OS X are not affected by this issue because the
    file system encoding is hardcoded.)

At 2010-10-17, I wrote:

    Status of this issue, 5 months later: most tests pass except test_gc
    test_gdb test_runpy test_sys test_wsgiref test_zipimport. Said differently,
    95% of the task (or more?) is done. It's possible to run Python installed
    in a non-ascii directory with any locale (I tested ascii, iso-8859-1 and
    utf-8).

Add PYTHONFSENCODING environment variable
=========================================

`bpo-8622 <https://bugs.python.org/issue8622>`__: Add PYTHONFSENCODING environment variable

Change::

    commit 94908bbc1503df830d1d615e7b57744ae1b41079
    Author: Victor Stinner <victor.stinner@haypocalc.com>
    Date:   Wed Aug 18 21:23:25 2010 +0000

        Issue #8622: Add PYTHONFSENCODING environment variable to override the
        filesystem encoding.

        initfsencoding() displays also a better error message if get_codeset() failed.


Redecode filenames when setting the filesystem encoding
=======================================================

At that time, I already noticed the most complex part of this option: the need
to "reencode filenames when setting the filesystem encoding".

`bpo-9630 <https://bugs.python.org/issue9630>`__:

    I wrote a patch to reencode filenames of all module and code objects in
    initfsencoding() when the locale encoding is known.

Amaury Forgeot d'Arc::

    > Python is installed in a directory called b'py3k\xc3\xa9'
    > and your locale is C

    Do we really want to support this kind of configuration?

Comment::

    > Why is this needed ?

    Py_FilesystemDefaultEncoding is changed too late. Some modules are already
    loaded, sys.executable is already set, etc. Py_FilesystemDefaultEncoding is
    changed but modules filenames are decoded with utf-8 and should be
    "redecoded".

Another option::

    Another solution would be to unload all modules, clear all caches,
    delete all code objects, etc. after setting the filesystem encoding. But
    I think that it is inefficient and nobody wants a slower Python startup.

"I commited redecode_modules_path-4.patch as r85115 in Python 3.2." ::

    commit c39211f51e377919952b139c46e295800cbc2a8d
    Author: Victor Stinner <victor.stinner@haypocalc.com>
    Date:   Wed Sep 29 16:35:47 2010 +0000

        Issue #9630: Redecode filenames when setting the filesystem encoding

        Redecode the filenames of:

         - all modules: __file__ and __path__ attributes
         - all code objects: co_filename attribute
         - sys.path
         - sys.meta_path
         - sys.executable
         - sys.path_importer_cache (keys)

        Keep weak references to all code objects until initfsencoding() is called, to
        be able to redecode co_filename attribute of all code objects.


Issues when the filesystem encoding is different than the locale encoding
=========================================================================

[Python-Dev] Inconsistencies if locale and filesystem encodings are different
https://mail.python.org/pipermail/python-dev/2010-October/104509.html

"G_FILENAME_ENCODING env var to guide GTK2/GLib"

Use locale encoding and remove redecode_filenames()::

    commit f3170ccef8809e4a3f82fe9f82dc7a4a486c28c1
    Author: Victor Stinner <victor.stinner@haypocalc.com>
    Date:   Fri Oct 15 12:04:23 2010 +0000

        Use locale encoding if Py_FileSystemDefaultEncoding is not set

         * PyUnicode_EncodeFSDefault(), PyUnicode_DecodeFSDefaultAndSize() and
           PyUnicode_DecodeFSDefault() use the locale encoding instead of UTF-8 if
           Py_FileSystemDefaultEncoding is NULL
         * redecode_filenames() functions and _Py_code_object_list (issue #9630)
           are no more needed: remove them


