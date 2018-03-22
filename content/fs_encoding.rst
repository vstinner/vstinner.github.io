+++++++++++++++++++++++++++++++++++++++++++++++++++++
Python 3.2 Painful History of the Filesystem Encoding
+++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2018-03-15 23:00
:tags: cpython
:category: python
:slug: painful-history-python-filesystem-encoding
:authors: Victor Stinner

Between Python 3.0 released in 2008 and Python 3.4 released in 2014, the Python
filesystem encoding changed multiple times. **It took 6 years to choose the best
Python filesystem encoding on each platform.**

**I have been officially promoted as a core developer** in January 2010 by
**Martin von Loewis**. I spent the whole year of 2010 to fix dozens of encoding
issues during the development of Python 3.2, following my Unicode work started
in 2008.

This article is focused on the long discussions to choose the best Python
filesystem encoding on each platform in 2010 for Python 3.2.

**This article is the third in a series of articles telling the history and
rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.6 now uses UTF-8 on Windows <{filename}/windows_utf8.rst>`_

.. image:: {filename}/images/maze.jpg
   :alt: Maze
   :target: https://commons.wikimedia.org/wiki/File:Longleat-maze.jpg

Python 3.0 loves UTF-8
======================

When Python 3.0 was released, it was unclear which encodings should be used
for:

* File content: ``open().read()``
* Filenames: ``os.listdir()``, ``open()``, etc.
* Command line arguments: ``sys.argv`` and ``subprocess.Popen`` arguments
* Environment variables: ``os.environ``
* etc.

Python 3.0 was forked from Python 2.6 and functions were modified to use
Unicode. Many Python 3 functions only used UTF-8 because the implementation
were modified to use the default encoding which is UTF-8: it was not a
deliberate choice.

**While UTF-8 is a good choice in most cases, it is not the best choice in
all cases.** Almost everything worked well in Python 3.0 when all data used
UTF-8, but Python 3.0 failed badly if the locale encoding was not UTF-8.

Python 3.1, 3.2 and 3.3 will get a lot of changes to adjust encodings in all
corners of the standard library.

Python 3.1 got the ``surrogateescape`` error handler (PEP 383) which reduced
Unicode errors: read my previous article `Python 3.1 surrogateescape error
handler (PEP 383) <{filename}/pep383.rst>`_.

Add sys.setfilesystemencoding()
===============================

September 2008, `bpo-3187 <https://bugs.python.org/issue3187>`__: To fix
``os.listdir(str)`` to support undecodable filenames, **Martin v.  Löwis**
`proposed a new function to change the filesystem encoding
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

    Together this means that the various **suggested higher-level solutions**
    (like returning path-like objects, or some kind of roudtripping
    almost-but-not-quite-utf-8 encoding) **can be implemented in pure Python**.

October 2008, **Martin v. Löwis** pushed the `commit 04dc25c5
<https://github.com/python/cpython/commit/04dc25c53728f5c2fe66d9e66af67da0c9b8959d>`__::

    Issue #3187: Add sys.setfilesystemencoding.

Python 3.0 will be the first major release with this function.

In retrospective, I see this function as asking developers and users to be
smart and choose the encoding themself.

While the ISO-8859-1 encoding trick is tempting, we will see later that
``setfilesystemencoding()`` is broken by design and so cannot be used in
practice.

What if getting the locale encoding fails?
==========================================

May 2010, I reported `bpo-8610 <https://bugs.python.org/issue8610>`__,
"Python3/POSIX: errors if file system encoding is None":

    On POSIX (but not on Mac OS X), Python3 calls get_codeset() to get the file
    system encoding. If this function fails, sys.getfilesystemencoding()
    returns None.

I pushed the `commit b744ba1d
<https://github.com/python/cpython/commit/b744ba1d14c5487576c95d0311e357b707600b47>`__:

    Issue #8610: Load file system codec at startup, and **display a fatal error
    on failure**. **Set the file system encoding to utf-8** (instead of None)
    **if getting the locale encoding failed**, or if nl_langinfo(CODESET)
    function is missing.

This change **adds the function initfsencoding()**: logic to initialize the
filesystem encoding.

In practice, Python already used UTF-8 when the filesystem encoding was set to
``None``, but this change makes the default more obvious. The change also makes
the error case better defined: Python exits immediately with a fatal error.


Support locale encodings different than UTF-8
=============================================

My biggest Unicode project in Python 3 was to **fix the encoding** in all
corners of the standard library. This task kept me busy between Python 3.0 and
Python 3.4, at least.

