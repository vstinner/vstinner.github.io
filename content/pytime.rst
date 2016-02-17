+++++++++++++++++++++++++++++++++++++++++++
History of the Python private C API _PyTime
+++++++++++++++++++++++++++++++++++++++++++

:date: 2016-02-17 22:00
:tags: cpython
:category: python
:slug: pytime
:authors: Victor Stinner
:summary: History of the Python private C API _PyTime

Before _PyTime, Python 3.2
--------------------------

Until Python 3.2, CPython has various code to handle timestamps. A lot of code
was duplicated. Handling timestamps is complex, there are many corner cases.
The C time_t type is a signed integer number, but it can have a size of 32 or
64 bits. The exact behaviour of time functions of the C standard library
depends a lot on the platform. The tv_sec field of timeval and timespec
structures has always the type time_t, but the tv_usec and tv_nsec field may be
an int or a long, depending on the platform.

_PyTime, Python 3.3
-------------------

http://bugs.python.org/issue14180 "Factorize code to convert int/float to
time_t, timeval or timespec" was the first step to move the code to the
internal "pytime" library (Include/pytime.h and Python/pytime.c). Hopefully,
the API was private, because it changed a lot.

The first step added two functions:

* _PyTime_ObjectToTime_t(obj, &sec)
* _PyTime_ObjectToTimeval(obj, &sec, &usec)

There was no rounding parameter, it used ROUND_CEILING, but it was not a
deliberate choice.

New rounding mode parameter, Python 3.4
----------------------------------------

The _PyTime API was extended to add a new rounding mode parameter. The API
supported two rounding modes:

* _PyTime_ROUND_DOWN: Round towards zero.
* _PyTime_ROUND_UP: Round away from zero.

The ROUND_CEILING rounding mode was no more supported.

_PyTime_ROUND_DOWN was used by:

* datetime.date.fromtimestamp()
* datetime.datetime.fromtimestamp()
* datetime.datetime.utcfromtimestamp()
* os.utime()
* time.clock_settime()
* time.ctime()
* time.gmtime()
* time.localtime()

_PyTime_ROUND_UP was used by:

* select.select()
* select.kqueue.control()
* signal.sigtimedwait()


Rounding mode fixed for negative numbers, Python 3.5
----------------------------------------------------

The _PyTime_ROUND_DOWN and _PyTime_ROUND_UP have been removed in Python 3.5,
replaced with two new rounding modes:

* _PyTime_ROUND_FLOOR: Round towards minus infinity (-inf).
   For example, used to read a clock.
* _PyTime_ROUND_CEILING:  Round towards infinity (+inf).
  For example, used for timeout to wait "at least" N seconds.

The major difference is that the rounding modes now come with examples on use
case. It's a consequence on a deeper research on how timestamps are expected
to be rounded.

_PyTime_ROUND_FLOOR:

* datetime.date.fromtimestamp()
* datetime.datetime.fromtimestamp()
* datetime.datetime.utcfromtimestamp()
* os.utime()
* time.clock_settime()
* time.ctime()
* time.gmtime()
* time.localtime()

_PyTime_ROUND_CEILING:

* select.devpoll.poll()
* select.epoll.poll()
* select.kqueue.control()
* select.poll.poll()
* select.select()
* socket: timeout of socket methods like socket.recv() or socket.send()
* ssl: timeout of SSL socket methods
* threading.Lock.acquire(timeout)
* threading.RLock.acquire(timeout)
* signal.sigtimedwait()
* time.sleep()

PEP 410, rejected
-----------------

https://www.python.org/dev/peps/pep-0410/

The PEP was rejected because it required to modify at least 33 functions to
add an optional parameter to choose the return type. Passing a parameter to
choose the result type is a bad pattern.


_PyTime_t type for nanosecond resolution, Python 3.5
----------------------------------------------------

Operating systems provide more and more API supporting nanosecond resolution.
Examples:

* GetSystemTimeAdjustment() (res: 100 ns), ex: used by time.time()
* clock_gettime(), ex: used by time.time()
* sigtimedwait(): signal.sigtimedwait()
* os.fstat(): atime, mtime, ctime

Python used internally a C double to store timestamps. The problem is that it
caused rounding issues. Since the PEP 410 was rejected, a compromise was found
for os.stat(): 3 new fields were added to os.stat_result, timestamp as a
integer number of nanoseconds.

But the problem was wider than os.stat(). So I added a _PyTime_t type which is
an integer with no known unit. The value must not be set manually, but
functions should be used instead. API:

* _PyTime_FromSeconds(secs)
* _PyTime_FromNanoseconds(ns)
* _PyTime_FromSecondsObject(&t, obj, round)
* _PyTime_FromMillisecondsObject(&t, obj, round)
* _PyTime_AsSecondsDouble(t)
* _PyTime_AsMilliseconds(t, round) -> _PyTime_t
* _PyTime_AsMicroseconds(t, round) -> _PyTime_t
* _PyTime_AsNanosecondsObject(t): used by os.stat()
* _PyTime_AsTimeval(t, tv, round): tv is a 'struct timeval'
* _PyTime_AsTimeval_noraise(t, tv, round): tv is a 'struct timeval'
* _PyTime_AsTimespec(t, ts): tv is a 'struct timespec'

Other functions:

* _PyTime_GetSystemClock()
* _PyTime_GetMonotonicClock()

The API was designed to force the caller to check for error. A Python
exception is raised on overflow.

The API was designed to minimize the number of functions. There are 2 main
family of functions:

* _PyTime_FromXXX(): initialize a timestamp from any kind of timestamp
* _PyTime_AsYYY(): convert a timestamp from _PyTime_t format to another format

Instead of having one function per combination (FromXXXToYYY).

Since _PyTime_t is a number, usually math operations can be used::

    deadline = now + timeout;
    ...
    sleep = deadline - now;

But it's not possible to use literal numbers::

    timestamp = 1;

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

That's why legacy functions are kept:

* _PyTime_ObjectToTime_t()
* _PyTime_ObjectToTimeval()
* _PyTime_ObjectToTimespec()

The functions are still used in:

* datetime.date.fromtimestamp()
* datetime.datetime.fromtimestamp()
* datetime.datetime.utcfromtimestamp()
* os.utime()
* time.ctime()
* time.gmtime()
* time.localtime()


_PyTime_ROUND_HALF_UP rounding mode, Python 3.6
-----------------------------------------------

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

Rounding modes used of datetime.datetime.fromtimestamp():

* Python 2.7: ROUND_HALF_UP
* Python 3.3: ROUND_CEILING
* Python 3.4: ROUND_DOWN
* Python 3.5, 3.6: ROUND_FLOOR

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
----------

The work started in 2012 and is still active in 2015, so it took me three
years to stabilize the API and fix all issues. Well, I didn't spend all my
days on it, but it shows that handling time is not a simple issue.

The Python public API hasn't changed, timestamps are still handled as floating
point numbers.

In 2015, Python has still a very basic handling of timezones. Unaware datetime
objects and aware datetime objects can be compared to bytes (unknown encoding)
and unicode strings (very well defined character set). It's still an hot topic
and a SIG mailing list was created to solve the issue!

