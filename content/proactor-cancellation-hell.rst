++++++++++++++++++++++++++++++++++++++++
Asyncio: Proactor Cancellation From Hell
++++++++++++++++++++++++++++++++++++++++

:date: 2019-01-28 20:20
:tags: asyncio
:category: cpython
:slug: asyncio-proactor-cancellation-from-hell
:authors: Victor Stinner

Between 2014 and 2015, I was working on the new shiny ``asyncio`` module
(module added to Python 3.4 released in March 2014). I helped to stabilize the
Windows implementation because... well, nobody else was paying attention to it,
and I was worried that test_asyncio **randomly crashed** on Windows.

One bug really annoyed me, I started to fix it in July 2014, but I only
succeeded to **fix the root issue** in January 2015: **six months later**!

It was really difficult to find documentation on IOCP and asynchronous
programming on Windows. **I had to ask for help to someone who had access to
the Windows source code** to understand the bug...

**Spoiler:** cancelling an overlapped ``RegisterWaitForSingleObject()`` with
``UnregisterWait()`` is asynchronous. The asynchronous part is not well
documented and it took me months of debug to understand it. Moreover, the bug
was well hidden for various reasons that we will see below.

Next article: `Asyncio: Proactor ConnectPipe() Race Condition
<{filename}/proactor-connect-pipe-race-condition.rst>`__.

.. image:: {filename}/images/south_park_hell.jpg
   :alt: South Park Hell

Fix cancel() when called twice
==============================

July 2014, `asyncio issue #195
<https://github.com/python/asyncio/issues/195>`__: while working on a
``SIGINT`` signal handler for the ``ProactorEventLoop`` on Windows (`asyncio
issue #191 <https://github.com/python/asyncio/issues/195>`_), I hit a bug on
Windows: ``_WaitHandleFuture.cancel()`` crash if the wait event was already
unregistered by ``finish_wait_for_handle()``. The bug was that
``UnregisterWait()`` was called twice.

I pushed `commit fea6a100
<https://github.com/python/cpython/commit/fea6a100dc51012cb0187374ad31de330ebc0035>`__
to fix this crash::

   commit fea6a100dc51012cb0187374ad31de330ebc0035
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Fri Jul 25 00:54:53 2014 +0200

       Improve stability of the proactor event loop, especially operations on
       overlapped objects (...)

Main changes:

* Fix a crash: **don't call UnregisterWait() twice if a _WaitHandleFuture
  is cancelled twice**.
* Fix another crash: ``_OverlappedFuture.cancel()`` doesn't cancel the
  overlapped anymore if it is already cancelled or completed. Log also an error
  if the cancellation failed.
* ``IocpProactor.close()`` now cancels futures rather than cancelling directly
  underlaying overlapped objects.
* Add a destructor to the ``IocpProactor`` class which closes it

Clear reference from _OverlappedFuture to overlapped
====================================================

July 2014, I created `asyncio issue #196
<https://github.com/python/asyncio/issues/196>`__:
``_OverlappedFuture.set_result()`` should clear the its reference to the
overlapped object.

It is important to explicitly clear references to Python objects as soon as
possible to release resources. Otherwise, an object can remain alive
longer than expected.

I noticed that _OverlappedFuture kept a reference to the undelying overlapped
object even after the asynchronous operation completed. I started to work on a
fix but I had many issues to fix completely this bug... it is just the
beginning of a long journey.

Clear the reference on cancellation and error
---------------------------------------------

I pushed a first fix: `commit 18a28dc5
<https://github.com/python/cpython/commit/18a28dc5c28ae9a953f537486780159ddb768702>`__
clears the reference to the overlapped in ``cancel()`` and ``set_exception()``
methods of ``_OverlappedFuture``::

   commit 18a28dc5c28ae9a953f537486780159ddb768702
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Fri Jul 25 13:05:20 2014 +0200

       * _OverlappedFuture.cancel() now clears its reference to the overlapped object.
         Make also the _OverlappedFuture.ov attribute private.
       * _OverlappedFuture.set_exception() now cancels the overlapped operation.
       * (...)

I started by this change because it didn't make the tests less stable.

Clear the reference in poll()
-----------------------------

