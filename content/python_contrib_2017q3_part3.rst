+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q3: Part 3 (funny bugs)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2017-10-19 16:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q3-part3
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q3
(july, august, september), Part 3 (funny bugs).

Previous report: `My contributions to CPython during 2017 Q3: Part 2 (dangling
threads) <{filename}/python_contrib_2017q3_part2.rst>`_.

Summary:

* FreeBSD bug: minor() device regression
* regrtest snowball effect when hunting memory leaks
* Bugfixes
* Other Changes


FreeBSD bug: minor() device regression
======================================

.. image:: {filename}/images/freebsd.png
   :alt: Logo of the FreeBSD project
   :target: https://www.freebsd.org/

`bpo-31044 <https://bugs.python.org/issue31044>`__: The test_makedev() of
test_posix started to fail in the build 632 (Wed Jul 26 10:47:01 2017) of AMD64
FreeBSD CURRENT. The test failed on Debug, but also Non-Debug buildbots, in
master and 3.6 branches. It looks more like a change on the buildbot, maybe a
FreeBSD upgrade?

Thanks to **koobs**, I have a SSH access to the buildbot. I was able to
reproduce the bug manually. I noticed that minor() truncates most significant
bits.

I continued my analysis and I found that, at May 23, the FreeBSD ``dev_t`` type
changed from 32 bits to 64 bits in the kernel, but the ``minor()`` userland
function was not updated.

I reported a bug to FreeBSD: `Bug 221048 - minor() truncates device number to
32 bits, whereas dev_t type was extended to 64 bits
<https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=221048>`_.

In the meanwhile, I skipped test_posix.test_makedev() on FreeBSD if ``dev_t``
is larger than 32-bit.

Hopefully, the FreeBSD bug was quickly fixed!


regrtest snowball effect when hunting memory leaks
==================================================

While trying to fix all reference leaks on the new Windows and Linux "Refleaks"
buildbots, I reported the bug `bpo-31217
<https://bugs.python.org/issue31217>`__::

    test_code leaked [1, 1, 1] memory blocks, sum=3

Two weeks after reporting the bug, I was able to reproduce the bug, but **only
with Python compiled in 32-bit mode**. Strange.

I spent one day to understand the bug. I removed as much as possible while
making sure that I can still reproduce the bug. At the end, I wrote `leak2.py
<https://bugs.python.org/file47114/leak2.py>`_ which reproduces the bug with a
single import: ``import sys``. Even if the script is only 86 lines long, I was
still unable to understand the bug.

My first hypothesis:

    It seems like the "leak" is the call to ``sys.getallocatedblocks()`` which
    creates a new integer, and the integer is kept alive between two loop
    iterations.

**Antoine Pitrou** rejected it:

    I doubt it. If that was the case, the reference count would increase as
    well.

It was Antoine Pitrou who understood the bug::

    Ahah.
    Actually, it's quite simple :-) On 64-bit Python:

    >>> id(82914 - 82913) == id(1)
    True

    On 32-bit Python:

    >>> id(82914 - 82913) == id(1)
    False

    So the first non-zero alloc_delta really has a snowball effect, as it
    creates new memory block which will produce a non-zero alloc_delta on the
    next run, etc.

I implemented Antoine's idea to fix the bug, `commit
<https://github.com/python/cpython/commit/6c2feabc5dac2f3049b15134669e9ad5af573193>`__::

    Use a pool of integer objects to prevent false alarm when checking for
    memory block leaks. Fill the pool with values in -1000..1000 which
    are the most common (reference, memory block, file descriptor)
    differences.

    Co-Authored-By: Antoine Pitrou <pitrou@free.fr>

The bug is probably as old as the code hunting memory leaks.


Bugfixes
========

* `bpo-30891 <https://bugs.python.org/issue30891>`__: Second fix for
  importlib ``_find_and_load()`` to handle correctly parallelism with threads.
  Call ``sys.modules.get()`` in the ``with _ModuleLockManager(name):`` block to
  protect the dictionary key with the module lock and use an atomic get to
  prevent race conditions.
* `bpo-31019 <https://bugs.python.org/issue31019>`__:
  ``multiprocessing.Process.is_alive()`` now removes the process from the
  ``_children set`` if the process completed. The change prevents leaking
  "dangling" processes.
* `bpo-31326 <https://bugs.python.org/issue31326>`__, ``concurrent.futures``:
  ``ProcessPoolExecutor.shutdown()`` now explicitly closes the call queue.
  Moreover, ``shutdown(wait=True)`` now also joins the call queue thread, to
  prevent leaking a dangling thread.
* `bpo-31170 <https://bugs.python.org/issue31170>`__: Update libexpat from
  2.2.3 to 2.2.4: fix copying of partial characters for UTF-8 input (`libexpat
  bug 115 <https://github.com/libexpat/libexpat/issues/115>`_). Later, I also
  wrote non-regression tests for this bug (libexpat doesn't have any test
  for this bug).
* `bpo-31499 <https://bugs.python.org/issue31499>`__, ``xml.etree``:
  ``xmlparser_gc_clear()`` now sets self.parser to ``NULL`` to prevent a crash
  in ``xmlparser_dealloc()`` if ``xmlparser_gc_clear()`` was called previously
  by the garbage collector, because the parser was part of a reference cycle.
  Fix co-written with **Serhiy Storchaka**.
* `bpo-30892 <https://bugs.python.org/issue30892>`__: Fix ``_elementtree``
  module initialization (accelerator of ``xml.etree``), handle correctly
  ``getattr(copy, 'deepcopy')`` failure to not fail with an assertion error.


Other Changes
=============

* `bpo-30866 <https://bugs.python.org/issue30866>`__: Add _testcapi.stack_pointer(). I used it to write the "Stack
  consumption" section of a previous report: `My contributions to CPython
  during 2017 Q1 <{filename}/python_contrib_2017q1.rst>`_
* _ssl_: Fix compiler warning. Cast Py_buffer.len (Py_ssize_t, signed) to
  size_t (unsigned) to prevent the "comparison between signed and unsigned
  integer expressions" warning.
* `bpo-30486 <https://bugs.python.org/issue30486>`__: Make cell_set_contents() symbol private. Don't export the
  ``cell_set_contents()`` symbol in the C API.
