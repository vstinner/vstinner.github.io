++++++++++++++++++++++++++++++++++++++++++++++
Python 3.0 listdir() and undecodable filenames
++++++++++++++++++++++++++++++++++++++++++++++

:date: 2018-03-09 13:00
:tags: cpython
:category: python
:slug: python-filesystem-encoding-history
:authors: Victor Stinner

In Python 3.0 final, ``os.listdir(str)`` simply ignores undecodable filenames::

    $ python3.0
    Python 3.0 (unknown, Mar 13 2018, 14:24:02)
    [GCC 7.2.1 20170915 (Red Hat 7.2.1-2)] on linux4
    >>> os.mkdir(b'x')
    >>> open(b'x/nonascii\xff', 'w').close()
    >>> os.listdir('x')
    []

You have to use bytes to see all filenames::

    >>> os.listdir(b'x')
    [b'nonascii\xff']

If the locale encoding is ASCII, listdir() simply ignores all non-ASCII
filenames. Hopefully, ``os.listdir()`` accepts ``bytes``, right? In fact, 4
months before 3.0 final, it wasn't the case.

Ignoring undecodable filenames looks very stupid and error-prone: lying on the
real content of a directory cannot be a good idea. Well, there is a long
rationale behind this silly design. Let me tell you this old and long story.

When I first looked at this bug in August 2008, **I didn't know that this kind
of bug will haunt me for the next following 10 years**...

The os.walk() bug
=================

`bpo-3187 <https://bugs.python.org/issue3187>`__, june 2008: **Helmut Jarausch** tested the **first beta release of
Python 3.0** and reported a bug on ``os.walk()``::

    Traceback (most recent call last):
      File "WalkBug.py", line 5, in <module>
        for Dir, SubDirs, Files in os.walk('/home/jarausch') :
      File "/usr/local/lib/python3.0/os.py", line 278, in walk
        for x in walk(path, topdown, onerror, followlinks):
      File "/usr/local/lib/python3.0/os.py", line 268, in walk
        if isdir(join(top, name)):
      File "/usr/local/lib/python3.0/posixpath.py", line 64, in join
        if b.startswith('/'):
    TypeError: expected an object with the buffer interface

In Python 3.0b1, ``os.listdir(str)`` returned undecodable filenames as
``bytes``. The caller must be prepared to get filenames as two types: ``str``
and ``bytes``. It wasn't the case for ``os.walk()``.

At the first look, the bug seems trivial to fix. At that time, **I didn't know
that this kind of bug will haunt me for the next following 10 years**...

I proposed a new Filename class
===============================

August 2008, my first comment `proposed
<https://bugs.python.org/issue3187#msg71612>`__ to use a custom "Filename" type
to store the original ``bytes`` filename, but also gives a Unicode view of the
filename, in a single object::

    class Filename:
        def __init__(self, orig):
            self.as_bytes = orig
            self.as_str = myformat(orig)
        def __str__(self):
            return self.as_str
        def __bytes__(self):
            return self.as_bytes

**Antoine Pitrou** suggested to inherit from ``str``:

    I agree that logically it's the right solution. It's also the most
    invasive. If that class is **made a subclass of str**, however, existing
    code shouldn't break more than it currently does.

I preferred to inherit from ``bytes`` for pratical reasons, but Antoine noticed
that the native type for filenames on Windows is ``str``.

Anyway, `Guido van Rossum disliked the idea
<https://bugs.python.org/issue3187#msg71749>`_ (comment on InvalidFilename,
an evolution of the class):

    I'm not interested in the InvalidFilename class; it's an API complification
    that might seem right for your situation but will hinder most other people.


Guido van Rossum proposed errors="replace"
==========================================

**Guido van Rossum** `proposed <https://bugs.python.org/issue3187#msg71655>`__
to use the ``replace`` error handler to prevent decoding error. For example,
``b'nonascii\xff'`` is decoded as ``'nonascii�'``.

Problem: this filename cannot be used to read the file using ``open()`` or to
remove the file using ``os.unlink()``, the operating system doesn't know the
filename containing "�".

An important property has been, indirectly, identified: **we must be able to
encode back Unicode filenames as their original bytes filename**.


Defer the choice to the caller: pass a callback
===============================================

As no obvious choice arised, `I proposed
<https://bugs.python.org/issue3187#msg71680>`_ to give the ability to the
``os.listdir()`` caller to decide how to handle undecodable filenames. Example
of new listdir implementation (pseudo-code)::

   charset = sys.getfilesystemcharset()
   dirobj = opendir(path)
   try:
      for bytesname in readdir(dirobj):
          try:
              name = str(bytesname, charset)
          exept UnicodeDecodeError:
              name = fallback_encoder(bytesname)
          yield name
   finally:
      closedir(dirobj)

The default ``fallback_encoder`` callback::

   def fallback_encoder(name):
      raise

Example of callback to keep the raw bytes string unchanged (Python 3.0 beta1
behaviour)::

   def fallback_encoder(name):
      return name

Example to use your own custom filename class::

   class Filename:
      ...

   def fallback_encoder(name):
      return Filename(name)

Guido also `disliked my callback idea
<https://bugs.python.org/issue3187#msg71699>`_:

    The callback variant is too complex; you could write it yourself by
    using os.listdir() with a bytes argument.

Ignore undecodable filenames but emit a warning?
================================================

As ignoring undecodable filenames in ``os.listdir(str)`` slowly became the most
popular option, **Benjamin Peterson** `proposed to emit a warning
<https://bugs.python.org/issue3187#msg71700>`_ if a filename cannot be decoded,
to ease debugging:

    (...) I don't like the idea of silently losing the contents of a directory.
    That's asking for difficult to discover bugs. Could Python emit a warning
    in this case?

