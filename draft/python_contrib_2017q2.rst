++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q2
++++++++++++++++++++++++++++++++++++++++++

:date: 2017-07-13 16:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q2
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q2
(april, may, june):

* Statistics
* Buidbots and test.bisect
* Mentoring
* Python 3.6.0 regression
* struct.Struct.format type
* Optimization: one less syscall per open() call
* make regen-all
* Trick bug: Clang 4.0, dtoa and strict aliasing
* sigwaitinfo() race condition in test_eintr
* FreeBSD test_subprocess core dump
* Security
* GitHub migration (continued)
* Refleaks
* Contributions
* Test fixes
* Stars of the cpython GitHub project

Previous report: `My contributions to CPython during 2017 Q1
<{filename}/python_contrib_2017q1.rst>`_.


Statistics
==========

::

    # All branches
    $ git log --after=2017-03-31 --before=2017-06-30 --reverse --branches='*' --author=Stinner > 2017Q2
    $ grep '^commit ' 2017Q2|wc -l
    222

    # Master branch only
    $ git log --after=2017-03-31 --before=2017-06-30 --reverse --author=Stinner origin/master|grep '^commit '|wc -l
    85

Statistics: **85** commits in the master branch, a **total of 222 commits**:
most (but not all) of the remaining 137 commits are cherry-picked backports to
2.7, 3.5 and 3.6 branches.

Note: I didn't use ``--no-merges`` since we don't use merge anymore, but ``git
cherry-pick -x``, to *backport* fixes. Before GitHub, we used **forwardport**
with Mercurial merges.


Buildbots and test.bisect
=========================

See the `Work on Python buildbots, 2017 Q2 <{filename}/buildbots_2017q2.rst>`_
article.

See the `New Python test.bisect tool <{filename}/python_test_bisect.rst>`_
article.


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


Python 3.6.0 regression
=======================

I am ashamed, I introduced a tricky regression in Pyton 3.6.0 with my work on
FASTCALL optimizations. A special way to call C builtin functions was broken::

    from datetime import datetime
    next(iter(datetime.now, None))

This code raises a ``StopIteration`` exception instead of formatting the
current date and time.

It's even worse: I was aware of the bug and already fixed it in master, but I
just forgot to backport my fix: bpo-30524, fix _PyStack_UnpackDict().

To prevent regressions, I now wrote exhaustive unit tests on all C functions
calling functions: the commit `bpo-30524: Write unit tests for FASTCALL
<https://github.com/python/cpython/commit/3b5cf85edc188345668f987c824a2acb338a7816>`__


struct.Struct.format type
=========================

Sometimes, fixing a bug can take longer than expected. In March 2014, **Zbyszek
Jędrzejewski-Szmek** reported a bug on the ``format`` attribute of the
``struct.Struct`` class: this attribute type is bytes, whereas a Unicode string
(str) was expected.

I proposed to "just" change the attribute type in December 2014, but it was an
incompatible change which would break the backward compatibility. **Martin
Panter** agreed and wrote a patch. **Serhiy Storchaka** asked to discuss such
incompatible change on python-dev, but then nothing happened during longer than
2 years.

In March 2017, I converted the old Martin's patch into a new GitHub pull
request. **Serhiy** asked again to write to python-dev, so I wrote:
[Python-Dev] `Issue #21071: change struct.Struct.format type from bytes to str
<https://mail.python.org/pipermail/python-dev/2017-March/147688.html>`_. And...
I got zero answer.

Well, I didn't expect any, since it's a trivial change, and I don't expect that
anyone rely on the exact ``format`` attribute type.  Moreover, the
``struct.Struct`` constructor already accepts bytes and str types, if the
attribute is passed to the constructor: it just works.

In June 2017, Serhiy Storchaka replied to my email: `If nobody opposed to this
change it will be made in short time.
<https://mail.python.org/pipermail/python-dev/2017-June/148360.html>`_.

Since nobody replied, again, I just merged my pull request. So it took **3
years and 3 months** to change the type of an uncommon attribute :-)

