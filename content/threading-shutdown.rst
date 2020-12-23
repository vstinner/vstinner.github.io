++++++++++++++++++++++++++++++++++
Threading shutdown race condition
++++++++++++++++++++++++++++++++++

:date: 2020-04-03 20:00
:tags: cpython, subinterpreters
:category: cpython
:slug: threading-shutdown-race-condition
:authors: Victor Stinner

This article is about a race condition in threading shutdown that I fixed in
Python 3.9 in March 2019. I also forbid spawning daemon threads in
subinterpreters to fix another related bug.

.. image:: {static}/images/coronamaison_jneel.jpg
   :alt: #CoronaMaison by Julien Neel
   :target: https://twitter.com/neeljulien/status/1240292383369150464

Drawing: `#CoronaMaison by Julien Neel
<https://twitter.com/neeljulien/status/1240292383369150464>`_.


Race condition in threading shutdown
====================================

Random test failure noticed on FreeBSD buildbot
-----------------------------------------------

In March 2019, I noticed that ``test_threading.test_threads_join_2()`` was
killed by SIGABRT on the FreeBSD CURRENT buildbot, `bpo-36402
<https://bugs.python.org/issue36402>`_::

    Fatal Python error: Py_EndInterpreter: not the last thread

The ``test_threads_join_2()`` test **failed randomly** on buildbots when tests
were **run in parallel**, but test_threading **passed** when it was **re-run
sequentially**.  Such failure was silently ignored, since the build was seen
overall as a success.

The test ``test_threading.test_threads_join_2()`` was added by in 2013 `commit
7b476993
<https://github.com/python/cpython/commit/7b4769937fb612d576b6829c3b834f3dd31752f1>`__.

In 2016, I already reported the same test failure: `bpo-27791
<https://bugs.python.org/issue27791>`_ (same test, also on FreeBSD). And
Christian Heimes reported a similar issue: `bpo-28084
<https://bugs.python.org/issue28084>`_. I simply closed these issues because I
only saw the failure once in 4 months and **I didn't have access to FreeBSD to
attempt to reproduce the crash**.

Reproduce the race condition
----------------------------

In 2019, I had a FreeBSD VM to attempt to reproduce the bug locally.

In June 2019, I found a reliable way to reproduce the bug by `adding random
sleeps to the test <https://github.com/python/cpython/pull/13889/files>`_. With
this patch, I was also able to reproduce the bug on Linux. **I am way more
comfortable to debug an issue on Linux** with my favorite debugging tools!

I identified a race condition in the Python finalization. I also understood
that the bug was not specific to subinterpreters:

    The test shows the bug using subinterpreters (Py_EndInterpreter), but
    **the bug also exists in Py_Finalize()** which has the same race condition.

I wrote a patch for ``Py_Finalize()`` to help me to reproduce the bug without
subinterpreters::

    +    if (tstate != interp->tstate_head || tstate->next != NULL) {
    +        Py_FatalError("Py_EndInterpreter: not the last thread");
    +    }

threading._shutdown() race condition
------------------------------------

``threading._shutdown()`` uses ``threading.enumerate()`` which iterates on
``threading._active`` dictionary.

``threading.Thread`` registers itself into ``threading._active`` when the
thread starts. It unregisters itself from ``threading._active`` when it
completes.

The bug occurs when the thread is unregistered whereas the underlying native
thread is still running and **the Python thread state is not deleted yet**.

``_thread._set_sentinel()`` creates a lock and registers a
``tstate->on_delete`` callback to release this lock. It's called by
``threading.Thread`` when the thread starts to set
``threading.Thread._tstate_lock``.  This lock is used by
``threading.Thread.join()`` method to wait until the thread completes.

``_thread.start_new_thread()`` calls the C function ``t_bootstrap()`` which
ends with::

    tstate->interp->num_threads--;
    PyThreadState_Clear(tstate);
    PyThreadState_DeleteCurrent();
    PyThread_exit_thread();

When the native thread completes, ``_PyThreadState_DeleteCurrent()`` is called:
it calls ``tstate->on_delete()`` callback which releases
``threading.Thread._tstate_lock`` lock.

The root issue is that:

* ``threading._shutdown()`` rely on ``threading._alive`` dictionary
* ``Py_EndInterpreter()`` rely on the interpreter linked list of Python thread
  states of the interpreter (``interp->tstate_head``).