May 2010, I created `bpo-8611 <https://bugs.python.org/issue8611>`__:

    **Python3 is unable to start** (bootstrap failure) on a POSIX system **if
    the locale encoding is different than utf8 and the Python path** (standard
    library path where the encoding module is stored) **contains a non-ASCII
    character**. (Windows and Mac OS X are not affected by this issue because
    the file system encoding is hardcoded.)

For example, `bpo-8242 <https://bugs.python.org/issue8242>`__ "Improve support
of PEP 383 (surrogates) in Python3" is a meta issue tracking multiple issues:

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

I fixed all these issues, and reported most of them.

October 2010, finally, five months later, I succeeded to close the issue!

    Starting at r85691, the full test suite of Python 3.2 pass with ASCII,
    ISO-8859-1 and UTF-8 locale encodings in a non-ascii directory.
    **The work on this issue is done.**

At that time, I didn't know that it will take me a few more years to really fix
**all** encoding issues. For example, it will take me **3 years** to modify the
core of the import machinery to pass filenames as Unicode on Windows: `bpo-3080
<https://bugs.python.org/issue3080>`__ **Full unicode import system**.

Add PYTHONFSENCODING environment variable
=========================================

May 2010, while discussing how to fix `bpo-8610
<https://bugs.python.org/issue8610>`__ "Python3/POSIX: errors if file system
encoding is None", I asked what is the best encoding if reading the locale
encoding fails. As a follow-up, **Marc-Andre Lemburg** created `bpo-8622
<https://bugs.python.org/issue8622>`__:

    As discussed on issue8610, we need a way to **override the automatic
    detection of the file system encoding** - for much the same reasons we also
    do for the I/O encoding: the detection mechanism isn't fail-safe.

    We should add a new environment variable with the same functionality as
    ``PYTHONIOENCODING``::

        PYTHONFSENCODING: Encoding[:errors] used for file system.

I implemented the idea since I liked it. August 2010, I pushed the `commit
94908bbc
<https://github.com/python/cpython/commit/94908bbc1503df830d1d615e7b57744ae1b41079>`__:

    Issue #8622: Add ``PYTHONFSENCODING`` environment variable to override the
    filesystem encoding.

    ``initfsencoding()`` displays also a better error message
    if ``get_codeset()`` failed.


Remove sys.setfilesystemencoding()
==================================

