++++++++++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q3: Part 1
++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2017-10-18 15:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q3-part1
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q3
(july, august, september), Part 1.

Previous report: `My contributions to CPython during 2017 Q2 (part1)
<{filename}/python_contrib_2017q2_part1.rst>`_.

Next reports:

* `My contributions to CPython during 2017 Q3: Part 2 (dangling
  threads) <{filename}/python_contrib_2017q3_part2.rst>`_.
* `My contributions to CPython during 2017 Q3: Part 3 (funny bugs)
  <{filename}/python_contrib_2017q3_part3.rst>`_.

Summary:

* Statistics
* Security fixes
* Enhancement: socket.close() now ignores ECONNRESET
* Removal of the macOS job of Travis CI
* New test.pythoninfo utility
* Revert commits if buildbots are broken
* Fix the Python test suite


Statistics
==========

::

    # All branches
    $ git log --after=2017-06-30 --before=2017-10-01 --reverse --branches='*' --author=Stinner|grep '^commit ' -c
    209

    # Master branch only
    $ git log --after=2017-06-30 --before=2017-10-01 --reverse --author=Stinner origin/master|grep '^commit ' -c
    97

Statistics: I pushed **97** commits in the master branch on a **total of 209
commits**, remaining: 112 commits in the other branches (backports, fixes
specific to Python 2.7, security fixes in Python 3.3 and 3.4, etc.)


Security fixes
==============

* `bpo-30947 <https://bugs.python.org/issue30947>`__: Update libexpat from 2.2.1 to 2.2.3. Fix applied to master, 3.6,
  3.5, 3.4, 3.3 and 2.7 branches! Expat 2.2.2 and 2.2.3 fixed multiple security
  vulnerabilities.
  http://python-security.readthedocs.io/vuln/expat_2.2.3.html
* Fix whichmodule() of _pickle: : _PyUnicode_FromId() can return NULL, replace
  Py_INCREF() with Py_XINCREF(). Fix coverity report: CID 1417269.
* `bpo-30860 <https://bugs.python.org/issue30860>`__: ``_PyMem_Initialize()`` contains code which is never executed.
  Replace the runtime check with a build assertion. Fix Coverity CID 1417587.

See also my `python-security website <http://python-security.readthedocs.io/>`_.


Enhancement: socket.close() now ignores ECONNRESET
==================================================

`bpo-30319 <https://bugs.python.org/issue30319>`__: socket.close() now ignores ECONNRESET. Previously, many network
tests failed randomly with ConnectionResetError on socket.close().

Patching all functions calling socket.close() would require a lot of work, and
it was surprising to get a "connection reset" when closing a socket.

Who cares that the peer closed the connection, since we are already closing
it!?

Note: socket.close() was modified in Python 3.6 to raise OSError on failure
(`bpo-26685 <https://bugs.python.org/issue26685>`__).


Removal of the macOS job of Travis CI
=====================================

.. image:: {static}/images/travis-ci.png
   :alt: call_method microbenchmark
   :align: right
   :target: https://travis-ci.org/

While the Linux jobs of Travis CI usually takes 15 minutes, up to 30 minutes in
the worst case, the macOS job of Travis CI regulary took longer than 30
minutes, sometimes longer than 1 hour.

While the macOS job was optional, sometimes it gone mad and prevented a PR to
be merged. Cancelling the job marked Travis CI as failed on a PR, so it was
still not possible to merge the PR, whereas, again, the job is marked as
optional ("Allowed Failure").

Moreover, when the macOS job failed, the failure was not reported on the PR,
since the job was marked as optional. The only way to notify a failure was to
go to Travis CI and wait at least 30 minutes (whereas the Linux jobs already
completed and it was already possible merge a PR...).

I sent a first mail in June: `[python-committers] macOS Travis CI job became
mandatory?
<https://mail.python.org/pipermail/python-committers/2017-June/004661.html>`_

In september, we decided to remove the macOS job during the CPython sprint at
Instagram (see my previous `New C API <{filename}/new_python_c_api.rst>`_
article), to not slowdown our development speed (`bpo-31355 <https://bugs.python.org/issue31355>`__). I sent another
email to announce the change: `[python-committers] Travis CI: macOS is now
blocking -- remove macOS from Travis CI?
<https://mail.python.org/pipermail/python-committers/2017-September/004824.html>`_.

After the sprint, it was decided to not add again the macOS job, since we have
3 macOS buildbots. It's enough to detect regressions specific to macOS.

