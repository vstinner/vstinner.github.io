+++++++++++++++++++++++++++
Locale Bugfixes in Python 3
+++++++++++++++++++++++++++

:date: 2019-01-05 00:20
:tags: unicode, locales
:category: cpython
:slug: locale-bugfixes-python3
:authors: Victor Stinner

Each language and each country has different ways to represent dates, monetary
values, numbers, etc. Unix has "locales" to configure applications for a
specific language and a specific country. For example, there are fr_BE for
Belgium (french) and fr_FR for France (french) locales.

In practice, each locale uses its own encoding and problems arise when an
application uses a different encoding than the locale. There are LC_NUMERIC
locale for numbers, LC_MONETARY locale for monetary and LC_CTYPE for the
encoding. Not only it's possible to configure an application to use LC_NUMERIC
with a different encoding than LC_CTYPE, but some users use such configuration!

In an application which only uses bytes for text, as Python 2 does mostly, it's
mostly fine: in the worst case, users see mojibake, but the application doesn't
"crash" (exit and/or data loss). On the other side, Python 3 is designed to use
Unicode for text and fail with hard Unicode errors if it fails to decode bytes
and fails to encode text.

This article describes 3 locale bugs that I fixed in Python 3.

See also my previous locale bugfixes: `Python 3, locales and encodings
<{filename}/python3_locales_encodings.rst>`_

Bug 1: non-ascii fill character
===============================

January 2012, I fixed the first locale issue in Python 3.3: `bpo-13706
<https://bugs.python.org/issue13706>`__ and `commit 41a863cb
<https://github.com/python/cpython/commit/41a863cb81608c779d60b49e7be8a115816734fc>`__::

   commit 41a863cb81608c779d60b49e7be8a115816734fc
   Author: Victor Stinner <victor.stinner@haypocalc.com>
   Date:   Fri Feb 24 00:37:51 2012 +0100

       Issue #13706: Fix format(int, "n") for locale with non-ASCII thousands separator

        * Decode thousands separator and decimal point using PyUnicode_DecodeLocale()
          (from the locale encoding), instead of decoding them implicitly from latin1
        * Remove _PyUnicode_InsertThousandsGroupingLocale(), it was not used
        * Change _PyUnicode_InsertThousandsGrouping() API to return the maximum
          character if unicode is NULL
        * Replace MIN/MAX macros by Py_MIN/Py_MAX
        * stringlib/undef.h undefines STRINGLIB_IS_UNICODE
        * stringlib/localeutil.h only supports Unicode


https://bugs.python.org/issue13706
non-ascii fill characters no longer work in formatting


Bug 1 reoccurs: Crash on formatting a number with the locale
============================================================

Six years later.. the bug comes back...

2018-06-25
float.__format__('n') fails with _PyUnicode_CheckConsistency assertion error for locales with non-ascii thousands separator
https://bugs.python.org/issue33954

Aha, the problem occurs when the thousands separator code point is greater than 255.

Ref::

   It seems like I introduced the regression 6 years ago in `bpo-13706 <https://bugs.python.org/issue13706>`__:

   `commit 90f50d4d <https://github.com/python/cpython/commit/90f50d4df9e21093f006427fd7ed11a0d704f792>`__
   Author: Victor Stinner <victor.stinner@haypocalc.com>
   Date:   Fri Feb 24 01:44:47 2012 +0100

       Issue #13706: Fix format(float, "n") for locale with non-ASCII decimal point (e.g. ps_aF)


Bug 2: LC_NUMERIC
=================

2017-10-30
https://bugs.python.org/issue31900
localeconv() should decode numeric fields from LC_NUMERIC encoding, not from LC_CTYPE encoding

   `bpo-31900 <https://bugs.python.org/issue31900>`__: The locale.localeconv() function now sets temporarily the LC_CTYPE locale to the LC_NUMERIC locale to decode decimal_point and thousands_sep byte strings if they are non-ASCII or longer than 1 byte, and the LC_NUMERIC locale is different than the LC_CTYPE locale. This temporary change affects other threads.

   Same change for the str.format() method when formatting a number (int, float, float and subclasses) with the n type (ex: '{:n}'.format(1234)).

https://bugzilla.redhat.com/show_bug.cgi?id=1484497
UnicodeDecodeError in localeconv() makes test_float fail in Koji
Petr Viktorin 2017-08-23 17:58:16 UTC

   "This is tripped by Python's test suite, namely
   test_float.GeneralFloatCases.test_float_with_comma"


Bug 3: LC_MONETARY
==================

2016-11-03
`bpo-28604 <https://bugs.python.org/issue28604>`__: locale.localeconv() now sets temporarily the LC_CTYPE locale to the LC_MONETARY locale if the two locales are different and monetary strings are non-ASCII. This temporary change affects other threads.
https://bugs.python.org/issue28604

   After switching the monetary locale to en_GB, python then raises an exception when calling locale.localeconv()

Bug 1391280 - Exception raised by python3.5 when using en_GB locale
https://bugzilla.redhat.com/show_bug.cgi?id=1391280
Guillaume Pasquet 2016-11-02 22:45:28 UTC


Tests
=====

I started with manual tests. My first issue was to identify locales with
problematic characters. I wrote my own "test suite" for Windows, Linux, macOS
and FreeBSD:

https://vstinner.readthedocs.io/unicode.html#test-non-ascii-characters-with-locales

Tested on??:

* Fedora
* macOS
* FreeBSD
* Windows???


Manual tests became more and more complex, since there are so many cases, each
OS has a different locale name and different expected result. So I wrote my own
test suite:

https://github.com/vstinner/misc/blob/master/python/test_all_locales.py

Sadly, I don't think that it's possible to integrate these tests into Python
test suite since the tests depending on the libc version and the operating
system.
