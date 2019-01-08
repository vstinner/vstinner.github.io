+++++++++++++++++++++++++++
Locale Bugfixes in Python 3
+++++++++++++++++++++++++++

:date: 2019-01-09 00:30
:tags: unicode, locales
:category: cpython
:slug: locale-bugfixes-python3
:authors: Victor Stinner

This article describes a few locales bugs that I fixed in Python 3:

* Support non-ASCII decimal point and thousands separator
* Crash with non-ASCII decimal point
* LC_NUMERIC encoding different than LC_CTYPE encoding
* LC_MONETARY encoding different than LC_CTYPE encoding
* Tests non-ASCII locales

See also my previous locale bugfixes: `Python 3, locales and encodings
<{filename}/python3_locales_encodings.rst>`_

Introduction
============

Each language and each country has different ways to represent dates, monetary
values, numbers, etc. Unix has "locales" to configure applications for a
specific language and a specific country. For example, there are ``fr_BE`` for
Belgium (french) and ``fr_FR`` for France (french).

In practice, each locale uses its own encoding and problems arise when an
application uses a different encoding than the locale. There are LC_NUMERIC
locale for numbers, LC_MONETARY locale for monetary and LC_CTYPE for the
encoding. Not only it's possible to configure an application to use LC_NUMERIC
with a different encoding than LC_CTYPE, but some users use such configuration!

In an application which only uses bytes for text, as Python 2 does mostly, it's
mostly fine: in the worst case, users see `mojibake
<https://en.wikipedia.org/wiki/Mojibake>`__, but the application doesn't
"crash" (exit and/or data loss). On the other side, **Python 3 is designed to
use Unicode for text and fail with hard Unicode errors if it fails to decode
bytes and fails to encode text**.

Support non-ASCII decimal point and thousands separator
=======================================================

The Unicode type has been reimplemented in Python 3.3 to use "compact string":
`PEP 393 "Flexible String Representation"
<https://www.python.org/dev/peps/pep-0393/>`__. The new implementation is more
complex and the format() function has been limited to ASCII for the decimal
point and thousands separator (format a number using the "n" type).

In January 2012, Stefan Krah noticed the regression (compared to Python 3.2)
and reported `bpo-13706 <https://bugs.python.org/issue13706>`__. I fixed the
code to support non-ASCII in format (`commit a4ac600d
<https://github.com/python/cpython/commit/a4ac600d6f9c5b74b97b99888b7cf3a7973cadc8>`__).
But when I did more tests, I noticed that the "n" type doesn't decode properly
the decimal point and thousands seprator which come from the ``localeconv()``
function which uses byte strings.

The first locale issue fix was `commit 41a863cb
<https://github.com/python/cpython/commit/41a863cb81608c779d60b49e7be8a115816734fc>`__
in Python 3.3 to use the decode from the correct encoding::

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

The main change is that the decimal point and the thousands separator are now
decoded from the locale encoding by ``PyUnicode_DecodeLocale()``.

Note: I decided to not fix Python 3.2:

   Hum, it is not trivial to redo the work on Python 3.2. I prefer to leave the
   code unchanged to not introduce a regression, and I wait until a Python 3.2
   user complains (the bug exists since Python 3.0 and nobody complained).


Crash with non-ASCII decimal point
==================================

Six years later, June 2018, I noticed that Python does crash when running tests
on locales::

   $ ./python
   Python 3.8.0a0 (heads/master-dirty:bcd3a1a18d, Jun 23 2018, 10:31:03)
   [GCC 8.1.1 20180502 (Red Hat 8.1.1-1)] on linux
   >>> import locale
   >>> locale.str(2.5)
   '2.5'
   >>> '{:n}'.format(2.5)
   '2.5'
   >>> locale.setlocale(locale.LC_ALL, '')
   'fr_FR.UTF-8'
   >>> locale.str(2.5)
   '2,5'
   >>> '{:n}'.format(2.5)
   python: Objects/unicodeobject.c:474: _PyUnicode_CheckConsistency: Assertion `maxchar < 128' failed.
   Aborted (core dumped)

I opened the issue `bpo-33954 <https://bugs.python.org/issue33954>`__. The bug
only occurred for decimal point larger than U+00FF (code point greater than
255). It was a bug in my fix (`commit a4ac600d
<https://github.com/python/cpython/commit/a4ac600d6f9c5b74b97b99888b7cf3a7973cadc8>`__)
for `bpo-13706 <https://bugs.python.org/issue13706>`__.

