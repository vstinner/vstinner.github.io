+++++++++++++++++++++++++++++++
Python 3, locales and encodings
+++++++++++++++++++++++++++++++

:date: 2018-09-06 16:00
:tags: unicode, locales
:category: cpython
:slug: python3-locales-encodings
:authors: Victor Stinner

Recently, I worked on a change which looked simple: move the code to initialize
the ``sys.stdout`` encoding before ``Py_Initialize()``. While I was on it,
I also decided to move the code which selects the Python "filesystem encoding".
I didn't expect that I would spend 2 weeks on these issues... This article
tells me about my recent journey in locales and encodings on AIX, HP-UX,
Windows, Linux, macOS, Solaris and FreeBSD.

.. image:: {static}/images/i-square-unicode.jpg
   :alt: I □ Unicode

Table of Contents:

* Lying HP-UX
* Standard streams and filesystem encodings
* POSIX locale on FreeBSD
* C locale on Windows
* Back to stdio encoding
* Back to filesystem encoding
* Use surrogatepass on Windows
* Filesystem encoding documentation
* Final FreeBSD 10 issue
* Configuration of locales and encodings


Lying HP-UX
===========

At 2018-08-14, Michael Osipov reported `bpo-34403 <https://bugs.python.org/issue34403>`__:
"test_utf8_mode.test_cmd_line() fails on HP-UX due to false assumptions"::

   ======================================================================
   FAIL: test_cmd_line (test.test_utf8_mode.UTF8ModeTests)
   ----------------------------------------------------------------------
   Traceback (most recent call last):
     (...)
   AssertionError: "['h\\xc3\\xa9\\xe2\\x82\\xac']" != "['h\\udcc3\\udca9\\udce2\\udc82\\udcac']"
   - ['h\xc3\xa9\xe2\x82\xac']
   + ['h\udcc3\udca9\udce2\udc82\udcac']
    : roman8:['h\xc3\xa9\xe2\x82\xac']

Interesting, HP-UX uses "roman8" as its locale encoding. What is this "new"
encoding? Wikipedia: `HP Roman-8
<https://en.wikipedia.org/wiki/HP_Roman#Roman-8>`_. Oh, that's even older than
the common ISO 8859 encodings like Latin1!

Michael Felt was working on a similar test_utf8_mode failure on AIX, so they
tried to debug the issue together, but failed to understand the issue. Osipov
proposed to give up and just skip the test on HP-UX...

I showed up and proposed a fix for the unit test: `PR 8967
<https://github.com/python/cpython/pull/8967/files>`_. The test was hardcoding
the expected locale encoding. I modified the test to query the locale encoding
at runtime instead.

Bad surprise, the test still fails, oh. `I commented
<https://bugs.python.org/issue34403#msg324219>`_:

   Hum, it looks like a bug in the C library of HP-UX.

I wrote a C program calling mbstowcs() to check what is the actual encoding
used by the C library: `c_locale.c
<https://bugs.python.org/file47767/c_locale.c>`__. `Result
<https://bugs.python.org/issue34403#msg324225>`_:

   Well, it confirms what I expected: ``nl_langinfo(CODESET)`` announces
   ``"roman8"``, but ``mbstowcs()`` uses Latin1 encoding in practice.