After the removal of the macOS end, at the end of september, Travis CI
published an article about the bad performances of their macOS fleet: `Updating
Our macOS Open Source Offering
<https://blog.travis-ci.com/2017-09-22-macos-update>`_. Sadly, the article
confirms that the situation is not going to evolve quickly.


New test.pythoninfo utility
===========================

To understand the "Segfault when readline history is more then 2 * history
size" crash of `bpo-29854 <https://bugs.python.org/issue29854>`__, I modified
``test_readline`` to log libreadline  versions.  I also added
``readline._READLINE_LIBRARY_VERSION``. My colleague **Nir Soffer** wrote the
final readline fix: skip the test on old readline versions.

As a follow-up of this issue, I added a new ``test.pythoninfo`` program to log
many information to debug Python tests (`bpo-30871 <https://bugs.python.org/issue30871>`__). pythoninfo is now run on
Travis CI, AppVeyor and buildbots.

Example of output::

    $ ./python -m test.pythoninfo
    (...)
    _decimal.__libmpdec_version__: 2.4.2
    expat.EXPAT_VERSION: expat_2.2.4
    gdb_version: GNU gdb (GDB) Fedora 8.0.1-26.fc26
    locale.encoding: UTF-8
    os.cpu_count: 4
    (...)
    time.timezone: -3600
    time.tzname: ('CET', 'CEST')
    tkinter.TCL_VERSION: 8.6
    tkinter.TK_VERSION: 8.6
    tkinter.info_patchlevel: 8.6.6
    zlib.ZLIB_RUNTIME_VERSION: 1.2.11
    zlib.ZLIB_VERSION: 1.2.11

``test.pythoninfo`` can be easily extended to log more information, without
polluting the output of the Python test suite which is already too verbose and
very long.


Revert commits if buildbots are broken
======================================

Thanks to my work done last months on the Python test suite, the buildbots are
now very reliable. When a buildbot fails, it becomes very likely that it's a
real regression, and not a random failure caused by a bug in the Python test
suite.

I proposed a new rule: **revert a change if it breaks builbots and the but
cannot be fixed easily**:

    So I would like to set a new rule: if I'm unable to fix buildbots
    failures caused by a recent change quickly (say, in less than 2
    hours), I propose to revert the change.

    It doesn't mean that the commit is bad and must not be merged ever.
    No. It would just mean that we need time to work on fixing the issue,
    and it shouldn't impact other pending changes, to keep a sane master
    branch.

`[python-committers] Revert changes which break too many buildbots
<https://mail.python.org/pipermail/python-committers/2017-June/004588.html>`__.

test_datetime
-------------