Note: I never used this attribute... Before reading this issue, I didn't even
know that the ``struct`` module has a ``struct.Struct`` type...


Optimization: one less syscall per open() call
==============================================

In bpo-30228, I modified FileIO.seek() and FileIO.tell() methods to now set the
internal seekable attribute to avoid one ``fstat()`` syscall per Python open()
call in buffered or text mode.

The seekable property is now also more reliable since its value is
set correctly on memory allocation failure.

I still have a second pending pull request to remove one more ``fstat()``
syscall: `bpo-30228: TextIOWrapper uses abs_pos, not tell()
<https://github.com/python/cpython/pull/1385>`_.


make regen-all
==============

I started to look at bpo-23404, because the Python compilation failed on the
"AMD64 FreeBSD 9.x 3.x" buildbot when trying to regenerate the
``Include/opcode.h`` file.

We had a ``make touch`` command to workaround this file timestamp issue, but
the command uses Mercurial, whereas Python migrated to Git last february. The
buildobt "touch" step was removed because ``make touch`` was broken.

I was always annoyed by the Makefile which wants to regenerate generated files
because of wrong file modification time, whereas the generated files were
already up to date.

The bug annoyed me on OpenIndiana where "make touch" didn't work beause the
operating system only provides Python 2.6 and Mercurial didn't work on this
version.

The bug also annoyed me on FreeBSD which has no "python" command, only
"python2.7", and so required manual steps.

The bug was also a pain point when trying to cross-compile Python.

I decided to rewrite the Makefile to not regenerate generated files based on
the file modification time anymore. Instead, I added a new ``make regen-all``
command to regenerate explicitly all generated files. Basically, I replaced
``make touch`` with ``make regen-all``.

Changes:

* Add a new "make regen-all" command to rebuild all generated files
* Add subcommands to only generate specific files:

  - regen-ast: Include/Python-ast.h and Python/Python-ast.c
  - regen-grammar: Include/graminit.h and Python/graminit.c
  - regen-importlib: Python/importlib_external.h and Python/importlib.h
  - regen-opcode: Include/opcode.h
  - regen-opcode-targets: Python/opcode_targets.h
  - regen-typeslots: Objects/typeslots.inc

* Rename PYTHON_FOR_GEN to PYTHON_FOR_REGEN
* pgen is now only built by "make regen-grammar"
* Add $(srcdir)/ prefix to paths to source files to handle correctly
  compilation outside the source directory
* Remove "make touch", Tools/hg/hgtouch.py and .hgtouch

Note: By default, $(PYTHON_FOR_REGEN) is no more used nor needed by "make".


Trick bug: Clang 4.0, dtoa and strict aliasing
==============================================

Aha, another funny story about compilers.

I noticed that the following tests started to fail on the "AMD64 FreeBSD
CURRENT Debug 3.x" buildbot:

* test_cmath
* test_float
* test_json
* test_marshal
* test_math
* test_statistics
* test_strtod

First, I bet on a libc change on FreeBSD. Then, I found that test_strtod fails
on FreeBSD using clang 4.0, but pass on FreeBSD using clang 3.8.

I started to bisect the code on Linux using a subset of ``Python/dtoa.c``:

* Start (integrated in CPython code base): 2,876 lines
* dtoa2.c (standalone): 2,865 lines
* dtoa5.c: 50 lines

Extract of dtoa5.c::

    typedef union { double d; uint32_t L[2]; } U;

    struct Bigint { int wds; };

    static double
    ratio(struct Bigint *a)
    {
        U da, db;
        int k, ka, kb;
        double r;

        da.d = 1.682;
        ka = 6;
        db.d = 1.0;
        kb = 5;
        k = ka - kb + 32 * (a->wds - 12);
        printf("k=%i\n", k);

        if (k > 0)
            da.L[1] += k * 0x100000;
        else {
            k = -k;
            db.L[1] += k * 0x100000;
        }
        r = da.d / db.d;
        /* r == 3.364 */
        return r;
    }