So I wrote a workaround similar to the one used on FreeBSD and Solaris: check
if the libc is announcing an encoding different than the real encoding, and if
it's the case: force the usage of the ASCII encoding in Python. See
my `commit d500e530 <https://github.com/python/cpython/commit/d500e5307aec9c5d535f66d567fadb9c587a9a36>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Tue Aug 28 17:27:36 2018 +0200

       bpo-34403: On HP-UX, force ASCII for C locale (GH-8969)

       On HP-UX with C or POSIX locale, sys.getfilesystemencoding() now returns
       "ascii" instead of "roman8" (when the UTF-8 Mode is disabled and the C locale
       is not coerced).

       nl_langinfo(CODESET) announces "roman8" whereas it uses the Latin1
       encoding in practice.

Extract of the heuristic code::

    if (strcmp(encoding, "roman8") == 0) {
        unsigned char ch = (unsigned char)0xA7;
        wchar_t wch;
        size_t res = mbstowcs(&wch, (char*)&ch, 1);
        if (res != (size_t)-1 && wch == L'\xA7') {
            /* On HP-UX withe C locale or the POSIX locale,
               nl_langinfo(CODESET) announces "roman8",
               whereas mbstowcs() uses Latin1 encoding in practice.
               Force ASCII in this case.  Roman8 decodes 0xA7
               to U+00CF. Latin1 decodes 0xA7 to U+00A7. */
            return 1;
        }
    }

Python 3.8 will handle better Unicode support on HP-UX. The test_utf8_mode
failure was just a hint for a real underlying bug!

Standard streams and filesystem encodings
=========================================

While reworking the Python initialization, I tried to move **all**
configuration parameters to a new ``_PyCoreConfig`` structure. But I know that
I missed at least the standard streams encoding (ex: ``sys.stdout.encoding``).
My first attempt failed to move the code, it broke many tests. I created
`bpo-34485 <https://bugs.python.org/issue34485>`__: "_PyCoreConfig: add
stdio_encoding and stdio_errors".

While I was working on stdio encoding, I also recalled that the Python
filesystem encoding is also initialized "late". I also created `bpo-34523
<https://bugs.python.org/issue34523>`__: "Choose the filesystem encoding before
Python initialization (add _PyCoreConfig.filesystem_encoding)" to move this
code as well.

I quickly had an implementation, but it didn't go as well as expected...


POSIX locale on FreeBSD
=======================

`bpo-34485 <https://bugs.python.org/issue34485>`__: For me, the "C" and "POSIX"
locales were the same locale: C is an alias to POSIX, or the opposite, it
didn't really matter for me. But Python handles them differently in some corner
cases. For example, Nick Coghlan's PEP 538 (C locale coercion) is only enabled
if the LC_CTYPE locale is equal to "C", not if it's equal to "POSIX".

In Python 3.5, I changed stdin and stdout error handlers from strict to
surrogateescape if the LC_CTYPE locale is "C": `bpo-19977 <https://bugs.python.org/issue19977>`__. But when I tested my
stdio and filesystem changes on Linux, FreeBSD and Windows, I noticed that
I forgot to handle the "POSIX" locale. On FreeBSD, ``LC_ALL=POSIX`` and ``LC_ALL=C``
behave differently:

* With ``LC_ALL=POSIX`` environment, ``setlocale(LC_CTYPE, "")`` returns ``"POSIX"``
* With ``LC_ALL=C`` environment, ``setlocale(LC_CTYPE, "")`` returns ``"C"``

I fixed that to also use the "surrogateescape" error handler for the POSIX
locale on FreeBSD. `Commit 315877dc
<https://github.com/python/cpython/commit/315877dc361d554bec34b4b62c270479ad36a1be>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Wed Aug 29 09:58:12 2018 +0200

       bpo-34485: stdout uses surrogateescape on POSIX locale (GH-8986)

       Standard streams like sys.stdout now use the "surrogateescape" error
       handler, instead of "strict", on the POSIX locale (when the C locale is not
       coerced and the UTF-8 Mode is disabled).

       Add tests on sys.stdout.errors with LC_ALL=POSIX.

The most important change is just one line::

   -        if (strcmp(ctype_loc, "C") == 0) {
   +        if (strcmp(ctype_loc, "C") == 0 || strcmp(ctype_loc, "POSIX") == 0) {
                return "surrogateescape";
            }

`bpo-34527 <https://bugs.python.org/issue34527>`__: Since I was testing
various configurations, I also noticed that my UTF-8 Mode (PEP 540) had the
same bug. Python 3.7 enables it if the LC_CTYPE locale is equal to "C",
but not if it's equal to "POSIX". I also changed that (`commit 5cb25895
<https://github.com/python/cpython/commit/5cb258950ce9b69b1f65646431c464c0c17b1510>`__).


