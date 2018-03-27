+++++++++++++++++++++
Python 3.7 UTF-8 Mode
+++++++++++++++++++++

:date: 2018-03-26 22:00
:tags: cpython
:category: python
:slug: python37-new-utf8-mode
:authors: Victor Stinner

Since Python 3.0 was released in 2008, each time an user reports an encoding
issue, someone shows up and asks why Python does not simply always use UTF-8.
Well, it's not that easy. UTF-8 is the best encoding in most cases, but it is
still not the best encoding in all cases, even in 2018. The locale encoding
remains the best **default** filesystem encoding for Python. I would say that
**the locale encoding is the least bad choice**.

I proposed an opt-in UTF-8 Mode for Python 3.7, and also to use UTF-8 for the C
locale.

**This article is the sixth and last in a series of articles telling the
history and rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.6 now uses UTF-8 on Windows <{filename}/windows_utf8.rst>`_
* 5. `Python 3.7 and the POSIX locale <{filename}/posix_locale.rst>`_
* 6. `Python 3.7 UTF-8 Mode <{filename}/utf8_mode.rst>`_

.. image:: {filename}/images/sunrise.jpg
   :alt: Sunrise
   :target: https://www.flickr.com/photos/99444752@N06/9368903367/

Fallback to UTF-8 if getting the locale encoding fails?
=======================================================

May 2010, I reported `bpo-8610 <https://bugs.python.org/issue8610>`__:
"Python3/POSIX:  errors if file system encoding is None". I asked what should
be the default encoding when getting the locale encoding fails. I proposed
to fallback to UTF-8. `I wrote <https://bugs.python.org/issue8610#msg105008>`__:

    **UTF-8 is also an optimist choice**: I bet that more and more operating
    systems will move to UTF-8.

`Marc-Andre commented <https://bugs.python.org/issue8610#msg105010>`_:

    Ouch, that was a poor choice. **In Python we have a tradition to avoid
    guessing**, if possible. Since we cannot guarantee that the file system
    will indeed use UTF-8, it would have been safer to use ASCII. Not sure why
    this reasoning wasn't applied for the file system encoding.

In practice, Python already used UTF-8 when the filesystem encoding was set to
``None``. I pushed the `commit b744ba1d
<https://github.com/python/cpython/commit/b744ba1d14c5487576c95d0311e357b707600b47>`__
into the Python 3.2 development branch to make the default encoding (UTF-8)
more obvious. But before Python 3.2 was released, I removed the fallback with
my `commit e474309b
<https://github.com/python/cpython/commit/e474309bb7f0ba6e6ae824c215c45f00db691889>`__
(Oct 2010):

    ``initfsencoding()``: ``get_codeset()`` failure is now a fatal error

    Don't fallback to UTF-8 anymore to avoid mojibake. I never got any error
    from his function.

The utf8 option proposed for Windows
====================================

August 2016, `bpo-27781 <https://bugs.python.org/issue27781>`__: when **Steve
Dower** `was working on changing the filesystem encoding to UTF-8
<{filename}/windows_utf8.rst>`__, I was not sure that Windows should use UTF-8
by default, I was more in favor on **making the backward incompatible change an
opt-in option**. `I wrote <https://bugs.python.org/issue27781#msg272950>`__:

    **If you go in this direction, I would like to follow you for the UNIX/BSD
    side to make the switch portable. I was thinking about "-X utf8" which
    avoids to change the command line parser.**

    If we agree on a plan, I would like to write it down as a PEP since I
    expect a lot of complains and questions which I would prefer to only
    answer once (see for example the length of your thread on python-ideas
    where each people repeated the same things multiple times ;-))

`I added <https://bugs.python.org/issue27781#msg272962>`__:

    I mean that ``python3 -X utf8`` should force
    ``sys.getfilesystemencoding()`` to UTF-8 on UNIX/BSD, it would ignore the
    current locale setting.

Since Steve chose to **change the default to UTF-8** on Windows, my ``-X utf8``
option idea was ignored in this issue.

The utf8 option proposed for the POSIX locale
=============================================

September 2016: **Jan Niklas Hasse** opened `bpo-28180
<https://bugs.python.org/issue28180>`__ about Docker images,
**"sys.getfilesystemencoding() should default to utf-8"**.