Even if I had a very short C code (50 lines) reproducing the bug, I was still
unable to understand the bug. I read many articles about aliasing, and I still
don't understand fully the bug... I suggest you these two good articles:

* `Understanding Strict Aliasing
  <http://cellperformance.beyond3d.com/articles/2006/06/understanding-strict-aliasing.html>`_
  (Mike Acton, June 1, 2006)
* `Demystifying The Restrict Keyword
  <http://cellperformance.beyond3d.com/articles/2006/05/demystifying-the-restrict-keyword.html>`_
  (Mike Acton, May 29, 2006)

Anyway, I wanted to report the bug to clang (LLVM), but the LLVM bug tracker was
migrating and I was unable to subscribe to get an account!

In the meanwhile, **Dimitry Andric**, a FreeBSD developer, told me that he got
*exactly* the same clang 4.0 issue with "dtoa.c" in the *julia* programming
language. He reported the bug to FreeBSD: `lang/julia: fails to build with
clang 4.0 <https://bugs.freebsd.org/216770>`_, and to clang: `After r280351:
if/else blocks incorrectly optimized away?
<https://bugs.llvm.org//show_bug.cgi?id=31928>`_. The "problem" is that clang
developers disagree that it's a bug. In short, the discussion was around the C
standard: does clang respect C aliasing rules or not? At the end, clang
developers consider that they are right to optimize. To summarize:

    It's a bug in the code, not in the compiler

So I made a first change to use the ``-fno-strict-aliasing`` flag when Python
is compiled with clang:

    Python/dtoa.c is not compiled correctly with clang 4.0 and
    optimization level -O2 or higher, because of an aliasing issue on
    the double/ULong[2] union.

But this change can make Python slower when compiled on clang, so I was asked
to only compile ``Python/dtoa.c`` with this flag:

    On clang, only compile dtoa.c with -fno-strict-aliasing, use strict
    aliasing to compile all other C files.


sigwaitinfo() race condition in test_eintr
==========================================

When I wrote and implemented the `PEP 475, Retry system calls failing with
EINTR <https://www.python.org/dev/peps/pep-0475/>`_, I didn't expect so many
annoying bugs of the newly written ``test_eintr`` unit test. This test calls
system calls while sending signals every 100 ms. Usually the test tries to
block on a system call during at least 200 ms, to make sure that the syscall
was interrupted at least once by a signal.

Since the PEP was implemented, I already fixed many race conditions in
``test_eintr``, but there was still a race condition on the ``sigwaitinfo()``
unit test. *Sometimes* on a *few specific buildbots* (FreeBSD), the test fails
randomly.

My first attempt was the `bpo-25277 <http://bugs.python.org/issue25277>`_,
opened at 2015-09-30. I added faulthandler to dump tracebacks if a test hangs
longer than 10 minutes. Then I changed the sleep from 200 ms to 2 seconds in
the ``sigwaitinfo()`` test... just to reduce the risk of race condition, but
using a longer sleep doesn't fix the root issue.

My second attempt was the `bpo-25868 <http://bugs.python.org/issue25868>`_,
opened at 2015-12-15. I added a pipe to "synchronize the parent and the child
processes", to try to make the sigwaitinfo() test a little bit more reliable. I
also reduced the sleep from 2 seconds to 100 ms.

7 minutes after my fix, **Martin Panter** wrote:

    With the pipe, there is still a potential race after the parent writes to
    the pipe and before sigwaitinfo() is invoked, versus the child sleep()
    call.

    What do you think of my suggestion to block the signal? Then (in theory) it
    should be robust, rather than relying on timing.

I replied that I wasn't sure that sigwaitinfo() EINTR error was still tested if
we make his proposed change.

One month later, Martin wrote a patch but I was unable to take a decision on
his change. In september 2016, Martin noticed a new test failure on the FreeBSD
9 buildbot.

