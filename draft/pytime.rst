+++++++++++++++++++++++++++++++++++++++++++
History of the Python private C API _PyTime
+++++++++++++++++++++++++++++++++++++++++++

:date: 2016-02-17 22:00
:tags: cpython
:category: python
:slug: pytime
:authors: Victor Stinner
:summary: History of the Python private C API _PyTime

Python 3.2
==========

Until Python 3.2, CPython had various code to handle timestamps. A lot of code
was duplicated.

Handling timestamps is complex, there are many corner cases.  The C time_t type
is a signed integer number, but it can have a size of 32 or 64 bits. The tv_sec
field of timeval and timespec structures has always the type time_t, but the
tv_usec and tv_nsec field may be an int or a long, depending on the platform.

When converting timestamps from/to other C types like int or long, it becomes
hard to handle correctly integer overflow.


Python 3.3
==========

Rejected PEP 410 (decimal for timestamp)
----------------------------------------

In 2012, I proposed the `PEP 410 -- Use decimal.Decimal type for timestamps
<https://www.python.org/dev/peps/pep-0410/>`_. The PEP proposes to add an
optional ``timestamp`` parameter to all functions returning timestamps to
choose between the default float format and the ``decimal.Decimal`` format.
For example, ``time.time(timestamp=decimal.Decimal)`` would return the system
clock as a ``Decimal`` object.

The motivation was to keep the nanosecond resolution (or even better) on
timestamp, while floating point numbers looses precision.

The PEP was rejected because it required to modify at least 33 functions to add
an optional parameter to choose the return type. Passing a parameter to choose
the result type is a bad pattern. There was also an objection on the effictive
clock accuracy.


os.stat(): new "ns" fields
---------------------------

The PEP 410 was rejected, but the loss of precision on file timestamps was not
fixed. Copying a file in Python may change its exact timestamps.

A compromise was found for os.stat(). Three new fields were added to
os.stat_result in Python 3.3: atime_ns, mtime_ns, ctime_ns. There are timestamp
stored as a number of nanoseconds (Python ``int``) since January 1, 1970.


Accepted PEP 418: time.monotonic()
----------------------------------

I spent a lot of time to write the `PEP 418 -- Add monotonic time, performance
counter, and process time functions
<https://www.python.org/dev/peps/pep-0418/>`_. It was much more difficult than
I expected to describe a clock, assumptions on a clock, define "wall clock",
etc.

The result is that Python 3.3 got 4 new functions:

* ``time.monotonic()``: Monotonic clock, i.e. cannot go backward. It is not
  affected by system clock updates.
* ``time.perf_counter()``: performance counter with the highest available
  resolution to measure a short duration
* ``time.process_time()``: sum of the system and user CPU time of the current
  process.
* ``time.get_clock_info(name)``: Get information on the specified clock.

In 2016, we are still fighting on projects using Python 2.7 to get a monotonic
clock... Come on, this issue is now solved in Python 3!


New _PyTime API
---------------

In 2012, I opened the `issue #14180: Factorize code to convert int/float to
time_t, timeval or timespec <http://bugs.python.org/issue14180>`_. It was a
first step to move the code to the internal "pytime" library
``(Include/pytime.h`` and ``Python/pytime.c`` files). Hopefully, the API was
private, because it changed a lot later!

The first step added two private functions to Python 3.3::

    _PyTime_ObjectToTime_t(obj, &sec)
    _PyTime_ObjectToTimeval(obj, &sec, &usec)

There was no rounding parameter, it used ROUND_CEILING rounding method (round
towards +infinity). It was not a deliberate choice, just a consequence of the
implementation.


Python 3.4
==========

Python 3.4 was released in March 2014.

New rounding mode parameter
---------------------------

In Python 3.4, I exteneded the _PyTime API to add a new rounding mode
parameter. The API supported two rounding modes:

* _PyTime_ROUND_DOWN: Round towards zero
* _PyTime_ROUND_UP: Round away from zero

The ROUND_CEILING rounding mode was no more supported.

_PyTime_ROUND_DOWN was used by:

* datetime.date.fromtimestamp(), datetime.datetime.fromtimestamp(),
  datetime.datetime.utcfromtimestamp()
* os.utime()
* time.clock_settime(), time.ctime(), time.gmtime(), time.localtime()

_PyTime_ROUND_UP was used by:

* select.select(), select.kqueue.control()
* signal.sigtimedwait()


Python 3.5
==========

Python 3.4 was released in September 2015.

Rounding mode fixed for negative numbers
----------------------------------------

In Python 3.5 (2015), I replaced the _PyTime_ROUND_DOWN and _PyTime_ROUND_UP
with two new rounding modes:

* _PyTime_ROUND_FLOOR: Round towards minus infinity (-inf).
  For example, used to read a clock.
* _PyTime_ROUND_CEILING: Round towards infinity (+inf).
  For example, used for timeout to wait "at least" N seconds.

The major difference is that the rounding modes now come with examples on use
case. It was the result of a deeper research on how timestamps are expected to
be rounded.

_PyTime_ROUND_FLOOR was used by:

* datetime.date.fromtimestamp(), datetime.datetime.fromtimestamp(),
  datetime.datetime.utcfromtimestamp()
* os.utime()
* time.clock_settime(), time.ctime(), time.gmtime(), time.localtime()

_PyTime_ROUND_CEILING was used by:

* select.devpoll.poll(), select.epoll.poll(), select.kqueue.control(),
  select.poll.poll(), select.select()
* socket: timeout of socket methods like socket.recv() or socket.send()
* ssl: timeout of SSL socket methods
* threading.Lock.acquire(timeout), threading.RLock.acquire(timeout)
* signal.sigtimedwait()
* time.sleep()


