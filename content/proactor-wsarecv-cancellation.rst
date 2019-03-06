+++++++++++++++++++++++++++++++++++++++++++++++++
asyncio: WSARecv() cancellation causing data loss
+++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2019-01-31 15:20
:tags: asyncio
:category: cpython
:slug: asyncio-proactor-wsarecv-cancellation-data-loss
:authors: Victor Stinner

In December 2017, **Yury Selivanov** pushed the long awaited ``start_tls()``
function.

A newly added test failed on Windows. Later, the test started to fail
randomly on Linux as well. In fact, it was a well hidden race condition in the
asynchronous handshake of ``SSLProtocol`` which will take 5 months of work to
be identified and fixed. The bug wasn't a recent regression, but only spotted
thanks to newly added tests.

Even after this bug has been fixed, the same test still failed randomly on
Windows! Once I found how to reproduce the bug, I understood that it's a **very
scary bug**: ``WSARecv()`` cancellation randomly caused **data loss**! Again,
it was a very well hidden bug which likely existing since the early days of the
``ProactorEventLoop`` implementation.

Previous article: `Asyncio: Proactor ConnectPipe() Race Condition
<{filename}/proactor-connect-pipe-race-condition.rst>`__.
Next article: `asyncio: WSASend() memory leak
<{filename}/proactor-wsasend-memory-leak.rst>`__.

.. image:: {static}/images/lock.jpg
   :alt: Unlocked lock
   :target: https://www.flickr.com/photos/joybot/6026542856/


New start_tls() function
========================

The "starttls" feature have been requested since creation of asyncio. At
October 24, 2013, **Guido van Rossum** created `asyncio issue #79
<https://github.com/python/asyncio/issues/79>`__:

   **Glyph [Lefkowitz]** and **Antoine [Pitrou]** really want a API to upgrade an
   existing Transport/Protocol pair to SSL/TLS, without having to create a new
   protocol.

At March 23, 2015, **Giovanni Cannata** created `bpo-23749
<https://bugs.python.org/issue23749>`__ which is basically the same feature
request. I `replied <https://bugs.python.org/issue23749#msg239022>`__:

   asyncio got a new SSL implementation which makes possible to implement
   STARTTLS. Are you interested to implement it?

**Elizabeth Myers**, **Antoine Pitrou**, **Guido van Rossum** and
**Yury Selivanov** designed the feature. Yury `wrote a prototype
<https://bugs.python.org/issue23749#msg253495>`_ in 2015 for PostgreSQL.  In
2017, **Barry Warsaw** `wrote his own implementation for SMTP
<https://bugs.python.org/issue23749#msg293912>`_.

At the end of 2017, **four year** after Guido van Rossum created the feature
request, **Yury Selivanov** implemented the feature and pushed the `commit
f111b3dc
<https://github.com/python/cpython/commit/f111b3dcb414093a4efb9d74b69925e535ddc470>`__::

   commit f111b3dcb414093a4efb9d74b69925e535ddc470
   Author: Yury Selivanov <yury@magic.io>
   Date:   Sat Dec 30 00:35:36 2017 -0500

       bpo-23749: Implement loop.start_tls() (#5039)


SSLProtocol Race Condition
==========================

Test fails on AppVeyor (Windows): temporary fix
-----------------------------------------------

At December 30, 2017, just after Yury pushed his implementation of
``start_tls()`` (the same day), **Antoine Pitrou** reported `bpo-32458
<https://bugs.python.org/issue32458>`__: it seems test_asyncio fails
sporadically on AppVeyor::

   ERROR: test_start_tls_server_1 (test.test_asyncio.test_sslproto.ProactorStartTLS)
   ----------------------------------------------------------------------
   Traceback (most recent call last):
     File "C:\projects\cpython\lib\test\test_asyncio\test_sslproto.py", line 284, in test_start_tls_server_1
       asyncio.wait_for(main(), loop=self.loop, timeout=10))
     File "C:\projects\cpython\lib\asyncio\base_events.py", line 440, in run_until_complete
       return future.result()
     File "C:\projects\cpython\lib\asyncio\tasks.py", line 398, in wait_for
       raise futures.TimeoutError()
   concurrent.futures._base.TimeoutError