My third attempt is the bpo-30320, opened at 2017-05-09. This time, I really
wanted to fix *all* buildbot random failures. Since I was able to reproduce the
bug, I was able to write a fix but also to check that:

* sigwaitinfo() and sigtimedwait() fail with EINTR and Python automatically
  restarts the interrupted syscall
* running the test in a loop doesn't fail: I ran the test during 5 minutes in 10
  shells (tests running 10 times in parallel) => no failure, the race condition
  seems to be gone. I hacked the test file to only run the sigwaitinfo() and
  sigtimedwait() unit tests.

So I `pushed my fix
<https://github.com/python/cpython/commit/211a392cc15f9a7b1b8ce65d8f6c9f8237d1b77f>`_:

    bpo-30320: test_eintr now uses pthread_sigmask()

    Rewrite sigwaitinfo() and sigtimedwait() unit tests for EINTR using
    pthread_sigmask() to fix a race condition between the child and the
    parent process.

    Remove the pipe which was used as a weak workaround against the race
    condition.

    sigtimedwait() is now tested with a child process sending a signal
    instead of testing the timeout feature which is more unstable
    (especially regarding to clock resolution depending on the platform).

To be honest, I wasn't really confident when I pushed my fix that blocking the
waited signal is the proper fix.

So it took **1 year and 8 months** to really find and fix the root bug.

Sadly, while I was working on dozens of other bugs, I completely lost track of
Martin's patch, even if I opened the bpo-25868. Sorry Martin for forgotting to
review your patch! But when you wrote it, I was unable to test that
sigwaitinfo() was still failing with EINTR.


FreeBSD test_subprocess core dump
=================================

bpo-30448: During one month, some FreeBSD buildbots was emitting this warning
which started to annoy me, since I was trying to fix *all* buildbots warnings::

    Warning -- files was modified by test_subprocess
      Before: []
      After:  ['python.core']

I tried and failed to reproduce the warning on my FreeBSD 11 VM. I also asked a
friend who also failed to reproduce it. I was developping my ``test.bisect``
tool and I wanted to guess access to a machine to reproduce the bug, but I
failed to find such machine.

Later, **Kubilay Kocak** aka *koobs* gave me access to his FreeBSD buildbots
and in a few seconds with my new test.bisect tool, I identified that the
``test_child_terminated_in_stopped_state()`` test triggers a deliberate crash,
but doesn't disable core dump creation. The fix is simple, use
``test.support.SuppressCrashReport`` context manager.

Maybe only FreeBSD 10 and older dump a core on this specific test, not FreeBSD
11. I don't know why. The test is special, it tests a process which is traced
using ``ptrace()``.


Security
========

expat 2.2
---------

See `CVE-2016-0718: expat 2.2, bug #537
<http://python-security.readthedocs.io/vuln/cve-2016-0718_expat_2.2_bug_537.html>`_.