C locale on Windows
===================

While testing my changes on Windows, I noticed that Python starts with the
LC_CTYPE locale equal to "C", whereas ``locale.setlocale(locale.LC_CTYPE, "")``
changes the LC_CTYPE locale to something like ``English_United States.1252``
(English with the code page 1252). Example with Python 3.6::

   C:\> python
   Python 3.6.4 (v3.6.4:d48eceb, Dec 19 2017, 06:54:40) [MSC v.1900 64 bit (AMD64)] on win32
   >>> import locale
   >>> locale.setlocale(locale.LC_CTYPE, None)
   'C'
   >>> locale.setlocale(locale.LC_CTYPE, "")
   'English_United States.1252'
   >>> locale.setlocale(locale.LC_CTYPE, None)
   'English_United States.1252'

On UNIX, Python 2 starts with the default C locale, whereas Python 3 always
sets the LC_CTYPE locale to my preference. Example on Fedora 28 with
``LANG=fr_FR.UTF-8``::

   $ python2 -c 'import locale; print(locale.setlocale(locale.LC_CTYPE, None))'
   C
   $ python3 -c 'import locale; print(locale.setlocale(locale.LC_CTYPE, None))'
   fr_FR.UTF-8

I modified Windows to behave as UNIX, `commit 177d921c
<https://github.com/python/cpython/commit/177d921c8c03d30daa32994362023f777624b10d>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Wed Aug 29 11:25:15 2018 +0200

       bpo-34485, Windows: LC_CTYPE set to user preference (GH-8988)

       On Windows, the LC_CTYPE is now set to the user preferred locale at
       startup: _Py_SetLocaleFromEnv(LC_CTYPE) is now called during the
       Python initialization. Previously, the LC_CTYPE locale was "C" at
       startup, but changed when calling setlocale(LC_CTYPE, "") or
       setlocale(LC_ALL, "").

       pymain_read_conf() now also calls _Py_SetLocaleFromEnv(LC_CTYPE) to
       behave as _Py_InitializeCore(). Moreover, it doesn't save/restore the
       LC_ALL anymore.

       On Windows, standard streams like sys.stdout now always use
       surrogateescape error handler by default (ignore the locale).

Example::

   C:\> python3.6 -c "import locale; print(locale.setlocale(locale.LC_CTYPE, None))"
   C
   C:\> python3.8 -c "import locale; print(locale.setlocale(locale.LC_CTYPE, None))"
   English_United States.1252

On Windows, Python 3.8 now starts with the LC_CTYPE locale set to my
preference, as it was already previously done on UNIX.


Back to stdio encoding
======================

After all previous changes and fixes, I was able to push my `commit dfe0dc74
<https://github.com/python/cpython/commit/dfe0dc74536dfb6f331131d9b2b49557675bb6b7>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Wed Aug 29 11:47:29 2018 +0200

       bpo-34485: Add _PyCoreConfig.stdio_encoding (GH-8881)

       * Add stdio_encoding and stdio_errors fields to _PyCoreConfig.
       * Add unit tests on stdio_encoding and stdio_errors.


Back to filesystem encoding
===========================

