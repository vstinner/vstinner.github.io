++++++++++++++++++++++++++++++
More asyncio proactor bugfixes
++++++++++++++++++++++++++++++

:date: 2019-01-28 22:00
:tags: asyncio
:category: cpython
:slug: more-asyncio-proactor-bugfixes
:authors: Victor Stinner

XXX Bugfixes in 2017..2019.


ConnectPipe
===========

While fixing crashes in ProactorEventLoop, I noticed a weird "special case" for
pipes. At XXX (25 Aug 2014), I opened `asyncio issue #204: Investigate
IocpProactor.accept_pipe() special case (don't register overlapped)
<https://github.com/python/asyncio/issues/204>`__. At January 21, 2015, I also
opened `bpo-23293: race condition related to IocpProactor.connect_pipe()
<https://bugs.python.org/issue23293>`_.

After I succeeded to eventually fix the random crashs on Windows (caused by the "Cancellation From The Hell", see my previous article)

`commit 7ffa2c5f <https://github.com/python/cpython/commit/7ffa2c5fdda8a9cc254edf67c4458b15db1252fa>`__::

   commit 7ffa2c5fdda8a9cc254edf67c4458b15db1252fa
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Thu Jan 22 22:55:08 2015 +0100

       Issue #23293, asyncio: Rewrite IocpProactor.connect_pipe()

       Add _overlapped.ConnectPipe() which tries to connect to the pipe for
       asynchronous I/O (overlapped): call CreateFile() in a loop until it doesn't
       fail with ERROR_PIPE_BUSY. Use an increasing delay between 1 ms and 100 ms.

       Remove Overlapped.WaitNamedPipeAndConnect() which is no more used.

`commit 2b77c546 <https://github.com/python/cpython/commit/2b77c5467f376257ae22cbfbcb3a0e5e6349e92d>`__::

   commit 2b77c5467f376257ae22cbfbcb3a0e5e6349e92d
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Thu Jan 22 23:50:03 2015 +0100

       asyncio, Tulip issue 204: Fix IocpProactor.accept_pipe()

       Overlapped.ConnectNamedPipe() now returns a boolean: True if the pipe is
       connected (if ConnectNamedPipe() failed with ERROR_PIPE_CONNECTED), False if
       the connection is in progress.

       This change removes multiple hacks in IocpProactor.


`commit 3d2256f6 <https://github.com/python/cpython/commit/3d2256f671b7ed5c769dd34b27ae597cbc69047c>`__::

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

`commit 41063d2a <https://github.com/python/cpython/commit/41063d2a59a24e257cd9ce62137e36c862e3ab1e>`__::

   commit 41063d2a59a24e257cd9ce62137e36c862e3ab1e
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Mon Jan 26 22:30:49 2015 +0100

       asyncio, Tulip issue 204: Fix IocpProactor.recv()

       If ReadFile() fails with ERROR_BROKEN_PIPE, the operation is not pending: don't
       register the overlapped.

       I don't know if WSARecv() can fail with ERROR_BROKEN_PIPE. Since
       Overlapped.WSARecv() already handled ERROR_BROKEN_PIPE, let me guess that it
       has the same behaviour than ReadFile().

`commit 47cd10d7 <https://github.com/python/cpython/commit/47cd10d7a903773f574fc93220dbca850067fa0c>`__::

   commit 47cd10d7a903773f574fc93220dbca850067fa0c
   Author: Victor Stinner <victor.stinner@gmail.com>
   Date:   Fri Jan 30 00:05:19 2015 +0100

       asyncio: sync with Tulip

       Issue #23347: send_signal(), kill() and terminate() methods of
       BaseSubprocessTransport now check if the transport was closed and if the
       process exited.

       Issue #23347: Refactor creation of subprocess transports. Changes on
       BaseSubprocessTransport:

       * Add a wait() method to wait until the child process exit
       * The constructor now accepts an optional waiter parameter. The _post_init()
         coroutine must not be called explicitly anymore. It makes subprocess
         transports closer to other transports, and it gives more freedom if we want
         later to change completly how subprocess transports are created.
       * close() now kills the process instead of kindly terminate it: the child
         process may ignore SIGTERM and continue to run. Call explicitly terminate()
         and wait() if you want to kindly terminate the child process.
       * close() now logs a warning in debug mode if the process is still running and
         needs to be killed
       * _make_subprocess_transport() is now fully asynchronous again: if the creation
         of the transport failed, wait asynchronously for the process eixt. Before the
         wait was synchronous. This change requires close() to *kill*, and not
         terminate, the child process.
       * Remove the _kill_wait() method, replaced with a more agressive close()
         method. It fixes _make_subprocess_transport() on error.
         BaseSubprocessTransport.close() calls the close() method of pipe transports,
         whereas _kill_wait() closed directly pipes of the subprocess.Popen object
         without unregistering file descriptors from the selector (which caused severe
         bugs).

       These changes simplifies the code of subprocess.py.

Misc bugfixes
=============

Fix a race condition in BaseSubprocessTransport._try_finish()
-------------------------------------------------------------

If the process exited before the ``_post_init()`` method was called, scheduling
the call to ``_call_connection_lost()`` with call_soon() is wrong:
``connection_made()`` must be called before ``connection_lost()``.

Reuse the ``BaseSubprocessTransport._call()`` method to schedule the call to
``_call_connection_lost()`` to ensure that ``connection_made()`` and
``connection_lost()`` are called in the correct order.

The explanation is long, but the change is basically a single line change,
extract of `commit 1b9763d0
<https://github.com/python/cpython/commit/1b9763d0a9c62c13dc2a06770032e5906b610c96>`__::

      - self._loop.call_soon(self._call_connection_lost, None)
      + self._call(self._call_connection_lost, None)

Ordering properly events in asyncio is challenging!

Close the transport on subprocess creation failure
--------------------------------------------------

Extract of `commit 4bf22e03
<https://github.com/python/cpython/commit/4bf22e033e975f61c33752db5a3764dc0f7d0b03>`__::

   -  yield from transp._post_init()
   +  try:
   +      yield from transp._post_init()
   +  except:
   +      transp.close()
   +      raise

Later, I will spend a lot of time to ensure that resources are properly
released. I will add many ``ResourceWarnings`` warnings in destructors when a
transport, subprocess or event loop is not closed explicitly.

Extract of the current code::

   class _SelectorTransport(transports._FlowControlMixin,
                            transports.Transport):

       def __del__(self, _warn=warnings.warn):
           if self._sock is not None:
               _warn(f"unclosed transport {self!r}",
                     ResourceWarning, source=self)
               self._sock.close()
