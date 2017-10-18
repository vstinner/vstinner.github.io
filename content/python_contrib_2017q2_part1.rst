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
* Python 3.6.0 regression
* struct.Struct.format type
* Optimization: one less syscall per open() call
* make regen-all

Previous report: `My contributions to CPython during 2017 Q1
<{filename}/python_contrib_2017q1.rst>`_.

Next reports:

* `My contributions to CPython during 2017 Q2 (part 2)
  <{filename}/python_contrib_2017q2_part2.rst>`_.
* `My contributions to CPython during 2017 Q2 (part 3)
  <{filename}/python_contrib_2017q2_part3.rst>`_.
* `My contributions to CPython during 2017 Q3
  <{filename}/python_contrib_2017q3.rst>`_.

Next parts


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