I pushed a second fix to properly support all cases, `commit 59423e3d
<https://github.com/python/cpython/commit/59423e3ddd736387cef8f7632c71954c1859bed0>`__::

   commit 59423e3ddd736387cef8f7632c71954c1859bed0
   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Mon Nov 26 13:40:01 2018 +0100

       bpo-33954: Fix _PyUnicode_InsertThousandsGrouping() (GH-10623)

       Fix str.format(), float.__format__() and complex.__format__() methods
       for non-ASCII decimal point when using the "n" formatter.

       Changes:

       * Rewrite _PyUnicode_InsertThousandsGrouping(): it now requires
         a _PyUnicodeWriter object for the buffer and a Python str object
         for digits.
       * Rename FILL() macro to unicode_fill(), convert it to static inline function,
         add "assert(0 <= start);" and rework its code.


LC_NUMERIC encoding different than LC_CTYPE encoding
====================================================

In August 2017, Petr Viktorin identified a bug in Koji (server building Fedora
packages): `UnicodeDecodeError in localeconv() makes test_float fail in Koji
<https://bugzilla.redhat.com/show_bug.cgi?id=1484497>`_

   "This is tripped by Python's test suite, namely
   test_float.GeneralFloatCases.test_float_with_comma"

He wrote a short reproducer script::

   import locale
   locale.setlocale(locale.LC_ALL, 'C.UTF-8')
   locale.setlocale(locale.LC_NUMERIC, 'fr_FR.ISO8859-1')
   print(locale.localeconv())

Two months later, Charalampos Stratakis reported the bug upstream: `bpo-31900
<https://bugs.python.org/issue31900>`__.  The problem arises when **the
LC_NUMERIC locale uses a different encoding than the LC_CTYPE encoding**.

In fact, the bug was already known:

* 2015-12-05: Serhiy Storchaka reported `bpo-25812
  <https://bugs.python.org/issue25812>`__ with uk_UA locale
* 2016-11-03: Guillaume Pasquet reported `bpo-28604
  <https://bugs.python.org/issue28604>`__ with en_GB locale

In fact, the bug was known since 2009, Stefan Krah reported a very similar bug
(LC_NUMERIC locale using an encoding different than the LC_CTYPE locale
encoding): `bpo-7442 <https://bugs.python.org/issue7442>`__. I was even
involved in this issue in 2013, but then I forgot about it.

In 2010, PostgreSQL `had the same issue
<https://www.postgresql.org/message-id/20100422015552.4B7E07541D0@cvs.postgresql.org>`__
and `fixed the bug by changing temporarily the LC_CTYPE locale to the
LC_NUMERIC locale
<https://anoncvs.postgresql.org/cvsweb.cgi/pgsql/src/backend/utils/adt/pg_locale.c?r1=1.53&r2=1.54>`__.

In January 2018, I came back to this 9 years old bug. I was fixing bugs in the
implementation of my `PEP 540 "Add a new UTF-8 Mode"
<https://www.python.org/dev/peps/pep-0540/>`__. I pushed a large change to fix
locale encodings in `bpo-29240 <https://bugs.python.org/issue29240>`__, `commit
7ed7aead
<https://github.com/python/cpython/commit/7ed7aead9503102d2ed316175f198104e0cd674c>`__::

   commit 7ed7aead9503102d2ed316175f198104e0cd674c
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 15 10:45:49 2018 +0100

       bpo-29240: Fix locale encodings in UTF-8 Mode (#5170)

       Modify locale.localeconv(), time.tzname, os.strerror() and other
       functions to ignore the UTF-8 Mode: always use the current locale
       encoding.

       Changes: (...)

Stefan Krah asked:

   I have the exact same questions as Marc-Andre.  This is one of the reasons
   why I blocked the _decimal change.  I don't fully understand the role of the
   new glibc, since #7442 has existed for ages -- and **it is a open question
   whether it is a bug or not**.

I replied (to Marc-Andre Lemburg):

   Past 10 years, I repeated to every single user I met that "Python 3 is
   right, your system setup is wrong". But that's a waste of time. People
   continue to associate Python3 and Unicode to annoying bugs, because they
   don't understand how locales work.

   Instead of having to repeat to each user that "hum, maybe your config is
   wrong", **I prefer to support this non convential setup and work as expected
   ("it just works")**. With my latest implementation, setlocale() is only done
   when LC_CTYPE and LC_NUMERIC are different, which is the corner case which
   "shouldn't occur in practice".

Marc-Andre Lemburg added:

   Sounds like a good compromise :-)

