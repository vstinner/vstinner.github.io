+++++++++++++++++++++++++++++++++++++++++++++++
asyncio: WSARecv() dropping network packets bug
+++++++++++++++++++++++++++++++++++++++++++++++

:date: 2019-01-31 15:20
:tags: asyncio
:category: cpython
:slug: asyncio-proactor-wsarecv-dropping-packets-bug
:authors: Victor Stinner

In May 2018, while looking yet another very boring buildbot test failure on
Windows, I discovered a really huge and critical bug in asyncio on Windows.
The **ProactorEventLoop randomly dropped received network packets**!

Yet another very boring buildbot test failure
=============================================

At May 30, 2018, I created `bpo-33694 <https://bugs.python.org/issue33694>`__.

test_asyncio.test_start_tls_server_1() got many fixes recently: see `bpo-32458
<https://bugs.python.org/issue32458>`__ and `bpo-33674
<https://bugs.python.org/issue33674>`__... but it still fails on Python on x86
Windows7 3.x at revision bb9474f1fb2fc7c7ed9f826b78262d6a12b5f9e8 which
contains all these fixes.

The test fails even when test_asyncio is re-run alone (not when other tests run
in parallel).

Example of failure::

   ERROR: test_start_tls_server_1 (test.test_asyncio.test_sslproto.ProactorStartTLSTests)
   ----------------------------------------------------------------------
   Traceback (most recent call last):
     File "...\lib\test\test_asyncio\test_sslproto.py", line 467, in test_start_tls_server_1
       self.loop.run_until_complete(run_main())
     File "...\lib\asyncio\base_events.py", line 566, in run_until_complete
       raise RuntimeError('Event loop stopped before Future completed.')
   RuntimeError: Event loop stopped before Future completed.

The test fails also on x86 Windows7 3.7. Moreover, 3.7 got an additional failure::

   ======================================================================
   ERROR: test_pipe_handle (test.test_asyncio.test_windows_utils.PipeTests)
   ----------------------------------------------------------------------
   Traceback (most recent call last):
     File "...\lib\test\test_asyncio\test_windows_utils.py", line 73, in test_pipe_handle
       raise RuntimeError('expected ERROR_INVALID_HANDLE')
   RuntimeError: expected ERROR_INVALID_HANDLE


Unable to reproduce the bug
===========================

**Yury Selivanov** `failed to reproduce the issue <https://bugs.python.org/issue33694#msg318193>`__ in Windows 7 VM (on macOS) using:

1. run test_asyncio
2. run test_asyncio.test_sslproto
3. run test_asyncio.test_sslproto -m test_start_tls_server_1

Andrew Svetlov `added <https://bugs.python.org/issue33694#msg318194>`_:

   I used SNDBUF to enforce send buffer overloading. It is not required by
   sendfile tests but I thought that better to have non-mocked way to test such
   situations. We can remove the socket buffers size manipulation at all
   without any problem.

But Yury Selivanov `replied to him
<https://bugs.python.org/issue33694#msg318195>`__:

   When I tried to do that I think **I was having more failures** with that
   test. But really up to you.

Next days, I reported more and more similar failures on Windows buildbots and
AppVeyor (our Windows CI).

I identified the root issue
===========================

Since this bug became more and more frequent, I decided to work on it. Yury and
Andrew failed to reproduce it.

At June 7, 2018, I managed to **reproduce the bug on Linux** by `inserting a
sleep at the right place <https://bugs.python.org/issue33694#msg318869>`_...
I understood one hour later that my patch is wrong: "it introduces a bug in
the test".

On the other hand, I found the root cause: calling ``pause_reading()`` and
``resume_reading()`` on the transport is not safe. Sometimes, we loose data.
See the "TODO" comment below::

   class _ProactorReadPipeTransport(_ProactorBasePipeTransport,
                                    transports.ReadTransport):
       """Transport for read pipes."""
       (...)
       def pause_reading(self):
           if self._closing or self._paused:
               return
           self._paused = True

           if self._read_fut is not None and not self._read_fut.done():
               # TODO: This is an ugly hack to cancel the current read future
               # *and* avoid potential race conditions, as read cancellation
               # goes through `future.cancel()` and `loop.call_soon()`.
               # We then use this special attribute in the reader callback to
               # exit *immediately* without doing any cleanup/rescheduling.
               self._read_fut.__asyncio_cancelled_on_pause__ = True

               self._read_fut.cancel()
               self._read_fut = None
               self._reschedule_on_resume = True

           if self._loop.get_debug():
               logger.debug("%r pauses reading", self)


If you remove the "ugly hack", the test no longer hangs...

