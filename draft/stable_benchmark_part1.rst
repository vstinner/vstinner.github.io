++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part 1
++++++++++++++++++++++++++++++++++++++

:date: 2016-05-21 16:50
:tags: optimization, benchmark
:category: python
:slug: journey-to-stable-benchmark-part1
:authors: Victor Stinner
:summary: My journey to stable benchmark, part 1

Background
==========

I like working on optimizations because the goal is well defined: Python must
be faster with the change. Micro-optimizations are even simpler: take a very
specific Python function and hack to make it faster without having to care
of the rest of Python.

I spent a lot of time to optimize each method of the Python 3 Unicode type,
``str``. See for example my :ref:`Fast _PyAccu, _PyUnicodeWriter
and_PyBytesWriter APIs to produce strings in CPython <pybyteswriter>` article.

More recently, on micro-optimizations very specific to some instructions like
int + int, I ran the CPython benchmark suite and I had many bad surprises when
analyzing results. Basically, the results don't make sense at all. In short, I
will say many benchmarks look completly unstable, not reliable. Some developers
started to say that since the benchmarks are unable, they don't trust these
benchmarks and chose to ignore them.

In the past, I also got results which didn't make sense when working on some
micro-optimizations. A change which should obviously make the code faster or a
change that has obvious no effect on the performance makes in fact Python
slower. Not much, betwen 5% and 10% slower on a microbenchmark. But I was very
disappointed to get a counter-intuitive result.

Ok, enough talking, let's see how to make microbenchmarks faster.


How to get stable benchmarks on a busy Linux system
===================================================

Goal
----

A common advice to get stable benchmark is to don't stay away the keyboard
and stop all other applications to only run one application, the benchmark.

Well well well. I'm working on a single computer and some benchmarks take
up to 2 hours. I just cannot stop working during 2 hours to wait for the
result of the benchmark.

The goal here is to remove the noise of the system: get the same result on an
idle or a busy system. Try my simple `system_load.py
<https://bitbucket.org/haypo/misc/src/tip/bin/system_load.py>`_ program. For
example, run with ``system_load.py 5`` in one terminal to get at least a system
load of 5 (busy system) and run the benchmark in a different terminal. Use
CTRL+c to stop ``system_load.py``.


CPU isolation
-------------

In 2016, it became common to get a CPU with multiple physical cores. For
example, my CPU has 4 physical cores and 8 logical cores thanks to
HyperThreading. You can use the CPU isolation feature of Linux to ask the
kernel to not schedule processes on isolated CPUs. You can also tune Linux to
not run IRQ handlers on isolate CPUs to isolate them even more.

If you have HyperThreading, you must isolate CPU cores by pair. You can use the
``lscpu --all --extended`` command to identify physical cores::

    $ lscpu -a -e
    CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE MAXMHZ    MINMHZ
    0   0    0      0    0:0:0:0       yes    5900,0000 1600,0000
    1   0    0      1    1:1:1:0       yes    5900,0000 1600,0000
    2   0    0      2    2:2:2:0       yes    5900,0000 1600,0000
    3   0    0      3    3:3:3:0       yes    5900,0000 1600,0000
    4   0    0      0    0:0:0:0       yes    5900,0000 1600,0000
    5   0    0      1    1:1:1:0       yes    5900,0000 1600,0000
    6   0    0      2    2:2:2:0       yes    5900,0000 1600,0000
    7   0    0      3    3:3:3:0       yes    5900,0000 1600,0000

I don't have NUMA system: all cores are attached to the NUMA node ``0``. I have
4 physical cores, each has two logical cores. For example, the logical cores
``0`` and ``4`` are on the same physical core ``0``.

NOHZ mode
---------

By default, the Linux kernel interrupts the application running on a CPU HZ
times perf seconds. HZ is usually between 100 (10 ms) and 1000 (1 ms).

The Linux realtime project added a ``NOHZ`` mode which allows to avoid these
interruptions when only one application runs on a CPU. The Linux kernel command
line ``nohz_full`` enables fully this feature on the specified cores.

Example of parameter to enable it on 4 cores::

    nohz_full=2,3,6,7


Other interruptions
-------------------

If you read articles from the Linux realtime project, you will learn that it's
not perfect. There are still exceptional events like System Maintenance
Interrupts (SMI), but these interruptions only take a few milliseconds and are
somehow ignored if you run the benchmark multiple times (use an inner-loop of
multiple iterations). There are also Non-maskable interrupts (NMI), but I don't
know anything about them :-)

On the Internet, I found the following kernel parameters, but I didn't test
them::

    nmi_watchdog=0 nowatchdog nosoftlockup


Example of effect of CPU isolation on a microbenchmark
======================================================

Microbenchmark on an idle system::

    $ python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 229 msec per loop

New try on a busy system using ``system_load.py 10`` command in a terminal and
``find /`` command in a different terminal::

    $ python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 372 msec per loop

Now, let's try our isolated cores on the busy system::

    $ taskset -c 1,3 python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 230 msec per loop

Just to check, new run without CPU isolation::

    $ python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 357 msec per loop

As you can see, on a busy system, the result with CPU isolation is the same as
an idle system, whereas the benchmark looks 56% slower without CPU isolation!

Great job Linux!

The effect is quite obvious. Ok! Now, our benchmark are very stable, no? no?
No, they are not, I found a lot of other sources of "noise". We will see more
in the following article ;-)

