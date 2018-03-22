+++++++++++++++++++++++++
Python 3.7 New UTF-8 Mode
+++++++++++++++++++++++++

:date: 2018-03-16 23:08
:tags: cpython
:category: python
:slug: python37-new-utf8-mode
:authors: Victor Stinner

**This article is the fourth and last in a series of articles telling the
history and rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.7 New UTF-8 Mode <{filename}/utf8_mode.rst>`_

Introduction
============

Since Python 3.0 was released in 2008, each time an user reports an encoding
issue, someone shows up and asks why Python does not simply always use UTF-8.
Well, it's not that easy. UTF-8 is the best encoding in most cases, but it is
still not the best encoding in all cases, even in 2018.

The locale encoding remains the best **default** filesystem encoding for
Python. I would say that **the locale encoding is the least bad choice**.

Option -X utf8
==============

August 2016, bpo-27781: "Change sys.getfilesystemencoding() on Windows to UTF-8".
When I was afraid that
changing the encoding from the ANSI code page to UTF-8 on Windows would break
all applications, `I proposed to make the change as an opt-in option, -X utf8
<https://bugs.python.org/issue27781#msg272916>`_:

    Would it be acceptable for you to add a new option to switch to UTF-8 in
    Python 3.6, and discuss later if it's ok to enable it by default?

`I added <https://bugs.python.org/issue27781#msg272950>`_:

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

One week later, I implemented my PEP 540: bpo-29240, and `I wrote a third
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


