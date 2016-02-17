+++++++++++++++++++++++++++++++++++++++++++
History of the Python private C API _PyTime
+++++++++++++++++++++++++++++++++++++++++++

:date: 2016-02-17 22:00
:tags: cpython
:category: python
:slug: pytime
:authors: Victor Stinner
:summary: History of the Python private C API _PyTime

I added functions to the private "pytime" library to convert timestamps from/to
various formats. I expected to spend a few days, at the end I spent 3 years
(2012-2015) on them!

Python 3.3
==========

In 2012, I proposed the `PEP 410 -- Use decimal.Decimal type for timestamps
<https://www.python.org/dev/peps/pep-0410/>`_ because storing timestamps as
floating point numbers looses precision. The PEP was rejected because it
modified many functions and had a bad API. At least, os.stat() got 3 new fields
(atime_ns, mtime_ns, ctime_ns): timestamps  as a number of nanoseconds
(``int``).

My `PEP 418 -- Add monotonic time, performance counter, and process time
functions <https://www.python.org/dev/peps/pep-0418/>`_ was accepted, Python
3.3 got a new ``time.monotonic()`` function (and a few others). Again, I spent
much more time than I expected on a problem which looked simple at the first
look.

With the `issue #14180 <http://bugs.python.org/issue14180>`_, I added functions
to convert timestamps to the private "pytime" API to factorize the code of
various modules. Timestamps were rounded towards +infinity (ROUND_CEILING), but
it was not a deliberate choice.


Python 3.4
==========

To fix correctly a performance issue in asyncio (`issue20311
<https://bugs.python.org/issue20311>`_), I added two rounding modes to the
pytime API: _PyTime_ROUND_DOWN (round towards zero), and _PyTime_ROUND_UP
(round away from zero). Polling for events (ex: using ``select.select()``) with
a non-zero timestamp must not call the underlying C level in non-blocking mode.


Python 3.5
==========

When working on the `issue #22117 <https://bugs.python.org/issue22117>`_, I
noticed that the implementation of rounding methods was buggy for negative
timestamps. I replaced the _PyTime_ROUND_DOWN with _PyTime_ROUND_FLOOR (round
towards minus infinity), and _PyTime_ROUND_UP with _PyTime_ROUND_CEILING (round
towards infinity).

This issue also introduced a new private ``_PyTime_t`` type to support
nanosecond resolution.  The type is an opaque integer type to store timestamps.
In practice, it's a signed 64-bit integer. Since it's an integer, it's easy and
natural to compute the sum or differecence of two timestamps: ``t1 + t2`` and
``t2 - t1``. I added _PyTime_XXX() functions to create a timestamp and
_PyTime_AsXXX() functions to convert a timestamp to a different format.

I had to keep three _PyTime_ObjectToXXX() functions for fromtimestamp() methods
of the datetime module. These methods must support extreme timestamps (year
1..9999), whereas _PyTime_t is "limited" to a delta of +/- 292 years (year
1678..2262).


Python 3.6
==========

In 2015, the `issue #23517 <http://bugs.python.org/issue23517>`_ reported that
Python 2 and Python 3 don't use the same rounding method in
datetime.datetime.fromtimestamp(): there was a difference of 1 microsecond.

After a long discussion, I modified fromtimestamp() methods of the datetime
module to round to nearest with ties going away from zero (ROUND_HALF_UP), as
done in Python 2.7, as round() in all Python versions.


Conclusion
==========

It took me three years to stabilize the API and fix all issues. Well, I didn't
spend all my days on it, but it shows that handling time is not a simple issue.

At the Python level, nothing changed, timestamps are still stored as float
(except of the 3 new fieleds of os.stat()).

Python 3.5 only supports timezones with fixed offset, it does not support the
locale timestamp for example. Timezones are still an hot topic: the
`datetime-sig mailing list
<https://mail.python.org/mailman/listinfo/datetime-sig>`_ was created to
enhance timezone support in Python.