August 2010, just after adding ``PYTHONFSENCODING``, I opened `bpo-9632
<https://bugs.python.org/issue9632>`__ to remove the
``sys.setfilesystemencoding()`` function:

    The ``sys.setfilesystemencoding()`` function is **dangerous** because it
    introduces a lot of inconsistencies: this function is **unable to reencode
    all filenames** of all objects (eg. Python is unable to find filenames in
    user objects or 3rd party libraries). Eg. if you change the filesystem from
    utf8 to ascii, it will not be possible to use existing non-ascii (unicode)
    filenames: they will raise UnicodeEncodeError.

    As ``sys.setdefaultencoding()`` in Python2, I think that
    ``sys.setfilesystemencoding()`` is the **root of evil** :-)
    **PYTHONFSENCODING** (issue #8622) **is the right solution** to set the
    filesysteme encoding.

**Marc-Andre Lemburg** complained that applications embedding Python may want
to set the encoding used by Python. I proposed to use the ``PYTHONFSENCODING``
environment variable as a workaround, even if it was not the best option.

One month later, I pushed the `commit 5b519e02
<https://github.com/python/cpython/commit/5b519e02016ea3a51f784dee70eead3be4ab1aff>`__:

    Issue #9632: Remove ``sys.setfilesystemencoding()`` function: use
    ``PYTHONFSENCODING`` environment variable to set the filesystem encoding at
    Python startup.  ``sys.setfilesystemencoding()`` created inconsistencies
    because it was unable to reencode all filenames of all objects.


Reencode filenames when setting the filesystem encoding
=======================================================

August 2010, I created `bpo-9630 <https://bugs.python.org/issue9630>`__:
"Reencode filenames when setting the filesystem encoding".

Since the beginning of 2010, I identified a design flaw in the Python
initialization. Python starts by **decoding strings from the default encoding
UTF-8**. Later, Python reads the locale encoding and loads the Python codec of
this encoding. Then Python **decodes string from the locale encoding**.
Problem: if the locale encoding is not UTF-8, **encoding strings decoded from
UTF-8 to the locale encoding can fail** in different ways.

I wrote a patch to "reencode" filenames of all module and code objects once the
filesystem encoding is set, in ``initfsencoding()``,

When I wrote the patch, I knew that it was an **ugly hack and not the proper
design**. I proposed to try to avoid importing any Python module before the Python
codec of the locale encoding is loaded, but there was a pratical issue. Python
only has builtin implementation (written in C) of the most popular encodings
like ASCII and UTF-8. Some encodings like ISO-8859-15 are only implemented in
Python.

I also proposed to "unload all modules, clear all caches and delete all code
objects" after setting the filesystem encoding. This option would be very
inefficient and make Python startup slower, whereas Python 3 startup was already
way slower than Python 2 startup.

September 2010, I pushed the `commit c39211f5
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
filesystem encoding" fix, there were **issues when the filesystem encoding was
different than the locale encoding**. I identified 4 bugs:

* `bpo-9992 <https://bugs.python.org/issue9992>`__, ``sys.argv``: decoded from the **locale** encoding, but subprocess encodes process arguments to the **filesystem** encoding
* `bpo-10014 <https://bugs.python.org/issue10014>`__, ``sys.path``: decoded from the **locale** encoding, but import encodes paths to the **filesystem** encoding
* `bpo-10039 <https://bugs.python.org/issue10039>`__, the script name: read on the command line
  (ex: ``python script.py``) which is decoded from the locale encoding, whereas
  it is used to fill ``sys.path[0]`` and import encodes paths to the
  **filesystem** encoding.
* `bpo-9988 <https://bugs.python.org/issue9988>`__, ``PYTHONWARNINGS`` environment variable: decoded from the
  **locale** encoding, but ``subprocess`` encodes environment variables to the
  **filesystem** encoding.

October 2010, I wrote an email to the python-dev list: `Inconsistencies if
locale and filesystem encodings are different
<https://mail.python.org/pipermail/python-dev/2010-October/104509.html>`_. I
proposed two solutions:

* (a) use the same encoding to encode and decode values (it can be different
  for each issue).
* (b) **remove PYTHONFSENCODING variable** and raise an error if locale and
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

This email is a good example of dilemma we had when having to choose **one**
encoding. There is a big temptation to use multiple encodings, but at the end,
**data are not isolated**. A filename can be found in command line arguments
(``python3 script.py file.txt``), in environment variables
(``LOG_FILE=log.txt``), in file content (ex: ``Makefile`` or a configuration
file), etc. Using multiple encodings does not work in practice.

.. image:: {filename}/images/dead_end.jpg
   :alt: Dead end

Remove PYTHONFSENCODING
=======================

September 2010, I reported `bpo-9992 <https://bugs.python.org/issue9992>`__:
Command-line arguments are not correctly decoded if locale and fileystem
encodings are different.

I proposed a patch to use the **locale encoding** to decode and encode command
line arguments, rather than using the **filesystem encoding**.

**Martin v. Löwis** proposed to use the **locale encoding** for the command
line arguments, environment variables and all filenames. `My summary
<https://bugs.python.org/issue9992#msg118352>`_:

    You mean that we should use the following encoding:

    - Mac OS X: UTF-8
    - Windows: unicode for command line/env, mbcs to decode filenames
    - others OSes: **locale encoding**

    To do that, we have to:

    - "others OSes": **delete the PYTHONFSENCODING variable**
    - Mac OS X: use UTF-8 to decode the command line arguments (we can use
      ``PyUnicode_DecodeUTF8()`` + ``PyUnicode_AsWideCharString()`` before
      Python is initialized)

October 2010, I pushed the `commit 8f6b6b0c
<https://github.com/python/cpython/commit/8f6b6b0cc3febd15e33a96bd31dcb3cbef2ad1ac>`__:

    Issue #9992: Remove PYTHONFSENCODING environment variable.

Two days later, I pushed an important change to **use the locale encoding** and
remove the ugly ``redecode_filenames()`` hack, `commit f3170cce
<https://github.com/python/cpython/commit/f3170ccef8809e4a3f82fe9f82dc7a4a486c28c1>`__:

    Use locale encoding if ``Py_FileSystemDefaultEncoding`` is not set

    * ``PyUnicode_EncodeFSDefault()``, ``PyUnicode_DecodeFSDefaultAndSize()``
      and ``PyUnicode_DecodeFSDefault()`` use the locale encoding instead of
      UTF-8 if ``Py_FileSystemDefaultEncoding`` is ``NULL``
    * ``redecode_filenames()`` functions and ``_Py_code_object_list`` (issue #9630)
      are no more needed: remove them

This change has been made possible by enhancements of
``PyUnicode_EncodeFSDefault()`` and ``PyUnicode_DecodeFSDefaultAndSize()``.
Previously, **these functions used UTF-8** before the filesystem was set. With
my change, these functions **now use the C implementation of the locale
encoding**: use ``mbstowcs()`` to decode and ``wcstombs()`` to encode.  In
practice, the code is more complex because Python uses the ``surrogateescape``
error handler.

Using the C implementation of the locale encoding fixed a lot of "bootstrap"
issues of the Python initialization. It works because **the Python codec of the
locale encoding is 100% compatible with the C implementation** of the locale
codec.

Encodings used by Python 3.2
============================

February 2011, Python 3.2 has been released. Summary of the used filesystem
encodings:

* **ANSI code page** on Windows;
* **UTF-8** on macOS;
* **locale encoding** on other platforms.

Note: UTF-8 is used if the ``nl_langinfo(CODESET)`` function is not available.

Force ASCII encoding on FreeBSD and Solaris
===========================================

November 2012, I created `bpo-16455 <https://bugs.python.org/issue16455>`__:

    On FreeBSD and OpenIndiana, ``sys.getfilesystemencoding()`` returns
    ``'ascii'`` when the locale is not set, whereas the locale encoding is
    ``ISO-8859-1`` in practice.

    This inconsistency causes different issues.

December 2012, I pushed the `commit d45c7f8d
<https://github.com/python/cpython/commit/d45c7f8d74d30de0a558b10e04541b861428b7c1>`__:

    Issue #16455: On FreeBSD and Solaris, if the locale is C, the
    ASCII/surrogateescape codec is now used, instead of the locale encoding, to
    decode the command line arguments. This change fixes inconsistencies with
    os.fsencode() and os.fsdecode() because these operating systems announces
    an ASCII locale encoding, whereas the ISO-8859-1 encoding is used in
    practice.

Extract of the main comment:

    Workaround FreeBSD and OpenIndiana locale encoding issue with the C locale.
    On these operating systems, **nl_langinfo(CODESET) announces an alias of
    the ASCII encoding, whereas mbstowcs() and wcstombs() functions use the
    ISO-8859-1 encoding**. The problem is that os.fsencode() and
    ``os.fsdecode()`` use ``locale.getpreferredencoding()`` codec. For example,
    if command line arguments are decoded by ``mbstowcs()`` and encoded back by
    ``os.fsencode()``, we get a ``UnicodeEncodeError`` instead of retrieving
    the original byte string.

    The workaround is enabled if ``setlocale(LC_CTYPE, NULL)`` returns ``"C"``,
    ``nl_langinfo(CODESET)`` announces ``"ascii"`` (or an alias to ASCII), and
    at least one byte in range 0x80-0xff can be decoded from the locale
    encoding. The workaround is also enabled on error, for example if getting
    the locale failed.

Python 3.4 will be the first major release getting fix (March 2014), but I also
backported the change to Python 3.2 and 3.3 branches.


Conclusion
==========

**It took 6 years** to fix Python to use the best Python filesystem encoding.

Python 3.0 mostly uses UTF-8 everywhere, but it was not a deliberate choice and
it caused many issues when the locale encoding was not UTF-8. Python 3.1 got
the ``surrogateescape`` error handler (PEP 383) which reduced Unicode errors.

October 2008, **Martin v. Löwis** added ``sys.setfilesystemencoding()`` to
Python 3.0.

August 2010, I added a new ``PYTHONFSENCODING`` environment variable,
**Marc-Andre Lemburg**'s idea.

September 2010, I removed the ``sys.setfilesystemencoding()`` function because
it creates mojibake by design. I also pushed an ugly change to reencode
filenames to fix many ``PYTHONFSENCODING`` bugs.

October 2010, I fixed all tests when Python lives in a non-ASCII directory:
first milestone of supporting locale encodings different than UTF-8. I also
removed the ``PYTHONFSENCODING`` environment variable after a long discussion.
Moreover, I pushed the most important Python 3.2 change: **Python now uses the
locale encoding as the filesystem encoding**. This change fixed many issues.

December 2012, I forced the filesystem encoding to ASCII on FreeBSD and Solaris
when the announced locale encoding is wrong.

