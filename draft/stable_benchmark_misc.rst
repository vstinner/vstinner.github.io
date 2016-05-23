<<<<<<< faa37002582a262c70ffd5614ba41414355f22d0
++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part xxx
++++++++++++++++++++++++++++++++++++++
=======
++++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part xxx
++++++++++++++++++++++++++++++++++++++++
>>>>>>> artlce

:date: 2016-05-23 23:50
:tags: optimization, benchmark
:category: python
:slug: journey-to-stable-benchmark-xxx
:authors: Victor Stinner
:summary: My journey to stable benchmark, part xxx

Sources of "noise" when running a Python microbenchmark
=======================================================

I found two kinds of noise: "random" noise and "constant" noise. For example,
with a random noise changes, the benchmark will take between 190 and 210 ms, so
an average of 200 ms +/- 10 ms. A constant noise is different: it always has
the same impact. For example, with a constant noise 1, the benchmark always
takes 204 ms, but with the constant noise 2, it only takes 195 ms.

Technically, it is possible to remove almost all sources of noise and really
get a benchmark 100% reproductible: something like 206 ms +/- 0.1 ms. The
problem is that some sources of noise are "legit" and removing this noise
makes the benchmark result completly useless because it is not representative
of a real use case.

Concrete example: the Python hash function is randomized in Python 3 for
security reasons. It *is* possible to disable the randomization and use a fixed
hash function, it is common to do that in unit tests to get a determinstic
behaviour. Problem: in practice, applications run with the hash function
randomized.

Let's say that PYTHONHASHSEED=42 creates hash tables without hash collision, at
least in the hash tables used by the hot code of the benchmark. Let's say that
PYTHONHASHSEED=100 is worse: the most important dictionary lookup of the
benchmark always requires 2 iterations because of hash collisions. The question
is: should you use PYTHONHASHSEED=42 or PYTHONHASHSEED=100 to prove that your
patch makes Python faster?

The answer is that you must no design an optimization for one very specific
artificial environment, whereas users will run your code with a random hash
seed.

Ok, this example is too abstract. You can technically force a specific hash
function to always run your application in the ideal case with the lowest
number of hash collisions.

In my journey to stable benchmark, I hit hard other very concrete examples.

The first one was the fact that adding dead code (adding new functions which
are never called, at least never called by the benchmark) makes the code faster
or slower depending on the size of the deadcode. But I found a workaround to
this issue: PGO+LTO compilation. Next!

Near the end of my journey, I found a much more annoying issue. The result of a
benchmark depends on the command line used to run it. It also depends on
environment variables, even environment variables which have no impact on the
hot code. I'm not sure, but it looks like it also depends on the current
working directory. Well, basically, it depends on a lot of external parameters
of the UNIX environment. Using strace and ltrace, I noticed that the memory
addresses changed, whereas ASLR was disabled.

Python initialization code is quite complex. It depends on a lot of external
files, uses many environment variables, etc. You may try to always replicate
exactly the same file system, the same environment variables, etc. But it is
very likely that you will forget something.

Basically, any very tiny change in your environment changes the memory layout. So what?

According to benchmarks, a memory layout 1 gives a performance of 205 ms,
whereas a layout B gives 197 ms, and a layout C gives 209 ms. Which one is the
good one?

The answer is simple: users will run your application with ASLR enabled. ASLR
is system-wide: you must disable it for all applications if you want to disable
it. In practice, it's enabled by default and users don't care.

With ASLR, you get a random memory layout, and it's a very good thing for own
benchmarks!  Using ASLR, we can *remove* the random noise from the memory
layout! Run 50 processes sequentially to get random results, and then take the
average. That's all.

Let's begin to summarize:

* Never ever again use the minimum in benchmarks

* Leave random noise sources enable if users will have them enabled anyway
  to avoid constant noise which is much worse than random noise!

--

Sources of noise:

* Operating system load:
  CPU isolation, IRQ pinning, disable ASLR. Easy to test using system_load.py.

* Speedup or slowdown when adding dead code, performance basically depends
  on link order and locality of functions in memory: PGO compilation, maybe
  also LTO compilation

* Use the minimum: this is just plain wrong. It's not easy to explain,
  but using the minimum can only lead to false conclusion about the performance
  of a patched Python. Use the average *and* check the standard deviation
  (stdev).

* Random minor difference between two runs:
  PYTHONHASHSEED, already handled by perf.py. Easy to reproduce using two
  different PYTHONHASHSEED values.

* Random temporary performance slow-down:
  CPU Turbo Mode (maybe also HyperThreading)

* Environment variables, command line, current working directory, etc.
  Any tiny change in the environment changes the "memory layout", the exact
  address of objects. On microbenchmarks, it has a real impact, and the effect
  is constant.




