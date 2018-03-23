+++++++++++++++++++++++++
Python 3.7 New UTF-8 Mode
+++++++++++++++++++++++++

:date: 2018-03-23 00:00
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

**This article is the fifth and last in a series of articles telling the
history and rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.6 now uses UTF-8 on Windows <{filename}/windows_utf8.rst>`_
* 5. `Python 3.7 New UTF-8 Mode <{filename}/utf8_mode.rst>`_

Fallback
========

`bpo-8610 <https://bugs.python.org/issue8610>`__.

2010-05-05, `I wrote <https://bugs.python.org/issue8610#msg105008>`__:

    UTF-8 is also an optimist choice: I bet that more and more OS will move to
    UTF-8.

`Marc-Andre wrote <https://bugs.python.org/issue8610#msg105010>`_:

    Ouch, that was a poor choice. In Python we have a tradition to avoid
    guessing, if possible. Since we cannot guarantee that the file system will
    indeed use UTF-8, it would have been safer to use ASCII. Not sure why this
    reasoning wasn't applied for the file system encoding.

POSIX, first attempt, 2011
==========================

2011-12-20: `bpo-13643 <https://bugs.python.org/issue13643>`__
https://bugs.python.org/issue13643

I wrote
https://bugs.python.org/issue13643#msg149926

    It was already discussed: using a different encoding for filenames and for
    other things is really not a good idea. The main problem is the interaction
    with other programs.

    Read discussion of issues #8622, #8775 and #9992.

I added:

    The right fix is to fix your locale, not Python.

Antoine Pitrou:

    So why don't these supposedly "modern" systems at least set the appropriate
    environment variables for Python to infer the proper character encoding?
    (since these "modern" systems don't have a well-defined encoding...)

Antoine Pitrou:

    > The standard encoding is UTF-8.

    How so? I don't know of any Linux or Unix spec which says so.

2011-12-24, Terry J. Reedy closed the issue
https://bugs.python.org/issue13643#msg150204

    Martin, after reading most all of the unusually large sequence of messages,
    I am closing this because three of the core developers with the most
    experience in this area are dead-set against your proposal. That does not
    make it 'wrong', but does mean that it will not be approved and implemented
    without new data and more persuasive arguments than those presented so far.
    I do not see that continued repetition of what has been said so far will
    change anything.

Another similar proposal by Armin Ronacher
https://bugs.python.org/issue11574#msg131144

    Right now Python happily falls back to ASCII if it can not parse your
    LC_CTYPE or something similar happens.  Instead of falling back to ASCII it
    would be better if it falls back to UTF-8. (...)

[Python-Dev] Low-Level Encoding Behavior on Python 3
https://mail.python.org/pipermail/python-dev/2011-March/109361.html
Armin Ronacher
Mar 16, 2011

I closed it
2012-04-25
https://bugs.python.org/issue11574#msg159340

    I don't think that using a fallback is a good idea. So I'm closing the
    issue. You can reopen the discussion on the python-dev mailing list if you
    don't agree with me or Martin.

POSIX, second attempt, 2013
===========================

2013-11-30, `bpo-19846 <https://bugs.python.org/issue19846>`__: ``LANG=C python3 -c 'print("\xe4")'`` fails.

Antoine Pitrou
https://bugs.python.org/issue19846#msg205419

    In the long term, all sensible UNIX systems should be configured for utf-8
    filenames and contents, so it won't make a difference anymore.

I wrote
https://bugs.python.org/issue19846#msg205497

    There was a previous try to use a file encoding different than the locale encoding and it introduces too many issues:
    https://mail.python.org/pipermail/python-dev/2010-October/104509.html
    "Inconsistencies if locale and filesystem encodings are different"

I wrote
https://bugs.python.org/issue19846#msg205625

    If you are talking to me: I'm currently opposed to change anything, so I'm
    not interested to work on a patch. IMO Python works fine and you should try
    to workaround the current limitations :-)

    If someone is interested to write an huge patch fixing all these issues, I
    would be able to reconsider my opinion on point (a).

I wrote
https://bugs.python.org/issue19846#msg205670

    Again, the issue is not specific to Python. So it's time to learn how to
    configure correctly your locales.

