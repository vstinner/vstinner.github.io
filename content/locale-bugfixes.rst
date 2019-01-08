+++++++++++++++++++++++++++
Locale Bugfixes in Python 3
+++++++++++++++++++++++++++

:date: 2019-01-05 00:20
:tags: unicode, locales
:category: cpython
:slug: locale-bugfixes-python3
:authors: Victor Stinner


Each language and each country has different ways to represent dates, monetary
values, numbers, etc.

See also my previous locale bugfixes: `Python 3, locales and encodings
<{filename}/python3_locales_encodings.rst>`_

Bug 1: non-ascii fill character
===============================

2012-01-03
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

   It seems like I introduced the regression 6 years ago in bpo-13706:

   commit 90f50d4df9e21093f006427fd7ed11a0d704f792
   Author: Victor Stinner <victor.stinner@haypocalc.com>
   Date:   Fri Feb 24 01:44:47 2012 +0100

       Issue #13706: Fix format(float, "n") for locale with non-ASCII decimal point (e.g. ps_aF)


Bug 2: LC_NUMERIC
=================

2017-10-30
https://bugs.python.org/issue31900
localeconv() should decode numeric fields from LC_NUMERIC encoding, not from LC_CTYPE encoding

   bpo-31900: The locale.localeconv() function now sets temporarily the LC_CTYPE locale to the LC_NUMERIC locale to decode decimal_point and thousands_sep byte strings if they are non-ASCII or longer than 1 byte, and the LC_NUMERIC locale is different than the LC_CTYPE locale. This temporary change affects other threads.

   Same change for the str.format() method when formatting a number (int, float, float and subclasses) with the n type (ex: '{:n}'.format(1234)).

https://bugzilla.redhat.com/show_bug.cgi?id=1484497
UnicodeDecodeError in localeconv() makes test_float fail in Koji
Petr Viktorin 2017-08-23 17:58:16 UTC

   "This is tripped by Python's test suite, namely
   test_float.GeneralFloatCases.test_float_with_comma"


Bug 3: LC_MONETARY
==================

2016-11-03
bpo-28604: locale.localeconv() now sets temporarily the LC_CTYPE locale to the LC_MONETARY locale if the two locales are different and monetary strings are non-ASCII. This temporary change affects other threads.
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
