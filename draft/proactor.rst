The cancelled overlapped of the devil
=====================================

I had to find a copy of the Windows source code to understand the bug...

bpo-33694: Fix race condition in asyncio proactor
=================================================

https://github.com/python/cpython/commit/79790bc35fe722a49977b52647f9b5fe1deda2b7

proactor memory leak
====================

* problem: cannot run the test more than once, so it's a leak of a single
  reference, very difficult to track
* simplify the code: remove dependencies, inline calls, remove useless code,
  etc. put most code into a single file
* tracemalloc
* gc.get_referrers()

https://github.com/python/cpython/pull/11469
