++++++++++++
POSIX locale
++++++++++++

:date: 2018-03-23 13:00
:tags: cpython
:category: python
:slug: posix-locale
:authors: Victor Stinner

During the childhood of Python 3, encodings issues were common, even on well
configured systems. Python used UTF-8 rather than the locale encoding, and so
commonly produced `mojibake <https://en.wikipedia.org/wiki/Mojibake>`_. For
these reasons, when users complained about the Python behaviour with the POSIX
locale, bug reports were closed with a message like: "your system is not
correctly configured, please fix your locale".

I only started to make a shy change in Python 3.5 for the POSIX locale at the
end of 2013 (Python 3.5 was released in 2015). We will have to wait for Nick
Coghlan for significant changes in Python 3.7 (commit in 2017, released
scheduled in 2018).

**This article is the fifth in a series of articles telling the history and
rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.6 now uses UTF-8 on Windows <{filename}/windows_utf8.rst>`_

First rejected attempt, 2011
============================

December 2011, **Martin Packman**, a Bazaar developer, reported `bpo-13643
<https://bugs.python.org/issue13643>`__ proposed to use UTF-8 in Python if the
locale encoding is ASCII:

    Currently when running Python on a non-OSX posix environment under either
    the **C locale**, or with an invalid or missing locale, it's **not possible
    to operate using unicode filenames outside the ascii range**. Using bytes
    works, as does reading expecting unicode, using the surrogates hack.

    This makes robustly working with non-ascii filenames on different platforms
    needlessly annoying, given no modern nix should have problems just using
    UTF-8 in these cases.

    See the `downstream bzr bug for more
    <https://bugs.launchpad.net/bzr/+bug/794353>`__.

    One option is to **just use UTF-8** for encoding and decoding filenames
    **when otherwise ascii would be used**. As a strict superset, this
    shouldn't break too many existing assumptions, and **it's unlikely that
    non-UTF-8 filenames will accidentally be mangled due to a locale setting
    blip.** See the attached patch for this behaviour change. It does not
    include a test currently, but it's possible to write one using subprocess
    and overriden ``LANG`` and ``LC_ALL`` vars.

`He added <https://bugs.python.org/issue13643#msg149928>`__:

    This is more about **un-encodable filenames**.

    At the moment work with non-ascii filenames in Python robustly requires two
    branches, one using unicode and one that encodes to bytestrings and deals
    with the case where the name can't be represented in the declared
    filesystem encoding.

    **That may be something that just had to be lived with**, but it's a little
    annoying when even without a UTF-8 locale for a particular process, that's
    what most systems will want on disk.

At this time, I was still traumatised by the ``PYTHONFSENCODING`` mess: using a
filesystem encoding different than the locale encoding caused many issues (see
`Python 3.2 Painful History of the Filesystem Encoding
<{filename}/fs_encoding.rst>`__). `I wrote
<https://bugs.python.org/issue13643#msg149926>`__:

    It was already discussed: using a different encoding for filenames and for
    other things is really not a good idea. (...)

`I added <https://bugs.python.org/issue13643#msg149927>`__:

    The right fix is to **fix your locale, not Python**.

Antoine Pitrou `suggested to fix the operating system, not Python
<https://bugs.python.org/issue13643#msg149949>`__:

    So why don't these supposedly "modern" systems at least **set the
    appropriate environment variables** for Python to infer the proper
    character encoding?  (since these "modern" systems don't have a
    well-defined encoding...)

    Answer: because they are not modern at all, **they are antiquated,
    inadapted and obsolete pieces of software designed and written by clueless
    Anglo-American people**. Please report bugs against these systems. **The
    culprit is not Python, it's the Unix crap** and the utterly clueless
    attitude of its maintainers ("filesystems are just bytes", yeah,
    whatever...).

**Martin Pool** `wrote <https://bugs.python.org/issue13643#msg149951>`__:

    The standard encoding is UTF-8. Python shouldn't need to have a variable
    set to tell it this.