2.2::

    bpo-29591: Upgrade Modules/expat to libexpat 2.2 (#2164)

    * bpo-29591: Upgrade Modules/expat to libexpat 2.2

    * bpo-29591: Restore Python changes on expat

    * bpo-29591: Remove expat config of unsupported platforms

    Remove the configuration (Modules/expat/*config.h) of unsupported
    platforms:

    * Amiga
    * MacOS Classic on PPC32
    * Open Watcom

    * bpo-29591: Remove useless XML_HAS_SET_HASH_SALT

    The XML_HAS_SET_HASH_SALT define of Modules/expat/expat.h became
    useless since our local expat copy was upgrade to expat 2.1 (it's now
    expat 2.2.0).

Fixed in master, 3.6, 3.5, 2.7. Pending PR for 3.4 and 3.3: XXX.

expat 2.2.1
-----------

See `CVE-2017-9233: Expat 2.2.1
<http://python-security.readthedocs.io/vuln/cve-2017-9233_expat_2.2.1.html>`_

bpo-30694: Upgrade expat copy from 2.2.0 to 2.2.1 to get fixes
of multiple security vulnerabilities including: CVE-2017-9233 (External
entity infinite loop DoS), CVE-2016-9063 (Integer overflow, re-fix),
CVE-2016-0718 (Fix regression bugs from 2.2.0's fix to CVE-2016-0718)
and CVE-2012-0876 (Counter hash flooding with SipHash).
Note: the CVE-2016-5300 (Use os-specific entropy sources like getrandom)
doesn't impact Python, since Python already gets entropy from the OS to set
the expat secret using ``XML_SetHashSalt()``.

Fixed in master, 3.6, 3.5, 2.7. Pending PR for 3.4 and 3.3: XXX.

urllib splithost() vulnerability
--------------------------------

See `bpo-30500: urllib connects to a wrong host
<http://python-security.readthedocs.io/vuln/bpo-30500_urllib_connects_to_a_wrong_host.html>`_
vulnerability.

bpo-30500: Fix urllib.parse.splithost() to correctly parse fragments. For
example, ``splithost('//127.0.0.1#@evil.com/')`` now correctly returns the
``127.0.0.1`` host, instead of treating ``@evil.com`` as the host in an
authentification (``login@host``).

Fix applied to master, 3.6, 3.5 and 2.7. Pending PR for 3.4 and 3.3: XXX.

Travis CI
---------

Pending PR adding Travis CI and AppVeyor to 3.4 and 3.3 branches.


GitHub migration (continued)
============================

SCM, backported to 2.7::

    bpo-27593: Get SCM build info from git instead of hg (#1327)

    Based on commit 5c4b0d063aba0a68c325073f5f312a2c9f40d178 by Ned
    Deily, which is based on original patches by Brett Cannon and Steve
    Dower.

    Remove also the private _Py_svnversion() function and SVNVERSION
    variable.

    Note: Py_SubversionRevision() and Py_SubversionShortBranch() are
    unchanged, they are part of the public API.

::

    bpo-30232: Support Git worktree in configure.ac (#1391)

    Don't test if .git/HEAD file exists, but only if the .git file (or
    directory) exists.


Enhancements
============

* bpo-30265: support.unlink() now only ignores ENOENT and ENOTDIR, instead of
  ignoring all OSError exception.
* bpo-30054: Expose tracemalloc C API: make PyTraceMalloc_Track() and
  PyTraceMalloc_Untrack() functions public. numpy is now able to use
  tracemalloc since numpy 1.13 (XXX check version XXX link to PR).


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


Contributions
=============

* bpo-9850: Deprecate the macpath module. Co-Authored-By: **Chi Hsuan Yen**.
* bpo-30595: Fix multiprocessing.Queue.get(timeout).
  multiprocessing.Queue.get() with a timeout now polls its reader in
  non-blocking mode if it succeeded to aquire the lock but the acquire took
  longer than the timeout. Co-Authored-By: **Grzegorz Grzywacz**.

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


Stars of the cpython GitHub project
===================================

https://mail.python.org/pipermail/python-dev/2017-June/148523.html

GitHub has a showcase page of hosted programming languages:

   https://github.com/showcases/programming-languages

Python is only #11 with 8,539 stars, behind PHP and Ruby!

Hey, you should "like" ("star"?) the CPython project if you like Python!

   https://github.com/python/cpython/
   Click on "Star" at the top right.

https://mail.python.org/pipermail/python-dev/2017-July/148548.html

4 days later, we got +2,389 new stars, thank you! (8,539 => 10,928)

Python moved from the 11th place to the 9th, before Elixir and Julia.

Python is still behind Ruby (12,511) and PHP (12,318), but it's
already much better than before!


 Ben Hoyt benhoyt at gmail.com

I also posted it on reddit.com/r/Python, where it got a bit of traction:
https://www.reddit.com/r/Python/comments/6kg4w0/cpython_recently_moved_to_github_star_the_project/

I just posted on python-list, Terry Jan Reedy



Update, 2017-07-12: 11,467 stars, only 902 stars behind PHP ;-)