Clearing the reference to the overlapped in ``cancel()`` and
``set_exception()`` **works well**. But when I try to do the same on success (in
``set_result()``), **I get random errors**. Example::

   C:\haypo\tulip>\python33\python.exe runtests.py test_pipe
   ...
   Exception RuntimeError: '<_overlapped.Overlapped object at 0x00000000035E7660> s
   till has pending operation at deallocation, the process may crash' ignored
   ...
   Fatal read error on pipe transport
   protocol: <asyncio.streams.StreamReaderProtocol object at 0x00000000035EE668>
   transport: <_ProactorDuplexPipeTransport fd=348>
   Traceback (most recent call last):
     File "C:\haypo\tulip\asyncio\proactor_events.py", line 159, in _loop_reading
       data = fut.result()  # deliver data later in "finally" clause
     File "C:\haypo\tulip\asyncio\futures.py", line 271, in result
       raise self._exception
     File "C:\haypo\tulip\asyncio\windows_events.py", line 488, in _poll
       value = callback(transferred, key, ov)
     File "C:\haypo\tulip\asyncio\windows_events.py", line 279, in finish_recv
       return ov.getresult()
   OSError: [WinError 996] Overlapped I/O event is not in a signaled state
   ...

It seems that the problem only occurs in the fast-path of
``IocpProactor._register()``, when the overlapped is not added to ``_cache``.

Clearing the reference in ``_poll()``, when ``GetQueuedCompletionStatus()`` read
the status, **works**! I pushed a second fix, `commit 65dd69a3
<https://github.com/python/cpython/commit/65dd69a3da16257bd86b92900e5ec5a8dd26f1d9>`__
changes ``_poll()``::

   commit 65dd69a3da16257bd86b92900e5ec5a8dd26f1d9
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Fri Jul 25 22:36:05 2014 +0200

       IocpProactor._poll() clears the reference to the overlapped operation
       when the operation is done. (...)

Ignore false alarms
-------------------

I tried to add the overlapped into ``_cache`` but **then the event loop started
to hang or to fail with new errors**.

I analyzed an overlapped ``WSARecv()`` which has been cancelled. Just after
calling ``CancelIoEx()``, ``HasOverlappedIoCompleted()`` returns 0.

Even after ``GetQueuedCompletionStatus()`` read the status,
``HasOverlappedIoCompleted()`` still returns 0.

**After hours of debug, I eventually found the main issue!**

Sometimes ``GetQueuedCompletionStatus()`` returns an overlapped operation which
has not completed yet. I modified ``IocpProactor._poll()`` to ignore the false
alarm, `commit 51e44ea6
<https://github.com/python/cpython/commit/51e44ea66aefb4229e506263acf40d35596d279c>`__::

   commit 51e44ea66aefb4229e506263acf40d35596d279c
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Sat Jul 26 00:58:34 2014 +0200

       _OverlappedFuture.set_result() now clears its reference to the
       overlapped object.

       IocpProactor._poll() now also ignores false alarms:
       GetQueuedCompletionStatus() returns the overlapped but it is still
       pending.

The fix adds this comment::

   # FIXME: why do we get false alarms?

Keep a reference of overlapped
------------------------------

To stabilize the code, I modified ``ProactorIocp`` to keep a reference to the
overlapped object (it already kept a reference previously but not in all cases).
**Otherwise the memory may be reused and GetQueuedCompletionStatus() may use
random bytes and behaves badly**. I pushed `commit 42d3bdee
<https://github.com/python/cpython/commit/42d3bdeed6e34117b787d61a471563a0dba6a894>`__::

   commit 42d3bdeed6e34117b787d61a471563a0dba6a894
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jul 28 00:18:43 2014 +0200

       ProactorIocp._register() now registers the overlapped
       in the _cache dictionary, even if we already got the result. We need to keep a
       reference to the overlapped object, otherwise the memory may be reused and
       GetQueuedCompletionStatus() may use random bytes and behaves badly.

       There is still a hack for ConnectNamedPipe(): the overlapped object is not
       registered into _cache if the overlapped object completed directly.

       Log also an error in debug mode in ProactorIocp._loop() if we get an unexpected
       event.

       Add a protection in ProactorIocp.close() to avoid blocking, even if it should
       not happen. I still don't understand exactly why some the completion of some
       overlapped objects are not notified.

The change adds a long comment::

   # Even if GetOverlappedResult() was called, we have to wait for the
   # notification of the completion in GetQueuedCompletionStatus().
   # Register the overlapped operation to keep a reference to the
   # OVERLAPPED object, otherwise the memory is freed and Windows may
   # read uninitialized memory.
   #
   # For an unknown reason, ConnectNamedPipe() behaves differently:
   # the completion is not notified by GetOverlappedResult() if we
   # already called GetOverlappedResult(). For this specific case, we
   # don't expect notification (register is set to False).