`Commit b2457efc
<https://github.com/python/cpython/commit/b2457efc78b74a1d6d1b77d11a939e886b8a4e2c>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Wed Aug 29 13:25:36 2018 +0200

       bpo-34523: Add _PyCoreConfig.filesystem_encoding (GH-8963)

       _PyCoreConfig_Read() is now responsible to choose the filesystem
       encoding and error handler. Using Py_Main(), the encoding is now
       chosen even before calling Py_Initialize().

       _PyCoreConfig.filesystem_encoding is now the reference, instead of
       Py_FileSystemDefaultEncoding, for the Python filesystem encoding.

       Changes:

       * Add filesystem_encoding and filesystem_errors to _PyCoreConfig
       * _PyCoreConfig_Read() now reads the locale encoding for the file
         system encoding.
       * PyUnicode_EncodeFSDefault() and PyUnicode_DecodeFSDefaultAndSize()
         now use the interpreter configuration rather than
         Py_FileSystemDefaultEncoding and Py_FileSystemDefaultEncodeErrors
         global configuration variables.
       * Add _Py_SetFileSystemEncoding() and _Py_ClearFileSystemEncoding()
         private functions to only modify Py_FileSystemDefaultEncoding and
         Py_FileSystemDefaultEncodeErrors in coreconfig.c.
       * _Py_CoerceLegacyLocale() now takes an int rather than
         _PyCoreConfig for the warning.


Use surrogatepass on Windows
============================

While working on the filesystem encoding change, I had a bug in
_freeze_importlib.exe which failed at startup::

   ValueError: only 'strict' and 'surrogateescape' error handlers are supported, not 'surrogatepass'

I used the following workaround in ``_freeze_importlib.c``::

   #ifdef MS_WINDOWS
       /* bpo-34523: initfsencoding() is not called if _install_importlib=0,
          so interp->fscodec_initialized value remains 0.
          PyUnicode_EncodeFSDefault() doesn't support the "surrogatepass" error
          handler in such case, whereas it's the default error handler on Windows.
          Force the "strict" error handler to work around this bootstrap issue. */
       config.filesystem_errors = "strict";
   #endif

But I wasn't fully happy with the workaround. When running more manual tests, I
found that the ``PYTHONLEGACYWINDOWSFSENCODING`` environment variable wasn't
handled properly. I pushed a first fix,
`commit c5989cd8 <https://github.com/python/cpython/commit/c5989cd87659acbfd4d19dc00dbe99c3a0fc9bd2>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Wed Aug 29 19:32:47 2018 +0200

       bpo-34523: Py_DecodeLocale() use UTF-8 on Windows (GH-8998)

       Py_DecodeLocale() and Py_EncodeLocale() now use the UTF-8 encoding on
       Windows if Py_LegacyWindowsFSEncodingFlag is zero.

       pymain_read_conf() now sets Py_LegacyWindowsFSEncodingFlag in its
       loop, but restore its value at exit.

My intent was to be able to use the ``surrogatepass`` error handler. If
``Py_DecodeLocale()`` is hardcoded to use UTF-8 on Windows, we should get
access to the ``surrogatepass`` error handler. Previously, ``mbstowcs()``
function was used and this function only support ``strict`` or
``surrogateescape`` error handlers.

I pushed a second big change to add support for the ``surrogatepass`` error
handler in locale codecs, `commit 3d4226a8
<https://github.com/python/cpython/commit/3d4226a832cabc630402589cc671cc4035d504e5>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Wed Aug 29 22:21:32 2018 +0200

       bpo-34523: Support surrogatepass in locale codecs (GH-8995)

       Add support for the "surrogatepass" error handler in
       PyUnicode_DecodeFSDefault() and PyUnicode_EncodeFSDefault()
       for the UTF-8 encoding.

       Changes:

       * _Py_DecodeUTF8Ex() and _Py_EncodeUTF8Ex() now support the
         surrogatepass error handler (_Py_ERROR_SURROGATEPASS).
       * _Py_DecodeLocaleEx() and _Py_EncodeLocaleEx() now use
         the _Py_error_handler enum instead of "int surrogateescape" to pass
         the error handler. These functions now return -3 if the error
         handler is unknown.
       * Add unit tests on _Py_DecodeLocaleEx() and _Py_EncodeLocaleEx()
         in test_codecs.
       * Rename get_error_handler() to _Py_GetErrorHandler() and expose it
         as a private function.
       * _freeze_importlib doesn't need config.filesystem_errors="strict"
         workaround anymore.

``PyUnicode_DecodeFSDefault()`` and ``PyUnicode_EncodeFSDefault()`` functions
use ``Py_DecodeLocale()`` and ``Py_EncodeLocale()`` before the Python codec of
the filesystem encoding is loaded. With this big change, ``Py_DecodeLocale()``
and ``Py_EncodeLocale()`` now really behave as the Python codec.

Previously, Python started with the ``surrogateescape`` error handler, and
switched to the ``surrogatepass`` error handler once the Python codec was
loaded.


Filesystem encoding documentation
=================================

One "last" change, I documented how Python selects the filesystem encoding,
`commit de427556
<https://github.com/python/cpython/commit/de427556746aa41a8b5198924ce423021bc0c718>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Wed Aug 29 23:26:55 2018 +0200

       bpo-34523: Py_FileSystemDefaultEncoding NULL by default (GH-9003)

       * Py_FileSystemDefaultEncoding and Py_FileSystemDefaultEncodeErrors
         default value is now NULL: initfsencoding() set them
         during Python initialization.
       * Document how Python chooses the filesystem encoding and error
         handler.
       * Add an assertion to _PyCoreConfig_Read().

