++++++++++++++++++++++
Python 3.7 nanoseconds
++++++++++++++++++++++

:date: 2018-03-06 17:00
:tags: cpython
:category: python
:slug: python37-nanoseconds
:authors: Victor Stinner

Six years ago (2012), I wrote PEP 410 which proposes a large and complex change
of all Python functions returning time to support nanosecond resolution using
the ``decimal.Decimal`` type. The PEP was rejected for different reasons.

But I never abandonned my project. I modified CPython internals to use
nanoseconds and so avoid precision loss, at least internally.

Recently, I succeeded to reimplement ``time.perf_counter()`` to use nanoseconds
internally, and so I wrote a new PEP 564 to read clocks with nanosecond
resolution at the Python level.

time.clock()
------------

bpo-31803: ``time.clock()`` and ``time.get_clock_info('clock')`` now emit a
DeprecationWarning warning. Replace ``time.clock()`` with
``time.perf_counter()`` in tests and demos.

Remove also ``hasattr(time, 'monotonic')`` in ``test_time`` since
``time.monotonic()`` is always available since Python 3.5.

os.stat_float_times()
---------------------

os.stat_float_times() was introduced in Python 2.3 to get file modification
times with sub-second resolution. The default remains to get time as seconds
(integer). See commit f607bdaa77475ec8c94614414dc2cecf8fd1ca0a.

The function was introduced to get a smooth transition to time as floating
point number, to keep the backward compatibility with Python 2.2.

In Python 2.5, os.stat() returns time as float by default: commit
fe33d0ba87f5468b50f939724b303969711f3be5.

Python 2.5 was released 11 years ago. I consider that people had enough time to
migrate their code to float time :-)

I modified os.stat_float_times() to emit a DeprecationWarning in Python 3.1:
commit 034d0aa2171688c40cee1a723ddcdb85bbce31e8 (bpo-14711).

bpo-31827: Remove os.stat_float_times().

Serhiy: "stat_result is a named 10-tuple, containing several additional
attributes. The last three items are st_atime, st_mtime and st_ctime as
integers. Accessing them by name returns floats. Isn't a time to make them
floats when access stat_result as a tuple?"

I tried to remove the backward compatibility layer: I modified
stat_result[ST_MTIME] to return float rather than int. Problem: it broke
test_logging, the code deciding if a log file should be rotated or not.

While I'm not strongly opposed to modify stat_result[ST_MTIME], I prefer to do
it in a separated PR. Moreover, we need maybe to emit a DeprecationWarning, or
at least deprecate the feature in the doc, before changing the type, no?"

Serhiy: "I agree, it should be done in a separate issue. It needs a
special discussion. And maybe this can't be changed."

faulthandler timeout
--------------------

faulthandler now uses the _PyTime_t C type rather than double for timeout. Use
the _PyTime_t type rather than double for the faulthandler timeout in
the ``dump_traceback_later()`` function.

This change should fix the following Coverity warning::

    CID 1420311:  Incorrect expression  (UNINTENDED_INTEGER_DIVISION)
    Dividing integer expressions "9223372036854775807LL" and "1000LL",
    and then converting the integer quotient to type "double". Any
    remainder, or fractional part of the quotient, is ignored.

        if ((timeout * 1e6) >= (double) PY_TIMEOUT_MAX) {

The warning comes from ``(double)PY_TIMEOUT_MAX`` with::

    #define PY_TIMEOUT_MAX (PY_LLONG_MAX / 1000)

PEP 564
-------

Six years ago (2012), I wrote PEP 410 which proposes a large and complex change
in all Python functions returning time to support nanosecond resolution using
the decimal.Decimal type. The PEP was rejected for different reasons.

Since all Python clock now use internally _PyTime_t, I wrote the PEP 564
to propose to add ``_ns()`` clock variants like ``time.time_ns()``: return
time as an integer number of nanoseconds.

People were now convinced by the need for nanosecond resolution, so I
added a "Issues caused by precision loss" section with 2 examples:

* Example 1: measure time delta in long-running process
* Example 2: compare times with different resolution

As for my previous PEP 410, many people proposed many alternatives recorded in
the PEP: sub-nanosecond resolution, modifying time.time() result type,
different types, different API, a new module, etc.

Implementaton of the PEP 564
----------------------------

bpo-31784, commit c29b585fd4b5a91d17fc5dd41d86edff28a30da3: Implement PEP 564:
add ``time.time_ns()``.

Add new time functions:

* ``time.clock_gettime_ns()``
* ``time.clock_settime_ns()``
* ``time.monotonic_ns()``
* ``time.perf_counter_ns()``
* ``time.process_time_ns()``
* ``time.time_ns()``

Add new _PyTime functions:

* ``_PyTime_FromTimespec()``
* ``_PyTime_FromNanosecondsObject()``
* ``_PyTime_FromTimeval()``

Other changes:

* Add ``os.times()`` tests to ``test_os``.
* ``pytime_fromtimeval()`` and ``pytime_fromtimeval()`` now return
  ``_PyTime_MAX`` or ``_PyTime_MIN`` on overflow, rather than undefined
  behaviour
* ``_PyTime_FromNanoseconds()`` parameter type changes from ``long long`` to
  ``_PyTime_t``


