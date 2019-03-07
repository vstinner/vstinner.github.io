+++++++++++++++++++++++++++++
asyncio WSASend() memory leak
+++++++++++++++++++++++++++++

:date: 2019-03-06 20:00
:tags: asyncio
:category: cpython
:slug: asyncio-proactor-wsasend-memory-leak
:authors: Victor Stinner

I fixed multiple bugs in asyncio ``ProactorEventLoop`` previously. But test_asyncio
still failed sometimes. I noticed a memory leak in ``test_asyncio`` which will
haunt me for 1 year in 2018...

**Yet another example of a test failure which looks harmless but hides a
critical bug.** The bug is that sending a network packet on Windows using
asyncio ``ProactorEventLoop`` can leak the packet. With such bug, it is easy to
imagine a very quick increase of the memory footprint of a network server...

I'm curious why nobody noticed it before me? For me, the only explanation is
that nobody was running a server using ``ProactorEventLoop``. Before Python
3.8, ``SelectorEventLoop`` was the default asyncio event loop on Windows.
`bpo-34687 <https://bugs.python.org/issue34687>`__: Andrew Svetlov, Yury
Selivanov and me agreed to make ``ProactorEventLoop`` the default in Python
3.8! ``Lib/asyncio/windows_events.py`` change of my `commit 6ea29c5e
<https://github.com/python/cpython/commit/6ea29c5e90dde6c240bd8e0815614b52ac307ea1>`__::

    -DefaultEventLoopPolicy = WindowsSelectorEventLoopPolicy
    +DefaultEventLoopPolicy = WindowsProactorEventLoopPolicy

The bug wasn't a regression. It was only discovered 5 years and fixed 6 years
after the code has been written thanks to new tests.

**UPDATE:** I updated the article to add the "Regression? Nope" section and
elaborate the Conclusion.

Previous article:
`asyncio: WSARecv() cancellation causing data loss
<{filename}/proactor-wsarecv-cancellation.rst>`__.

.. image:: {static}/images/leaking_tap.jpg
   :alt: Leaking tap
   :target: https://www.flickr.com/photos/jronaldlee/5996590138/

Yet another random buildbot failure
===================================

One day at the end of January 2018, I noticed a new failure on the AMD64
Windows8.1 Refleaks 3.x" buildbot worker. I reported `bpo-32710
<https://bugs.python.org/issue32710>`__:

    AMD64 Windows8.1 Refleaks 3.x:
    http://buildbot.python.org/all/#/builders/80/builds/118

    test_asyncio leaked [4, 4, 3] memory blocks, sum=11

    I reproduced the issue. I'm running test.bisect to try to isolate this bug.

Only 15 minutes later thanks to my ``test.bisect`` tool, I identified the
leaking test, **test_sendfile_close_peer_in_middle_of_receiving()**::

    It seems to be related to sendfile():

    C:\vstinner\python\master>python -m test -R 3:3 test_asyncio \
        -m test.test_asyncio.test_events.ProactorEventLoopTests.test_sendfile_close_peer_in_middle_of_receiving
    ...
    test_asyncio leaked [1, 2, 1] memory blocks, sum=4

The test is identified, so it should take a few hours, maximum, to fix the bug,
no? We will see...

April
=====

3 months later, I asked:

    The test is still leaking memory blocks. Any progress on investigating the
    issue?

Nobody replied.

At that time, I was busy to fix a bunch of various other bugs reported by
buildbots which were easier to fix and I was kind of exhausted by asyncio, I
didn't want to touch it.

June
====

Oh, I found again this bug while working on my `PR 7827
<https://github.com/python/cpython/pull/7827>`_ (detect handle leaks on Windows
in regrtest).

In 2018, I was very busy with fixing dozens of multiprocessing bugs (fix tests
but also fix some bugs in multiprocessing).

For example, I noticed another memory leak on AMD64 Windows8.1 Refleaks
3.7, `bpo-33735 <https://bugs.python.org/issue33735#msg318425>`_:

    http://buildbot.python.org/all/#/builders/132/builds/154

    test_multiprocessing_spawn leaked [1, 2, 1] memory blocks, sum=4

This test_multiprocessing_spawn leak and the test_asyncio leak on Windows
Refleaks haunted me in 2018...