**Yury Selivanov** `wrote <https://bugs.python.org/issue32458#msg309254>`_:

   I'm leaving on a two-weeks vacation today.  To avoid risking breaking the workflow, I'll mask this tests on AppVeyor.  I'll investigate this when I get back.

and skipped the test as a **temporary fix**, `commit 0c36bed1
<https://github.com/python/cpython/commit/0c36bed1c46d07ef91d3e02e69e974e4f3ecd31a>`__::

   commit 0c36bed1c46d07ef91d3e02e69e974e4f3ecd31a
   Author: Yury Selivanov <yury@magic.io>
   Date:   Sat Dec 30 15:40:20 2017 -0500

       bpo-32458: Temporarily mask start-tls proactor test on Windows (#5054)

Bug reproduced on Linux
-----------------------

At May 23, 2018, five month after the bug have been reported, `I wrote
<https://bugs.python.org/issue32458#msg317468>`_:

   test_start_tls_server_1() just failed on my Linux. It likely depends on the system load.

Christian Heimes `added <https://bugs.python.org/issue32458#msg317760>`__:

   [On Linux,] It's failing reproducible with OpenSSL 1.1.1 and TLS 1.3
   enabled. I haven't seen it failing with TLS 1.2 yet.

At May 28, 2018, I found a reliable way to `reproduce the issue on Linux
<https://bugs.python.org/issue32458#msg317833>`_:

   Open 3 terminals and run these commands in parallel:

   (1) ``./python -m test test_asyncio -m test_start_tls_server_1 -F``
   (2) ``./python -m test -j16 -r``
   (3) ``./python -m test -j16 -r``

   It's a **race condition** which doesn't depend on the OS, but on the system
   load.

Root issue identified
---------------------

Once I found how to reproduce the bug, I was able to investigate it. I created
`bpo-33674 <https://bugs.python.org/issue33674>`__.

I found a race condition in ``SSLProtocol`` of ``asyncio/sslproto.py``.
Sometimes, ``_sslpipe.feed_ssldata()`` is called before
``_sslpipe.shutdown()``.

* ``SSLProtocol.connection_made()`` -> ``SSLProtocol._start_handshake()``: ``self._loop.call_soon(self._process_write_backlog)``
* ``SSLProtoco.data_received()``: direct call to ``self._sslpipe.feed_ssldata(data)``
* Later, ``self._process_write_backlog()`` calls ``self._sslpipe.do_handshake()``

The first **write** is **delayed** by ``call_soon()``, whereas the first
**read** is a **direct call** to the SSL pipe.

Workaround::

   diff --git a/Lib/asyncio/sslproto.py b/Lib/asyncio/sslproto.py
   index 2bfa45dd15..4a5dbb38a1 100644
   --- a/Lib/asyncio/sslproto.py
   +++ b/Lib/asyncio/sslproto.py
   @@ -592,7 +592,7 @@ class SSLProtocol(protocols.Protocol):
            # (b'', 1) is a special value in _process_write_backlog() to do
            # the SSL handshake
            self._write_backlog.append((b'', 1))
   -        self._loop.call_soon(self._process_write_backlog)
   +        self._process_write_backlog()
            self._handshake_timeout_handle = \
                self._loop.call_later(self._ssl_handshake_timeout,
                                      self._check_handshake_timeout)

Yury Selivanov wrote:

   **The fix is correct and the bug is now obvious**: ``data_received()`` occurs
   pretty much any time after ``connection_made()`` call; if ``call_soon()`` is
   used in ``connection_made()``, ``data_received()`` may find the protocol in
   an incorrect state.

   **Kudos Victor for debugging this.**

I pushed `commit be00a558 <https://github.com/python/cpython/commit/be00a5583a2cb696335c527b921d1868266a42c6>`__::

   commit be00a5583a2cb696335c527b921d1868266a42c6
   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Tue May 29 01:33:35 2018 +0200

       bpo-33674: asyncio: Fix SSLProtocol race (GH-7175)

       Fix a race condition in SSLProtocol.connection_made() of
       asyncio.sslproto: start immediately the handshake instead of using
       call_soon(). Previously, data_received() could be called before the
       handshake started, causing the handshake to hang or fail.

... the change is basically a single line change::

   - self._loop.call_soon(self._process_write_backlog)
   + self._process_write_backlog()

I closed `bpo-32458 <https://bugs.python.org/issue32458>`__ and **Yury
Selivanov** closed `bpo-33674 <https://bugs.python.org/issue33674>`__.

Not a regression
----------------

The SSLProtocol race condition wasn't new: it existed since January 2015,
`commit 231b404c
<https://github.com/python/cpython/commit/231b404cb026649d4b7172e75ac394ef558efe60>`__::

   commit 231b404cb026649d4b7172e75ac394ef558efe60
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Wed Jan 14 00:19:09 2015 +0100

       Issue #22560: New SSL implementation based on ssl.MemoryBIO

       The new SSL implementation is based on the new ssl.MemoryBIO which is only
       available on Python 3.5. On Python 3.4 and older, the legacy SSL implementation
       (using SSL_write, SSL_read, etc.) is used. The proactor event loop only
       supports the new implementation.

       The new asyncio.sslproto module adds _SSLPipe, SSLProtocol and
       _SSLProtocolTransport classes. _SSLPipe allows to "wrap" or "unwrap" a socket
       (switch between cleartext and SSL/TLS).

       Patch written by Antoine Pitrou. sslproto.py is based on gruvi/ssl.py of the
       gruvi project written by Geert Jansen.

       This change adds SSL support to ProactorEventLoop on Python 3.5 and newer!

       It becomes also possible to implement STARTTTLS: switch a cleartext socket to
       SSL.

This is the new cool asynchronous SSL implementation written by **Antoine
Pitrou** and **Geert Jansen**. It took **3 years** and **new functional tests**
to discover the race condition.


WSARecv() cancellation causing data loss
========================================

Yet another very boring buildbot test failure
---------------------------------------------

At May 30, 2018, the day after I fixed SSLProtocol race condition, I created
`bpo-33694 <https://bugs.python.org/issue33694>`__.

test_asyncio.test_start_tls_server_1() got multiple fixes recently (see
`bpo-32458 <https://bugs.python.org/issue32458>`__ and `bpo-33674
<https://bugs.python.org/issue33674>`__)... but it still fails on Python on x86
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

   ERROR: test_pipe_handle (test.test_asyncio.test_windows_utils.PipeTests)
   ----------------------------------------------------------------------
   Traceback (most recent call last):
     File "...\lib\test\test_asyncio\test_windows_utils.py", line 73, in test_pipe_handle
       raise RuntimeError('expected ERROR_INVALID_HANDLE')
   RuntimeError: expected ERROR_INVALID_HANDLE


Unable to reproduce the bug
---------------------------

**Yury Selivanov** `failed to reproduce the issue <https://bugs.python.org/issue33694#msg318193>`__ in Windows 7 VM (on macOS) using:

1. run ``test_asyncio``
2. run ``test_asyncio.test_sslproto``
3. run ``test_asyncio.test_sslproto -m test_start_tls_server_1``

**Andrew Svetlov** `added <https://bugs.python.org/issue33694#msg318194>`__:

   I used ``SNDBUF`` to enforce send buffer overloading. It is not required by
   sendfile tests but I thought that better to have non-mocked way to test such
   situations. We can remove the socket buffers size manipulation at all
   without any problem.

But Yury Selivanov `replied
<https://bugs.python.org/issue33694#msg318195>`__:

   When I tried to do that I think **I was having more failures** with that
   test. But really up to you.

Next days, I reported more and more similar failures on Windows buildbots and
AppVeyor (our Windows CI).

Root issue identified: pause_reading()
--------------------------------------

Since this bug became more and more frequent, I decided to work on it. Yury and
Andrew failed to reproduce it.

At June 7, 2018, I managed to **reproduce the bug on Linux** by `inserting a
sleep at the right place <https://bugs.python.org/issue33694#msg318869>`_...
I understood one hour later that my patch is wrong: "it introduces a bug in
the test".

On the other hand, I found the root cause: calling ``pause_reading()`` and
``resume_reading()`` on the transport is not safe. Sometimes, we loose data.
See the **ugly hack** described in the TODO comment below::

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

This method **cancels the pending overlapped** ``WSARecv()``, and then creates
a new overlapped ``WSARecv()``.

Even after ``CancelIoEx(old overlapped)``, the IOCP loop still gets an event
for the completion of the cancelled overlapped ``WSARecv()``. Problem: **since
the Python future is cancelled, the event is ignored and so 176 bytes of data
are lost**.

I'm surprised that an overlapped ``WSARecv()`` **cancelled** by
``CancelIoEx()`` still returns data when IOCP polls for events.

Something else. The bug occurs when ``CancelIoEx()`` (on the current overlapped
``WSARecv()``) fails internally with ``ERROR_NOT_FOUND``. According to
overlapped.c, it means::

   /* CancelIoEx returns ERROR_NOT_FOUND if the I/O completed in-between */

``HasOverlappedIoCompleted()`` returns 0 in that case.

The problem is that currently, ``Overlapped.cancel()`` also returns ``None`` in
that case, and later the asyncio IOCP loop ignores the completion event and so
**drops incoming received data**.

Release blocker bug?
--------------------

Yury, Andrew, Ned: I set the priority to release blocker because I'm scared by
what I saw. The START TLS has a race condition in its ProactorEventLoop
implementation. But the bug doesn't see to be specific to START TLS, but rather
to ``transport.set_transport()``, and even more generally to
``transport.pause_reading()`` / ``transport.resume_reading()``. The bug is quite
severe: we loose data and it's really hard to know why (I spent a few hours to
add many many print and try to reproduce on a very tiny reliable unit test). As
an asyncio user, I expect that transports are 100% reliable, and I would first
look into my code (like looking into ``start_tls()`` implementation in my case).

