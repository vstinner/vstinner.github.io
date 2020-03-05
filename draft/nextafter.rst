+++++++++++++++++++++++++++++++++++++++++++++++
Python 3.9 nextafter() and ulp() math functions
+++++++++++++++++++++++++++++++++++++++++++++++

:date: 2020-03-04 23:00
:tags: cpython, maths
:category: python
:slug: python39-nextafter-ulp-functions
:authors: Victor Stinner

Binary floating points numbers are hard to use and understand. Humans are
used to decimal numbers. Using "float" (IEEE binary64 float) causes bad
surprises to young developers. Most programming languages have a FAQ entry
about "0.1 + 0.2" surprising result. Example with Python 3.7::

    >>> 0.1 + 0.2
    0.30000000000000004

What's going on? Why does Python added 0.0000000000000004 to my number: the
result must be exactly 0.3! Well... binary64 is not exact: it has a limited
precision. Moreover, conversion between binary (base 2) and decimal (base 10)
causes "rounding issues". Let's inspect the number ``0.1``::

    >>> "%.3f" % 0.1
    '0.100'
    >>> "%.10f" % 0.1
    '0.1000000000'

Exactly the expected result, great! Let's try to get more digits... ::

    >>> "%.20f" % 0.1
    '0.10000000000000000555'

Oh wait. 0.1 "in Python" is not exactly the number 0.1? Let's inspect it
differently, format it in hexadecimal (base 16)::

    >>> (0.1).hex()
    '0x1.999999999999ap-4'

There is no rounding issue between binary (base 2) and hexadecimal (base 16).
So what are all these ``99999``? Why is it not an exact number?

An IEEE 754 binary64 number is stored as ``x * 2^n`` where ``n`` is an integer
and ``x`` is a number in [1.0; 2.0[ range. Let me ignore the sign to simplify
the problem.

nextafter
=========

Let's start with 1.0::

    $ ./python
    Python 3.9.0a4+ (heads/setup_py_bootstrap:9e7b47e66f, Mar  4 2020, 15:48:31)
    [GCC 9.2.1 20190827 (Red Hat 9.2.1-1)] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import math
    >>> math.nextafter(1.0, math.inf)
    1.0000000000000002
    >>> math.nextafter(1.0, -math.inf)
    0.9999999999999999

The second nextafter() parameter is the direction: do we want the next number
towards minus infinity ("previous" number) or towards infinity ("next" number).

Wait. The result is not symmetrical: the absolute difference is not the same::

    >>> a=abs(math.nextafter(1.0, +math.inf) - 1.0)
    >>> b=abs(math.nextafter(1.0, -math.inf) - 1.0)
    >>> a, b
    (2.220446049250313e-16, 1.1102230246251565e-16)
    >>> a / b
    2.0

Towards +inf, the difference is the double, and the difference towards -inf. It
means that the precision decreases when the float value increases. Large
numbers have a worse precision than small numbers. What is the "precision" of a
number? The new ulp() function helps to understand that::

    >>> math.ulp(1.0)
    2.220446049250313e-16
    >>> math.ulp(1.0) == (math.nextafter(1.0, +math.inf) - 1.0)
    True

What if we test larger numbers? ::

    >>> math.ulp(2 ** 10)
    2.2737367544323206e-13
    >>> math.ulp(2 ** 30)
    2.384185791015625e-07
    >>> math.ulp(2 ** 52)
    1.0
    >>> math.ulp(2 ** 60)
    256.0

So 2**52 has a precision of 1.0::

    >>> (x + 1) == x  # good!
    False
    >>> (x + 0.5) == x  # BAD :-( precision loss
    True

Adding a number smaller than 1.0 to 2**52 is simply ignored.


Unix timestamp precision
========================

Python conmmonly uses float to store time as a number of seconds since the Unix
epoch (January 1st, 1970) as a float. Example with ``time.time()`` which uses
the UTC timezone::

    >>> time.time()
    1583363594.414554
    >>> (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()
    1583363594.989763

What is the "precision" of time.time()? ::

    >>> math.ulp(time.time())
    2.384185791015625e-07
    >>> math.ulp(time.time()) * 1e9
    238.4185791015625

When I wrote this article, the precision was around 238 nanoseconds. It means
that even if the clock has a better precision, float itself only has a
precision of 238 nanoseconds.

I added time.time_ns() to Python 3.7. It returns an integer number of
nanoseconds and so doesn't loss precision:
https://docs.python.org/dev/library/time.html#time.time_ns

The ``int`` type returned by this function has a precision of 1 nanosecond. But
on Windows, time.monotonic_ns() only has a bad effective precision around 16
ms, even if the int type has a good precision of 1 nanosecond (0.000001 ms).


Fabien
======

http://fabiensanglard.net/floating_point_visually_explained/


Comparison between C time_t and C double
========================================

* https://bugs.python.org/issue39277
* https://github.com/python/cpython/pull/17933/files

Maximum value of int64_t type::


    >>> 2**63-1
    9223372036854775807
    >>> int(float(9223372036854775807))
    9223372036854775808
    >>> x=float(2**63-1)
    >>> math.ulp(x)
    2048.0
    >>> int(x)
    9223372036854775808
    >>> x - math.nextafter(x, -math.inf)  # before
    1024.0
    >>> math.nextafter(x, +math.inf) - x  # after
    2048.0

The float number can be seen as **a range**:

    ]9223372036854775808-1024; 9223372036854775808-2048[

or the range

    [9223372036854775808-1023; 9223372036854775808-2047].

Operation::

    >>> 1024/2
    512.0
    >>> int((x-512)) - int(x)
    0
    >>> int((x-513)) - int(x)
    -1024


::

    /* Check if the floating-point number v (double) would overflow when casted to
     * the integral type 'type'.
     *
     * Test (double)type_min(type) <= v <= (double)type_max(type) where v is a
     * double, and type_min() and type_max() integers are rounded towards zero when
     * casted to a double.
     *
     * (double)int cast rounds to nearest with ties going to nearest even integer
     * (ROUND_HALF_EVEN). Use nextafter() to round towards zeros (ROUND_DOWN).
     *
     * For example, _Py_IntegralTypeMax(int64_t)=2**63-1 casted to double gives
     * 2**63 which is greater than 2**63-1. The problem is that "v <= 2**63" fails
     * to detect that v will overflow when casted to int64_t.
     * nextafter((double)(2**63-1), 0.0) gives the floating-point number 2**63-1024
     * which is less than or equal to the integer 2**63-1 and so can be used to
     * test that v would overflow.
     *
     * In short, nextafter((double)x, 0.0) rounds the integer x towards zero. */
    #define _Py_DoubleInIntegralTypeRange(type, v) \
        (nextafter((double)_Py_IntegralTypeMin(type), 0.0) <= v \
         && v <= nextafter((double)_Py_IntegralTypeMax(type), 0.0))