I pushed another change to attempt to stabilize the code, `commit 313a9809
<https://github.com/python/cpython/commit/313a9809043ed2ed1ad25282af7169e08cdc92a3>`__::

   commit 313a9809043ed2ed1ad25282af7169e08cdc92a3
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Tue Jul 29 12:58:23 2014 +0200

       * _WaitHandleFuture.cancel() now notify IocpProactor through the overlapped
         object that the wait was cancelled.
       * Optimize IocpProactor.wait_for_handle() gets the result if the wait is
         signaled immediatly.
       (...)

asyncio issue #196 closed
-------------------------

The initial issue "_OverlappedFuture.set_result() should clear its reference to
the overlapped object" has been fixed, so **I closed this issue**. I didn't
know at this point that all bugs were not fixed yet...

I also opened the new `asyncio issue #204
<https://github.com/python/asyncio/issues/204>`__ to investigate
``accept_pipe()`` special case. We will analyze this funny bug in another article.


bpo-23095: race condition when cancelling a _WaitHandleFuture
=============================================================

At December 21, 2014, five months after a long serie of changes to stabilize
asyncio...  **asyncio was still crashing randomly on Windows**! I created
`bpo-23095: race condition when cancelling a _WaitHandleFuture
<https://bugs.python.org/issue23095>`__.

On Windows using the IOCP (proactor) event loop, I noticed race conditions when
running the test suite of Trollius (my old deprecated asyncio port to Python
2). For example, sometimes the return code of a process was ``None``, whereas
this case **must never happen**. It looks like the ``wait_for_handle()`` method
doesn't behave properly.

When I run the test suite of asyncio in debug mode (PYTHONASYNCIODEBUG=1),
sometimes I see the message "GetQueuedCompletionStatus() returned an unexpected
event" which **should never occur neither**.

I added debug traces. I saw that the ``IocpProactor.wait_for_handle()`` calls
later ``PostQueuedCompletionStatus()`` through its internal C callback
(``PostToQueueCallback``). It looks like **sometimes the callback is called
whereas the wait was cancelled/acked** by ``UnregisterWait()``.

... I didn't understand the logic between ``RegisterWaitForSingleObject()``,
``UnregisterWait()`` and the callback ....

It looks like sometimes the overlapped object created in Python
(``ov = _overlapped.Overlapped(NULL)``) is destroyed, before
``PostToQueueCallback()`` is called. In the unit tests, **it doesn't crash
because a different overlapped object is created and it gets the same memory
address** (the memory allocator reuses a just freed memory block).

The implementation of ``wait_for_handle()`` had an optimization: it polls
immediatly the wait to check if it already completed. I tried to remove it, but
I got some different issues. If I understood correctly, **this optimization
hides other bugs and reduce the probability of getting the race condition**.

``wait_for_handle()`` is used to wait for the completion of a subprocess, so by
all unit tests running subprocesses, but also in ``test_wait_for_handle()`` and
``test_wait_for_handle_cancel()`` tests. I suspect that running
``test_wait_for_handle()`` or ``test_wait_for_handle_cancel()`` triggers the
bug.

Removing ``_winapi.CloseHandle(self._iocp)`` in ``IocpProactor.close()``
works around the bug. The bug looks to be an expected call to
``PostToQueueCallback()`` which calls ``PostQueuedCompletionStatus()`` on an
IOCP. Not closing the IOCP means using a different IOCP for each test, so the
unexpected call to ``PostQueuedCompletionStatus()`` has no effect on following
tests.

I rewrote some parts of the IOCP code in asyncio. Maybe I introduced this issue
during the refactoring. Maybe **it already existed before but nobody noticed
it, asyncio had fewer unit tests before**.


Fixing the root issue: Overlapped Cancellation From Hell
========================================================

I looked into Twisted implemented of proactor, but it didn't support
subprocesses.

I looked at libuv: it supported processes but not cancelling a wait on a
process handle...

**I had to ask for help to someone who had access to the Windows source code**
to understand the bug...

**After six months of intense debugging, I eventually identified the root
issue** (I pushed the first fix at July 25, 2014). I pushed the `commit
d0a28dee
<https://github.com/python/cpython/commit/d0a28dee78d099fcadc71147cba4affb6efa0c97>`__
(`bpo-23095 <https://bugs.python.org/issue23095>`__)::

   commit d0a28dee78d099fcadc71147cba4affb6efa0c97
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Wed Jan 21 23:39:51 2015 +0100

       Issue #23095, asyncio: Rewrite _WaitHandleFuture.cancel()