The lock on Python thread states (``threading.Thread._tstate_lock``) and
``PyThreadState.on_delete`` callback were added in 2013 by **Antoine Pitrou**
to Python 3.4, `commit 7b476993
<https://github.com/python/cpython/commit/7b4769937fb612d576b6829c3b834f3dd31752f1>`__
of `bpo-18808 <https://bugs.python.org/issue18808>`_::

    Issue #18808: Thread.join() now waits for the underlying thread state
    to be destroyed before returning. This prevents unpredictable aborts
    in Py_EndInterpreter() when some non-daemon threads are still running.


Fix threading._shutdown()
-------------------------

Finally in June 2019, I fixed the race condition in ``threading._shutdown()``
with `commit 468e5fec
<https://github.com/python/cpython/commit/468e5fec8a2f534f1685d59da3ca4fad425c38dd>`__::

    bpo-36402: Fix threading._shutdown() race condition (GH-13948)

    Fix a race condition at Python shutdown when waiting for threads.  Wait
    until the Python thread state of all non-daemon threads get deleted
    (join all non-daemon threads), rather than just wait until Python
    threads complete.

The fix is to modify ``threading._shutdown()`` to wait until the Python thread
state of all non-daemon threads get deleted, rather than calling the ``join()``
method of all non-daemon threads. The ``join()`` does not ensure that the
Python thread state is deleted.

The Python finalization calls ``threading._shutdown()`` to wait until all
threads complete. Only non-daemon threads are awaited: daemon threads can
continue to run after ``threading._shutdown()``.

``Py_EndInterpreter()`` requires that the Python thread states of all threads
have been deleted. **What about daemon threads?** More about that in the next
section ;-)

Note: This change introduced a regression (memory leak) which is not fixed yet:
`bpo-37788 <https://bugs.python.org/issue37788>`_.


Forbid daemon threads in subinterpreters
========================================

In June 2019, while fixing the threading shutdown, I found a reliable way to
trigger a bug with daemon threads when a subinterpreter is finalized::

    Fatal Python error: Py_EndInterpreter: not the last thread

By design, daemon threads can run after a Python interpreter is finalized,
whereas ``Py_EndInterpreter()`` requires that all threads completed.

I reported `bpo-37266 <https://bugs.python.org/issue37266>`_ to propose to
forbid the creation of daemon threads in subinterpreters. I fixed the issue
with `commit 066e5b1a
<https://github.com/python/cpython/commit/066e5b1a917ec2134e8997d2cadd815724314252>`__::

    bpo-37266: Daemon threads are now denied in subinterpreters (GH-14049)

    In a subinterpreter, spawning a daemon thread now raises an
    exception. Daemon threads were never supported in subinterpreters.
    Previously, the subinterpreter finalization crashed with a Pyton
    fatal error if a daemon thread was still running.

The change adds this check to ``Thread.start()``::

    if self.daemon and not _is_main_interpreter():
        raise RuntimeError("daemon thread are not supported "
                           "in subinterpreters")

I commented:

    **Daemon threads must die.** That's a first step towards their death!

**Antoine Pitrou** created `bpo-39812: Avoid daemon threads in
concurrent.futures <https://bugs.python.org/issue39812>`_ as a follow-up.

In February 2020, when rebuilding Fedora Rawhide with Python 3.9, **Miro
Hrončok** of my team noticed that my change `broke the python-jep project
<https://bugzilla.redhat.com/show_bug.cgi?id=1792062>`_. I `reported the bug
upstream <https://github.com/ninia/jep/issues/229>`_. It has been fixed by
using regular threads, rather than daemon threads: `commit
<https://github.com/ninia/jep/commit/a31d461c6cacc96de68d68320eaa83e19a45d0cc>`__.


Conclusion
==========

A random failure on a FreeBSD buildbot was hiding a severe race condition in
the threading shutdown. The bug existed since 2013, but was silently ignored
since the test passed when re-run.

The race condition was that that the threading shutdown didn't ensure that the
Python thread state of all non-daemon threads are deleted, whereas it is a
``Py_EndInterpreter()`` requirement.

I fixed the threading shutdown by waiting until the Python thread state of all
non-daemon threads is deleted.

I also modified ``Thread.start()`` to forbid spawning daemon threads in Python
subinterpreters to fix a related issue.