New _PyTime_t type for nanosecond resolution
--------------------------------------------

Operating systems provide more and more API supporting nanosecond resolution.
Examples:

* ``GetSystemTimeAdjustment()`` (resolution of 100 ns) used by ``time.time()``
* ``clock_gettime()``, ex: used by ``time.time()``
* ``sigtimedwait()``: exposed as ``signal.sigtimedwait()``
* ``os.fstat()``: atime, mtime and ctime fields

Python used internally a C double to store timestamps. The problem is that it
caused rounding issues. Since the PEP 410 was rejected, a compromise was found
for os.stat(): 3 new fields were added to os.stat_result (atime_ns, mtime_ns,
ctime_ns), number of nanoseconds as a Python int.

But the problem was wider than os.stat(). So I added a _PyTime_t type which is
an integer with no known unit. The value must not be set manually, but
functions should be used instead.

API::

    _PyTime_FromSeconds(secs)
    _PyTime_FromNanoseconds(ns)
    _PyTime_FromSecondsObject(&t, obj, round)
    _PyTime_FromMillisecondsObject(&t, obj, round)
    _PyTime_AsSecondsDouble(t)
    _PyTime_AsMilliseconds(t, round) -> _PyTime_t
    _PyTime_AsMicroseconds(t, round) -> _PyTime_t
    _PyTime_AsNanosecondsObject(t)
        used by os.stat()
    _PyTime_AsTimeval(t, struct timeval *tv, round)
    _PyTime_AsTimeval_noraise(t, struct timeval *tv, round)
    _PyTime_AsTimespec(t, struct timespec *ts)

Other functions::

    _PyTime_GetSystemClock(&t)
    _PyTime_GetMonotonicClock(&t)

The API was designed to force the caller to check for error. A Python
exception is raised on overflow.

The API was designed to minimize the number of functions. There are 2 main
family of functions:

* ``_PyTime_FromXXX()``: initialize a timestamp from any kind of timestamp
* ``_PyTime_AsYYY()``: convert a timestamp from _PyTime_t format to another
  format

Instead of having one function per combination (FromXXXToYYY).

Since _PyTime_t is a number, usual math operations can be used::

    deadline = now + timeout;
    ...
    sleep = deadline - now;

But it's not possible to use literal numbers::

    timestamp = 1;

You have to use functions like::

    timestamp = _PyTime_FromSeconds(1);

What is the unit of timestamp? It's not specified because it can change in the
future. Maybe we may use a resolution of 1 microsecond on some systems, or 1
picosecond on other systems?

Currently, _PyTime_t is a 64-bit signed integer and the internal resolution
is 1 nanosecond. The resolution is enough to handle all functions of all
current operating systems.

The problem is that 64-bit with a resolution of 1 nanosecond cannot store any
timestamp from the C type time_t. The C type time_t is used to store a number
of seconds. If time_t is also 64-bit (default on 64-bit UNIX systems, it
can be found on some 32-bit systems too), _PyTime_t is too small to store such
timestamp.

That's why "legacy" functions are kept:

* ``_PyTime_ObjectToTime_t()``
* ``_PyTime_ObjectToTimeval()``
* ``_PyTime_ObjectToTimespec()``

These functions are still used in:

* datetime.date.fromtimestamp(), datetime.datetime.fromtimestamp(),
  datetime.datetime.utcfromtimestamp()
* os.utime()
* time.ctime(), time.gmtime(), time.localtime()


Python 3.6
==========

Python 3.6.0 is scheduled for December 2016.

_PyTime_ROUND_HALF_UP rounding mode
-----------------------------------

In february 2015, an user reported (`issue #23517
<http://bugs.python.org/issue23517>`_) that Python 2 and Python 3 don't round
timestamp in datetime.datetime.fromtimestamp()::

    $ python2
    >>> import datetime
    >>> datetime.datetime.utcfromtimestamp(1424817268.274)
    datetime.datetime(2015, 2, 24, 22, 34, 28, 274000)

    $ python3
    >>> import datetime
    >>> datetime.datetime.utcfromtimestamp(1424817268.274)
    datetime.datetime(2015, 2, 24, 22, 34, 28, 273999)

274,000 microseconds for Python 2 and 273,999 microseconds (1 less) for
Python 3.

The problem is that the decimal number "1424817268.274" is converted
to 64-bit floating point number in the base 2 (IEEE 754 format) which
is unable to store the exact decimal number::

    >>> "%.10f" % 1424817268.274
    '1424817268.2739999294'

Summary of rounding modes used of datetime.datetime.fromtimestamp():

* Python 2.7: ROUND_HALF_UP
* Python 3.3: ROUND_CEILING
* Python 3.4: ROUND_DOWN
* Python 3.5: ROUND_FLOOR

It was decided to use again the ROUND_HALF_UP rounding mode in Python 3.6,
because this mode has less surprising behaviour and it was used in Python 2
which is widely deployed.

The ROUND_HALF_UP was added to Python 3.6 and used by:

* datetime.datetime.fromtimestamp()
* datetime.datetime.utcfromtimestamp()

The datetime.timedelta constructor also uses the same rounding mode, but it
doesn't use the _PyTime API (a timedelta object stores a timestamp as 3
numbers: number of days, seconds and microseconds).


Conclusion
==========

The work started in 2012 and is still active in 2015, so it took me three
years to stabilize the API and fix all issues. Well, I didn't spend all my
days on it, but it shows that handling time is not a simple issue.

The Python public API hasn't changed, timestamps are still handled as floating
point numbers.

In 2015, Python has still a very basic handling of timezones. Unaware datetime
objects and aware datetime objects can be compared to bytes (unknown encoding)
and unicode strings (very well defined character set). It's still an hot topic
and a SIG mailing list was created to solve the issue!
