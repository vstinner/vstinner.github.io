+++++++++++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q2 (part 2)
+++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2017-07-13 16:30
:tags: cpython
:category: python
:slug: contrib-cpython-2017q2-part2
:authors: Victor Stinner

This is the second part of my contributions to `CPython
<https://www.python.org/>`_ during 2017 Q2 (april, may, june):

* FreeBSD test_subprocess core dump
* Security
* Contributions
* Enhancements
* Refleaks
* Bugfixes
* Test fixes
* Stars of the CPython GitHub project


FreeBSD test_subprocess core dump
=================================

bpo-30448: During one month, some FreeBSD buildbots was emitting this warning
which started to annoy me, since I was trying to fix *all* buildbots warnings::

    Warning -- files was modified by test_subprocess
      Before: []
      After:  ['python.core']

I tried and failed to reproduce the warning on my FreeBSD 11 VM. I also asked a
friend to reproduce the bug, but he also failed. I was developping my
``test.bisect`` tool and I wanted to get access to a machine to reproduce the
bug!

Later, **Kubilay Kocak** aka *koobs* gave me access to his FreeBSD buildbots
and in a few seconds with my new test.bisect tool, I identified that the
``test_child_terminated_in_stopped_state()`` test triggers a deliberate crash,
but doesn't disable core dump creation. The fix is simple, use
``test.support.SuppressCrashReport`` context manager. Thanks *koobs* for the
access!

Maybe only FreeBSD 10 and older dump a core on this specific test, not FreeBSD
11. I don't know why. The test is special, it tests a process which crashs
while being traced with ``ptrace()``.


Security
========

Backport fixes
--------------

I am trying to fix all known security fixes in the 6 maintained Python
branches: 2.7, 3.3, 3.4, 3.5, 3.6 and master.

I created the `python-security.readthedocs.io
<http://python-security.readthedocs.io/>`_ website to track these
vulnerabilities, especially which Python versions are fixed, to identifiy
missing backports.

Python 2.7, 3.5, 3.6 and master are quite good, I am still working on
backporting fixes into 3.4 and 3.3. Larry Hastings merged my 3.4 backports and
other security fixes, and scheduled a new 3.4.7 release next weeks. Later, I
will try to fix Python 3.3 as well, before its end-of-life, scheduled for the
end of september.

See also the `Status of Python branches
<https://docs.python.org/devguide/#status-of-python-branches>`_ in the
devguide.

libexpat 2.2
------------

Python embeds a copy of libexpat to ease Python compilation on Windows and
macOS. It means that we have to remind to upgrade it at each libexpat release.
It is especially important when security vulerabilities are fixed in libexpat.

libexpat 2.2 was released at 2016-06-21 and it contains such fixes for
vulnerabilities, see: `CVE-2016-0718: expat 2.2, bug #537
<http://python-security.readthedocs.io/vuln/cve-2016-0718_expat_2.2_bug_537.html>`_.

Sadly, it took us a few months to upgrade libexpat. I wrote a short shell
script to easily upgrade libexpat: recreate Modules/expat/ directory from a
libexpat tarball.