While Guido van Rossum `liked the idea
<https://bugs.python.org/issue3187#msg71705>`_ ("*This may be the best
compromise yet.*"), **Amaury Forgeot d'Arc** `asked
<https://bugs.python.org/issue3187#msg73535>`_:

    Does the warning warn multiple times? IIRC the default behaviour is to warn
    once.

**Benjamin Peterson** `replied <https://bugs.python.org/issue3187#msg73535>`__:

    **Making a warning happen more than once is tricky because it requires
    messing with the warnings filter.** This of course takes away some of the
    user's control which is one of the main reasons for using the Python
    warning system in the first place.

Because of this issue, ``os.listdir()`` will no emit the proposed warning.


Support bytes and fix os.listdir()
==================================

I started to write on multiple times to support passing filenames as ``bytes``
in many functions of the ``os`` module:

* posix_path_bytes.patch: ``posixpath.join()``
* io_byte_filename.patch: ``open()``
* fnmatch_bytes.patch: ``fnmatch.filter()``
* glob1_bytes.patch: ``glob.glob()``
* getcwd_bytes.patch: ``os.getcwd()`` returns bytes if unicode conversion fails
* merge_os_getcwd_getcwdu.patch: Remove ``os.getcwdu()``;
  ``os.getcwd(bytes=True)`` returns bytes
* os_getcwdb.patch: Fix ``os.getcwd()`` (use ``PyUnicode_Decode()``) and create
  ``getcwdb()`` -> bytes

Guido van Rossum created a `review on my combined patches
<https://codereview.appspot.com/3055>`_ using the Google Rietveld tool (this
tool was only integrated later into the Python bug tracker). Then I combined my
patches into a single ``python3_bytes_filename.patch`` file.

After one month of development, 6 versions of the patch set, Guido commited my
big change as the commit `f0af3e30
<https://github.com/python/cpython/commit/f0af3e30db9475ab68bcb1f1ce0b5581e214df76>`__::

    commit f0af3e30db9475ab68bcb1f1ce0b5581e214df76
    Author: Guido van Rossum <guido@python.org>
    Date:   Thu Oct 2 18:55:37 2008 +0000

        Issue #3187: Better support for "undecodable" filenames.  Code by Victor
        Stinner, with small tweaks by GvR.

     Lib/fnmatch.py                |  27 ++++---
     Lib/genericpath.py            |   5 +-
     Lib/glob.py                   |  17 +++--
     Lib/io.py                     |  15 ++--
     Lib/posixpath.py              | 171 +++++++++++++++++++++++++++++++-----------
     Lib/test/test_fnmatch.py      |   9 +++
     Lib/test/test_posix.py        |   2 +-
     Lib/test/test_posixpath.py    | 150 ++++++++++++++++++++++++++++++++----
     Lib/test/test_unicode_file.py |   6 +-
     Misc/NEWS                     |  10 ++-
     Modules/posixmodule.c         |  90 +++++++++-------------
     11 files changed, 358 insertions(+), 144 deletions(-)

My change:

* Modify ``os.listdir(str)`` to **ignore undecodable filenames**, instead of
  returning them as ``bytes``
* Add ``os.getcwdb()`` function: similar to ``os.getcwd()`` but returns the
  current working directory as ``bytes``.
* Support ``bytes`` paths:

  * ``fnmatch.filter()``
  * ``glob.glob1()``
  * ``glob.iglob()``
  * ``open()``
  * ``os.path.isabs()``
  * ``os.path.issep()``
  * ``os.path.join()``
  * ``os.path.split()``
  * ``os.path.splitext()``
  * ``os.path.basename()``
  * ``os.path.dirname()``
  * ``os.path.splitdrive()``
  * ``os.path.ismount()``
  * ``os.path.expanduser()``
  * ``os.path.expandvars()``
  * ``os.path.normpath()``
  * ``os.path.abspath()``
  * ``os.path.realpath()``

More bytes patches
==================

While first my "bytes" change is big, it was only the very first patch of a
long serie which will keep me busy during a few years. A few examples between
2008 and 2010:

* `bpo-4035 <https://bugs.python.org/issue4035>`__: Support bytes in os.exec*()
* `bpo-4036 <https://bugs.python.org/issue4036>`__: Support bytes in subprocess.Popen()
* `bpo-8513 <https://bugs.python.org/issue8513>`__: subprocess: support bytes program name (POSIX)
* `bpo-8514 <https://bugs.python.org/issue8514>`__: Add fsencode() functions to os module
* `bpo-8603 <https://bugs.python.org/issue8603>`__: Create a bytes version of os.environ and getenvb()
* `bpo-8412 <https://bugs.python.org/issue8412>`__: os.system() doesn't support surrogates nor bytes
* `bpo-8468 <https://bugs.python.org/issue8468>`__: bz2: support surrogates in filename, and bytes/bytearray filename
* `bpo-8477 <https://bugs.python.org/issue8477>`__: _ssl: support surrogates in filenames, and bytes/bytearray filenames
* `bpo-8640 <https://bugs.python.org/issue8640>`__: subprocess: canonicalize env to bytes on Unix (Python3)
* `bpo-8776 <https://bugs.python.org/issue8776>`__: Bytes version of sys.argv (REJECTED)

Conclusion
==========

Sadly, I didn't know that I opened a giant can of worms: "Unicode support".  I
will work 5 more years (Python 3.0 - Python 3.4) on fixing all these tiny
"Unicode issues" on Windows, Linux, macOS, FreeBSD, Solaris, etc.