Documentation::

    /* Python filesystem encoding and error handler:
       sys.getfilesystemencoding() and sys.getfilesystemencodeerrors().

       Default encoding and error handler:

       * if Py_SetStandardStreamEncoding() has been called: they have the
         highest priority;
       * PYTHONIOENCODING environment variable;
       * The UTF-8 Mode uses UTF-8/surrogateescape;
       * locale encoding: ANSI code page on Windows, UTF-8 on Android,
         LC_CTYPE locale encoding on other platforms;
       * On Windows, "surrogateescape" error handler;
       * "surrogateescape" error handler if the LC_CTYPE locale is "C" or "POSIX";
       * "surrogateescape" error handler if the LC_CTYPE locale has been coerced
         (PEP 538);
       * "strict" error handler.

       Supported error handlers: "strict", "surrogateescape" and
       "surrogatepass". The surrogatepass error handler is only supported
       if Py_DecodeLocale() and Py_EncodeLocale() use directly the UTF-8 codec;
       it's only used on Windows.

       initfsencoding() updates the encoding to the Python codec name.
       For example, "ANSI_X3.4-1968" is replaced with "ascii".

       On Windows, sys._enablelegacywindowsfsencoding() sets the
       encoding/errors to mbcs/replace at runtime.


       See Py_FileSystemDefaultEncoding and Py_FileSystemDefaultEncodeErrors.
       */
    char *filesystem_encoding;
    char *filesystem_errors;

Final FreeBSD 10 issue
======================

`bpo-34544 <https://bugs.python.org/issue34544>`__: The stdio and filesystem
encodings are now properly selected before Py_Initialize(), the LC_CTYPE locale
should be properly initialized, the "POSIX" locale is now properly handled, but
the FreeBSD 10 buildbot still complained about my recent changes... Many
``test_c_locale_coerce`` tests started to fail with:

   Fatal Python error: get_locale_encoding: failed to get the locale encoding: nl_langinfo(CODESET) failed

Sadly, I wasn't able to reproduce the issue on my FreeBSD 11 VM. I also got
access to the FreeBSD CURRENT buildbot, but I also failed to reproduce the bug
there. I was supposed to get access to the FreeBSD 10 buildbot, but there was a
DNS issue.

I had to *guess* the origin of the bug and I attempted a fix, `commit f01b2a1b
<https://github.com/python/cpython/commit/f01b2a1b84ee08df73a78cf1017eecf15e3cb995>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Mon Sep 3 14:38:21 2018 +0200

       bpo-34544: Fix setlocale() in pymain_read_conf() (GH-9041)

       bpo-34485, bpo-34544: On some FreeBSD, nl_langinfo(CODESET) fails if
       LC_ALL or LC_CTYPE is set to an invalid locale name. Replace
       _Py_SetLocaleFromEnv(LC_CTYPE) with _Py_SetLocaleFromEnv(LC_ALL) to
       initialize properly locales.

       Partially revert commit 177d921c8c03d30daa32994362023f777624b10d.

... but it didn't work.

I decided to install a FreeBSD 10 VM and one week later... I finally succeded
to reproduce the issue!

The bug was that the ``_Py_CoerceLegacyLocale()`` function doesn't restore the
LC_CTYPE to its previous value if it attempted to coerce the LC_CTYPE locale
but no locale worked.

Previously, it didn't matter, since the LC_CTYPE locale was initialized again
later, or it was saved/restored indirectly. But with my latest changes, the
LC_CTYPE was left unchanged.

The fix is just to restore LC_CTYPE if ``_Py_CoerceLegacyLocale()`` fails,
`commit 8ea09110
<https://github.com/python/cpython/commit/8ea09110d413829f71d979d8c7073008cb87fb03>`__::

   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Mon Sep 3 17:05:18 2018 +0200

       _Py_CoerceLegacyLocale() restores LC_CTYPE on fail (GH-9044)

       bpo-34544: If _Py_CoerceLegacyLocale() fails to coerce the C locale,
       restore the LC_CTYPE locale to the its previous value.