My commit:

    bpo-29591: Upgrade Modules/expat to libexpat 2.2 (#2164)

    Remove the configuration (``Modules/expat/*config.h``) of unsupported
    platforms: Amiga, MacOS Classic on PPC32, Open Watcom.

    Remove XML_HAS_SET_HASH_SALT define: it became useless since our local
    expat copy was upgrade to expat 2.1 (it's now expat 2.2.0).

I upgraded our libexpat copy to 2.2 in 2.7, 3.4, 3.5, 3.6 and master branches.
I still have a pending pull request for 3.3.

libexpat 2.2.1
--------------

Just after I finally upgraded our libexpat copy to 2.2.0... libexpat 2.2.1 was
released with new security fixes!  See `CVE-2017-9233: Expat 2.2.1
<http://python-security.readthedocs.io/vuln/cve-2017-9233_expat_2.2.1.html>`_

Again, I upgraded libexpat to 2.2.1 in all branches (pending: 3.3), see
bpo-30694.

    Upgrade expat copy from 2.2.0 to 2.2.1 to get fixes
    of multiple security vulnerabilities including:

    * CVE-2017-9233 (External entity infinite loop DoS),
    * CVE-2016-9063 (Integer overflow, re-fix),
    * CVE-2016-0718 (Fix regression bugs from 2.2.0's fix to CVE-2016-0718)
    * CVE-2012-0876 (Counter hash flooding with SipHash).

    Note: the CVE-2016-5300 (Use os-specific entropy sources like getrandom)
    doesn't impact Python, since Python already gets entropy from the OS to set
    the expat secret using ``XML_SetHashSalt()``.

urllib splithost() vulnerability
--------------------------------

Vulnerability: `bpo-30500: urllib connects to a wrong host
<http://python-security.readthedocs.io/vuln/bpo-30500_urllib_connects_to_a_wrong_host.html>`_.

While it was quick to confirm the vulnerability, it was tricky to decide how to
properly fix it without breaking backward compatibility. We had too few unit
tests, and no obvious definition of the *expected* behaviour. I contributed to
the discussed and to polish the fix:

Commit of bpo-30500:

    Fix urllib.parse.splithost() to correctly parse fragments. For example,
    ``splithost('//127.0.0.1#@evil.com/')`` now correctly returns the
    ``127.0.0.1`` host, instead of treating ``@evil.com`` as the host in an
    authentification (``login@host``).

Fix applied to master, 3.6, 3.5, 3.4 and 2.7; pending pull request for 3.3.

Travis CI
---------

I also wrote a pull request to enable Travis CI and AppVeyor CI on Python 3.3
and 3.4 branches, but these changes are complex and not merged yet. I am now
confident that the CI will be enabled on 3.4!

The PR for Python 3.4: `[3.4] Backport CI config from master
<https://github.com/python/cpython/pull/2475>`_.


Contributions
=============

* bpo-9850: Deprecate the macpath module. Co-Authored-By: **Chi Hsuan Yen**.
* bpo-30595: Fix multiprocessing.Queue.get(timeout).
  multiprocessing.Queue.get() with a timeout now polls its reader in
  non-blocking mode if it succeeded to aquire the lock but the acquire took
  longer than the timeout. Co-Authored-By: **Grzegorz Grzywacz**.

Enhancements
============

* bpo-30265: support.unlink() now only ignores ENOENT and ENOTDIR, instead of
  ignoring all OSError exception.
* bpo-30054: Expose tracemalloc C API: make PyTraceMalloc_Track() and
  PyTraceMalloc_Untrack() functions public. numpy is now able to use
  tracemalloc since numpy 1.13 (XXX check version XXX link to PR).


Refleaks
========

* bpo-30598: _PySys_EndInit() now duplicates warnoptions. Fix a reference leak
  in subinterpreters, like test_callbacks_leak() of test_atexit. warnoptions is
  a list used to pass options from the command line to the sys module
  constructor. Before this change, the list was shared by multiple interpreter
  which is not the expected behaviour. Each interpreter should have their own
  independent mutable world. This change duplicates the list in each
  interpreter. So each interpreter owns its own list, so each interpreter can
  clear its own list.
* bpo-30601: Fix a refleak in WindowsConsoleIO. Fix a reference leak in
  _io._WindowsConsoleIO: PyUnicode_FSDecoder() always initialize decodedname
  when it succeed and it doesn't clear input decodedname object.
* bpo-30599: Fix test_threaded_import reference leak. Mock
  os.register_at_fork() when importing the random module, since this function
  doesn't allow to unregister callbacks and so leaked memory.
* 2.7: _tkinter: Fix refleak in getint(). PyNumber_Int() creates a new reference:
  need to decrement result reference counter.
* bpo-30635: Fix refleak in test_c_locale_coercion. When checking for reference
  leaks, test_c_locale_coercion is run multiple times and so
  _LocaleCoercionTargetsTestCase.setUpClass() is called multiple times.
  setUpClass() appends new value at each call, so it looks like a reference
  leak. Moving the setup from setUpClass() to setUpModule() avoids this,
  eliminating the false alarm.
* bpo-30602: Fix refleak in os.spawnve(). When os.spawnve() fails while
  handling arguments, free correctly argvlist: pass lastarg+1 rather than
  lastarg to free_string_array() to also free the first item.
* bpo-30602: Fix refleak in os.spawnv(). When os.spawnv() fails while handling
  arguments, free correctly argvlist: pass lastarg+1 rather than lastarg to
  free_string_array() to also free the first item.
* Fix ref cycles in TestCase.assertRaises(). bpo-23890:
  unittest.TestCase.assertRaises() now manually breaks a reference cycle to not
  keep objects alive longer than expected.
* Python 2.7: bpo-30675: Fix refleak hunting in regrtest. regrtest now warms up
  caches: create explicitly all internal singletons which are created on demand
  to prevent false positives when checking for reference leaks.
* _winconsoleio: Fix memory leak. Fix memory leak when _winconsoleio tries to
  open a non-console file: free the name buffer.
* bpo-30813: Fix unittest when hunting refleaks. bpo-11798, bpo-16662,
  bpo-16935, bpo-30813: Skip
  test_discover_with_module_that_raises_SkipTest_on_import() and
  test_discover_with_init_module_that_raises_SkipTest_on_import() of
  test_unittest when hunting reference leaks using regrtest.

Fix for Python 3.5::

    bpo-30675: Fix multiprocessing code in regrtest (#2220)

    * Rewrite code to pass slaveargs from the master process to worker
      processes: reuse the same code of the Python master branch
    * Move code to initialize tests in a new setup_tests() function,
      similar change was done in the master branch
    * In a worker process, call setup_tests() with the namespace built
      from slaveargs to initialize correctly tests

    Before this change, warm_caches() was not called in worker processes
    because the setup was done before rebuilding the namespace from
    slaveargs. As a consequence, the huntrleaks feature was unstable. For
    example, test_zipfile reported randomly false positive on reference
    leaks.

* bpo-30704, bpo-30604: Fix memleak in code_dealloc(): Free also
  co_extra->ce_extras, not only co_extra. XXX Serhiy rewrote the structure in
  master to use a single memory block, implemented my idea.

False positives
---------------

bpo-30776: reduce regrtest -R false positives (#2422)

* Change the regrtest --huntrleaks checker to decide if a test file
  leaks or not. Require that each run leaks at least 1 reference.
* Warmup runs are now completely ignored: ignored in the checker test
  and not used anymore to compute the sum.
* Add an unit test for a reference leak.

Example of reference differences previously considered a failure
(leak) and now considered as success (success, no leak)::

    [3, 0, 0]
    [0, 1, 0]
    [8, -8, 1]

bpo-30776: regrtest: reduce memleak false positive.

Only report a leak if each run leaks at least one memory block.


Bugfixes
========

* bpo-30284: Fix regrtest for out of tree build. Use a build/ directory in the
  build directory, not in the source directory, since the source directory may
  be read-only and must not be modified. Fallback on the source directory if
  the build directory is not available (missing "abs_builddir" sysconfig
  variable).
* test_locale now ignores the DeprecationWarning, don't fail anymore if test
  run with ``python3 -Werror``. Fix also deprecation message: add a space.
* Only define get_zone() and get_gmtoff() if needed, fix warnings on AIX.
* bpo-30125: On Windows, faulthandler.disable() now removes the exception
  handler installed by faulthandler.enable().
* tmtotuple(): use time_t for gmtoff.
* bpo-30264: ExpatParser closes the source on error. ExpatParser.parse() of
  xml.sax.xmlreader now always closes the source: close the file object or the
  urllib object if source is a string (not an open file-like object). The
  change fixes a ResourceWarning on parsing error. Add
  test_parse_close_source() unit test.
* Fix SyntaxWarning on importing test_inspect. Fix the following warning when
  test_inspect.py is compiled to test_inspect.pyc:
  ``SyntaxWarning: tuple parameter unpacking has been removed in 3.x``
* bpo-30418: Popen.communicate() always ignore EINVAL. On Windows,
  subprocess.Popen.communicate() now also ignore EINVAL on stdin.write() if the
  child process is still running but closed the pipe.


Test fixes
==========

* bpo-29887: test_normalization handles PermissionError
* bpo-30257: _bsddb: Fix newDBObject(). Don't set cursorSetReturnsNone to
  DEFAULT_CURSOR_SET_RETURNS_NONE anymore if self->myenvobj is set.
  Fix a GCC warning on the strange indentation.
* bpo-30231: Remove skipped test_imaplib tests. The public cyrus.andrew.cmu.edu
  IMAP server (port 993) doesn't accept TLS connection using our self-signed
  x509 certificate. Remove the two tests which are already skipped. Write a new
  test_certfile_arg_warn() unit test for the certfile deprecation warning.


Stars of the CPython GitHub project
===================================

At June 30, I wrote `an email to python-dev
<https://mail.python.org/pipermail/python-dev/2017-June/148523.html>`_ about
`GitHub showcase of hosted programming languages
<https://github.com/showcases/programming-languages>`_: Python is only #11 with
8,539 stars, behind PHP and Ruby! I suggested to "like" ("star"?) the project
to GitHub if you like the Python programming language!

Four days later, `we got +2,389 new stars (8,539 => 10,928)
<https://mail.python.org/pipermail/python-dev/2017-July/148548.html>`_, thank
you! Python moved from the 11th place to the 9th, before Elixir and Julia.

Ben Hoyt `posted it on reddit.com/r/Python
<https://www.reddit.com/r/Python/comments/6kg4w0/cpython_recently_moved_to_github_star_the_project/>`_,
where it got a bit of traction.

Terry Jan Reedy also `posted it on python-list
<https://mail.python.org/pipermail/python-list/2017-July/723476.html>`_.

Update, 2017-07-12: 11,467 stars, only 902 stars behind PHP ;-)

Screenshot showing Ruby, PHP and CPython:

.. image:: {filename}/images/github_cpython_stars.png
   :alt: GitHub showcase: Programming languages
   :target: https://github.com/showcases/programming-languages