Extract of ``_ProactorReadPipeTransport.set_transport()``::

        if self.is_reading():
            # reset reading callback / buffers / self._read_fut
            self.pause_reading()
            self.resume_reading()

This method cancels the pending overlapped ``WSARecv()``, and then creates a
new overlapped ``WSARecv()``.

Even after ``CancelIoEx(old overlapped)``, the IOCP loop still gets an event
for the completion of the cancelled overlapped ``WSARecv()``. Problem: **since
the Python future is cancelled, the event is ignored and so 176 bytes of data
are lost**.

I'm surprised that an overlapped ``WSARecv()`` cancelled by ``CancelIoEx()``
still returns data when IOCP polls for events.

Something else. The bug occurs when ``CancelIoEx()`` (on the current overlapped
``WSARecv()``) fails internally with ``ERROR_NOT_FOUND``. According to
overlapped.c, it means::

   /* CancelIoEx returns ERROR_NOT_FOUND if the I/O completed in-between */

``HasOverlappedIoCompleted()`` returns 0 in that case.

The problem is that currently, ``Overlapped.cancel()`` also returns ``None`` in
that case, and later the asyncio IOCP loop ignores the completion event and so
**drops incoming received data**.

Release blocker bug and functional test reproducing the bug
===========================================================

Yury, Andrew, Ned: I set the priority to release blocker because I'm scared by
what I saw. The START TLS has a race condition in its ProactorEventLoop
implementation. But the bug doesn't see to be specific to START TLS, but rather
to transport.set_transport(), and even more generally to
transport.pause_reading() / transport.resume_reading(). The bug is quite
severe: we loose data and it's really hard to know why (I spent a few hours to
add many many print and try to reproduce on a very tiny reliable unit test). As
an asyncio user, I expect that transports are 100% reliable, and I would first
look into my look (like looking into start_tls() implementation in my case).

If the bug was very specific to start_tls(), I would suggest to "just"
"disable" start_tls() on ProactorEventLoop (sorry, Windows!). But since the
data loss seems to concern basically any application using ProactorEventLoop, I
don't see any simple workaround.

My hope is that a fix can be written shortly to not block the 3.7.0 final
release for too long :-(

Yury, Andrew: Can you please just confirm that it's a regression and that a
release blocker is justified?

race.py: simple echo client and server sending packets in both directions.
Pause/resume reading the client transport every 100 ms to trigger the bug.

Using ProactorEventLoop and 2000 packets of 16 KiB, I easily reproduce the bug.

So again, it's nothing related to start_tls(), start_tls() was just one way to
spot the bug.

The bug is in Proactor transport: the cancellation of overlapped WSARecv()
sometime drops packets. The bug occurs when CancelIoEx() fails with
ERROR_NOT_FOUND which means that the I/O (WSARecv()) completed.

One solution would be to not cancel WSARecv() on pause_reading(): wait until
the current WSARecv() completes, store data something but don't pass it to
protocol.data_received()!, and no schedule a new WSARecv(). Once reading is
resumed: call protocol.data_received() and schedule a new WSARecv().

That would be a workaround. I don't know how to really fix WSARecv()
cancellation without loosing data. A good start would be to modify
Overlapped.cancel() to return a boolean to notice if the overlapped I/O
completed even if we just cancelled it. Currently, the corner case
(CancelIoEx() fails with ERROR_NOT_FOUND) is silently ignored, and then the
IOCP loop silently ignores the event of completed I/O...

Fix the bug
===========

At Jun 8, 2018, I pushed `commit 79790bc3
<https://github.com/python/cpython/commit/79790bc35fe722a49977b52647f9b5fe1deda2b7>`__::

   commit 79790bc35fe722a49977b52647f9b5fe1deda2b7
   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Fri Jun 8 00:25:52 2018 +0200

       bpo-33694: Fix race condition in asyncio proactor (GH-7498)

       The cancellation of an overlapped WSARecv() has a race condition
       which causes data loss because of the current implementation of
       proactor in asyncio.

       No longer cancel overlapped WSARecv() in _ProactorReadPipeTransport
       to work around the race condition.

       Remove the optimized recv_into() implementation to get simple
       implementation of pause_reading() using the single _pending_data
       attribute.

       Move _feed_data_to_bufferred_proto() to protocols.py.

       Remove set_protocol() method which became useless.

I fixed the root issue (in Python 3.7 and future Python 3.8), a race condition
in ProactorEventLoop. But I prefer to keep the issue open a few days to see if
the bug is really gone from all CIs.

Conclusion
==========

You have to write extensive test suite for your software. You have to keep an
eye on your continuous integration (CI). Any tiny test failure can hide a very
severe bug.
