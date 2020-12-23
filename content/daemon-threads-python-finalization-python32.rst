++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Daemon threads and the Python finalization in Python 3.2 and 3.3
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2020-03-26 22:00
:tags: cpython, subinterpreters
:category: cpython
:slug: daemon-threads-python-finalization-python32
:authors: Victor Stinner

At exit, the Python finalization calls Python objects finalizers (the
``__del__()`` method) and deallocates memory.  The daemon threads are a special
kind of threads which continue to run during and after the Python finalization.
They are causing race conditions and tricky bugs in the Python finalization.

This article covers bugs fixed in the Python finalization in Python 3.2 and
Python 3.3 (2009 to 2011), and a backport in Python 2.7.8 (2014).

.. image:: {static}/images/coronamaison_luppi.jpg
   :alt: #CoronaMaison by Luppi
   :target: https://twitter.com/LuppiChan/status/1240346448606171136

Drawing: `#CoronaMaison by Luppi
<https://twitter.com/LuppiChan/status/1240346448606171136>`_.

Daemon threads
==============

Python has a special kind of thread: "daemon" threads. The difference with
regular threads is that Python doesn't wait until daemon threads complete at
exit, whereas it waits until all regular ("non-daemon") threads complete.
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

Note: The ``Thread.join()`` method can be called explicitly to wait until a
daemon thread completes.


Don't destroy the GIL at exit
=============================

In November 2009, **Antoine Pitrou** implemented a new GIL (Global Interpreter
Lock) in Python 3.2: `commit 074e5ed9
<https://github.com/python/cpython/commit/074e5ed974be65fbcfe75a4c0529dbc53f13446f>`__.

In September 2010, he found a crash with daemon threads while stressing
``test_threading``: `bpo-9901: GIL destruction can fail
<https://bugs.python.org/issue9901>`_. ``test_finalize_with_trace()`` failed
with::

    Fatal Python error: pthread_mutex_destroy(gil_mutex) failed

He pushed a fix for this crash in Python 3.2, `commit b0b384b7
<https://github.com/python/cpython/commit/b0b384b7c0333bf1183cd6f90c0a3f9edaadd6b9>`__::

    Issue #9901: Destroying the GIL in Py_Finalize() can fail if some other
    threads are still running.  Instead, reinitialize the GIL on a second
    call to Py_Initialize().

The Python GIL internally uses a lock. If the lock is destroyed while a daemon
thread is waiting for it, the thread can crash. The fix is to **no longer
destroy the GIL at exit**.


Exit the thread in PyEval_RestoreThread()
=========================================

The Python finalization clears and deallocates the "Python thread state" of all
threads (in ``PyInterpreterState_Delete()``) which calls Python object
finalizers of these threads. Calling a finalizer can drop the GIL to call a
system call. For example, closing a file drops the GIL. When the GIL is
dropped, a daemon thread is awaken to take the GIL. Since the Python thread
state was just deallocated, the daemon thread crash.

This bug is a race condition. It depends on which order threads are executed,
on which order objects are finalized, on which order memory is deallocated,
etc.

The crash was first reported in April 2005: `bpo-1193099: Embedded python thread
crashes <https://bugs.python.org/issue1193099>`_. In January 2008, **Gregory P.
Smith** reported `bpo-1856: shutdown (exit) can hang or segfault with daemon
threads running <https://bugs.python.org/issue1856#msg60014>`_. He wrote a
short Python program reproducing the bug: spawn 40 daemon threads which do some
I/O operations and sleep randomly between 0 ms and 5 ms in a loop.

**Adam Olsen** `proposed a solution
<https://bugs.python.org/issue1856#msg60059>`_ (with a patch):

    I think **non-main threads should kill themselves off** if they grab the
    interpreter lock and the interpreter is tearing down. They're about to get
    killed off anyway, when the process exits.

In May 2011, **Antoine Pitrou** pushed a fix to Python 3.3 (6 years after the
first bug report) which implements this solution, `commit 0d5e52d3
<https://github.com/python/cpython/commit/0d5e52d3469a310001afe50689f77ddba6d554d1>`__::

    Issue #1856: Avoid crashes and lockups when daemon threads run while the
    interpreter is shutting down; instead, these threads are now killed when
    they try to take the GIL.


PyEval_RestoreThread() fix explanation
======================================

The fix adds a new ``_Py_Finalizing`` variable which is set by
``Py_Finalize()`` to the (Python thread state of the) thread which runs the
finalization.

Simplified patch of the ``PyEval_RestoreThread()`` fix::

    @@ -440,6 +440,12 @@ PyEval_RestoreThread()
             take_gil(tstate);
    +        if (_Py_Finalizing && tstate != _Py_Finalizing) {
    +            drop_gil(tstate);
    +            PyThread_exit_thread();
    +        }

If Python is finalizing (``_Py_Finalizing`` is not NULL) and
``PyEval_RestoreThread()`` is called by a thread which is not thread running
the finalization, the thread exits immediately (call
``PyThread_exit_thread()``).

``PyEval_RestoreThread()`` is called when a thread takes the GIL.  Typical
example of code which drops the GIL to call a system call (close a file
descriptor, ``io.FileIO()`` finalizer) and then takes again the GIL::

        Py_BEGIN_ALLOW_THREADS
        close(fd);
        Py_END_ALLOW_THREADS

The ``Py_BEGIN_ALLOW_THREADS`` macro calls ``PyEval_SaveThread()`` to drop the
GIL, and the ``Py_END_ALLOW_THREADS`` macro calls ``PyEval_RestoreThread()`` to
take the GIL.  Pseudo-code::

        PyEval_SaveThread();     // drop the GIL
        close(fd);
        PyEval_RestoreThread();  // take the GIL

With Antoine's fix, if Python is finalizing, a thread now exits immediately
when calling ``PyEval_RestoreThread()``.


Revert take_gil() backport to 2.7
=================================

In June 2014, **Benjamin Peterson** (Python 2.7 release manager) backported
Antoine's change to Python 2.7: fix included in 2.7.8.

Problem: the Ceph project `started to crash with Python 2.7.8
<https://tracker.ceph.com/issues/8797>`_.

In November 2014, the change was reverted in Python 2.7.9: see
`bpo-21963 discussion <https://bugs.python.org/issue21963>`_ for the rationale.

In 2014, I already wrote:

    Anyway, **daemon threads are evil** :-( Expecting them to exit cleanly
    automatically is not good. Last time I tried to improve code to cleanup
    Python at exit in Python 3.4, I also had a regression (just before the
    release of Python 3.4.0): see the `issue #21788
    <https://bugs.python.org/issue21788>`_.

Conclusion
==========

Daemon threads caused crashes in the Python finalization, first noticed in
2005.

Python 3.2 (released in February 2011) got a new GIL and also a bugfix for
daemon thread. Python 3.3 (released in September 2012) also got a bugfix for
daemon threads. The Python finalization became more reliable.

Changing Python finalization is risky. A backport of a bugfix into Python 2.7.8
caused a regression which required to revert the bugfix in Python 2.7.9.
