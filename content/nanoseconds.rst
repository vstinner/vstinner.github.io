++++++++++++++++++++++
Python 3.7 nanoseconds
++++++++++++++++++++++

:date: 2018-03-06 17:00
:tags: cpython
:category: python
:slug: python37-nanoseconds
:authors: Victor Stinner

XXX

Nanoseconds, PEP 564
====================

Part 1: Add _PyTime_GetPerfCounter()
------------------------------------

bpo-31415: Add ``_PyTime_GetPerfCounter()`` function and use it for `-X
importtime <https://docs.python.org/dev/using/cmdline.html#id5>`_, previously a
monotonic clock was used which has a bad resolution on Windows: usually 15.6
ms, whereas most Python imports take less than 10 ms.

The new ``-X importtime`` command line option is a great enhacement of Python
3.7 written by INADA Naoki to analyze the performance of Python imports to
optimize the startup time of your application.  Read also `How to speed up
Python application startup time
<https://dev.to/methane/how-to-speed-up-python-application-startup-time-nkf>`_
by INADA Naoki (Jan 19, 2018).

Part 2: Add _PyTime_GetPerfCounterDoubleWithInfo()
--------------------------------------------------

The commit a997c7b434631f51e00191acea2ba6097691e859 of bpo-31415 moved the
implementation of time.perf_counter() from Modules/timemodule.c to
Python/pytime.c. The change not only moved the code, but also changed the
internal type storing time from floatting point number (C double) to integer
number (_PyTyime_t = int64_t).

The drawback of this change is that time.perf_counter() now converts
QueryPerformanceCounter() / QueryPerformanceFrequency() double into a _PyTime_t
(integer) and then back to double. Two useless conversions required by the
_PyTime_t format used in Python/pytime.c. These conversions introduced a loss
of precision.

Try attached round.py script which implements the double <=> _PyTime_t
conversions and checks to check for precision loss. The script shows that we
loose precision even with a single second for QueryPerformanceFrequency() ==
3579545.

It seems like QueryPerformanceFrequency() now returns 10 ** 7 (10_000_000,
resolution of 100 ns) on Windows 8 and newer, but returns 3,579,545 (3.6 MHz,
resolution of 279 ns) on Windows 7. It depends maybe on the hardware clock, I
don't know. Anyway, whenever possible, we should avoid precision loss of a
clock.

bpo-31773: time.perf_counter() uses again double. time.clock() and
time.perf_counter() now use again C double internally. Remove also
_PyTime_GetWinPerfCounterWithInfo(): use _PyTime_GetPerfCounterDoubleWithInfo()
instead on Windows.

Part 3
------

The day after, I reopened the issue since I found a solution to only use
integer in pytime.c for QueryPerformanceCounter() / QueryPerformanceFrequency()
*and* prevent integer overflow.

Commit::

    bpo-31773: _PyTime_GetPerfCounter() uses _PyTime_t (GH-3983)

    * Rewrite win_perf_counter() to only use integers internally.
    * Add _PyTime_MulDiv() which compute "ticks * mul / div"
      in two parts (int part and remaining) to prevent integer overflow.
    * Clock frequency is checked at initialization for integer overflow.
    * Enhance also pymonotonic() to reduce the precision loss on macOS
      (mach_absolute_time() clock).

Since 6 years (2012), I'm trying to only use integer numbers to store time.

PyTime_t: 2014, Python 3.5

I'm working on pytime.c since xxx

I looked at the Linux kernel source code: clock sources only use integers. I'm
always impressed by the quality of the Linux kernel source code.

Using a pencil and a sheet of paper, I found a solution for my problem.

The "trick" is implemented in this function::

    Py_LOCAL_INLINE(_PyTime_t)
    _PyTime_MulDiv(_PyTime_t ticks, _PyTime_t mul, _PyTime_t div)
    {
        _PyTime_t intpart, remaining;
        /* Compute (ticks * mul / div) in two parts to prevent integer overflow:
           compute integer part, and then the remaining part.

           (ticks * mul) / div == (ticks / div) * mul + (ticks % div) * mul / div

           The caller must ensure that "(div - 1) * mul" cannot overflow. */
        intpart = ticks / div;
        ticks %= div;
        remaining = ticks * mul;
        remaining /= div;
        return intpart * mul + remaining;
    }

On Windows, I added the following sanity checks::

    /* Check that frequency can be casted to _PyTime_t.

       Make also sure that (ticks * SEC_TO_NS) cannot overflow in
       _PyTime_MulDiv(), with ticks < frequency.

       Known QueryPerformanceFrequency() values:

       * 10,000,000 (10 MHz): 100 ns resolution
       * 3,579,545 Hz (3.6 MHz): 279 ns resolution

       None of these frequencies can overflow with 64-bit _PyTime_t, but
       check for overflow, just in case. */
    if (frequency > _PyTime_MAX
        || frequency > (LONGLONG)_PyTime_MAX / (LONGLONG)SEC_TO_NS) {
        PyErr_SetString(PyExc_OverflowError,
                        "QueryPerformanceFrequency is too large");
        return -1;
    }

with _PyTime_MAX = 2**63-1 (currently, _PyTime_t uses a resolution of 1
nanosecond, so 2**63-1 nanoseconds).

macOS check, added later::

    /* Make sure that (ticks * timebase.numer) cannot overflow in
       _PyTime_MulDiv(), with ticks < timebase.denom.

       Known time bases:

       * always (1, 1) on Intel
       * (1000000000, 33333335) or (1000000000, 25000000) on PowerPC

       None of these time bases can overflow with 64-bit _PyTime_t, but
       check for overflow, just in case. */
    if ((_PyTime_t)timebase.numer > _PyTime_MAX / (_PyTime_t)timebase.denom) {
        PyErr_SetString(PyExc_OverflowError,
                        "mach_timebase_info is too large");
        return -1;
    }

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


