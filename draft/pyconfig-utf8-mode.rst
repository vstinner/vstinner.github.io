++++++++++++++++++++
PyConfig: UTF-8 Mode
++++++++++++++++++++

:date: 2020-01-13 23:00
:tags: cpython
:category: python
:slug: pyconfig-utf8-mode
:authors: Victor Stinner

Implementation of the PEP 540: UTF-8 Mode
=========================================

Issue created in January 2017: https://bugs.python.org/issue29240

"TODO: re-encode sys.argv from the local encoding to UTF-8 in Py_Main()
when the UTF-8 mode is enabled"

PR created in March 2017: https://github.com/python/cpython/pull/855

2017-12-13::

    bpo-29240: PEP 540: Add a new UTF-8 Mode (#855)
    https://github.com/python/cpython/commit/91106cd9ff2f321c0f60fbaa09fd46c80aa5c266

At the first PEP 540 commit, _PyCoreConfig had 14 fields.


2017-12-16::

    New changeset 9454060e84a669dde63824d9e2fcaf295e34f687 by Victor Stinner in branch 'master':
    bpo-29240, bpo-32030: Py_Main() re-reads config if encoding changes (#4899)
    https://github.com/python/cpython/commit/9454060e84a669dde63824d9e2fcaf295e34f687

    while (1) {
        /* Watchdog to prevent an infinite loop */
        loops++;
        if (loops == 3) {
            pymain->err = _Py_INIT_ERR("Encoding changed twice while "
                                       "reading the configuration");
            goto done;
        }
        ...
        res = pymain_read_conf_impl(pymain);
        ...

        if (!encoding_changed) {
            break;
        }
        ...
    }

2017-12-21, problems arise::

    New changeset 424315fa865b43f67e36a40647107379adf031da by Victor Stinner in branch 'master':
    bpo-29240: Skip test_readline.test_nonascii() (#4968)
    https://github.com/python/cpython/commit/424315fa865b43f67e36a40647107379adf031da


2018-01-10::

    New changeset 2cba6b85797ba60d67389126f184aad5c9e02ff3 by Victor Stinner in branch 'master':
    bpo-29240: readline now ignores the UTF-8 Mode (#5145)
    https://github.com/python/cpython/commit/2cba6b85797ba60d67389126f184aad5c9e02ff3

    Add new fuctions ignoring the UTF-8 mode:

    * _Py_DecodeCurrentLocale()
    * _Py_EncodeCurrentLocale()
    * _PyUnicode_DecodeCurrentLocaleAndSize()
    * _PyUnicode_EncodeCurrentLocale()

time.strftime() must use the current LC_CTYPE encoding, not UTF-8 if the
UTF-8 mode is enabled.

2018-01-15::

    https://github.com/python/cpython/commit/7ed7aead9503102d2ed316175f198104e0cd674c

    bpo-29240: Fix locale encodings in UTF-8 Mode (#5170)

    Modify locale.localeconv(), time.tzname, os.strerror() and other
    functions to ignore the UTF-8 Mode: always use the current locale
    encoding.



