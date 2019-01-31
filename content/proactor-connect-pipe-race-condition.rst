++++++++++++++++++++++++++++++++++++++++++++++
Asyncio: Proactor ConnectPipe() Race Condition
++++++++++++++++++++++++++++++++++++++++++++++

:date: 2019-01-30 18:00
:tags: asyncio
:category: cpython
:slug: asyncio-proactor-connect-pipe-race-condition
:authors: Victor Stinner

Between December 2014 and January 2015, once I succeeded to fix the root issue
of the random asyncio crashes on Windows (`Proactor Cancellation From Hell
<{filename}/proactor-cancellation-hell.rst>`__), I fixed more race conditions
and bugs in ``ProactorEventLoop``:

* ``ConnectPipe()`` Race Condition
* Race Condition in ``BaseSubprocessTransport._try_finish()``
* Close the transport on failure: ResourceWarning
* Cleanup code handling pipes

Previous article: `Proactor Cancellation From Hell
<{filename}/proactor-cancellation-hell.rst>`__.

ConnectPipe() Race Condition
============================

Once I succeeded to fix the root issue of the random asyncio crashes on Windows
(`Proactor Cancellation From Hell
<{filename}/proactor-cancellation-hell.rst>`__), I started to look at the
ConnectPipe special case: `asyncio issue #204: Investigate
IocpProactor.accept_pipe() special case (don't register overlapped)
<https://github.com/python/asyncio/issues/204>`__ (issue created at 25 Aug
2014).

.. image:: {static}/images/pipes.jpg
   :alt: Pipes
   :target: https://www.flickr.com/photos/phrawr/7612947262/

At January 21, 2015, I opened `bpo-23293: race condition related to
IocpProactor.connect_pipe() <https://bugs.python.org/issue23293>`_.

While fixing `bpo-23095 (race condition when cancelling a _WaitHandleFuture)
<https://bugs.python.org/issue23095>`__, I saw that
``IocpProactor.connect_pipe()`` causes "GetQueuedCompletionStatus() returned an
unexpected event" messages to be logged, but also to hang the test suite.

``IocpProactor._register()`` contains the comment::

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

``IocpProactor.close()`` contains this comment::

   # The operation was started with connect_pipe() which
   # queues a task to Windows' thread pool.  This cannot
   # be cancelled, so just forget it.

``IocpProactor.connect_pipe()`` is implemented with ``QueueUserWorkItem()``
which **starts a thread that cannot be interrupted**. Because of that, this
function requires special cases in ``_register()`` and ``close()`` methods of
``IocpProactor``.

I proposed a solution to reimplement ``IocpProactor.connect_pipe()`` **without
a thread**: `asyncio issue #197: Rewrite IocpProactor.connect_pipe() with
non-blocking calls to avoid non interruptible QueueUserWorkItem()
<https://code.google.com/p/tulip/issues/detail?id=197>`__.

At January 22, 2015, I pushed `commit 7ffa2c5f
<https://github.com/python/cpython/commit/7ffa2c5fdda8a9cc254edf67c4458b15db1252fa>`__::

   commit 7ffa2c5fdda8a9cc254edf67c4458b15db1252fa
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Thu Jan 22 22:55:08 2015 +0100

       Issue #23293, asyncio: Rewrite IocpProactor.connect_pipe()

The change adds ``_overlapped.ConnectPipe()`` which tries to connect to the
pipe for asynchronous I/O (overlapped): **call CreateFile() in a loop until
it doesn't fail with ERROR_PIPE_BUSY**. Use an increasing delay between 1 ms
and 100 ms.


Race Condition in BaseSubprocessTransport._try_finish()
=======================================================

If the process exited before the ``_post_init()`` method was called, scheduling
the call to ``_call_connection_lost()`` with ``call_soon()`` is wrong:
``connection_made()`` must be called before ``connection_lost()``.

Reuse the ``BaseSubprocessTransport._call()`` method to schedule the call to
``_call_connection_lost()`` to ensure that ``connection_made()`` and
``connection_lost()`` are called in the correct order.


At Dec 18, 2014, I pushed `commit 1b9763d0
<https://github.com/python/cpython/commit/1b9763d0a9c62c13dc2a06770032e5906b610c96>`__.
The explanation is long, but the change is basically a single line change,
extract::

      - self._loop.call_soon(self._call_connection_lost, None)
      + self._call(self._call_connection_lost, None)

**Ordering properly callbacks in asyncio is challenging!** The order matters
for the semantics of asyncio: it is part of the design of the `PEP 3156 --
Asynchronous IO Support Rebooted: the "asyncio" Module
<https://www.python.org/dev/peps/pep-3156/>`__.


Close the transport on failure: ResourceWarning
===============================================

