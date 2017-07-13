+++++++++++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q2 (part 3)
+++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2017-07-13 17:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q2-part3
:authors: Victor Stinner

This is the third part of my contributions to `CPython
<https://www.python.org/>`_ during 2017 Q2 (april, may, june):

* Security
* Trick bug: Clang 4.0, dtoa and strict aliasing
* sigwaitinfo() race condition in test_eintr
* FreeBSD test_subprocess core dump

Previous reports:

* `My contributions to CPython during 2017 Q2 (part 1)
  (part 2) <{filename}/python_contrib_2017q2_part1.rst>`_.
* `My contributions to CPython during 2017 Q2 (part 2)
  (part 2) <{filename}/python_contrib_2017q2_part2.rst>`_.


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

See the `Status of Python branches
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
script to easily upgrade libexpat: recreate the ``Modules/expat/`` directory
from a libexpat tarball.

My commit:

    bpo-29591: Upgrade Modules/expat to libexpat 2.2 (#2164)

    Remove the configuration (``Modules/expat/*config.h``) of unsupported
    platforms: Amiga, MacOS Classic on PPC32, Open Watcom.

    Remove XML_HAS_SET_HASH_SALT define: it became useless since our local
    expat copy was upgrade to expat 2.1 (it's now expat 2.2.0).

I upgraded libexpat to 2.2 in Pytohn 2.7, 3.4, 3.5, 3.6 and master branches.
I still have a pending pull request for 3.3.

libexpat 2.2.1
--------------

Just after I finally upgraded our libexpat copy to 2.2.0... libexpat 2.2.1 was
released with new security fixes!  See `CVE-2017-9233: Expat 2.2.1
<http://python-security.readthedocs.io/vuln/cve-2017-9233_expat_2.2.1.html>`_

Again, I upgraded libexpat to 2.2.1 in all branches (pending: 3.3), see
bpo-30694. My commit:

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
properly **fix it without breaking backward compatibility**. We had too few
unit tests, and no obvious definition of the *expected* behaviour. I
contributed to the discussed and to polish the fix:

bpo-30500 commit:

    Fix urllib.parse.splithost() to correctly parse fragments. For example,
    ``splithost('//127.0.0.1#@evil.com/')`` now correctly returns the
    ``127.0.0.1`` host, instead of treating ``@evil.com`` as the host in an
    authentification (``login@host``).

Fix applied to master, 3.6, 3.5, 3.4 and 2.7; pending pull request for 3.3.

Travis CI
---------

I also wrote a pull request to enable Travis CI and AppVeyor CI on Python 3.3
and 3.4 branches, to test security on CI. These changes are complex and not
merged yet, but I am now confident that the CI will be enabled on 3.4!

My PR for Python 3.4: `[3.4] Backport CI config from master
<https://github.com/python/cpython/pull/2475>`_.


Tricky bug: Clang 4.0, dtoa and strict aliasing
===============================================

Aha, another funny story about compilers: bpo-30104.

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
language. Two months before I saw the same bug, he already reported the bug to
FreeBSD: `lang/julia: fails to build with clang 4.0
<https://bugs.freebsd.org/216770>`_, and to clang: `After r280351: if/else
blocks incorrectly optimized away?
<https://bugs.llvm.org//show_bug.cgi?id=31928>`_.

The "problem" is that clang
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

The tricky test_eintr
---------------------

When I wrote and implemented the `PEP 475, Retry system calls failing with
EINTR <https://www.python.org/dev/peps/pep-0475/>`_, I didn't expect so many
annoying bugs of the newly written ``test_eintr`` unit test. This test calls
system calls while sending signals every 100 ms. Usually the test tries to
block on a system call during at least 200 ms, to make sure that the syscall
was interrupted at least once by a signal, to check that Python correctly
retries the interrupted system call.

Since the PEP was implemented, I already fixed many race conditions in
``test_eintr``, but there was still a race condition on the ``sigwaitinfo()``
unit test. *Sometimes* on a *few specific buildbots* (FreeBSD), the test fails
randomly.

First attempt
-------------

My first attempt was the `bpo-25277 <http://bugs.python.org/issue25277>`_,
opened at 2015-09-30. I added faulthandler to dump tracebacks if a test hangs
longer than 10 minutes. Then I changed the sleep from 200 ms to 2 seconds in
the ``sigwaitinfo()`` test... just to make the bug less likely, but using a
longer sleep doesn't fix the root issue.

Second attempt
--------------

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

Third attempt
-------------

My third attempt is the bpo-30320, opened at 2017-05-09. This time, I really
wanted to fix *all* buildbot random failures. Since I was now able to reproduce
the bug on my FreeBSD VM, I was able to write a fix but also to check that:

* sigwaitinfo() and sigtimedwait() fail with EINTR and Python automatically
  restarts the interrupted syscall
* I hacked the test file to only run the sigwaitinfo() and sigtimedwait() unit
  tests. Running the test in a loop doesn't fail: I ran the test during 5
  minutes in 10 shells (tests running 10 times in parallel) => no failure, the
  race condition seems to be gone.

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

To be honest, I wasn't really confident, when I pushed my fix, that blocking
the waited signal is the proper fix.

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


