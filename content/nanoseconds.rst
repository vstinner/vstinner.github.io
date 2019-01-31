++++++++++++++++++++++
Python 3.7 nanoseconds
++++++++++++++++++++++

:date: 2018-03-06 16:30
:tags: cpython
:category: python
:slug: python37-pep-564-nanoseconds
:authors: Victor Stinner

Thanks to my `latest change on time.perf_counter()
<{filename}/perf_counter_nanoseconds.rst>`_, all Python 3.7 clocks now use
nanoseconds as integer internally. It became possible to propose again my old
idea of getting time as nanoseconds at Python level and so I wrote a new
:pep:`564` "Add new time functions with nanosecond resolution". While the PEP
was discussed, I also deprecated ``time.clock()`` and removed
``os.stat_float_times()``.

.. image:: {static}/images/clock.jpg
   :alt: Old clock
   :target: https://www.flickr.com/photos/dkalo/2909921582/

time.clock()
============

Since I wrote the :pep:`418` "Add monotonic time, performance counter, and
process time functions" in 2012, I dislike ``time.clock()``. This clock is not
portable: on Windows it mesures wall-clock, whereas it measures CPU time on
Unix. Extract of `time.clock() documentation
<https://docs.python.org/dev/library/time.html#time.clock>`_:

    *Deprecated since version 3.3: The behaviour of this function depends on
    the platform: use perf_counter() or process_time() instead, depending on
    your requirements, to have a well defined behaviour.*

My PEP 418 deprecated ``time.clock()`` in the documentation. In `bpo-31803
<https://bugs.python.org/issue31803>`__, I modified ``time.clock()`` and
``time.get_clock_info('clock')`` to also emit a ``DeprecationWarning`` warning.
I replaced ``time.clock()`` with ``time.perf_counter()`` in tests and demos. I
also removed ``hasattr(time, 'monotonic')`` in ``test_time`` since
``time.monotonic()`` is always available since Python 3.5.

os.stat_float_times()
=====================

The ``os.stat_float_times()`` function was introduced in Python 2.3 to get file
modification times with sub-second resolution (commit `f607bdaa
<https://github.com/python/cpython/commit/f607bdaa77475ec8c94614414dc2cecf8fd1ca0a>`__),
the default was still to get time as seconds (integer). The function was
introduced to get a smooth transition to time as floating point number, to keep
the backward compatibility with Python 2.2.

``os.stat()`` was modified to return time as float by default in Python 2.5
(commit `fe33d0ba
<https://github.com/python/cpython/commit/fe33d0ba87f5468b50f939724b303969711f3be5>`__).
Python 2.5 was released 11 years ago, I consider that people had enough time to
migrate their code to float time :-) I modified ``os.stat_float_times()`` in
Python 3.1 to emit a ``DeprecationWarning`` warning (commit `034d0aa2
<https://github.com/python/cpython/commit/034d0aa2171688c40cee1a723ddcdb85bbce31e8>`__
of `bpo-14711 <https://bugs.python.org/issue14711>`__).

Finally, I removed ``os.stat_float_times()`` in Python 3.7: `bpo-31827
<https://bugs.python.org/issue31827>`__.

Serhiy Storchaka proposed to also remove last three items from
``os.stat_result``. For example, ``stat_result[stat.ST_MTIME]`` could be
replaced with ``stat_result.st_time``.  But I tried to remove these items and
it broke the ``logging`` module, so I decided to leave it unchanged.

PEP 564: time.time_ns()
=======================

Six years ago (2012), I wrote the :pep:`410` "Use decimal.Decimal type for
timestamps" which proposes a large and complex change in all Python functions
returning time to support nanosecond resolution using the ``decimal.Decimal``
type.  The PEP was `rejected for different reasons
<https://mail.python.org/pipermail/python-dev/2012-February/116837.html>`_.

Since all clock now use nanoseconds internally in Python 3.7, I proposed a new
:pep:`564` "Add new time functions with nanosecond resolution". Abstract:

    Add six new "nanosecond" variants of existing functions to the ``time``
    module: ``clock_gettime_ns()``, ``clock_settime_ns()``,
    ``monotonic_ns()``, ``perf_counter_ns()``, ``process_time_ns()`` and
    ``time_ns()``.  While similar to the existing functions without the
    ``_ns`` suffix, they provide nanosecond resolution: they return a number of
    nanoseconds as a Python ``int``.

    The ``time.time_ns()`` resolution is 3 times better than the ``time.time()``
    resolution on Linux and Windows.

People were now convinced by the need for nanosecond resolution, so I
added an "Issues caused by precision loss" section with 2 examples:

* Example 1: measure time delta in long-running process
* Example 2: compare times with different resolution

As for my previous PEP 410, many people proposed many alternatives recorded in
the PEP: sub-nanosecond resolution, modifying ``time.time()`` result type,
different types, different API, a new module, etc.

Hopefully for me, Guido van Rossum quickly approved my PEP for Python 3.7!

Implementaton of the PEP 564
============================

I implemented my PEP 564 in `bpo-31784 <https://bugs.python.org/issue31784>`__
with the commit `c29b585f
<https://github.com/python/cpython/commit/c29b585fd4b5a91d17fc5dd41d86edff28a30da3>`__.
I added 6 new time functions:

* ``time.clock_gettime_ns()``
* ``time.clock_settime_ns()``
* ``time.monotonic_ns()``
* ``time.perf_counter_ns()``
* ``time.process_time_ns()``
* ``time.time_ns()``

Example::

    $ python3.7
    Python 3.7.0b2+ (heads/3.7:31e2b76f7b, Mar  6 2018, 15:31:29)
    [GCC 7.2.1 20170915 (Red Hat 7.2.1-2)] on linux
    >>> import time
    >>> time.time()
    1520354387.7663522
    >>> time.time_ns()
    1520354388319257562

I also added tests on ``os.times()`` in ``test_os``, previously the function
wasn't tested at all!

Conclusion
==========

I added 6 new functions to get time with a nanosecond resolution like
``time.time_ns()`` with my approved :pep:`564`. I also modified
``time.clock()`` to emit a ``DeprecationWarning`` and I removed the legacy
``os.stat_float_times()`` function.

