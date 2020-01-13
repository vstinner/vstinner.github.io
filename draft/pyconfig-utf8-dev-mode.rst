+++++++++++++++++++++++++++++++++++++++++
PyConfig: Development Mode and UTF-8 Mode
+++++++++++++++++++++++++++++++++++++++++

:date: 2020-01-13 23:00
:tags: cpython
:category: python
:slug: pyconfig-utf8-dev-mode
:authors: Victor Stinner

Development mode: -X dev
========================

In March 2016, I proposed on Python-ideas, `Add a developer mode to Python: -X
dev command line option
<https://mail.python.org/pipermail/python-ideas/2016-March/039314.html>`__:

    When I develop on CPython, I'm always building Python in debug mode
    using ``./configure --with-pydebug``. This mode enables a **lot** of extra
    checks which helps me to detect bugs earlier. The debug mode makes Python
    much slower and so is not the default.

    I propose to add a "development mode" to Python, to get a few checks
    to detect bugs earlier: a new ``-X dev`` command line option. Example::

       python3.6 -X dev script.py

    I propose to enable:

    * Show ``DeprecationWarning`` and ``ResourceWarning warnings``: ``python -Wd``
    * Show ``BytesWarning`` warning: ``python -b``
    * Enable Python assertions (``assert``) and set ``__debug__`` to True:
      remove (or just ignore) ``-O`` or ``-OO`` command line arguments
    * faulthandler to get a Python traceback on segfault and fatal errors:
      ``python -X faulthandler``
    * Debug hooks on Python memory allocators: ``PYTHONMALLOC=debug``

In Novembre 2017, Nick Coghlan proposed `PEP 565: Show DeprecationWarning in
__main__ <https://www.python.org/dev/peps/pep-0565/>`_. I wasn't convinced that
this idea was enough, so I came back with my idea, now on the python-dev list,
`Add a developer mode to Python: -X dev command line option
<https://mail.python.org/pipermail/python-dev/2017-November/150514.html>`__.

In `bpo-32030 <https://bugs.python.org/issue32030>`__, I prepared the Python
code base to be able to implement ``-X dev`` more easily later::

    commit f7e5b56c37eb859e225e886c79c5d742c567ee95
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Nov 15 15:48:08 2017 -0800

        bpo-32030: Split Py_Main() into subfunctions (#4399)

    ommit a7368ac6360246b1ef7f8f152963c2362d272183
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Nov 15 18:11:45 2017 -0800

        bpo-32030: Enhance Py_Main() (#4412)

XXX yet another problem: implement -X dev without fork() nor exec(),
https://bugs.python.org/issue32030#msg306246:

    The problem is that currently the code parsing command line options
    and the code setting the memory allocator (handle PYTHONMALLOC
    environment variable) are mixed, it's not possible to touch this
    code.

In `bpo-32043 <https://bugs.python.org/issue32043>`__, I pushed `commit ccb0442a
<https://github.com/python/cpython/commit/ccb0442a338066bf40fe417455e5a374e5238afb>`__::

    commit ccb0442a338066bf40fe417455e5a374e5238afb
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Thu Nov 16 03:20:31 2017 -0800

        bpo-32043: New "developer mode": "-X dev" option (#4413)

        Add a new "developer mode": new "-X dev" command line option to
        enable debug checks at runtime.

In `bpo-32101 <https://bugs.python.org/issue32101>`__, I pushed `commit
5e3806f8
<https://github.com/python/cpython/commit/5e3806f8cfd84722fc55d4299dc018ad9b0f8401>`__::

    commit 5e3806f8cfd84722fc55d4299dc018ad9b0f8401
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Thu Nov 30 11:40:24 2017 +0100

        bpo-32101: Add PYTHONDEVMODE environment variable (#4624)

        * bpo-32101: Add sys.flags.dev_mode flag
          Rename also the "Developer mode" to the "Development mode".
        * bpo-32101: Add PYTHONDEVMODE environment variable
          Mention it in the development chapiter.

https://bugs.python.org/issue32047

https://bugs.python.org/issue31970


I completed the documentation and fixed warnings filters (`bpo-32089 <https://bugs.python.org/issue32089>`__).

    https://bugs.python.org/issue32089

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


