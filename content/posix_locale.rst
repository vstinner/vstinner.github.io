+++++++++++++++++++++++++++++++
Python 3.7 and the POSIX locale
+++++++++++++++++++++++++++++++

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
properly configured, please fix your locale".

I only started to make a shy change for the POSIX locale in Python 3.5 at the
end of 2013: use ``surrogateescape`` for stdin and stdout. We will have to wait
for Nick Coghlan in 2017 for significant changes in Python 3.7.

This article explains the slow transition, **six years** since the first bug
report (2011) to the significant change (2017), from "you must fix your locale"
to "maybe Python can do something for you".

**This article is the fifth in a series of articles telling the history and
rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.6 now uses UTF-8 on Windows <{filename}/windows_utf8.rst>`_
* 5. `Python 3.7 and the POSIX locale <{filename}/posix_locale.rst>`_

.. image:: {filename}/images/bee.jpg
   :alt: Bee
   :target: https://www.flickr.com/photos/rj65/15010849568/

First rejected attempt, 2011
============================

December 2011, **Martin Packman**, a Bazaar developer, reported `bpo-13643
<https://bugs.python.org/issue13643>`__ to propose to use UTF-8 in Python if the
locale encoding is ASCII:

    Currently when running Python on a non-OSX posix environment under either
    the **C locale**, or with an invalid or missing locale, it's **not possible
    to operate using unicode filenames outside the ascii range**. Using bytes
    works, as does reading expecting unicode, using the surrogates hack.

    This makes robustly working with non-ascii filenames on different platforms
    needlessly annoying, given **no modern nix should have problems just using
    UTF-8 in these cases**.

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

and `I added <https://bugs.python.org/issue13643#msg149927>`__:

    The right fix is to **fix your locale, not Python**.

Antoine Pitrou `suggested to fix the operating system, not Python
<https://bugs.python.org/issue13643#msg149949>`__:

    So **why don't these supposedly "modern" systems at least set the
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

Four days and 34 messages later, **Terry J. Reedy**
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

November 2013, **Sworddragon** reported `bpo-19846
<https://bugs.python.org/issue19846>`__: ``LANG=C python3 -c 'print("\xe4")'``
fails with an ``UnicodeEncodeError``.

**Antoine Pitrou** wrote a patch to use UTF-8 when the locale encoding is
ASCII, same approach than the first attempt `bpo-13643
<https://bugs.python.org/issue13643>`__.

**The patch was incomplete and so caused many issues.** Python used the C codec
of the locale encoding during Python initialization, and so Python had to use
the locale encoding as its filesystem encoding.

I listed all functions that should be modified to fix issues and get a fully
working solution. Nobody came up with a full implementation, likely because
**too many changes were required**.

One month and 66 messages (almost the double of the previous attempt) later,
again, `I closed the issue <https://bugs.python.org/issue19846#msg205675>`__:

    I'm closing the issue as invalid, because **Python 3 behaviour is correct**
    and must not be changed.

    Standard streams (sys.stdin, sys.stdout, sys.stderr) uses the locale
    encoding. (...) These encodings and error handlers can be overriden by the
    **PYTHONIOENCODING**.

My `full long comment <https://bugs.python.org/issue19846#msg205675>`_
describes encodings used on each platform.

Use surrogateescape for stdin and stdout in Python 3.5
======================================================

December 2013: Just after closing the second attempt `bpo-19846
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

Previously, **Python 3 was very strict on encodings**, all core developers were
convinced to be able to force developers to fix their applications. This change
is one the **first Python 3 change which can produce "mojibake" on purpose**.

**Six years after the Python 3.0 release, we started to understand that while
developers can fix their code, we cannot ask users to fix their configuration
("fix their locale").**

Read /etc/locale.conf?
======================

April 2014, **Nick Coghlan** created `bpo-21368 <https://bugs.python.org/issue21368>`__: "Check for systemd locale on
startup if current locale is set to POSIX".

    If a modern Linux system is using systemd as the process manager, then
    there will likely be **a "/etc/locale.conf" file** providing settings like
    LANG - due to problematic requirements in the POSIX specification, **this
    file** (when available) is **likely to be a better "source of truth"
    regarding the system encoding** than the environment where the interpreter
    process is started, at least when the latter is claiming ASCII as the
    default encoding.

`I disliked the idea <https://bugs.python.org/issue21368#msg217328>`__:

    I don't think that Python should read such configuration file. If you
    consider that something is wrong here, **please report the issue to the C
    library**.

Since no consensus was found, no action was taken.

Misconfigured locales in Docker images
======================================

