++++++++++++
POSIX locale
++++++++++++

:date: 2018-03-23 13:00
:tags: cpython
:category: python
:slug: posix-locale
:authors: Victor Stinner


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