2013-12-09: I closed the issue
https://bugs.python.org/issue19846#msg205675

    I'm closing the issue as invalid, because Python 3 behaviour is correct and
    must not be changed.

    Standard streams (sys.stdin, sys.stdout, sys.stderr) uses the locale
    encoding. sys.stdin and sys.stdout use the strict error handler, sys.stderr
    uses the backslashreplace error handler. These encodings and error handlers
    can be overriden by the PYTHONIOENCODING. Since Python 3.3, it's possible
    to only set the error handler using ":errors" syntax (ex:
    PYTHONIOENCODING=":replace").

    Python uses sys.getfilesystemencoding() to decode data from / encode data
    to the operating system. Example of operating system data: command line
    arguments, environment variables, host names, filenames, user names, etc.

    On Windows, Python tries to use the wide character (Unicode) API of Windows
    anywhere to avoid any conversion, to not loose data. The MBCS codec (ANSI
    code page) of Windows uses a replace error handler by default, it looses
    data. Try for example os.listdir() in a directory containing filenames not
    encodable to the ANSI code page in Python 2 (or os.listdir(b'.') in Python
    3).

    On Mac OS X, Python always use UTF-8 for sys.getfilesystemencoding() (with
    the surrogateescape error handler, see the PEP 383). The locale encoding is
    ignored for sys.getfilesystemencoding() (the locale encoding is still used
    in some functions).

    On other operating systems... it's more complex. Python uses the locale
    encoding for sys.getfilesystemencoding() (with the surrogateescape error
    handler, see the PEP 383). For the POSIX locale (aka the "C" locale), you
    may get the ASCII encoding on Linux, ASCII on FreeBSD and Solaris (whereas
    these operating systems announce an alias of the ISO 8859-1 encoding, but
    use ASCII in practice), ISO 8859-1 on AIX etc. Using the locale encoding is
    the best choice for interoperability with other applications (which use
    also the locale encoding).

    Even if an application uses "raw bytes" (like Python 2), these bytes are
    still "locale aware". For example, when "raw bytes" are written to the
    standard output, bytes are decoded to find the appropriate character in the
    font of the terminal. When "raw bytes" are written into a socket to
    generate a HTML document (ex: listing of a directory, so a list of
    filenames), the web brower will decode them from them encoding announced in
    the HTML page. Even if the encoding is not explicit, it does still exist.
    Read other comments of this issue for other examples.

    Forcing the POSIX locale to get an user interface in english is wrong if
    you also expect from your application to still generate valid "raw bytes"
    in your "system" encoding (ISO 8859-1, ShiftJIS, UTF-8, whatever). To
    change the language, the correct environment variable is LC_CTYPE: use
    LC_CTYPE=C. Or better, use the real english locale which will probably
    handle better currency, numbers, etc. Example: LC_CTYPE=en_US.utf8 (on
    Fedora, "en_US" locale uses the ISO 8859-1 encoding).

Similar issue: https://bugs.python.org/issue19847

POSIX locale and surrogateescape
================================

2013-12-13: https://bugs.python.org/issue19977

Python X.Y

::

    Previous related work:

    changeset:   89836:bc06f67234d0
    user:        Victor Stinner <victor.stinner@gmail.com>
    date:        Tue Mar 18 01:18:21 2014 +0100
    files:       Doc/whatsnew/3.5.rst Lib/test/test_sys.py Misc/NEWS Python/pythonru
    description:
    Issue #19977: When the ``LC_TYPE`` locale is the POSIX locale (``C`` locale),
    :py:data:`sys.stdin` and :py:data:`sys.stdout` are now using the
    ``surrogateescape`` error handler, instead of the ``strict`` error handler.

History
=======

2016-08-17: `bpo-27781 <https://bugs.python.org/issue27781>`__, "Change sys.getfilesystemencoding() on Windows to UTF-8".

`I wrote <https://bugs.python.org/issue27781#msg272950>`__:

    If you go in this direction, I would like to follow you for the UNIX/BSD
    side to make the switch portable. I was thinking about ``-X utf8`` which
    avoids to change the command line parser.

    If we agree on a plan, I would like to write it down as a PEP since I
    expect a lot of complains and questions which I would prefer to only
    answer once (see for example the length of your thread on python-ideas
    where each people repeated the same things multiple times ;-))

`I added <https://bugs.python.org/issue27781#msg272962>`__:

    I mean that ``python3 -X utf8`` should force
    ``sys.getfilesystemencoding()`` to UTF-8 on UNIX/BSD, it would ignore the
    current locale setting.

History
=======

2016-09-16: `bpo-28180 <https://bugs.python.org/issue28180>`__, "sys.getfilesystemencoding() should default to utf-8".

`I wrote <https://bugs.python.org/issue28180#msg276707>`__:

    I proposed to add ``-X utf8`` command line option for UNIX to force utf8
    encoding. Would it work for you?

Jan Niklas Hasse `replied <https://bugs.python.org/issue28180#msg276709>`_:

    Unfortunately no, as this would mean I'll have to change all my python
    invocations in my scripts and it wouldn't work for executable files with