September 2016: **Jan Niklas Hasse** opened `bpo-28180
<https://bugs.python.org/issue28180>`__, **"sys.getfilesystemencoding() should
default to utf-8"**.

    **Working with Docker I often end up with an environment where the locale
    isn't correctly set.** In these cases **it would be great if
    sys.getfilesystemencoding() could default to 'utf-8'** instead of
    ``'ascii'``, as it's the encoding of the future and ascii is a subset of it
    anyway.

December 2016, **Jan Niklas Hasse** `mentioned
<https://bugs.python.org/issue28180#msg282972>`__ the ``C.UTF-8`` locale:

    `glibc C.UTF-8 article
    <https://sourceware.org/glibc/wiki/Proposals/C.UTF-8#Defaults>`_ mentions
    that **C.UTF-8 should be glibc's default**.

    This bug report `also mentions Python
    <https://sourceware.org/bugzilla/show_bug.cgi?id=17318>`_. It **hasn't been
    fixed yet**, though :/

**Marc-Andre Lemburg** `added <https://bugs.python.org/issue28180#msg282977>`_:

    If we just restrict this to the file system encoding (and not the whole
    LANG setting), how about:

    * default the file system encoding to 'utf-8' and use the surrogate escape
      handler as default error handler
    * add a ``PYTHONFSENCODING`` env var to set the file system encoding to
      something else (*)

    (*) I believe we discussed this at some point already, but don't remember the outcome.

The removed ``PYTHONFSENCODING`` environment variable, using a filesystem
encoding different than the locale encoding, caused many issues: see `Python
3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`__.

**Nick Coghlan** `proposed to experiment using the C.UTF-8 locale` in Fedora
26:

    **For Fedora 26,** I'm going to explore the feasibility of patching our system
    3.6 installation such that the python3 command itself (rather than the
    shared library) **checks for "LC_CTYPE=C"** as almost the first thing it
    does, and forcibly **sets LANG and LC_ALL to C.UTF-8** if it gets an answer
    it doesn't like. If we're able to do that successfully in the more
    constrained environment of a specific recent Fedora release, then I think
    it will bode well for doing something similar by default in CPython 3.7

    `Downstream Fedora issue proposing the above idea for F26
    <https://bugzilla.redhat.com/show_bug.cgi?id=1404918>`_.

The Fedora 26 `Python 3 C.UTF-8 locale
<https://fedoraproject.org/wiki/Releases/26/ChangeSet#Python_3_C.UTF-8_locale>`_
change was filled and owned by Nick, but it was not completed (Fedora 26 was
released in July 2017).

PEP 538: Coercing the C locale to a UTF-8 based locale
======================================================

.. image:: {filename}/images/nick_coghlan.jpg
   :alt: Nick Coghlan
   :target: http://www.curiousefficiency.org/

December 2016, as a follow-up of `bpo-28180 <https://bugs.python.org/issue28180>`__, **Nick Coghlan** wrote the `PEP
538: Coercing the legacy C locale to a UTF-8 based locale
<https://www.python.org/dev/peps/pep-0538/>`_ and `posted it to python-ideas
list
<https://mail.python.org/pipermail/python-ideas/2017-January/044130.html>`__
and `to the linux-sig list
<https://mail.python.org/pipermail/linux-sig/2017-January/000014.html>`_.

April 2017, Nick `proposed
<https://mail.python.org/pipermail/python-dev/2017-April/147795.html>`__
**INADA Naoki** as the BDFL Delegate for his PEP. Guido `accepted to delegate
<https://mail.python.org/pipermail/python-dev/2017-April/147796.html>`_.

May 2017, after 5 months of discussions and changes, INADA Naoki `approved the
PEP <https://mail.python.org/pipermail/python-dev/2017-May/148035.html>`_.

June 2017, `bpo-28180 <https://bugs.python.org/issue28180>`__: Nick Coghlan
pushed the `commit 6ea4186d
<https://github.com/python/cpython/commit/6ea4186de32d65b1f1dc1533b6312b798d300466>`__:

    bpo-28180: Implementation for PEP 538 (#659)

Conclusion
==========

A first attempt to use a different encoding for the POSIX locale was rejected
in 2011. A second attempt was also rejected in 2013.

I modified Python 3.5 in 2014 to use the ``surrogateescape`` error handler in
``stdin`` and ``stdout`` for the POSIX locale. Six years after the Python 3.0
release, we started to understand that while developers can fix their code, we
cannot ask users to "fix their locale" (configure properly their locale).

In 2016, the problem occurred again with misconfigured locales in Docker
images.  In 2017, Nick Coghlan wrote the PEP 538 "Coercing the legacy C locale
to a UTF-8 based locale" which has been approved by INADA Naoki and implemented
in Python 3.7.