This change fixes a race conditon related to ``_WaitHandleFuture.cancel()``
leading to a Python crash or "GetQueuedCompletionStatus() returned an
unexpected event" logs. Previously, **it was possible that the cancelled wait
completes whereas the overlapped object was already destroyed**. Sometimes, a
different overlapped was allocated at the same address, emitting a log about
unexpected completition (but no crash).

``_WaitHandleFuture.cancel()`` now **waits until the handle wait is cancelled**
(until the cancellation completes) before clearing its reference to the
overlapped object. To wait until the cancellation completes,
``UnregisterWaitEx()`` is used with an event (instead of using
``UnregisterWait()``).

To wait for this event, a new ``_WaitCancelFuture`` class was added. It's a
simplified version of ``_WaitCancelFuture``. For example, its ``cancel()``
method calls ``UnregisterWait()``, not ``UnregisterWaitEx()``.
``_WaitCancelFuture`` should not be cancelled.

The overlapped object is **kept alive** in ``_WaitHandleFuture`` **until the
wait is unregistered**.

Later, I pushed a few more changes to fix corner cases.

`commit 1ca9392c
<https://github.com/python/cpython/commit/1ca9392c7083972c1953c02e6f2cca54934ce0a6>`__::

   commit 1ca9392c7083972c1953c02e6f2cca54934ce0a6
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Thu Jan 22 00:17:54 2015 +0100

       Issue #23095, asyncio: IocpProactor.close() must not cancel pending
       _WaitCancelFuture futures

`commit 752aba7f
<https://github.com/python/cpython/commit/752aba7f999b08c833979464a36840de8be0baf0>`__::

   commit 752aba7f999b08c833979464a36840de8be0baf0
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Thu Jan 22 22:47:13 2015 +0100

       asyncio: IocpProactor.close() doesn't cancel anymore futures which are already
       cancelled

`commit 24dfa3c1 <https://github.com/python/cpython/commit/24dfa3c1d6b21e731bd167a13153968bba8fa5ce>`__::

   commit 24dfa3c1d6b21e731bd167a13153968bba8fa5ce
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 26 22:30:28 2015 +0100

       Issue #23095, asyncio: Fix _WaitHandleFuture.cancel()

       If UnregisterWaitEx() fais with ERROR_IO_PENDING, it doesn't mean that the wait
       is unregistered yet. We still have to wait until the wait is cancelled.


I think that *this* issue can now be closed: ``UnregisterWaitEx()`` really do
what we need in asyncio.

I don't like the complexity of the IocpProactor._unregister() method and of the
_WaitCancelFuture class, but it looks that it's how we are supposed to wait
until a wait for a handle is cancelled...

Windows IOCP API is much more complex that what I expected. It's probably
because some parts (especially ``RegisterWaitForSingleObject()``) are
implemented with threads in user land, not in the kernel.

In short, I'm very happy that have fixed this very complex but also very
annoying IOCP bug in asyncio.

I got a nice comment from `Guido van Rossum
<https://bugs.python.org/issue23095#msg234453>`_:

   **Congrats with the fix, and thanks for your perseverance!**

Summary of the race condition
=============================

Events of the crashing unit test:

* The loop (ProactorEventLoop) spawns a subprocess.
* The loop creates a _WaitHandleFuture object which creates an overlapped to
  wait until the process completes (call ``RegisterWaitForSingleObject()``):
  **allocate** memory for the overlapped.
* The wait future is cancelled (call ``UnregisterWait()``).
* The overlapped is destroyed: **free** overlapped memory.
* The overlapped completes: **write** into the overlapped memory.

The main issue is the order of the two last events.

Sometimes, the overlapped completed before the memory was freed: everything is
fine.

Sometimes, the overlapped completed after the memory was freed: Python crashed
(segmentation fault).

Sometimes, another _WaitHandleFuture was created in the meanwhile and created a
second overlapped which was allocated at the same memory address than the freed
memory of the previous overlapped. In this case, when the first overlapped
completes, Python didn't crash but logged an unexpected completion message.

Sometimes, the write was done in freed memory: the write didn't crash Python,
but caused bugs which didn't make sense.

There were even more cases causing even more surprising behaviors.

Summary of the fix:

* (... similar steps for the beginning ...)
* The wait future is cancelled: **create an event** to wait until the
  cancellation completes (call ``UnregisterWaitEx()``).
* Wait for the event.
* The event is signalled which means that the cancellation completed: **write**
  into the overlapped memory.
* The overlapped is destroyed: **free** overlapped memory.