At January 15, 2015, I pushed `commit 4bf22e03
<https://github.com/python/cpython/commit/4bf22e033e975f61c33752db5a3764dc0f7d0b03>`__,
extract::

   -  yield from transp._post_init()
   +  try:
   +      yield from transp._post_init()
   +  except:
   +      transp.close()
   +      raise

Later, I will spend a lot of time (push many more changes) to ensure that
resources are properly released (especially close transports on failure,
similar to this change).

I will add many **ResourceWarnings** warnings in destructors when a transport,
subprocess or event loop is not closed explicitly.

For example, notice the ``ResourceWarnings`` in the current destructor of
``_SelectorTransport``::

   class _SelectorTransport(transports._FlowControlMixin,
                            transports.Transport):

       def __del__(self, _warn=warnings.warn):
           if self._sock is not None:
               _warn(f"unclosed transport {self!r}", ResourceWarning, source=self)
               self._sock.close()

I even enhanced Python 3.6 to be able to provide the **traceback where the
leaked resource has been allocated** thanks to my ``tracemalloc`` module.
Example with ``filebug.py``::

   def func():
       f = open(__file__)
       f = None

   func()

Output with Python 3.6::

   $ python3 -Wd -X tracemalloc=5 filebug.py
   filebug.py:3: ResourceWarning: unclosed file <_io.TextIOWrapper name='filebug.py' mode='r' encoding='UTF-8'>
     f = None
   Object allocated at (most recent call first):
     File "filebug.py", lineno 2
       f = open(__file__)
     File "filebug.py", lineno 5
       func()

The line where the warning is emitted is usually useless to understand the bug,
whereas the traceback is very useful to identify the leaked resource.

See `my ResourceWarning documentation
<https://pythondev.readthedocs.io/debug_tools.html#resourcewarning>`__.


Cleanup code handling pipes
===========================

Thanks to the new implementation of ``connect_pipe()``, I was able to push
changes to simplify the code and remove various hacks in code handling pipes.

`commit 2b77c546
<https://github.com/python/cpython/commit/2b77c5467f376257ae22cbfbcb3a0e5e6349e92d>`__::

   commit 2b77c5467f376257ae22cbfbcb3a0e5e6349e92d
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Thu Jan 22 23:50:03 2015 +0100

       asyncio, Tulip issue 204: Fix IocpProactor.accept_pipe()

       Overlapped.ConnectNamedPipe() now returns a boolean: True if the pipe is
       connected (if ConnectNamedPipe() failed with ERROR_PIPE_CONNECTED), False if
       the connection is in progress.

       This change removes multiple hacks in IocpProactor.


`commit 3d2256f6
<https://github.com/python/cpython/commit/3d2256f671b7ed5c769dd34b27ae597cbc69047c>`__::

   commit 3d2256f671b7ed5c769dd34b27ae597cbc69047c
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 26 11:02:59 2015 +0100

       Issue #23293, asyncio: Cleanup IocpProactor.close()

       The special case for connect_pipe() is not more needed. connect_pipe() doesn't
       use overlapped operations anymore.

`commit a19b7b3f <https://github.com/python/cpython/commit/a19b7b3fcafe52b98245e14466ffc4d6750ca4f1>`__::

   commit a19b7b3fcafe52b98245e14466ffc4d6750ca4f1
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 26 15:03:20 2015 +0100

       asyncio: Fix ProactorEventLoop.start_serving_pipe()

       If a client connected before the server was closed: drop the client (close the
       pipe) and exit.

`commit e0fd157b <https://github.com/python/cpython/commit/e0fd157ba0cc92e435e7520b4ff641ca68d72244>`__::

   commit e0fd157ba0cc92e435e7520b4ff641ca68d72244
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 26 15:04:03 2015 +0100

       Issue #23293, asyncio: Rewrite IocpProactor.connect_pipe() as a coroutine

       Use a coroutine with asyncio.sleep() instead of call_later() to ensure that the
       schedule call is cancelled.

       Add also a unit test cancelling connect_pipe().

`commit 41063d2a
<https://github.com/python/cpython/commit/41063d2a59a24e257cd9ce62137e36c862e3ab1e>`__::

   commit 41063d2a59a24e257cd9ce62137e36c862e3ab1e
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 26 22:30:49 2015 +0100

       asyncio, Tulip issue 204: Fix IocpProactor.recv()

       If ReadFile() fails with ERROR_BROKEN_PIPE, the operation is not pending: don't
       register the overlapped.

       I don't know if WSARecv() can fail with ERROR_BROKEN_PIPE. Since
       Overlapped.WSARecv() already handled ERROR_BROKEN_PIPE, let me guess that it
       has the same behaviour than ReadFile().