`I proposed again my option <https://bugs.python.org/issue28180#msg276707>`__:

    I proposed to add ``-X utf8`` command line option for UNIX to force utf8
    encoding. Would it work for you?

**Jan Niklas Hasse** `answered
<https://bugs.python.org/issue28180#msg276709>`_:

    Unfortunately no, as this would mean I'll have to change all my python
    invocations in my scripts and it wouldn't work for executable files with

December 2016, `I added <https://bugs.python.org/issue28180#msg283408>`__:

    Usually, when a new option is added to Python, we add a command line option
    (-X utf8) but also an environment variable: **I propose PYTHONUTF8=1**.

    Use your favorite method to define the env var "system wide" in your docker
    containers.

    Note: Technically, I'm not sure that it's possible to support -E option
    with PYTHONUTF8, since -E comes from the command line, and we first need to
    decode command line arguments with an encoding to parse these options....
    Chicken-and-egg issue ;-)

Implement properly the ``-X utf8`` option was tricky. Parsing the command line
was done on ``wchar_t*`` C strings (Unicode), which requires to decode the
``char** argv`` C array of byte strings (bytes). Python starts by decoding byte
strings from the locale encoding. If the utf8 option is detected, ``argv`` byte
strings must be decoded again, but now from UTF-8. The problem was that the
code was not designed for that, and it required to refactor a lot of code in
``Py_Main()``.

**Nick Coghlan** `wrote his PEP 538 "Coercing the C locale to a UTF-8 based
locale" <{filename}/posix_locale.rst>`__ which has been approved in May 2017
and finally implemented in June 2017.

Again, my utf8 idea was ignored in this issue.

First version of my PEP 540: Add a new UTF-8 Mode
=================================================

January 2017, as a follow-up of `bpo-27781
<https://bugs.python.org/issue27781>`__ and `bpo-28180
<https://bugs.python.org/issue28180>`__, I wrote the `PEP 540: Add a new UTF-8
Mode <https://www.python.org/dev/peps/pep-0540/>`_ and `I posted it to
python-ideas for comments
<https://mail.python.org/pipermail/python-ideas/2017-January/044089.html>`_.

Abstract:

    Add a new UTF-8 mode, opt-in option to use UTF-8 for operating system
    data instead of the locale encoding. Add ``-X utf8`` command line option
    and ``PYTHONUTF8`` environment variable.

After ten hours after and a few messages, I `wrote a second version
<https://mail.python.org/pipermail/python-ideas/2017-January/044099.html>`_:

    I modified my PEP: **the POSIX locale now enables the UTF-8 mode**.

**INADA Naoki** `proposed to always use UTF-8 and always ignore the locale
<https://mail.python.org/pipermail/python-ideas/2017-January/044112.html>`_:

    I want UTF-8 mode is **enabled by default (opt-out option) even if locale
    is not POSIX**, like `PYTHONLEGACYWINDOWSFSENCODING`.

    Users depends on locale know what locale is and how to configure it.  They
    can understand difference between locale mode and UTF-8 mode and they can
    opt-out UTF-8 mode.

    **But many people lives in "UTF-8 everywhere" world**, and don't know about
    locale.

Always ignoring the locale to always use UTF-8 would be a backward incompatible
change.  I wasn't brave enough to propose it on UNIX, I only wanted to propose
an opt-in option, except of the specific case of the POSIX locale.

Not only people had different opinons, but most people had strong opinions on
how to handle Unicode and were not ready for compromises.

Third version of my PEP 540
===========================

One week and 59 emails later, I `implemented my PEP 540
<https://bugs.python.org/issue29240>`__ and `I wrote a third version of my PEP
<https://mail.python.org/pipermail/python-ideas/2017-January/044197.html>`_:

    I made multiple changes since the first version of my PEP:

    * The **UTF-8 Strict mode now only uses strict for inputs and outputs**:
      it keeps surrogateescape for operating system data. Read the "Use the
      strict error handler for operating system data" alternative for the
      rationale.

    * The POSIX locale now enables the UTF-8 mode. See the "Don't modify
      the encoding of the POSIX locale" alternative for the rationale.

    * Specify the priority between -X utf8, PYTHONUTF8, PYTHONIOENCODING, etc.

    The PEP version 3 has a longer rationale with more example. (...)

