+++++++++++++++++++++++++++++++++++++++++
History of the Python filesystem encoding
+++++++++++++++++++++++++++++++++++++++++

:date: 2018-03-09 13:00
:tags: cpython
:category: python
:slug: python-filesystem-encoding-history
:authors: Victor Stinner

Summary:

* 2008: cannot pass bytes to open(), annoying listdir(str) behaviour
* June 2009: PEP 383, surrogateescape
* 2010: initfsencoding()
* PYTHONFSENCODING attempt

Timeline:

* Python 3.0: December 2008
* Python 3.1: June 2009
* Python 3.2: February 2011
* Python 3.3: September 2012
* Python 3.4: March 2014
* Python 3.5: September 2015


Quick history of Unicode in Python 3
====================================

In Python 3.0, ``os.listdir()`` failed to list the content of a directory if a
single filename was not decodable from the locale encoding.

In 2008, `I proposed <https://bugs.python.org/issue3187#msg71612>`_ to use a
custom type::

    class Filename:
        def __init__(self, orig):
            self.as_bytes = orig
            self.as_str = myformat(orig)
        def __str__(self):
            return self.as_str
        def __bytes__(self):
            return self.as_bytes


But `Guido van Rossum disliked the idea
<https://bugs.python.org/issue3187#msg71749>`_:

    I'm not interested in the InvalidFilename class; it's an API complification
    that might seem right for your situation but will hinder most other people.

The workaround at that time was to pass filenames as ``bytes`` rather than
Unicode (``str``). Guido asked for patches to support passing filenames as
``bytes``.

I wrote patches to accept ``bytes`` in:

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

My patch also added ``os.getcwdb()``.

My patch modified ``os.listdir(str)`` to no longer return undecodable filenames
as ``bytes``, but instead **ignore** them.

**Benjamin Peterson** `proposed to emit a UnicodeWarning warning
<https://bugs.python.org/issue3187#msg73678>`_ if ``os.listdir(dir)`` fails to
decode a filename.

Then **Benjamin Peterson** `proposed another possibility
<https://bugs.python.org/issue3187#msg73909>`_:

    Ok. Here's another possibility. It adds another optional parameter to
    listdir. If False, bytes strings can be returned. Otherwise, the
    UnicodeDecodeError is reraised.

End of september 2008, **Martin v. Löwis** showed up and `proposed an idea
<https://bugs.python.org/issue3187#msg73992>` which will later become his
:pep:`383` "Non-decodable Bytes in System Character Interfaces":

    I'd like to propose yet another approach: make sure that conversion
    according to the file system encoding always succeeds. If an
    unconvertable byte is detected, map it into some private-use character.
    To reduce the chance of conflict with other people's private-use
    characters, we can use some of the plane 15 private-use characters, e.g.
    map byte 0xPQ to U+F30PQ (in two-byte Unicode mode, this would result in
    a surrogate pair).

    This would make all file names accessible to all text processing
    (including glob and friends); UI display would typically either report
    an encoding error, or arrange for some replacement glyph to be shown.

    There are certain variations of the approach possible, in case there is
    objection to a specific detail.

commit f0af3e30db9475ab68bcb1f1ce0b5581e214df76
Author: Guido van Rossum <guido@python.org>
Date:   Thu Oct 2 18:55:37 2008 +0000

    Issue #3187: Better support for "undecodable" filenames.  Code by Victor
    Stinner, with small tweaks by GvR.

2008-10-03, Martin v. Löwis:

    I've committed sys.setfilesystemencoding as r66769.

Then I started to write new patches to support bytes in os.exec*()
https://bugs.python.org/issue4035

and patches to support bytes in subprocess.Popen().
https://bugs.python.org/issue4036

Sadly, I didn't know that I opened a giant can of worms: "Unicode support".  I
will work 5 more years (Python 3.0 - Python 3.4) on fixing all these tiny
"Unicode issues" on Windows, Linux, macOS, FreeBSD, Solaris, etc.

It took many years to find the best encoding and error handler to encode and
decode data from/to the operating system, and to design new and enhance
existing APIs. Example: ``os.environb`` monster, ``sys.argvb`` idea, etc.

**Martin v. Löwis** wrote his :pep:`383` "Non-decodable Bytes in System
Character Interfaces" and implemented it in Python 3.1. The ``surrogateescape``
error handler fixed a lot of old and very complex Unicode issues on Unix.

In 2010, I already proposed to "fallback on UTF-8" if Python failed to get
the locale encoding: https://bugs.python.org/issue8610#msg104986

2010-05-05, bpo-8622: As a follow-up of bpo-8610, **Marc-Andre Lemburg**
proposed a way to override the automatic detection of the file system
encoding::

    PYTHONFSENCODING: Encoding[:errors] used for file system.

At that time, I already noticed the most complex part of this option: the need
to "reencode filenames when setting the filesystem encoding".

bpo-9630:

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


Other::

    commit b744ba1d14c5487576c95d0311e357b707600b47
    Author: Victor Stinner <victor.stinner@haypocalc.com>
    Date:   Sat May 15 12:27:16 2010 +0000

        Issue #8610: Load file system codec at startup, and display a fatal error on
        failure. Set the file system encoding to utf-8 (instead of None) if getting
        the locale encoding failed, or if nl_langinfo(CODESET) function is missing.