In fact, it wasn't a real leak. After a few runs, `the test stopped to leak
<https://bugs.python.org/issue33735#msg320948>`__::

    $ ./python -m test test_multiprocessing_spawn \
        -m test.test_multiprocessing_spawn.WithProcessesTestPool.test_imap_unordered \
        -R 1:30
    ...
    test_multiprocessing_spawn leaked [4, 5, 1, 5, 1, 2, 0, 0, 0, ..., 0, 0, 0] memory blocks, sum=18
    test_multiprocessing_spawn failed in 42 sec 470 ms

I fixed the test with `commit
23401fb9
<https://github.com/python/cpython/commit/23401fb960bb94e6ea62d2999527968d53d3fc65>`__.

I fixed other multiprocessing bugs like `bpo-33929
<https://bugs.python.org/issue33929>`__.

These multiprocessing bugs kept me busy.

July-December
=============

Nothing. Nobody looked at the issue.

Again, I was busy fixing various test failures reported by buildbots.


Update in January 2019
======================

In January 2019, after months of hard work on fixing every single buildbot
failure, I realized **suddenly** that the ``test_asyncio`` leak, `bpo-32710
<https://bugs.python.org/issue32710>`__, was one of the last unfixed known test
failure! So I decided to have a new look at it.

Update on ``test_asyncio.test_sendfile.ProactorEventLoopTests``:



* ``test_sendfile_close_peer_in_the_middle_of_receiving()`` leaks 1 reference per
  run: this leak was the obvious bug `bpo-35682
  <https://bugs.python.org/issue35682>`__, I already fixed it with `commit
  80fda712
  <https://github.com/python/cpython/commit/80fda712c83f5dd9560d42bf2aa65a72b18b7759>`__.
* ``test_sendfile_fallback_close_peer_in_the_middle_of_receiving()`` leaks 1
  reference per run: **I don't understand why**.

Note: I had to copy/paste these test names a lot of times. Pleeease, for my
comfort, use shorter test names! :-) (I had to copy/paste them, I don't think
that a regular human is able to type these very long names!)

I spent a lot of time to investigate
``test_sendfile_fallback_close_peer_in_the_middle_of_receiving()`` leak and I don't
understand the issue.

The main loop is ``BaseEventLoop._sendfile_fallback()``. For
the specific case of this test, the loop can be simplified to::

        proto = _SendfileFallbackProtocol(transp)
        try:
            while True:
                data = b'x' * (1024 * 64)
                await proto.drain()
                transp.write(data)
        finally:
            await proto.restore()

The server closes the connection after it gets 1024 bytes. The client socket
gets a ``ConnectionAbortedError`` exception in
``_ProactorBaseWritePipeTransport._loop_writing()`` which calls ``_fatal_error()``::

        except OSError as exc:
            self._fatal_error(exc, 'Fatal write error on pipe transport')

``_fatal_error()`` calls ``_force_close()`` which sets ``_closing`` to
``True``, and calls ``protocol.connection_lost()``. In the meanwhile,
``drain()`` raises ``ConnectionError`` because ``is_closing()`` is true::

    async def drain(self):
        if self._transport.is_closing():
            raise ConnectionError("Connection closed by peer")
        ...

Said differently: **everything works as expected**.


Regression caused by my previous proactor fix?
==============================================