The new thread also got 19 emails, total: **78 emails in one month**. The same
month, Nick Coghlan's PEP 538 was also under discussion.

Silence during one year
=======================

Because of the tone of the python-ideas threads and because I didn't know how
to deal with Nick Coghlan's PEP 538, **I decided to do nothing during one
year** (January to December 2017).

April 2017, Nick `proposed
<https://mail.python.org/pipermail/python-dev/2017-April/147795.html>`__
**INADA Naoki** as the BDFL Delegate for his PEP 538 and my PEP 540. Guido
`accepted to delegate
<https://mail.python.org/pipermail/python-dev/2017-April/147796.html>`_.

May 2017, Naoki approved Nick's PEP 538, and then Nick implemented it.

PEP 540 version 3 posted to python-dev
======================================

At the end of 2017, when I looked at my contributions in Python 3.7 in the
`What’s New In Python 3.7 <https://docs.python.org/dev/whatsnew/3.7.html>`_
document, I didn't see any major contribution. Moreover, the deadline for the
Python 3.7 feature freeze (first beta version) was getting close, end of
January 2018: see the `PEP 537: Python 3.7 Release Schedule
<https://www.python.org/dev/peps/pep-0537/>`_.

December 2017, I decided to move to the next step. I sent my PEP to the
python-dev mailing list: `[Python-Dev] PEP 540: Add a new UTF-8 Mode
<https://mail.python.org/pipermail/python-dev/2017-December/151054.html>`_.

