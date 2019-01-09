++++++++++++++++++++++++++++++
More asyncio proactor bugfixes
++++++++++++++++++++++++++++++

:date: 2019-01-28 22:00
:tags: asyncio
:category: cpython
:slug: more-asyncio-proactor-bugfixes
:authors: Victor Stinner

XXX Bugfixes in 2017..2019.

Data loss caused by WSARecv() cancellation
==========================================

`bpo-33694 <https://bugs.python.org/issue33694>`__, `commit 79790bc3 <https://github.com/python/cpython/commit/79790bc35fe722a49977b52647f9b5fe1deda2b7>`__::

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

WSASend() memory leak
=====================

One year of debug to add a single line to fix a test...

* problem: cannot run the test more than once, so it's a leak of a single
  reference, very difficult to track
* simplify the code: remove dependencies, inline calls, remove useless code,
  etc. put most code into a single file
* tracemalloc
* gc.get_referrers()

`bpo-32710 <https://bugs.python.org/issue32710>`__, `commit a234e148 <https://github.com/python/cpython/commit/a234e148394c2c7419372ab65b773d53a57f3625>`__::

   commit a234e148394c2c7419372ab65b773d53a57f3625
   Author: Victor Stinner <vstinner@redhat.com>
   Date:   Tue Jan 8 14:23:09 2019 +0100

       bpo-32710: Fix leak in Overlapped_WSASend() (GH-11469)

       Fix a memory leak in asyncio in the ProactorEventLoop when ReadFile()
       or WSASend() overlapped operation fail immediately: release the
       internal buffer.

