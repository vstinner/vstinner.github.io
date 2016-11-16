++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Analysis of a performance slowdown: impact of the code placement
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Problem
=======

Result of the call_method betwen March 2016 and December 2016 on the
``default`` branch of CPython:

image: call_method.png

It's easy to spot a peak at 29 ms whereas the average is closer to 17 ms. It's
like a single commit suddenly made Python 70% slower but was fixed in the
following commit.

Reproduce results
=================

To analyze the performance issue, the fist step is to check which exact
Mercurial revision introduced the regression and which revision fixed the bug.

Interesting dots on the graphic:

* 678fe178da0d, Oct 09: 17.0 ms
* 1ce50f7027c1, Oct 19: 28.9 ms
* 36af3566b67a, Nov 3: 16.9 ms

I'm using the following directories:

* ~/perf: checkout of the GitHub haypo/perf project
* ~/performance: checkout of the GitHub python/performance project
* ~/cpython: checkouf of the Mercurial CPython repository

First, try to reproduce these timings.

Fast::

    $ hg up -C -r 678fe178da0d
    $ ./configure --with-lto -C && make clean && make
    $ PYTHONPATH=~/perf ./python ~/performance/performance/benchmarks/bm_call_method.py --inherit-environ=PYTHONPATH --fast
    call_method: Median +- std dev: 17.0 ms +- 0.1 ms

Slow::

    $ hg up -C -r 1ce50f7027c1
    $ ./configure --with-lto -C && make clean && make
    $ PYTHONPATH=~/perf ./python ~/performance/performance/benchmarks/bm_call_method.py --inherit-environ=PYTHONPATH --fast
    call_method: Median +- std dev: 29.3 ms +- 0.9 ms

Note:: ``./configure`` + ``make clean`` avoids compilation errors.


perf record, 1
==============

To collect perf events, we will run the benchmark with ``--worker`` to run a
single process and with ``-w0 -n100`` to run long enough: 100 samples means at
least 10 secons, a single sample must take at least 100 ms).

If you used ``python3 -m perf system tune`` previously, you should reset the system configuration::

    sudo python3 -m perf system reset

Commands::

    PYTHONPATH=~/perf perf record ./python ~/performance/performance/benchmarks/bm_call_method.py --inherit-environ=PYTHONPATH --worker -v -w0 -n100
    perf report

Output::

     40.27%  python  python              [.] _PyEval_EvalFrameDefault
     10.30%  python  python              [.] call_function
     10.21%  python  python              [.] PyFrame_New
      8.56%  python  python              [.] frame_dealloc
      5.51%  python  python              [.] PyObject_GenericGetAttr
      5.19%  python  python              [.] _PyFunction_FastCall
      4.68%  python  python              [.] _PyType_Lookup
      3.63%  python  python              [.] PyMethod_New
      2.61%  python  python              [.] method_dealloc
      2.18%  python  python              [.] _Py_CheckFunctionResult
      2.00%  python  python              [.] PyObject_GetAttr
      1.72%  python  python              [.] PyObject_GC_UnTrack
      1.44%  python  python              [.] _PyThreadState_UncheckedGet
      1.31%  python  python              [.] PyErr_Occurred
      0.17%  python  python              [.] func_descr_get

So the top 5 CPython functions are:

* _PyEval_EvalFrameDefault()
* call_function()
* PyFrame_New()
* frame_dealloc()
* PyObject_GenericGetAttr()

Then tune again the system for benchmark (needed later)::

    sudo python3 -m perf system tune


perf stat
=========

Keep the current Python as ``python-slow`` and build revision 678fe178da0d as
``python-fast``::

    mv python python-slow
    hg up -C -r 678fe178da0d
    ./configure --with-lto -C && make clean && make
    mv python python-fast

Fisrt find the name of the perf event::

    $ perf list|grep L1
      L1-dcache-loads                                    [Hardware cache event]
      L1-dcache-load-misses                              [Hardware cache event]
      L1-dcache-stores                                   [Hardware cache event]
      L1-dcache-store-misses                             [Hardware cache event]
      L1-dcache-prefetches                               [Hardware cache event]
      L1-dcache-prefetch-misses                          [Hardware cache event]
      L1-icache-loads                                    [Hardware cache event]
      L1-icache-load-misses                              [Hardware cache event]

I'm interested by the code, so the instruction cache:

* L1-icache-loads
* L1-icache-load-misses

Compare the usage of the CPU L1 instruction cache::

    PYTHONPATH=~/perf perf stat -e L1-icache-loads,L1-icache-load-misses ./python-slow ~/performance/performance/benchmarks/bm_call_method.py --inherit-environ=PYTHONPATH --worker -w0 -n10
    PYTHONPATH=~/perf perf stat -e L1-icache-loads,L1-icache-load-misses ./python-fast ~/performance/performance/benchmarks/bm_call_method.py --inherit-environ=PYTHONPATH --worker -w0 -n10

Output::

 Performance counter stats for './python-slow (...)':

    10,753,371,258 L1-icache-loads
       848,511,308 L1-icache-load-misses     #    7.89% of all L1-icache hits

       6.020490449 seconds time elapsed

 Performance counter stats for './python-fast (...)':

    10,134,106,571 L1-icache-loads
        10,917,606 L1-icache-load-misses     #    0.11% of all L1-icache hits

       3.775067668 seconds time elapsed

