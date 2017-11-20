https://bugs.python.org/issue29639#msg302087

Author: STINNER Victor * (Python committer) 	Date: 2017-09-13 16:16

I would like to share a short story with you.

I'm working on fixing *all* bugs on our 3 CI (buildbots, Travis CI, AppVeyor). I fixed almost all random test failures.

Right now, I'm trying to fix all "dangling thread" warnings: bpo-31234.

I was sure that I was done, but no, test_ssl failed on Travis CI and AppVeyor. Hum. The failure doesn't make sense. The code is perfectly fine. The thread is supposed to be gone for a long time, but not, it's still here for some reason.

After one day of debugging, I found that the thread is kept alive by a variable of a frame. The frame is kept alive from an traceback object of an Exception. The exception is ConnectionRefusedError. I continue to follow links, I see that the exception comes from socket.create_connection()... Interesting.

socket.create_connection() tries to be nice and keeps the last exception to re-raise it if no connection succeed.

The code seems correct: it stores the exception in the variable "err", and "return sock" is used to exit on succeed.

*But*.

It seems like the exception stored in "err" is part of a reference cycle, so indirectly, a lot of frames are kept alive because of this cycle.

So, I wanted to share this story with you because test_ssl only started to fail recently. The reason is that support.HOST was modified from "127.0.0.1" to "localhost". So if the name resolution first returns an IPv6 address, we may get the ConnectionRefusedError error, stored in "err", and then the connection succeed with IPv4... but you get the reference cycle mess.

Modifying support.HOST to "localhost" triggered a reference cycle!? Strange story.

I'm working on a quick fix: https://github.com/python/cpython/pull/3546