Jan Niklas Hasse:

    https://sourceware.org/glibc/wiki/Proposals/C.UTF-8#Defaults mentions that C.UTF-8 should be glibc's default.

    This bug report also mentions Python: https://sourceware.org/bugzilla/show_bug.cgi?id=17318
    It hasn't been fixed yet, though :/

Marc-Andre Lemburg `added <https://bugs.python.org/issue28180#msg282977>`_:

    If we just restrict this to the file system encoding (and not the whole
    LANG setting), how about:

    * default the file system encoding to 'utf-8' and use the surrogate escape
      handler as default error handler
    * add a ``PYTHONFSENCODING`` env var to set the file system encoding to
      something else (*)

    (*) I believe we discussed this at some point already, but don't remember the outcome.

2016-12-16, `I wrote <https://bugs.python.org/issue28180#msg283408>`__:

    Usually, when a new option is added to Python, we add a command line option
    (-X utf8) but also an environment variable: I propose PYTHONUTF8=1.

    Use your favorite method to define the env var "system wide" in your docker
    containers.

    Note: Technically, I'm not sure that it's possible to support -E option
    with PYTHONUTF8, since -E comes from the command line, and we first need to
    decode command line arguments with an encoding to parse these options....
    Chicken-and-egg issue ;-)

Read /etc/locale.conf
=====================

https://bugs.python.org/issue21368
Read /etc/locale.conf

PEP 538
=======

Core issue: https://bugs.python.org/issue28180

Nick Coghlan proposed the PEP 538.

https://bugs.python.org/issue28180#msg284150
msg284150 - (view) 	Author: Nick Coghlan (ncoghlan) * (Python committer) 	Date: 2016-12-28 02:45

I've now written this up as a PEP: https://github.com/python/peps/blob/master/pep-0538.txt

Nick Coghlan ncoghlan at gmail.com
Tue Jan 3 01:00:25 EST 2017
[Linux-SIG] PEP 538: Coercing the legacy C locale to C.UTF-8
https://mail.python.org/pipermail/linux-sig/2017-January/000014.html

Option -X utf8
==============

August 2016, `bpo-27781 <https://bugs.python.org/issue27781>`__: "Change sys.getfilesystemencoding() on Windows to UTF-8".
When I was afraid that
changing the encoding from the ANSI code page to UTF-8 on Windows would break
all applications, `I proposed to make the change as an opt-in option, -X utf8
<https://bugs.python.org/issue27781#msg272916>`_:

    Would it be acceptable for you to add a new option to switch to UTF-8 in
    Python 3.6, and discuss later if it's ok to enable it by default?

`I added <https://bugs.python.org/issue27781#msg272950>`__:

    (...) I would like to follow you for the UNIX/BSD side to make the switch
    portable. I was thinking about **"-X utf8"** which avoids to change the
    command line parser.

    If we agree on a plan, I would like to write it down as a PEP since I
    expect a lot of complains and questions which I would prefer to only
    answer once (see for example the length of your thread on python-ideas
    where each people repeated the same things multiple times ;-))

First PEP
=========

January 2017, I wrote the `PEP 540: Add a new UTF-8 Mode
<https://www.python.org/dev/peps/pep-0540/>`_ and `I posted it to python-ideas
for comments
<https://mail.python.org/pipermail/python-ideas/2017-January/044089.html>`_.

Abstract:

    Add a new UTF-8 mode, opt-in option to use UTF-8 for operating system
    data instead of the locale encoding. Add ``-X utf8`` command line option
    and ``PYTHONUTF8`` environment variable.

I quickly `made a change to the PEP
<https://mail.python.org/pipermail/python-ideas/2017-January/044099.html>`_:

    Ok, I modified my PEP: the POSIX locale now enables the UTF-8 mode.

`INADA Naoki wrote
<https://mail.python.org/pipermail/python-ideas/2017-January/044112.html>`_:

    I want UTF-8 mode is enabled by default (opt-out option) even if locale is
    not POSIX, like `PYTHONLEGACYWINDOWSFSENCODING`.

    Users depends on locale know what locale is and how to configure it.  They
    can understand difference between locale mode and UTF-8 mode and they can
    opt-out UTF-8 mode.

    But many people lives in "UTF-8 everywhere" world, and don't know about
    locale.

    (...)

Not only people had different opinon, but most people had strong opinions and
didn't seem ready for compromises.

... 59 emails later.

PEP version 3
=============

