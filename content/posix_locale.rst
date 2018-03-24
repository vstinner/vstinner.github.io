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

2011-12-24, **Terry J. Reedy** `closed the issue
<https://bugs.python.org/issue13643#msg150204>`__:

    Martin, after reading most all of the **unusually large sequence of
    messages**, I am closing this because **three of the core developers** with
    the most experience in this area are **dead-set against your proposal**.

    That does not make it 'wrong', but does mean that it will not be approved
    and implemented without new data and more persuasive arguments than those
    presented so far. I do not see that continued repetition of what has been
    said so far will change anything.

The issue got a total of 34 messages in 4 days, and two more years later.  Many
messages in short time is something common when discussing Unicode issues :-)

March 2011, **Armin Ronacher** and **Carl Meyer** reported a similar issue:
`bpo-11574 <https://bugs.python.org/issue11574>`__ and `[Python-Dev] Low-Level Encoding Behavior on Python 3
<https://mail.python.org/pipermail/python-dev/2011-March/109361.html>`_.  I
closed the issue as "wont fixed" in April 2012.

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

Mar 18 2014, I pushed my `commit 7143029d <https://github.com/python/cpython/commit/7143029d4360637aadbd7ddf386ea5c64fb83095>`__:

    Issue #19977: When the ``LC_TYPE`` locale is the POSIX locale (``C``
    locale), ``sys.stdin`` and ``sys.stdout`` are now using the
    ``surrogateescape`` error handler, instead of the ``strict`` error handler.

History
=======

2016-09-16: `bpo-28180 <https://bugs.python.org/issue28180>`__, "sys.getfilesystemencoding() should default to utf-8".

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