Guido van Rossum `complained about the length of the PEP
<https://mail.python.org/pipermail/python-dev/2017-December/151069.html>`_:

    I've been discussing this PEP offline with Victor, but he suggested we
    should discuss it in public instead.

    **I am very worried about this long and rambling PEP, and I propose that it
    not be accepted without a major rewrite to focus on clarity of the
    specification. The "Unicode just works" summary is more a wish than a
    proper summary of the PEP.**

    (...)

    So I guess PEP acceptance week is over. :-(

PEP rewritten from scratch
==========================

Even if **I was not fully convinced myself that my PEP was a good idea**, I
wanted to get an official vote, to know if my idea should be implemented or
abandonned. I decided to rewrite my PEP from scratch:

* `PEP version 3 (before rewrite)
  <https://github.com/python/peps/blob/f92b5fbdc2bcd9b182c1541da5a0f4ce32195fb6/pep-0540.txt>`_:
  1,017 lines
* `PEP version 4 (after rewrite)
  <https://github.com/python/peps/blob/0bb19ff93af9855db327e9a02f3e86b6f932a25a/pep-0540.txt>`_:
  263 lines (26% of the previous version)

I reduced the rationale to the strict minimum, to explain **key points** of the
PEP:

* Locale encoding and UTF-8
* Passthough undecodable bytes: surrogateescape
* Strict UTF-8 for correctness
* No change by default for best backward compatibility

Reading JPEG pictures with surrogateescape
==========================================

December 2017, I sent the `shorter PEP version 4 to python-dev
<https://mail.python.org/pipermail/python-dev/2017-December/151074.html>`_.

INADA Naoki, the BDFL-delegate, `spotted a design issue
<https://mail.python.org/pipermail/python-dev/2017-December/151081.html>`_:

    And I have one worrying point. With UTF-8 mode, open()'s **default**
    encoding/error handler **is UTF-8/surrogateescape**.

    (...)

    And **opening binary file without "b" option is very common mistake** of
    new developers.  If default error handler is surrogateescape, **they lose a
    chance to notice their bug**.

He `gave a concrete example
<https://mail.python.org/pipermail/python-dev/2017-December/151101.html>`_:

    With PEP 538 (C.UTF-8 locale), ``open()`` uses UTF-8/strict, not
    UTF-8/surrogateescape.

    For example, this code raise ``UnicodeDecodeError`` with PEP 538 if the
    file is JPEG file. ::

        with open(fn) as f:
            f.read()

`I replied <https://mail.python.org/pipermail/python-dev/2017-December/151132.html>`__:

    While I'm not strongly convinced that ``open()`` error handler must be
    changed for ``surrogateescape``, **first I would like to make sure that
    it's really a very bad idea** before changing it :-)

    (...)

    Using a JPEG image, the example is obviously wrong.

    But using surrogateescape on open() is written to **read text files
    which are mostly correctly encoded to UTF-8, except a few bytes**.

    I'm not sure how to explain the issue. The Mercurial wiki page has a good
    example of this issue that they call the `Makefile problem
    <https://www.mercurial-scm.org/wiki/EncodingStrategy#The_.22makefile_problem.22>`_.

**Guido van Rossum** `finished to convinced me
<https://mail.python.org/pipermail/python-dev/2017-December/151134.html>`_:

    You will quickly get decoding errors, and that is **INADA**'s point.
    (Unless you use ``encoding='Latin-1'``.) His worry is that the
    surrogateescape error handler makes it so that you won't get decoding
    errors, and then the failure mode is much harder to debug.

I `wrote a 5th version of my PEP
<https://mail.python.org/pipermail/python-dev/2017-December/151136.html>`_:

    I made the following two changes to the PEP 540:

    * open() error handler remains ``"strict"``
    * Remove the "Strict UTF8 mode" which doesn't make much sense anymore

Last question on locale.getpreferredencoding()
==============================================

December 2017, **INADA Naoki** `asked
<https://mail.python.org/pipermail/python-dev/2017-December/151144.html>`_:

    Or ``locale.getpreferredencoding()`` returns ``'UTF-8'`` in UTF-8 mode too?

Oh. I didn't look at this specific issue.

I `looked at the code
<https://mail.python.org/pipermail/python-dev/2017-December/151148.html>`_ and
agreed to return UTF-8:

    I checked the stdlib, and I found many places where
    ``locale.getpreferredencoding()`` is used to get the user preferred
    encoding:

    * builtin ``open()``: default encoding
    * ``cgi.FieldStorage``: encode the query string
    * ``encoding._alias_mbcs()``: check if the requested encoding is the ANSI
      code page
    * ``gettext.GNUTranslations``: ``lgettext()`` and ``lngettext()`` methods
    * ``xml.etree.ElementTree``: ``ElementTree.write(encoding='unicode')``

    In the UTF-8 mode, I would expect that cgi, gettext and xml.etree all use
    the UTF-8 encoding by default. So **locale.getpreferredencoding() should
    return UTF-8 if the UTF-8 mode is enabled**.

I `sent a 6th version of my PEP
<https://mail.python.org/pipermail/python-dev/2017-December/151151.html>`_:

    locale.getpreferredencoding() now returns 'UTF-8' in the UTF-8 Mode.

Finally, one year after the first PEP version, INADA Naoki `approved my PEP
<https://mail.python.org/pipermail/python-dev/2017-December/151193.html>`_.

First incomplete implementation
===============================

I started to work on the implementation of my PEP 540 in March 2017. Once the
PEP has been approved, I asked INADA Naoki for a review. `He asked to fix the
command line parsing
<https://github.com/python/cpython/pull/855#issuecomment-351089573>`_ to handle
properly the ``-X utf8`` option:

    And when ``-X utf8`` option is found, we can decode from ``char **argv``
    again.  Since ``mbstowcs()`` doesn't guarantee round tripping, it is better
    than re-encode ``wchar_t **argv``.

`I replied
<https://github.com/python/cpython/pull/855#issuecomment-351252873>`__:

    ``main()`` and ``Py_Main()`` are very complex. With the `PEP 432
    <https://www.python.org/dev/peps/pep-0432/>`_, **Nick Coghlan**, **Eric
    Snow** and me are working on making this code better. See for example
    `bpo-32030 <https://bugs.python.org/issue32030>`_.

    (...)

    For all these reasons, **I propose to merge this uncomplete PR and write a
    different PR for the most complex part**, re-encode wchar_t* command line
    arguments, implement Py_UnixMain() or another even better option?

December 2017, `bpo-29240 <https://bugs.python.org/issue29240>`__, I pushed my
`commit 91106cd9
<https://github.com/python/cpython/commit/91106cd9ff2f321c0f60fbaa09fd46c80aa5c266>`__:

    PEP 540: Add a new UTF-8 Mode

    * Add ``-X utf8`` command line option, ``PYTHONUTF8`` environment variable
      and a new ``sys.flags.utf8_mode`` flag.
    * ``locale.getpreferredencoding()`` now returns 'UTF-8' in the UTF-8
      mode. As a side effect, open() now uses the UTF-8 encoding by
      default in this mode.

Split Py_Main() into subfunctions
=================================

To be able to properly implement my PEP 540, I created `bpo-32030
<https://bugs.python.org/issue32030>`__ to split the big ``Py_Main()`` into
smaller subfunctions.

It will take me **3 months of work and 45 commits** to completely cleanup
``Py_Main()`` and put almost all Python configuration options into the private
C ``_PyCoreConfig`` structure.

Parse again the command line when -X utf8 is used
=================================================

December 2017, `bpo-32030 <https://bugs.python.org/issue32030>`__, thanks to
the ``Py_Main()`` refactoring, I was able to finish the implementation of my
PEP. If the encoding changed after reading the Python configuration, cleanup
the configuration and read again the configuration with the new configuration.
The key feature here is to be able to cleanup properly all the configuration.

I pushed my commit 9454060e84a669dde63824d9e2fcaf295e34f687:

    ``Py_Main()`` re-reads config if encoding changes

    If the encoding change (C locale coerced or UTF-8 Mode changed),
    ``Py_Main()`` now reads again the configuration with the new encoding.

Decode Current Locale
=====================

Decode Current Locale::

    PyObject*
    _PyUnicode_DecodeCurrentLocale(const char *str, const char *errors)

`commit 7ed7aead <https://github.com/python/cpython/commit/7ed7aead9503102d2ed316175f198104e0cd674c>`__::

    bpo-29240: Fix locale encodings in UTF-8 Mode (#5170)

    Modify locale.localeconv(), time.tzname, os.strerror() and other
    functions to ignore the UTF-8 Mode: always use the current locale
    encoding.

    Changes:

    * Add _Py_DecodeLocaleEx() and _Py_EncodeLocaleEx(). On decoding or
      encoding error, they return the position of the error and an error
      message which are used to raise Unicode errors in
      PyUnicode_DecodeLocale() and PyUnicode_EncodeLocale().
    * Replace _Py_DecodeCurrentLocale() with _Py_DecodeLocaleEx().
    * PyUnicode_DecodeLocale() now uses _Py_DecodeLocaleEx() for all
      cases, especially for the strict error handler.
    * Add _Py_DecodeUTF8Ex(): return more information on decoding error
      and supports the strict error handler.
    * Rename _Py_EncodeUTF8_surrogateescape() to _Py_EncodeUTF8Ex().
    * Replace _Py_EncodeCurrentLocale() with _Py_EncodeLocaleEx().
    * Ignore the UTF-8 mode to encode/decode localeconv(), strerror()
      and time zone name.
    * Remove PyUnicode_DecodeLocale(), PyUnicode_DecodeLocaleAndSize()
      and PyUnicode_EncodeLocale() now ignore the UTF-8 mode: always use
      the "current" locale.
    * Remove _PyUnicode_DecodeCurrentLocale(),
      _PyUnicode_DecodeCurrentLocaleAndSize() and
      _PyUnicode_EncodeCurrentLocale().

XXX Android

Summary of PEP 540 history
==========================

* Version 1: first version sent to python-ideas
* Version 2: the POSIX locale now enables the UTF-8 mode
* Version 3: the UTF-8 Strict mode now only uses the ``strict`` error handler
  for inputs and outputs
* Version 4: PEP rewritten from scratch to be shorter
* Version 5: open() error handler remains ``strict``, and the "Strict UTF8
  mode" has been removed
* Version 6: locale.getpreferredencoding() now returns 'UTF-8' in the UTF-8
  Mode.

Abstract of the final approved PEP:

    Add a new "UTF-8 Mode" to enhance Python's use of UTF-8.  When UTF-8 Mode
    is active, Python will:

    * use the ``utf-8`` encoding, irregardless of the locale currently set by
      the current platform, and
    * change the ``stdin`` and ``stdout`` error handlers to
      ``surrogateescape``.

    This mode is off by default, but is automatically activated when using
    the "POSIX" locale.

    Add the ``-X utf8`` command line option and ``PYTHONUTF8`` environment
    variable to control UTF-8 Mode.

Conclusion
==========

It's now time for a well deserved nap... until the next Unicode issue.

.. image:: {filename}/images/tiger_nap.jpg
   :alt: Tiger nap
   :target: https://www.flickr.com/photos/manager_2000/2911858714/

