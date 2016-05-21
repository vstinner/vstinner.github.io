+++++++++++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part 1 (system)
+++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-05-21 16:50
:tags: optimization, benchmark
:category: python
:slug: journey-to-stable-benchmark-part1
:authors: Victor Stinner
:summary: My journey to stable benchmark, part 1

Background
==========

In the CPython development, it became common to require the result of the
`CPython benchmark suite <https://hg.python.org/benchmarks>`_ ("The Grand
Unified Python Benchmark Suite") to evaluate the effect of an optimization
patch. The minimum requirement is to not introduce performance regressions.

I used the CPython benchmark suite and I had many bad surprises when trying to
analyze (understand) results. A change expected to be faster makes some
benchmarks slower without any obvious reason. At least, the change is expected
to be faster on some specific benchmarks, but have no impact on the other
benchmarks. The slow down is usually between 5% and 10% slower. I am not
confortable with any kind of slow down.

Many benchmarks look unstable. The problem is to trust the overall report.
Some developers started to say that they learnt to ignore some benchmarks known
to be unstable.

It's not the first time that I am totally disappointed by microbenchmark
results, so I decided to analyze completely the issue and go as deep as
possible to really understand the problem.


How to get stable benchmarks on a busy Linux system
===================================================

A common advice to get stable benchmark is to stay away the keyboard
("freeze!") and stop all other applications to only run one application, the
benchmark.

Well, I'm working on a single computer and the full CPython benchmark suite
take up to 2 hours in rigorous mode. I just cannot stop working during 2 hours
to wait for the result of the benchmark. I like running benchmarks locally. It
is convenient to run benchmarks on the same computer used to develop.

The goal here is to "remove the noise of the system". Get the same result on a
busy system than an idle system. My simple `system_load.py
<https://bitbucket.org/haypo/misc/src/tip/bin/system_load.py>`_ program can be
used to increase the system load. For example, run ``system_load.py 10`` in a
terminal to get at least a system load of 10 (busy system) and run the
benchmark in a different terminal. Use CTRL+c to stop ``system_load.py``.


CPU isolation
=============

In 2016, it is common to get a CPU with multiple physical cores. For example,
my Intel CPU has 4 physical cores and 8 logical cores thanks to
`Hyper-Threading <https://en.wikipedia.org/wiki/Hyper-threading>`_. It is
possible to configure the Linux kernel to not schedule processes on some CPUs
using the "CPU isolation" feature. It is the ``isolcpus`` parameter of the
Linux command line, the value is a list of CPUs. Example::

    isolcpus=2,3,6,7

Check with::

    $ cat /sys/devices/system/cpu/isolated
    2-3,6-7

If you have Hyper-Threading, you must isolate the two logicial cores of each
isolated physical core. You can use the ``lscpu --all --extended`` command to
identify physical cores. Example::

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

The physical core ``0`` (CORE column) is made of two logical cores (CPU
column): ``0`` and ``4``.


NOHZ mode
=========

By default, the Linux kernel uses a scheduling-clock which interrupts the
running application ``HZ`` times per second to run the scheduler. ``HZ`` is
usually between 100 and 1000: time slice between 1 ms and 10 ms.

Linux supports a `NOHZ mode
<https://www.kernel.org/doc/Documentation/timers/NO_HZ.txt>`_ which is able to
disable the scheduling-clock when the system is idle to reduce the power
consumption. Linux 3.10 introduces a `full ticketless mode
<https://lwn.net/Articles/549580/>`_, NOHZ full, which is able to disable the
scheduling-clock when only one application is running on a CPU.

NOHZ full is disabled by default. It can be enabled with the ``nohz_full``
parameter of the Linux command line, the value is a list of CPUs. Example::

    nohz_full=2,3,6,7

Check with::

    $ cat /sys/devices/system/cpu/nohz_full
    2-3,6-7


Interrupts (IRQ)
================

The Linux kernel can also be configured to not run `interruptions (IRQ)
<https://en.wikipedia.org/wiki/Interrupt_request_%28PC_architecture%29>`_
handlers on some CPUs using ``/proc/irq/default_smp_affinity`` and
``/proc/irq/<number>/smp_affinity`` files. The value is not a list of CPUs but
a bitmask.

The ``/proc/interrupts`` file can be read to see the number of interruptions
per CPU.

Read the `Linux SMP IRQ affinity
<https://www.kernel.org/doc/Documentation/IRQ-affinity.txt>`_ documentation.


Example of effect of CPU isolation on a microbenchmark
======================================================

Example with Linux parameters::

    isolcpus=2,3,6,7 nohz_full=2,3,6,7

Microbenchmark on an idle system (without CPU isolation)::

    $ python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 229 msec per loop

Result on a busy system using ``system_load.py 10`` and ``find /`` commands
running in other terminals::

    $ python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 372 msec per loop

The microbenchmark is 56% slower because of the high system load!

Result on the same busy system but using isolated CPUs. The ``taskset`` command
allows to pin an application to specific CPUs::

    $ taskset -c 1,3 python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 230 msec per loop

Just to check, new run without CPU isolation::

    $ python3 -m timeit 'sum(range(10**7))'
    10 loops, best of 3: 357 msec per loop

The result with CPU isolation on a busy system is the same than the result an
idle system! CPU isolation removes most of the noise of the system.


Conclusion
==========

Great job Linux!

Ok! Now, the benchmar is super stable, no? ...  Sorry, no, it's not stable yet.
I found a lot of other sources of "noise".  We will see them in the following
article ;-)