After doing more tests on FreeBSD, Linux and macOS, I pushed `commit cb064fc2
<https://github.com/python/cpython/commit/cb064fc2321ce8673fe365e9ef60445a27657f54>`__
to fix `bpo-31900 <https://bugs.python.org/issue31900>`__ by changing
temporarily the LC_CTYPE locale to the LC_NUMERIC locale::

   commit cb064fc2321ce8673fe365e9ef60445a27657f54
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 15 15:58:02 2018 +0100

       bpo-31900: Fix localeconv() encoding for LC_NUMERIC (#4174)

       * Add _Py_GetLocaleconvNumeric() function: decode decimal_point and
         thousands_sep fields of localeconv() from the LC_NUMERIC encoding,
         rather than decoding from the LC_CTYPE encoding.
       * Modify locale.localeconv() and "n" formatter of str.format() (for
         int, float and complex to use _Py_GetLocaleconvNumeric()
         internally.

I dislike my own fix because changing temporarily the LC_CTYPE locale impacts
all threads, not only the current thread. But we failed to find another
solution. **The LC_CTYPE locale is only changed if the LC_NUMERIC locale is
different than the LC_CTYPE locale and if the decimal point or the thousands
separator is non-ASCII.**

Note: I proposed a change to fix the same bug in the ``decimal`` module: `PR
#5191 <https://github.com/python/cpython/pull/5191>`__, but Stefan Krah
rejected my fix.

LC_MONETARY encoding different than LC_CTYPE encoding
=====================================================

Fixing `bpo-31900 <https://bugs.python.org/issue31900>`__ drained my energy,
but sadly there was a similar bug with LC_MONETARY.

At 2016-11-03, Guillaume Pasquet reported `bpo-28604: Exception raised by
python3.5 when using en_GB locale <https://bugs.python.org/issue28604>`__.

The fix is similar than the LC_NUMERIC fix: change temporarily the LC_CTYPE
locale to the LC_MONETARY locale, `commit 02e6bf7f
<https://github.com/python/cpython/commit/02e6bf7f2025cddcbde6432f6b6396198ab313f4>`__::

   commit 02e6bf7f2025cddcbde6432f6b6396198ab313f4
   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Tue Nov 20 16:20:16 2018 +0100

       bpo-28604: Fix localeconv() for different LC_MONETARY (GH-10606)

       locale.localeconv() now sets temporarily the LC_CTYPE locale to the
       LC_MONETARY locale if the two locales are different and monetary
       strings are non-ASCII. This temporary change affects other threads.

       Changes:

       * locale.localeconv() can now set LC_CTYPE to LC_MONETARY to decode
         monetary fields.
       * (...)


Tests non-ASCII locales
=======================

To test my bugfixes, I used manual tests. The first issue was to identify
locales with problematic characters: non-ASCII decimal point or thousands
separator for example. I wrote my own "test suite" for Windows, Linux, macOS
and FreeBSD on my website: `Test non-ASCII characters with locales
<https://vstinner.readthedocs.io/unicode.html#test-non-ascii-characters-with-locales>`__.

Example with localeconv() on Fedora 27:

==============  ========  ===============  ========================  ===================================
LC_ALL locale   Encoding  Field            Bytes                     Text
==============  ========  ===============  ========================  ===================================
es_MX.utf8      UTF-8     thousands_sep    ``0xE2 0x80 0x89``        U+2009
fr_FR.UTF-8     UTF-8     currency_symbol  ``0xE2 0x82 0xAC``        U+20AC (€)
ps_AF.utf8      UTF-8     thousands_sep    ``0xD9 0xAC``             U+066C (٬)
uk_UA.koi8u     KOI8-U    currency_symbol  ``0xC7 0xD2 0xCE 0x2E``   U+0433 U+0440 U+043d U+002E (грн.)
uk_UA.koi8u     KOI8-U    thousands_sep    ``0x9A``                  U+00A0
==============  ========  ===============  ========================  ===================================

Manual tests became more and more complex, since there are so many cases: each
operating system use different locale names and the result depends on the libc
version. After months of manual tests, I wrote my small personal **portable**
locale test suite: `test_all_locales.py
<https://github.com/vstinner/misc/blob/master/python/test_all_locales.py>`_.
It supports:

* FreeBSD 11
* macOS
* Fedora (Linux)

Example::

    def test_zh_TW_Big5(self):
        loc = "zh_TW.Big5" if BSD else "zh_TW.big5"
        if FREEBSD:
            currency_symbol = u'\uff2e\uff34\uff04'
            decimal_point = u'\uff0e'
            thousands_sep = u'\uff0c'
            date_str = u'\u661f\u671f\u56db 2\u6708'
        else:
            currency_symbol = u'NT$'
            decimal_point = u'.'
            thousands_sep = u','
            if MACOS:
                date_str =  u'\u9031\u56db 2\u6708'
            else:
                date_str = u'\u9031\u56db \u4e8c\u6708'

        self.set_locale(loc, "Big5")

        lc = locale.localeconv()
        self.assertLocaleEqual(lc['currency_symbol'], currency_symbol)
        self.assertLocaleEqual(lc['decimal_point'], decimal_point)
        self.assertLocaleEqual(lc['thousands_sep'], thousands_sep)

        self.assertLocaleEqual(time.strftime('%A %B', FEBRUARY), date_str)

The best would be to integrate directly these tests into the Python test suite,
but it's not portable nor future-proof, since most constants are hardcoded and
depends on the operating sytem and the libc version.
