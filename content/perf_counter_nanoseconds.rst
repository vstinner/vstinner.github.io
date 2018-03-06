+++++++++++++++++++++++++++++++++++++
Python 3.7 perf_counter() nanoseconds
+++++++++++++++++++++++++++++++++++++

:date: 2018-03-06 15:00
:tags: cpython
:category: python
:slug: python37-perf-counter-nanoseconds
:authors: Victor Stinner

Modify importtime to use time.perf_counter() clock
--------------------------------------------------

INADA Naoki added to Python 3.7 a new cool `-X importtime
<https://docs.python.org/dev/using/cmdline.html#id5>`_ command line option to
analyze the Python import performance. This tool can be used optimize the
startup time of your application: read Naoki's article `How to speed up Python
application startup time
<https://dev.to/methane/how-to-speed-up-python-application-startup-time-nkf>`_
(Jan 19, 2018) for an example.

Naoki uses time.monotonic() internally for its feature. On Windows, this clock
(``GetTickCount64()`` function) has a resolution around 15.6 ms, whereas most
Python imports take less than 10 ms.

bpo-31415: I added a new C function ``_PyTime_GetPerfCounter()`` to access
``time.perf_counter()`` at the C level and so use it in the "importtime" tool.

Double integer-float conversions
--------------------------------

My commit a997c7b434631f51e00191acea2ba6097691e859 of bpo-31415 adding
``_PyTime_GetPerfCounter()`` moved the C code (from ``Modules/timemodule.c`` to
``Python/pytime.c``), but also changed the internal type storing time from
floatting point number (C ``double``) to integer number (``_PyTyime_t`` which
is ``int64_t`` in practice).

The drawback of this change is that ``time.perf_counter()`` now converts
``QueryPerformanceCounter() / QueryPerformanceFrequency()`` float into a
``_PyTime_t`` (integer) and then back to a float, and these conversions cause a
loss of precision. I computed the conversions start to loose precision starting
after a single second with ``QueryPerformanceFrequency()`` equals to
``3,579,545`` (3.6 MHz).

I modified ``time.clock()`` and ``time.perf_counter()`` to not use
``_PyTime_t`` anymore, only double.

Some maths to avoid the precision loss
--------------------------------------

I'm trying to convert all Python clocks to ``_PyTime_t`` since 6 years (2012),
so I was grumpy of being blocked by a single clock, especially because the
issue was specific to Windows. The Linux implementation of
``time.perf_counter()`` uses ``clock_gettime()`` which directly returns
nanoseconds as integers.

I looked at the clock sources in the Linux kernel source code: Linux clocks
only use integers and support nanosecond resolution. I'm always impressed by
the quality of the Linux kernel source code. The code is straightforward C
code. If Linux is able to use integers to various kinds of clocks, I should be
able to use integers for my specific Windows implementations of
``time.perf_counter()``, no?

In practice, the ``_PyTime_t`` is a number of nanoseconds, so the computation
is::

    (QueryPerformanceCounter() * 1_000_000_000) / QueryPerformanceFrequency()

where ``1_000_000_000`` is the number of nanoseconds in one second. The problem
is to prevent integer overflow on the first part, using ``_PyTime_t`` which is
``int64_t`` in practice::

    QueryPerformanceCounter() * 1_000_000_000

Using a pencil and a sheet of paper and some maths, I found a solution::

    (a * b) / q == (a / q) * b + ((a % q) * b) / q

It reduces the maximum value of temporary values. The C implementation becomes::

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


On Windows, I added the following sanity checks to make sure that integer
overflows cannot occur::

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

Since I also modified the macOS implementation of ``time.monotonic()`` to use
``_PyTime_MulDiv()``, I also added this check for macOS::

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
