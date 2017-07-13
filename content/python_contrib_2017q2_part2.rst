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

* Mentoring
* Reference and memory leaks
* Contributions
* Enhancements
* Bugfixes
* Stars of the CPython GitHub project

Previous report: `My contributions to CPython during 2017 Q2 (part 1)
<{filename}/python_contrib_2017q2_part1.rst>`_.

Next report: `My contributions to CPython during 2017 Q2 (part 3)
<{filename}/python_contrib_2017q2_part3.rst>`_.


Mentoring
=========

During this quarter, I tried to mark "easy" issues using a "[EASY]" tag in
their title and the "easy" or "easy C" keyword. I announced these issues on the
`core-mentorship mailing list <https://www.python.org/dev/core-mentorship/>`_.
I asked core developers to not fix these easy issues, but rather explain how to
fix them. In each issue, I described how fix these issues.

It was a success since all easy issues were fixed quickly, usually the PR was
merged in less than 24 hours after I created the issue!

I mentored **Stéphane Wirtel** and **Louie Lu** to fix issues (easy or not).
During this quarter, Stéphane Wirtel got **5 commits** merged into master (on a
**total of 11 commits**), and Louie lu got **6 commits** merged into master (on
a **total of 10 commits**).

They helped me to fix reference leaks spotted by the new Refleaks buildbots.


Reference and memory leaks
==========================

Zachary Ware installed a Gentoo and a Windows buildbots running the Python test
suite with ``--huntrleaks`` to detect reference and memory leaks.

I worked hard with others, especially Stéphane Wirtel and Louie Lu, to fix
*all* reference leaks and memory leaks in Python 2.7, 3.5, 3.6 and master.
Right now, there is no more leaks on Windows! For Gentoo, the buildbot is
currently offline, but I am confident that all leaks also fixed.

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

* bpo-30704, bpo-30604: Fix memleak in code_dealloc(): Free also
  co_extra->ce_extras, not only co_extra. XXX Serhiy rewrote the structure in
  master to use a single memory block, implemented my idea.

Python 3.5 regrtest fix
-----------------------

bpo-30675, Fix the multiprocessing code in regrtest:

* Rewrite code to pass ``slaveargs`` from the master process to worker
  processes: reuse the same code of the Python master branch.
* Move code to initialize tests in a new ``setup_tests()`` function,
  similar change was done in the master branch.
* In a worker process, call ``setup_tests()`` with the namespace built
  from ``slaveargs`` to initialize correctly tests.

Before this change, ``warm_caches()`` was not called in worker processes
because the setup was done before rebuilding the namespace from ``slaveargs``.
As a consequence, the ``huntrleaks`` feature was unstable. For example,
``test_zipfile`` reported randomly false positive on reference leaks.


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

The same change was done to check for memory leaks.


Contributions
=============

This quarter, I helped to merge two contributions:

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
  PyTraceMalloc_Untrack() functions public. numpy is able to use
  tracemalloc since numpy 1.13.


Bugfixes
========

* bpo-30125: On Windows, faulthandler.disable() now removes the exception
  handler installed by faulthandler.enable().
* bpo-30284: Fix regrtest for out of tree build. Use a build/ directory in the
  build directory, not in the source directory, since the source directory may
  be read-only and must not be modified. Fallback on the source directory if
  the build directory is not available (missing "abs_builddir" sysconfig
  variable).
* test_locale now ignores the DeprecationWarning, don't fail anymore if test
  run with ``python3 -Werror``. Fix also deprecation message: add a space.
* Fix a compiler warnings on AIX: only define get_zone() and get_gmtoff() if
  needed.
* Fix a compiler warning in tmtotuple(): use the ``time_t`` type for the
  ``gmtoff`` parameter.
* bpo-30264: ExpatParser closes the source on error. ExpatParser.parse() of
  xml.sax.xmlreader now always closes the source: close the file object or the
  urllib object if source is a string (not an open file-like object). The
  change fixes a ResourceWarning on parsing error. Add
  test_parse_close_source() unit test.
* Fix SyntaxWarning on importing test_inspect. Fix the following warning when
  test_inspect.py is compiled to test_inspect.pyc:
  ``SyntaxWarning: tuple parameter unpacking has been removed in 3.x``
* bpo-30418: On Windows, subprocess.Popen.communicate() now also ignore EINVAL
  on stdin.write(): ignore also EINVAL if the child process is still running
  but closed the pipe.
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
8,539 stars, behind PHP and Ruby! I suggested to "like" ("star"?) the `CPython
project on GitHub <https://github.com/python/cpython/>`_ if you like the Python
programming language!

Four days later, `we got +2,389 new stars (8,539 => 10,928)
<https://mail.python.org/pipermail/python-dev/2017-July/148548.html>`_, thank
you! Python moved from the 11th place to the 9th, before Elixir and Julia.

Ben Hoyt `posted it on reddit.com/r/Python
<https://www.reddit.com/r/Python/comments/6kg4w0/cpython_recently_moved_to_github_star_the_project/>`_,
where it got a bit of traction. Terry Jan Reedy also `posted it on python-list
<https://mail.python.org/pipermail/python-list/2017-July/723476.html>`_.

Screenshot at 2017-07-13 showing Ruby, PHP and CPython:

.. image:: {filename}/images/github_cpython_stars.png
   :alt: GitHub showcase: Programming languages
   :target: https://github.com/showcases/programming-languages

CPython now has 11,512 stars, only 861 stars behind PHP ;-)
