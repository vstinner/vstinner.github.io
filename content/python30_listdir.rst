+++++++++++++++++++++++++++++++++++++++++++++++++
Python 3.0 listdir() Bug on Undecodable Filenames
+++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2018-03-09 13:00
:tags: cpython
:category: python
:slug: python30-listdir-undecodable-filenames
:authors: Victor Stinner

Ten years ago, when Python 3.0 final was released, ``os.listdir(str)``
**ignored silently undecodable filenames**::

    $ python3.0
    >>> os.mkdir(b'x')
    >>> open(b'x/nonascii\xff', 'w').close()
    >>> os.listdir('x')
    []

You had to use bytes to see all filenames::

    >>> os.listdir(b'x')
    [b'nonascii\xff']

If the locale is POSIX or C, listdir() ignored silently all non-ASCII
filenames.  Hopefully, ``os.listdir()`` accepts ``bytes``, right? In fact, 4
months before the 3.0 final release, it was not the case.

Lying on the real content of a directory looks like a very bad idea. Well,
there is a rationale behind this design. Let me tell you this story which is
now 10 years old.

**This article is the first in a series of articles telling the history and
rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.6 now uses UTF-8 on Windows <{filename}/windows_utf8.rst>`_
* 5. `Python 3.7 New UTF-8 Mode <{filename}/utf8_mode.rst>`_


The os.walk() bug
=================

.. image:: {filename}/images/car_accident_hole.jpg
   :alt: Boston Herald-Traveler photographer Leslie Jones had an eye for a dramatic scene, including when this seven-tonne dump truck plunged through the Warren Avenue bridge, in Boston
   :target: http://www.dailymail.co.uk/news/article-3592525/Classic-crashes-Incredible-black-white-photos-chaos-roads-early-days-automobile-beautiful-vintage-motors-smashing-trees-careering-canals-plummeting-bridges.html

`bpo-3187 <https://bugs.python.org/issue3187>`__, june 2008: **Helmut
Jarausch** tested the **first beta release of Python 3.0** and reported a bug
on ``os.walk()`` when he tried to walk into his home directory::

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
and ``bytes``: it wasn't the case for ``os.walk()`` which failed with a
``TypeError``.

**At the first look, the bug seems trivial to fix. In fact, many solutions were
proposed, it will take 4 months and 79 messages to fix the bug**.

I proposed a new Filename class
===============================

August 2008, `my first comment proposed
<https://bugs.python.org/issue3187#msg71612>`__ to use a custom "Filename" type
to store the original ``bytes`` filename, but also gives a Unicode view of the
filename, in a single object, using an hypothetical ``myformat()`` function::

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

I preferred to inherit from ``bytes`` for pratical reasons. Antoine noted that
the native type for filenames on Windows is ``str``, and so inheriting from
``bytes`` can be an issue on Windows.

Anyway, `Guido van Rossum disliked the idea
<https://bugs.python.org/issue3187#msg71749>`_ (comment on InvalidFilename, a
variant of the class):

    I'm not interested in the InvalidFilename class; it's an API complification
    that might seem right for your situation but **will hinder most other
    people**.


Guido van Rossum proposed to use replace error handler
======================================================

**Guido van Rossum** `proposed to use the replace error handler
<https://bugs.python.org/issue3187#msg71655>`__ to prevent decoding error. For
example, ``b'nonascii\xff'`` is decoded as ``'nonascii�'``.

The problem is that this filename cannot be used to read the file content using
``open()`` or to remove the file using ``os.unlink()``, since the operating
system doesn't know the Unicode filename containing the "�" character.

An important property is that **encoding back the Unicode filename to bytes
must return the same original bytes filename**.


Defer the choice to the caller: pass a callback
===============================================

As no obvious choice arised, `I proposed to use a callback to handle
undecodable filenames <https://bugs.python.org/issue3187#msg71680>`_.
Pseudo-code::

    def listdir(path, fallback_decoder=default_fallback_decoder):
        charset = sys.getfilesystemcharset()
        dir_fd = opendir(path)
        try:
            for bytesname in readdir(dir_fd):
                try:
                    name = str(bytesname, charset)
                exept UnicodeDecodeError:
                    name = fallback_decoder(bytesname)
                yield name
        finally:
            closedir(dir_fd)

The default behaviour is to raise an exception on decoding error::

   def default_fallback_decoder(name):
      raise

Example of callback returning the raw bytes string unchanged (Python 3.0 beta1
behaviour)::

   def return_undecodable_unchanged(name):
      return name

Example to use a custom filename class::

   class Filename:
      ...

   def filename_decoder(name):
      return Filename(name)

`Guido also disliked my callback idea
<https://bugs.python.org/issue3187#msg71699>`_:

    The callback variant is **too complex**; you could **write it yourself by
    using os.listdir() with a bytes argument**.

Emit a warning on undecodable filename
======================================

.. image:: {filename}/images/warning_venomous_snakes.png
   :alt: Warning: venoumous snakes
   :target: http://www.unicode.org/