Finally, I succeded to do what I wanted to do initially, remove the code which
saved/restored the LC_ALL locale: ``pymain_read_conf()`` is now really
responsible to set the LC_CTYPE locale, and it doesn't modify the LC_ALL locale
anymore.


Configuration of locales and encodings
======================================

Python has **many** options to configure the locales and encodings.

Main options of Python 3.7:

* Legacy Windows stdio (PEP 528)
* Legacy Windows filesystem encoding (PEP 529)
* C locale coercion (PEP 538)
* UTF-8 mode (PEP 540)

The combination of C locale coercion and UTF-8 mode is non-obvious and should
be carefully tested!

Environment variables:

* ``PYTHONCOERCECLOCALE=0``
* ``PYTHONCOERCECLOCALE=1``
* ``PYTHONCOERCECLOCALE=warn``
* ``PYTHONIOENCODING=:<errors>``
* ``PYTHONIOENCODING=<encoding>:<errors>``
* ``PYTHONIOENCODING=<encoding>``
* ``PYTHONLEGACYWINDOWSFSENCODING=1``
* ``PYTHONLEGACYWINDOWSSTDIO=1``
* ``PYTHONUTF8=0``
* ``PYTHONUTF8=1``

Command line options:

* ``-X utf8=0``
* ``-X utf8`` or ``-X utf8=1``
* ``-E`` or ``-I`` (ignore ``PYTHON*`` environment variables)

Global configuration variables:

* ``Py_FileSystemDefaultEncodeErrors``
* ``Py_FileSystemDefaultEncoding``
* ``Py_LegacyWindowsFSEncodingFlag``
* ``Py_LegacyWindowsStdioFlag``
* ``Py_UTF8Mode``

_PyCoreConfig:

* ``coerce_c_locale``
* ``coerce_c_locale_warn``
* ``filesystem_encoding``
* ``filesystem_errors``
* ``stdio_encoding``
* ``stdio_errors``

The LC_CTYPE locale depends on 3 environment variables:

* ``LC_ALL``
* ``LC_CTYPE``
* ``LANG``

Depending on the platform, the following configuration gives a different
LC_CTYPE locale:

* ``LC_ALL= LC_CTYPE= LANG=`` (no variable set)
* ``LC_ALL= LC_CTYPE=C LANG=`` (C locale)
* ``LC_ALL= LC_CTYPE=POSIX LANG=`` (POSIX locale)

In case of doubt, I also tested:

* ``LC_ALL=C LC_CTYPE= LANG=`` (C locale)
* ``LC_ALL=POSIX LC_CTYPE= LANG=`` (POSIX locale)

The LC_CTYPE encoding (locale encoding) can be queried using
``nl_langinfo(CODESET)``. On FreeBSD, Solaris, HP-UX and maybe other platforms,
``nl_langinfo(CODESET)`` announces an encoding which is different than the
codec used by ``mbstowcs()`` and ``wcstombs()`` functions, and so Python forces
the usage of the ASCII encoding.

The test matrix of all these configurations and all platforms is quite big.
Honestly, I would not bet that Python 3.8 will behave properly in all possible
cases. At least, I tried to fix all issues that I spotted! Moreover, I added
many tests which should help to detect bugs and prevent regressions.