If the bug was very specific to ``start_tls()``, I would suggest to "just"
"disable" start_tls() on ProactorEventLoop (sorry, Windows!). But since the
data loss seems to concern basically any application using
``ProactorEventLoop``, I don't see any simple workaround.

**My hope is that a fix can be written shortly** to not block the 3.7.0 final
release for too long :-(

Yury, Andrew: Can you please just confirm that it's a regression and that a
release blocker is justified?

Functional test reproducing the bug
-----------------------------------

I wrote `race.py script <https://bugs.python.org/file47632/race.py>`_: simple
echo client and server sending packets in both directions.  Pause/resume
reading the client transport every 100 ms to trigger the bug.

Using ``ProactorEventLoop`` and 2000 packets of 16 KiB, I easily reproduce the
bug.

So again, it's nothing related to ``start_tls()``, ``start_tls()`` was just one
way to spot the bug.

The bug is in Proactor transport: the cancellation of overlapped ``WSARecv()``
sometime drops packets. The bug occurs when ``CancelIoEx()`` fails with
``ERROR_NOT_FOUND`` which means that the I/O (``WSARecv()``) completed.

One solution would be to not cancel ``WSARecv()`` on pause_reading(): wait
until the current ``WSARecv()`` completes, store data somewhere but don't pass
it to ``protocol.data_received()``, and don't schedule a new ``WSARecv()``.
Once reading is resumed: call ``protocol.data_received()`` and schedule a new
``WSARecv()``.

That would be a workaround. I don't know how to really fix ``WSARecv()``
cancellation without loosing data. A good start would be to modify
``Overlapped.cancel()`` to return a boolean to notice if the overlapped I/O
completed even if we just cancelled it. Currently, the corner case
(``CancelIoEx()`` fails with ``ERROR_NOT_FOUND``) is silently ignored, and then
the IOCP loop silently ignores the event of completed I/O...

Fix the bug: no longer cancel WSARecv()
---------------------------------------

At June 8, 2018, I pushed `commit 79790bc3
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

I fixed the root issue (in Python 3.7 and future Python 3.8).

I used my ``race.py`` script to validate that the issue is fixed for real.

Conclusion
==========

I fixed one race condition in the asynchronous handshake of ``SSLProtocol``.

I found and fixed a data loss bug caused by ``WSARecv()`` cancellation.

Lessons learnt from these two bugs:

* You should **write an extensive test suite** for your code.
* You should **keep an eye on your continuous integration (CI)**: any tiny test
  failure can hide a very severe bug.