Cache miss on the L1 instruction cache:

* Slow: 8.0%
* Fast: 0.1%

The slow Python has 71.7x more cache misses than the fast Python!


Generic statistics
------------------

``perf stat``::

 Performance counter stats for ./python-fast:

       3773.585194 task-clock (msec)         #    0.998 CPUs utilized
               369 context-switches          #    0.098 K/sec
                 0 cpu-migrations            #    0.000 K/sec
             8,300 page-faults               #    0.002 M/sec
    12,981,234,867 cycles                    #    3.440 GHz                     [83.27%]
     1,460,980,720 stalled-cycles-frontend   #   11.25% frontend cycles idle    [83.36%]
       435,806,788 stalled-cycles-backend    #    3.36% backend  cycles idle    [66.72%]
    29,982,530,201 instructions              #    2.31  insns per cycle
                                             #    0.05  stalled cycles per insn [83.40%]
     5,613,631,616 branches                  # 1487.612 M/sec                   [83.40%]
        16,006,564 branch-misses             #    0.29% of all branches         [83.27%]

       3.780064486 seconds time elapsed

 Performance counter stats for ./python-slow:

       5906.239860 task-clock (msec)         #    0.998 CPUs utilized
               556 context-switches          #    0.094 K/sec
                 0 cpu-migrations            #    0.000 K/sec
             8,393 page-faults               #    0.001 M/sec
    20,651,474,102 cycles                    #    3.497 GHz                     [83.36%]
     8,480,803,345 stalled-cycles-frontend   #   41.07% frontend cycles idle    [83.37%]
     4,247,826,420 stalled-cycles-backend    #   20.57% backend  cycles idle    [66.64%]
    30,011,465,614 instructions              #    1.45  insns per cycle
                                             #    0.28  stalled cycles per insn [83.32%]
     5,612,485,730 branches                  #  950.264 M/sec                   [83.36%]
        13,584,136 branch-misses             #    0.24% of all branches         [83.29%]

       5.915402403 seconds time elapsed

Significant differences, fast => slow:

* Instruction per cycle: 2.31 => 1.45
* stalled-cycles-frontend: 11.25% => 41.07%
* stalled-cycles-backend: 3.36% => 20.57%


hg bisect
=========

Create a shell script ``cmd.sh`` to check if a revision is good or not::

    set -e -x
    ./configure --with-lto -C && make clean && make
    rm -f json
    PYTHONPATH=~/perf ./python ~/performance/performance/benchmarks/bm_call_method.py --inherit-environ=PYTHONPATH --worker -o json -v
    PYTHONPATH=~/perf python3 cmd.py json

It uses this script Python script::

    import perf, sys
    bench = perf.Benchmark.load('json')
    bad = (29 + 17) / 2.0
    ms = bench.median() * 1e3
    if ms >= bad:
        print("BAD! %.1f ms >= %.1f ms" % (ms, bad))
        sys.exit(1)
    else:
        print("good: %.1f ms < %.1f ms" % (ms, bad))

I'm interested to find the first revision introducing the slowdown, so I start
from the oldest change which was fast 678fe178da0d as the first "good" revision
and use the peak (1ce50f7027c1) as the first "bad" revision::

Commands::

    hg bisect --reset
    hg bisect -g 678fe178da0d
    hg bisect -b 1ce50f7027c1
    time hg bisect -c ./cmd.sh

3 min 52 sec later::

    The first bad revision is:
    changeset:   104531:83877018ef97
    parent:      104528:ce85a1f129e3
    parent:      104530:2d352bf2b228
    user:        Serhiy Storchaka <storchaka@gmail.com>
    date:        Tue Oct 18 13:27:54 2016 +0300
    files:       Misc/NEWS
    description:
    Issue #23782: Fixed possible memory leak in _PyTraceback_Add() and exception
    loss in PyTraceBack_Here().


    Not all ancestors of this changeset have been checked.
    Use bisect --extend to continue the bisection from
    the common ancestor, d32ec6591c49.


What is the faulty revision?
============================

https://hg.python.org/cpython/rev/83877018ef97/

This revision changes two files: Misc/NEWS and Python/traceback.c. NEWS is part
of the documentation (text), whereas Python/traceback.c is part of the C code
and so is more interesting.

But the commit only changes two C functions: PyTraceBack_Here() and
_PyTraceback_Add() which are not "hot" functions.

In fact, the commit doesn't touch the C code used in the benchmark. It's
similar to my pevious "deadcode" horror story. The performance difference is
caused by code placement.


GCC __attribute__((hot))
========================

PGO was the solution for deadcode, but PGO doesn't work on Ubuntu 14.04 (OS
used by the benchmark server, speed-python) and PGO seems to make benchmarks
less reliable.

So I wanted to try to mark hot functions using the GCC __attribute__((hot)).

http://bugs.python.org/issue28618

This attribute only has an impact on the code placement: where functions are
loaded in memory. The flag declares functions in the ``.text.hot`` ELF section
rather than the ``.text`` ELF section.