As ignoring undecodable filenames in ``os.listdir(str)`` slowly became the most
popular option, **Benjamin Peterson** `proposed to emit a warning
<https://bugs.python.org/issue3187#msg71700>`_ if a filename cannot be decoded,
to ease debugging:

    (...) I don't like the idea of silently losing the contents of a directory.
    That's asking for difficult to discover bugs. Could Python emit a warning
    in this case?

Guido van Rossum `liked the idea
<https://bugs.python.org/issue3187#msg71705>`_:

    This may be the best compromise yet.

**Amaury Forgeot d'Arc** `asked <https://bugs.python.org/issue3187#msg73535>`_:

    Does the warning warn multiple times? IIRC the default behaviour is to warn
    once.

**Benjamin Peterson** `replied <https://bugs.python.org/issue3187#msg73535>`__:

    **Making a warning happen more than once is tricky because it requires
    messing with the warnings filter.** This of course takes away some of the
    user's control which is one of the main reasons for using the Python
    warning system in the first place.

Because of this issue, the warning idea was abandonned.


Support bytes and fix os.listdir()
==================================

Guido repeated that the best workaround is to pass filenames as ``bytes``,
which is the native type for filenames on Unix, but most functions only
accepted filenames as ``str``.

I started to write multiple patches to support passing filenames as ``bytes``:

* ``posix_path_bytes.patch``: enhance ``posixpath.join()``
* ``io_byte_filename.patch``: enhance ``open()``
* ``fnmatch_bytes.patch``: enhance ``fnmatch.filter()``
* ``glob1_bytes.patch``: enhance ``glob.glob()``
* ``getcwd_bytes.patch``: ``os.getcwd()`` returns bytes if unicode conversion fails
* ``merge_os_getcwd_getcwdu.patch``: Remove ``os.getcwdu()``;
  ``os.getcwd(bytes=True)`` returns bytes
* ``os_getcwdb.patch``: Fix ``os.getcwd()`` by using ``PyUnicode_Decode()`` and
  add ``os.getcwdb()`` which returns ``bytes``

Guido van Rossum created a `review on my combined patches
<https://codereview.appspot.com/3055>`_. Then I also combined my patches into a
single ``python3_bytes_filename.patch`` file.

**After one month of development, 6 versions of the combined patch, Guido
commited my big change** as the `commit f0af3e30
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

* Modify ``os.listdir(str)`` to **ignore silently undecodable filenames**,
  instead of returning them as ``bytes``
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

I looked if other functions accepted passing filenames as ``bytes`` and... I
was disappointed. It took me some years to fix the full Python standard
library. Example of issues between 2008 and 2010:

* `bpo-4035 <https://bugs.python.org/issue4035>`__: Support bytes in ``os.exec*()``
* `bpo-4036 <https://bugs.python.org/issue4036>`__: Support bytes in ``subprocess.Popen()``
* `bpo-8513 <https://bugs.python.org/issue8513>`__: ``subprocess``: support bytes program name (POSIX)
* `bpo-8514 <https://bugs.python.org/issue8514>`__: Add ``fsencode()`` functions to os module
* `bpo-8603 <https://bugs.python.org/issue8603>`__: Create a bytes version of ``os.environ`` and ``getenvb()`` -- Add ``os.environb``
* `bpo-8412 <https://bugs.python.org/issue8412>`__: ``os.system()`` doesn't support surrogates nor bytes
* `bpo-8468 <https://bugs.python.org/issue8468>`__: ``bz2`` module: support surrogates in filename, and bytes/bytearray filename
* `bpo-8477 <https://bugs.python.org/issue8477>`__: ``ssl`` module: support surrogates in filenames, and bytes/bytearray filenames
* `bpo-8640 <https://bugs.python.org/issue8640>`__: ``subprocess:`` canonicalize env to bytes on Unix (Python3)
* `bpo-8776 <https://bugs.python.org/issue8776>`__: Bytes version of ``sys.argv`` (REJECTED)

Conclusion
==========

At the first look, **Helmut Jarausch**'s ``os.walk()`` bug looked trivial to
fix.

I proposed a **new Filename class** storing filenames as ``bytes`` and ``str``,
but Guido van Rossum rejected the idea because this API complification
would *hinder most people*.

Guido van Rossum proposed to **use the replace error handler**, but decoded
filenames were not recognized by the operating system making them useless for
most cases.

I proposed to **use callback to handle undecodable filenames**, but Guido van
Rossum also rejected this idea because it was too complex and could be written
using os.listdir() with a bytes argument.

Benjamin Peterson proposed to **emit a warning** when a filename cannot be
decoded, but the idea was abandonned because of the warnings filters complexity
to emit the warning multiple times.

I wrote a big change modifying ``os.listdir()`` to ignore silently undecodable
filenames, but also modify a lot of functions to also accept filenames as
``bytes``.  I made further changes the following years to fix the full Python
standard library to accept ``bytes``.

While it "only" took 4 months to fix the ``os.listdir(str)`` issue, **this kind
of bugs will keep me busy the next 10 years** (2008-2018)...

**This article is the first in a series of articles telling the history and
rationale of the Python 3 Unicode model for the operating system.**