One week later, I implemented my PEP 540: `bpo-29240 <https://bugs.python.org/issue29240>`__, and `I wrote a third
version of my PEP
<https://mail.python.org/pipermail/python-ideas/2017-January/044197.html>`_:

    I made multiple changes since the first version of my PEP:

    * The UTF-8 Strict mode now only uses strict for inputs and outputs:
      it keeps surrogateescape for operating system data. Read the "Use the
      strict error handler for operating system data" alternative for the
      rationale.

    * The POSIX locale now enables the UTF-8 mode. See the "Don't modify
      the encoding of the POSIX locale" alternative for the rationale.

    * Specify the priority between -X utf8, PYTHONUTF8, PYTHONIOENCODING, etc.

    The PEP version 3 has a longer rationale with more example. (...)

The new thread also got 19 emails.

Total: 78 emails in one month.

There was also Nick Coghlan's PEP 538 which was under discussion.

Silence
=======

Because of the tone of the two python-ideas threads and that I had to deal with
Nick Coghlan's PEP 538, I "decided" to do nothing.

UTF-8 Mode
==========

PEP 540 -- Add a new UTF-8 Mode
https://www.python.org/dev/peps/pep-0540/

BDFL-Delegate: INADA Naoki

PEP history in Git:
https://github.com/python/peps/commits/master/pep-0540.txt

PEP before rewrite:
https://github.com/python/peps/blob/f92b5fbdc2bcd9b182c1541da5a0f4ce32195fb6/pep-0540.txt
(1017 lines)

PEP just after rewrite:
https://github.com/python/peps/blob/0bb19ff93af9855db327e9a02f3e86b6f932a25a/pep-0540.txt
(263 lines)

Abstract
--------

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

Version History
---------------

* Version 4: ``locale.getpreferredencoding()`` now returns ``'UTF-8'``
  in the UTF-8 Mode.
* Version 3: The UTF-8 Mode does not change the ``open()`` default error
  handler (``strict``) anymore, and the Strict UTF-8 Mode has been
  removed.
* Version 2: Rewrite the PEP from scratch to make it much shorter and
  easier to understand.
* Version 1: First version posted to python-dev.

Post History
------------

* 2017-12: `[Python-Dev] PEP 540: Add a new UTF-8 Mode
  <https://mail.python.org/pipermail/python-dev/2017-December/151054.html>`_
* 2017-04: `[Python-Dev] Proposed BDFL Delegate update for PEPs 538 &
  540 (assuming UTF-8 for *nix system boundaries)
  <https://mail.python.org/pipermail/python-dev/2017-April/147795.html>`_
* 2017-01: `[Python-ideas] PEP 540: Add a new UTF-8 Mode
  <https://mail.python.org/pipermail/python-ideas/2017-January/044089.html>`_
* 2017-01: `bpo-28180: Implementation of the PEP 538: coerce C locale to
  C.utf-8 (msg284764) <https://bugs.python.org/issue28180#msg284764>`_
* 2016-08-17: `bpo-27781: Change sys.getfilesystemencoding() on Windows
  to UTF-8 (msg272916) <https://bugs.python.org/issue27781#msg272916>`_
  -- Victor proposed ``-X utf8`` for the :pep:`529` (Change Windows
  filesystem encoding to UTF-8)

Implementation
--------------

Commit::

    commit 91106cd9ff2f321c0f60fbaa09fd46c80aa5c266
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Dec 13 12:29:09 2017 +0100

        bpo-29240: PEP 540: Add a new UTF-8 Mode (#855)

        * Add -X utf8 command line option, PYTHONUTF8 environment variable
          and a new sys.flags.utf8_mode flag.
        * If the LC_CTYPE locale is "C" at startup: enable automatically the
          UTF-8 mode.
        * Add _winapi.GetACP(). encodings._alias_mbcs() now calls
          _winapi.GetACP() to get the ANSI code page
        * locale.getpreferredencoding() now returns 'UTF-8' in the UTF-8
          mode. As a side effect, open() now uses the UTF-8 encoding by
          default in this mode.
        * Py_DecodeLocale() and Py_EncodeLocale() now use the UTF-8 encoding
          in the UTF-8 Mode.
        * Update subprocess._args_from_interpreter_flags() to handle -X utf8
        * Skip some tests relying on the current locale if the UTF-8 mode is
          enabled.
        * Add test_utf8mode.py.
        * _Py_DecodeUTF8_surrogateescape() gets a new optional parameter to
          return also the length (number of wide characters).
        * pymain_get_global_config() and pymain_set_global_config() now
          always copy flag values, rather than only copying if the new value
          is greater than the old value.

XXX mercurial link

Commit 2::

    New changeset 9454060e84a669dde63824d9e2fcaf295e34f687 by Victor Stinner in branch 'master':
    bpo-29240, `bpo-32030 <https://bugs.python.org/issue32030>`__: Py_Main() re-reads config if encoding changes (#4899)
    https://github.com/python/cpython/commit/9454060e84a669dde63824d9e2fcaf295e34f687

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