I suspected my own `commit 79790bc3
<https://github.com/python/cpython/commit/79790bc35fe722a49977b52647f9b5fe1deda2b7>`__
pushed 7 months ago to fix a race condition in WSARecv() causing data loss
(that's my previous article: `asyncio: WSARecv() cancellation causing data loss
<{filename}/proactor-wsarecv-cancellation.rst>`__).

Hint: nah, it's unrelated. Moreover, this change has been pushed in May,
whereas I reported `bpo-32710 leak <https://bugs.python.org/issue32710>`__ in
January.


Short script reproducing the leak
=================================

**Identifying a leak of a single reference is really hard** since the test uses
hundreds of Python objects! My blocker issue was to repeat the test enough
times to trigger the leak N times rather than getting a leak of exactly a
single Python reference. The problem was that the test failed when ran more
than once.

All my previous attempts to identify the bug failed:

* Use ``gc.get_referrers()`` to track references between Python objects.
* Use ``tracemalloc`` to track memory usage: the leak is too small, it's lost
  in the results "noise".

I decided to do what I should have done first: **remove as much code as
possible** to reduce the code that I have to audit. I removed most Python
imports, I inlined manually function calls, I removed a lot of code which was
unused in the test, etc.

After a few hours, I managed to reduce the giant pile of code used by the test
into a very short script of only 159 lines of Python code: `test_aiosend.py
<https://bugs.python.org/file48030/test_aiosend.py>`_. The script doesn't call
the asyncio ``sendfile()`` implementation, but uses its own copy of the code,
simplified to do exactly what the test needs::

    async def sendfile(transp):
        proto = _SendfileFallbackProtocol(transp)
        try:
            data = b'x' * (1024 * 24)
            while True:
                await proto.drain()
                transp.write(data)
        finally:
            await proto.restore()

with a local copy of the code of ``_SendfileFallbackProtocol`` class.

Having all code involved in the bug in a single file is way more efficient to
follow the control flow and understands what happens.

The original code is waaaaay more complex, scattered across multiple Python
files in ``Lib/asyncio`` and ``Lib/test/test_asyncio/`` directories.


Root bug identified: WSASend()
==============================

**It took me 1 year, a few sleepless nights, multiple attempts to understand
the leak, but I eventually found it!** WSASend() doesn't release the memory if
it fails immediately. I expected something way more complex, but it's that
simple...

Using the ``test_aiosend.py`` script that I created, I was finally able to
repeat the test in a loop. Thanks to that, it became obvious using
``tracemalloc`` that the leaked memory was the memory passed to ``WSASend()``.

I pushed `commit a234e148
<https://github.com/python/cpython/commit/a234e148394c2c7419372ab65b773d53a57f3625>`__
to fix ``WSASend()``::

    commit a234e148394c2c7419372ab65b773d53a57f3625
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Tue Jan 8 14:23:09 2019 +0100

        bpo-32710: Fix leak in Overlapped_WSASend() (GH-11469)

        Fix a memory leak in asyncio in the ProactorEventLoop when ReadFile()
        or WSASend() overlapped operation fail immediately: release the
        internal buffer.

I was very disappointed by the simplicity of the fix, **it only adds a single
line**::

    diff --git a/Modules/overlapped.c b/Modules/overlapped.c
    index 69875a7f37da..bbaa4fb3008f 100644
    --- a/Modules/overlapped.c
    +++ b/Modules/overlapped.c
    @@ -1011,6 +1012,7 @@ Overlapped_WSASend(OverlappedObject *self, PyObject *args)
             case ERROR_IO_PENDING:
                 Py_RETURN_NONE;
             default:
    +            PyBuffer_Release(&self->user_buffer);
                 self->type = TYPE_NOT_STARTED;
                 return SetFromWindowsErr(err);
         }

So what? One year to add a single line? That's unfair!

My commit contains a very similar fix for ``do_ReadFile()`` used by
``Overlapped_ReadFile()`` and ``Overlapped_ReadFileInto()``.


Fixing more memory leaks
========================

By the way, the ``_overlapped.Overlapped`` type has no traverse function: it may
help the garbage collector to add one. Asyncio is famous for building reference
cycles by design in ``Future.set_exception()``.


I wrote `PR 11489 <https://github.com/python/cpython/pull/11489>`_ to implement
``tp_traverse`` for the ``_overlapped.Overlapped`` type. `Serhiy Storchaka
added
<https://github.com/python/cpython/pull/11489#pullrequestreview-191093765>`__:

    I suspect that there are leaks when self->type is set to TYPE_NOT_STARTED.

And he was right! I modified my PR to fix all memory leaks. After my PR has
been reviewed, I merged it, `commit 5485085b
<https://github.com/python/cpython/commit/5485085b324a45307c1ff4ec7d85b5998d7d5e0d>`__::

    commit 5485085b324a45307c1ff4ec7d85b5998d7d5e0d
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Fri Jan 11 14:35:14 2019 +0100

        bpo-32710: Fix _overlapped.Overlapped memory leaks (GH-11489)

        Fix memory leaks in asyncio ProactorEventLoop on overlapped operation
        failures.

        Changes:

        * Implement the tp_traverse slot in the _overlapped.Overlapped type
          to help to break reference cycles and identify referrers in the
          garbage collector.
        * Always clear overlapped on failure: not only set type to
          TYPE_NOT_STARTED, but release also resources.