`Antoine replied <https://bugs.python.org/issue13643#msg149952>`__:

    How so? I don't know of any Linux or Unix spec which says so.

Four days after the issue creation and 34 messages later, **Terry J. Reedy**
`closed the issue <https://bugs.python.org/issue13643#msg150204>`__:

    Martin, after reading most all of the **unusually large sequence of
    messages**, I am closing this because **three of the core developers** with
    the most experience in this area are **dead-set against your proposal**.

    That does not make it 'wrong', but does mean that it will not be approved
    and implemented without new data and more persuasive arguments than those
    presented so far. I do not see that continued repetition of what has been
    said so far will change anything.

Getting many messages in short time is common when discussing Unicode issues
:-)

March 2011, **Armin Ronacher** and **Carl Meyer** reported a similar issue:
`bpo-11574 <https://bugs.python.org/issue11574>`__ and `[Python-Dev] Low-Level Encoding Behavior on Python 3
<https://mail.python.org/pipermail/python-dev/2011-March/109361.html>`_.  I
closed the issue as "wont fixed" in April 2012.

Second attempt, 2013
====================

November 2013, **Sworddragon** reported a "simple" bug, `bpo-19846
<https://bugs.python.org/issue19846>`__:

    ``LANG=C python3 -c 'print("\xe4")'`` fails with an ``UnicodeEncodeError``.

**Antoine Pitrou** wrote a patch to use UTF-8 when the locale encoding is
ASCII, same approach than `bpo-13643 <https://bugs.python.org/issue13643>`__
(closed in December 2011).

The patch was incomplete and so caused many issues. Python used the C codec of
the locale encoding during Python initialization, and so Python had to use the
locale encoding as its filesystem encoding.

I listed all functions that should be modified to fix issues and get a fully
working solution. Nobody came up with a full implementation, likely because too
many changes were required.

One month and 66 messages (almost the double of the previous attempt) later, `I
closed the issue <https://bugs.python.org/issue19846#msg205675>`__:

    I'm closing the issue as invalid, because Python 3 behaviour is correct and
    must not be changed.

    Standard streams (sys.stdin, sys.stdout, sys.stderr) uses the locale
    encoding. (...) These encodings and error handlers can be overriden by the
    **PYTHONIOENCODING**.

My `full comment <https://bugs.python.org/issue19846#msg205675>`_ describes
encodings used on each platform.

Use surrogateescape for stdin and stdout in Python 3.5
======================================================

December 2013: Just after closing `bpo-19846
<https://bugs.python.org/issue19846>`__, I created `bpo-19977
<https://bugs.python.org/issue19977>`__ to propose to use the
``surrogateescape`` error handler in ``sys.stdin`` and ``sys.stdout`` for the
POSIX locale.

**R. David Murray** `disliked my idea <https://bugs.python.org/issue19977#msg206131>`_:

    **Reintroducing moji-bake intentionally doesn't sound like a particularly
    good idea**, wasn't that what python3 was supposed to help prevent?

    It does seem like a **utf-8 default is the Way of the Future**. Or even the
    present, most places.

March 2014, since **Serhiy Storchaka** and **Nick Coghlan** supported my idea,
I pushed my `commit 7143029d
<https://github.com/python/cpython/commit/7143029d4360637aadbd7ddf386ea5c64fb83095>`__
in Python 3.5:

    Issue #19977: When the ``LC_TYPE`` locale is the POSIX locale (``C``
    locale), ``sys.stdin`` and ``sys.stdout`` are now using the
    ``surrogateescape`` error handler, instead of the ``strict`` error handler.

History
=======

September 2016: **Jan Niklas Hasse** opened `bpo-28180
<https://bugs.python.org/issue28180>`__, **"sys.getfilesystemencoding() should
default to utf-8"**.

    Working with Docker I often end up with an environment where the locale
    isn't correctly set. In these cases it would be great if
    ``sys.getfilesystemencoding()`` could default to ``'utf-8'`` instead of
    ``'ascii'``, as it's the encoding of the future and ascii is a subset of it
    anyway.

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

XXX 82 messages.
