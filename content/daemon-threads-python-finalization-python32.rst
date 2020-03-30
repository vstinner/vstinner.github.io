++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Daemon threads and the Python finalization in Python 3.2
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2020-03-26 22:00
:tags: cpython
:category: cpython
:slug: daemon-threads-python-finalization-python32
:authors: Victor Stinner

At exit, the Python finalization calls Python objects finalizers and
deallocates memory.  The daemon threads are a special kind of threads which
continue to run during and after the Python finalization. These daemon threads
are causing race conditions and tricky issues in the Python finalization.

This article is about the bugs fixed in the Python finalization during the
Python 3.2 development (2009 and 2010).

.. image:: {static}/images/coronamaison_luppi.jpg
   :alt: Maze
   :target: https://twitter.com/LuppiChan/status/1240346448606171136

Drawing: `#CoronaMaison by Luppi
<https://twitter.com/LuppiChan/status/1240346448606171136>`_.

Daemon threads
==============

Python has a special kind of thread: "daemon" threads. The difference with
regular threads is that Python doesn't wait until daemon threads complete at
exit, whereas it blocks until all regular ("non-daemon") threads complete.
Example::

    import threading, time
    thread = threading.Thread(target=time.sleep, args=(5.0,), daemon=False)
    thread.start()

This Python program spawns a regular thread which sleeps for 5 seconds. Python
takes 5 seconds to exit::

    $ time python3 sleep.py

    real   0m5,047s

If ``daemon=False`` is replaced with ``daemon=True`` to spawn a daemon thread
instead, Python exits immediately (57 ms)::

    $ time python3 sleep.py

    real   0m0,057s

Note: Calling explicitly ``Thread.join()`` also waits until a daemon thread
completes.


Don't destroy the GIL at exit
=============================

November 2009, **Antoine Pitrou** implements a new GIL in Python 3.2: `commit
074e5ed9
<https://github.com/python/cpython/commit/074e5ed974be65fbcfe75a4c0529dbc53f13446f>`__.

September 2010, he finds a crash daemon threads while stressing
``test_threading``: `bpo-9901: GIL destruction can fail
<https://bugs.python.org/issue9901>`_. ``test_finalize_with_trace()`` fails
with::

    Fatal Python error: pthread_mutex_destroy(gil_mutex) failed

He pushs a fix for this crash in Python 3.2, `commit b0b384b7
<https://github.com/python/cpython/commit/b0b384b7c0333bf1183cd6f90c0a3f9edaadd6b9>`__::

    Issue #9901: Destroying the GIL in Py_Finalize() can fail if some other
    threads are still running.  Instead, reinitialize the GIL on a second
    call to Py_Initialize().

The Python GIL internally uses a lock. If the lock is destroyed while a daemon
thread is waiting for it, the thread can crash. The fix is to **no longer
destroy the GIL at exit**.


Crash in take_gil()
===================

A daemon thread can crash at exit after Python deallocates the Python thread
state of the thread in ``Py_Finalize()``. During ``Py_Finalize()``, the thread
running ``Py_Finalize()`` can release the GIL which wakes up the daemon thread.
The daemon thread crash while taking the the GIL in ``take_gil()``, since its
state was deallocated.

This problem is first reported in April 2005: `bpo-1193099: Embedded python
thread crashes <https://bugs.python.org/issue1193099>`_. In January 2008,
**Gregory P. Smith** reports `bpo-1856: shutdown (exit) can hang or segfault
with daemon threads running <https://bugs.python.org/issue1856#msg60014>`_
which will become the reference issue for this bug. He writes a short Python
program to reproduce the bug: spawn 40 daemon threads which some I/O and sleep
randomly between 0 ms and 5 ms in a loop.

**Adam Olsen** `proposes a solution
<https://bugs.python.org/issue1856#msg60059>`_ (with a patch):

    I think **non-main threads should kill themselves off** if they grab the
    interpreter lock and the interpreter is tearing down. They're about to get
    killed off anyway, when the process exits.

May 2011, **Antoine Pitrou** pushed a fix into Python 3.3 (6 years after the
first bug report!) which implements this solution::

    commit 0d5e52d3469a310001afe50689f77ddba6d554d1
    Author: Antoine Pitrou <solipsis@pitrou.net>
    Date:   Wed May 4 20:02:30 2011 +0200

        Issue #1856: Avoid crashes and lockups when daemon threads run while the
        interpreter is shutting down; instead, these threads are now killed when
        they try to take the GIL.

Simplified extract of the fix in ``PyEval_RestoreThread()`` function::

    @@ -440,6 +440,12 @@ PyEval_RestoreThread()
             take_gil(tstate);
    +        if (_Py_Finalizing && tstate != _Py_Finalizing) {
    +            drop_gil(tstate);
    +            PyThread_exit_thread();
    +        }

``PyEval_RestoreThread()`` now checks if Python is finalizing (or has been
finalized) using a new ``_Py_Finalizing`` variable which is set by
``Py_Finalize()``.

``PyEval_RestoreThread()`` is called when a threads tries to acquire the GIL.
Example of code releasing the GIL to call ``fchmod()``::

        Py_BEGIN_ALLOW_THREADS
        res = fchmod(fd, mode);
        Py_END_ALLOW_THREADS

The ``Py_BEGIN_ALLOW_THREADS`` macro calls ``PyEval_SaveThread()`` which
releases the GIL, whereas the ``Py_END_ALLOW_THREADS`` macro acquires the GIL.
Pseudo-code::

        PyEval_SaveThread();     // drop the GIL
        res = fchmod(fd, mode);
        PyEval_RestoreThread();  // take the GIL

With Antoine's change,  if Python is finalizing, a thread now exits immediately
when it attempts to take the GIL.


Revert take_gil() backport to 2.7
=================================

In June 2014, **Benjamin Peterson** (Python 2.7 release manager) backports
Antoine's change to Python 2.7: fix included in 2.7.8.

Problem, Ceph project `starts to crash with Python 2.7.8
<https://tracker.ceph.com/issues/8797>`_. In November 2014, the change is
reverted: see `bpo-21963 discussion <https://bugs.python.org/issue21963>`_.

In 2014, I already write:

    Anyway, **daemon threads are evil** :-( Expecting them to exit cleanly
    automatically is not good. Last time I tried to improve code to cleanup
    Python at exit in Python 3.4, I also had a regression (just before the
    release of Python 3.4.0): see the `issue #21788
    <https://bugs.python.org/issue21788>`_.

Conclusion
==========

Daemon threads are causing issues in Python finalization.

Python 3.2 gets a new GIL and also two fixes for bugs related to daemon
threads.

Changing Python finalization is risky. A backport of a bugfix into Python 2.7
causes a regression which requires to revert the backport.
