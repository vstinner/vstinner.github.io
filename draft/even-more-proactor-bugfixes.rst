++++++++++++++++++++++++++++++
More asyncio proactor bugfixes
++++++++++++++++++++++++++++++

:date: 2019-01-31 13:20
:tags: asyncio
:category: cpython
:slug: more-asyncio-proactor-bugfixes
:authors: Victor Stinner

asyncio ProactorEventLoop bugfixes between June 2018 and Jan 2019.

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

