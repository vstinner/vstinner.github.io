+++++++++++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q2 (part 1)
+++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2017-07-13 16:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q2-part1
:authors: Victor Stinner

This is the first part of my contributions to `CPython
<https://www.python.org/>`_ during 2017 Q2 (april, may, june):

* Statistics
* Buidbots and test.bisect
* Mentoring
* Python 3.6.0 regression
* struct.Struct.format type
* Optimization: one less syscall per open() call
* make regen-all
* Trick bug: Clang 4.0, dtoa and strict aliasing
* sigwaitinfo() race condition in test_eintr

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
with Mercurial merges (ex: commit into 3.6, then merge into master).


Buildbots and test.bisect
=========================

Since this article became way too long, I splitted it into sub-articles:

* `New Python test.bisect tool <{filename}/python_test_bisect.rst>`_
* `Work on Python buildbots, 2017 Q2 <{filename}/buildbots_2017q2.rst>`_


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
FASTCALL optimizations :-( A special way to call C builtin functions was broken::

    from datetime import datetime
    next(iter(datetime.now, None))

This code raises a ``StopIteration`` exception instead of formatting the
current date and time.

It's even worse. I was aware of the bug, it was already fixed it in master, but
I just forgot to backport my fix: bpo-30524, fix _PyStack_UnpackDict().

To prevent regressions, I wrote exhaustive unit tests on the 3 FASTCALL
functions, commit: `bpo-30524: Write unit tests for FASTCALL
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
incompatible change on python-dev, but then nothing happened during longer
than...  2 years!

In March 2017, I converted the old Martin's patch into a new GitHub pull
request. **Serhiy** asked again to write to python-dev, so I wrote:
`Issue #21071: change struct.Struct.format type from bytes to str
<https://mail.python.org/pipermail/python-dev/2017-March/147688.html>`_. And...
I got zero answer.

Well, I didn't expect any, since it's a trivial change, and I don't expect that
anyone rely on the exact ``format`` attribute type.  Moreover, the
``struct.Struct`` constructor already accepts bytes and str types. If the
attribute is passed to the constructor: it just works.

In June 2017, Serhiy Storchaka replied to my email: `If nobody opposed to this
change it will be made in short time.
<https://mail.python.org/pipermail/python-dev/2017-June/148360.html>`_

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

Old broken make touch
---------------------

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

New shiny make regen-all
------------------------

I decided to rewrite the Makefile to not regenerate generated files based on
the file modification time anymore. Instead, I added a new ``make regen-all``
command to regenerate explicitly all generated files. Basically, I replaced
``make touch`` with ``make regen-all``.

Changes:

* Add a new ``make regen-all`` command to rebuild all generated files
* Add subcommands to only generate specific files:

  - ``regen-ast``: Include/Python-ast.h and Python/Python-ast.c
  - ``regen-grammar``: Include/graminit.h and Python/graminit.c
  - ``regen-importlib``: Python/importlib_external.h and Python/importlib.h
  - ``regen-opcode``: Include/opcode.h
  - ``regen-opcode-targets``: Python/opcode_targets.h
  - ``regen-typeslots``: Objects/typeslots.inc

* Rename ``PYTHON_FOR_GEN`` to ``PYTHON_FOR_REGEN``
* pgen is now only built by ``make regen-grammar``
* Add ``$(srcdir)/`` prefix to paths to source files to handle correctly
  compilation outside the source directory
* Remove ``make touch``, ``Tools/hg/hgtouch.py`` and ``.hgtouch``

Note: By default, ``$(PYTHON_FOR_REGEN)`` is no more used nor needed by "make".


Trick bug: Clang 4.0, dtoa and strict aliasing
==============================================

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