The first revert was an enhancement of test_datetime, `bpo-30822
<https://bugs.python.org/issue30822>`__::

    commit 98b6bc3bf72532b784a1c1fa76eaa6026a663e44
    Author: Utkarsh Upadhyay <mail@musicallyut.in>
    Date:   Sun Jul 2 14:46:04 2017 +0200

        bpo-30822: Fix testing of datetime module. (#2530)

        Only C implementation was tested.

I wrote an email to announce the revert: `[python-committers] Revert changes
which break too many buildbots
<https://mail.python.org/pipermail/python-committers/2017-July/004673.html>`__.

It took 15 days to decide how to fix properly the issue (exclude ``tzdata``
from test resources). I don't regret my revert, since having broken buildbots
for 15 days would be very annoying.

python-gdb.py fix
-----------------

I also reverted this commit of `bpo-30983 <https://bugs.python.org/issue30983>`__::

    commit 2e0f4db114424a00354eab889ba8f7334a2ab8f0
    Author: Bruno "Polaco" Penteado <polaco@gmail.com>
    Date:   Mon Aug 14 23:14:17 2017 +0100

        bpo-30983: eval frame rename in pep 0523 broke gdb's python extension (#2803)

        pep 0523 renames PyEval_EvalFrameEx to _PyEval_EvalFrameDefault while the gdb python extension only looks for PyEval_EvalFrameEx to understand if it is dealing with a frame.

        Final effect is that attaching gdb to a python3.6 process doesnt resolve python objects. Eg. py-list and py-bt dont work properly.

        This patch fixes that. Tested locally on python3.6

My comment on the issue:

    I chose to revert the change because I don't have the bandwidth right now
    to investigate why the change broke test_gdb.

    I'm surprised that a change affecting python-gdb.py wasn't properly tested
    manually using test_gdb.py :-( I understand that Travis CI doesn't have gdb
    and/or that the test pass in some cases?

    The revert only gives us more time to design the proper solution.

Hopefully, a new fixed commit was pushed 4 days later and this one didn't break
buildbots!


Fix the Python test suite
=========================

As usual, I spent a significant part of my time to fix bugs in the Python test
suite to make it more reliable and more "usable".

* `bpo-30822 <https://bugs.python.org/issue30822>`__: Exclude ``tzdata`` from ``regrtest --all``. When running the test suite
  using ``--use=all`` / ``-u all``, exclude ``tzdata`` since it makes
  test_datetime too slow (15-20 min on some buildbots, just this single test
  file) which then times out on some buildbots. ``-u tzdata`` must now be
  enabled explicitly.
* `bpo-30188 <https://bugs.python.org/issue30188>`__, test_nntplib: Catch also
  ssl.SSLEOFError in NetworkedNNTPTests.setUpClass(), not only EOFError.
  (*Sadly, test_nntplib still fails randomly with EOFError or SSLEOFError...*)
* `bpo-31009 <https://bugs.python.org/issue31009>`__: Fix
  ``support.fd_count()`` on Windows. Call ``msvcrt.CrtSetReportMode()`` to not
  kill the process nor log any error on stderr on os.dup(fd) if the file
  descriptor is invalid.
* `bpo-31034 <https://bugs.python.org/issue31034>`__: Reliable signal handler for test_asyncio. Don't rely on the
  current SIGHUP signal handler, make sure that it's set to the "default"
  signal handler: SIG_DFL. A colleague reported me that the Python test suite
  hangs on running test_subprocess_send_signal() of test_asyncio. After
  analysing the issue, it seems like the test hangs because the RPM package
  builder ignores SIGHUP.
* `bpo-31028 <https://bugs.python.org/issue31028>`__: Fix test_pydoc when run
  directly. Fix ``get_pydoc_link()``: get the absolute path to ``__file__`` to
  prevent relative directories.
* `bpo-31066 <https://bugs.python.org/issue31066>`__: Fix
  ``test_httpservers.test_last_modified()``. Write the temporary file on disk
  and then get its modification time.
* `bpo-31173 <https://bugs.python.org/issue31173>`__: Rewrite WSTOPSIG test of test_subprocess.

  The current ``test_child_terminated_in_stopped_state()`` function test creates a
  child process which calls ``ptrace(PTRACE_TRACEME, 0, 0)`` and then crash
  (SIGSEGV). The problem is that calling ``os.waitpid()`` in the parent process is
  not enough to close the process: the child process remains alive and so the
  unit test leaks a child process in a strange state. Closing the child process
  requires non-trivial code, maybe platform specific.

  Remove the functional test and replaces it with an unit test which mocks
  ``os.waitpid()`` using a new ``_testcapi.W_STOPCODE()`` function to test the
  ``WIFSTOPPED()`` path.
* `bpo-31008 <https://bugs.python.org/issue31008>`__: Fix asyncio
  test_wait_for_handle on Windows, tolerate a difference of 50 ms.
* `bpo-31235 <https://bugs.python.org/issue31235>`__: Fix ResourceWarning in
  test_logging: always close all asyncore dispatchers (ignoring errors if any).
* `bpo-30121 <https://bugs.python.org/issue30121>`__: Add test_subprocess.test_nonexisting_with_pipes(). Test the Popen
  failure when Popen was created with pipes. Create also NONEXISTING_CMD
  variable in test_subprocess.py.
* `bpo-31250 <https://bugs.python.org/issue31250>`__, test_asyncio: fix EventLoopTestsMixin.tearDown(). Call
  doCleanups() to close the loop after calling executor.shutdown(wait=True).
* test_ssl: Implement timeout in ssl_io_loop(). The timeout parameter was not
  used.
* `bpo-31448 <https://bugs.python.org/issue31448>`__, test_poplib: Call POP3.close(), don't close close directly the
  sock attribute to fix a ResourceWarning.
* os.test_utime_current(): tolerate 50 ms delta.
* `bpo-31135 <https://bugs.python.org/issue31135>`__: ttk: fix LabeledScale and OptionMenu destroy() method. Call the
  parent destroy() method even if the used attribute doesn't exist. The
  LabeledScale.destroy() method now also explicitly clears label and scale
  attributes to help the garbage collector to destroy all widgets.
* `bpo-31479 <https://bugs.python.org/issue31479>`__: Always reset the signal alarm in tests. Use
  the ``try: ... finally: signal.signal(0)`` pattern to make sure that tests
  don't "leak" a pending fatal signal alarm. Move some signal.alarm() calls
  into the try block.

**Next report:** `My contributions to CPython during 2017 Q3: Part 2 (dangling
threads) <{filename}/python_contrib_2017q3_part2.rst>`_.