Regression? Nope
================

Was the memory leak a regression? Nope. The bug existed since the creation of
the ``overlapped.c`` file in the "Tulip" project in 2013, `commit 27c40353
<https://github.com/python/asyncio/commit/27c403531670f52cad8388aaa2a13a658f753fd5>`__::

    commit 27c403531670f52cad8388aaa2a13a658f753fd5
    Author: Richard Oudkerk <shibturn@gmail.com>
    Date:   Mon Jan 21 20:34:38 2013 +0000

        New experimental iocp branch.

Tulip was the old name of the asyncio project, when it was still an external
project on ``code.google.com``. In the meanwhile, ``code.google.com`` has been
closed and the project moved to https://github.com/python/asyncio/ (now
read-only).

`Extract of the original Overlapped_WSASend() implementation
<https://github.com/python/asyncio/blob/27c403531670f52cad8388aaa2a13a658f753fd5/overlapped.c#L632-L658>`_,
I added a comment to show the location of the bug::

    if (!PyArg_Parse(bufobj, "y*", &self->write_buffer))
        return NULL;

    #if SIZEOF_SIZE_T > SIZEOF_LONG
    if (self->write_buffer.len > (Py_ssize_t)PY_ULONG_MAX) {
        PyBuffer_Release(&self->write_buffer);
        PyErr_SetString(PyExc_ValueError, "buffer to large");
        return NULL;
    }
    #endif
    ...
    self->error = err = (ret < 0 ? WSAGetLastError() : ERROR_SUCCESS);
    switch (err) {
        case ERROR_SUCCESS:
        case ERROR_MORE_DATA:
        case ERROR_IO_PENDING:
            /********* !!! BUG HERE, BUFFER NOT RELEASED !!! ***********/
            Py_RETURN_NONE;
        ...
    }

**I fixed the memory leak 6 years after the code has been written!**

So... why was this bug only discovered in 2018? Multiple very asyncio old bugs
were discovered only recently thanks to more realistic and more advanced
**functional tests**. First tests of asyncio were mostly tiny unit tests
mocking most part of the code. It made sense in the early days of asyncio, when
the code was not mature.

By the way, the `code of the test
<https://github.com/python/cpython/blob/1f58f4fa6a0e3c60cee8df4a35c8dcf3903acde8/Lib/test/test_asyncio/test_sendfile.py#L446-L457>`_
which helped to discovered the bug is::

    def test_sendfile_close_peer_in_the_middle_of_receiving(self):
        srv_proto, cli_proto = self.prepare_sendfile(close_after=1024)
        with self.assertRaises(ConnectionError):
            self.run_loop(
                self.loop.sendfile(cli_proto.transport, self.file))
        self.run_loop(srv_proto.done)

        self.assertTrue(1024 <= srv_proto.nbytes < len(self.DATA),
                        srv_proto.nbytes)
        self.assertTrue(1024 <= self.file.tell() < len(self.DATA),
                        self.file.tell())
        self.assertTrue(cli_proto.transport.is_closing())

Note: The test name has been made even longer in the meanwhile (add "the") :-)


Conclusion
==========

For such complex bugs, **a reliable debugging method is to remove as much code as
possible** to reduce the number of lines of code that should be read.
``tracemalloc`` remains efficient to identify a memory leak when a test can be
run in a loop to make the leak more obvious (I was blocked at the beginning
because the test failed when run a second time in a loop).

Lessons learned? You should try to **investigate every single failure of your
CI**.  It is important to have a test suite with functional tests. "Mock tests"
are fine to quickly write reliable tests, but there are not enough: functional
tests make the difference.

Thanks **Richard Oudkerk** for your great code to use Windows native APIs in
**asyncio** and **multiprocessing**! I like `Windows IOCP
<https://en.wikipedia.org/wiki/Input/output_completion_port>`_, even if the
asyncio implementation is quite complex :-)

Ok, ``_overlapped.Overlapped`` should now have a few less memory leaks :-)
