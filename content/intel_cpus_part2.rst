++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Intel CPUs (part 2): Turbo Boost, temperature, frequency and Pstate C0 bug
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-09-23 23:00
:tags: optimization, benchmark, cpu
:category: benchmark
:slug: intel-cpus-part2
:authors: Victor Stinner
:summary: Intel CPUs (part 2): Turbo Boost, temperature, frequency and Pstate C0 bug

My first article `Intel CPUs <{filename}/intel_cpus.rst>`_ is a general
introduction on modern CPU technologies having an impact on benchmarks.

This second article is much more concrete with numbers and a concrete bug
having a major impact on benchmarks: a benchmark suddenly becomes 2x faster!

I will tell you how I first noticed the bug, which tests I ran to analyze the
issue, how I found commands to reproduce the bug, and finally how I identified
the bug.


"Glitch" in benchmarks
======================

Last week I ran a benchmark to check if enabling Profile Guided Optimization
(PGO) when compiling Python makes benchmark results less stable. I recompiled
Python 5 times, and after each compilation I ran a benchmark. I tested
different commands and options to compile Python. Everything was fine until
the last benchmark of the last compilation. **The benchmark suddenly became 2
times faster.**

Hopefully, my perf module collects a lot of metadata. I was able to analyze
in depth what happened.

The "glitch" occurred in a benchmark having 400 runs (benchmark run in 400
different processes), between the run 105 (20.3 ms) and the run 106
(11.0 ms).

I noticed that the CPU temperature was between 69°C and 72°C until the run 105,
and then decreased to from 69°C to 58°C.

The system load slowly increased from 1.25 up to 1.62 around the run 108 and
then slowly decreased to 1.00.

The system was not idle while the benchmark was running. I was working on the
PC too! But according to timestamps, it seems like the glitch was close to when
I stopped working. When I stopped working, I closed all applications (except of
the benchmark running in background) and turned of my two monitors.

Well, at this point, it's hard to correlate for sure an event with the major
performance change.

So I started to analyze different factors affecting CPUs and benchmarks: Turbo
Boost, CPU temperature and CPU frequency.


Impact of Turbo Boost on benchmarks
===================================

Without Turbo Boost, the maximum frequency of the "Intel(R) Core(TM) i7-3520M
CPU @ 2.90GHz" of my laptop is 2.9 GHz. With Turbo Boost, the maximum
frequency is 3.6 GHz if only one core is active, or 3.4 GHz otherwise::

    $ sudo cpupower frequency-info
      ...
      boost state support:
        Supported: yes
        Active: yes
        3400 MHz max turbo 4 active cores
        3400 MHz max turbo 3 active cores
        3400 MHz max turbo 2 active cores
        3600 MHz max turbo 1 active cores

I ran the bm_call_simple.py microbenchmark (CPU-bound) of performance 0.2.2.

Turbo Boost disabled:

* 1 physical CPU active: 2.9 GHz, Median +- std dev: 14.6 ms +- 0.3 ms
* 2 physical CPU active: 2.9 GHz, Median +- std dev: 14.7 ms +- 0.5 ms

Turbo Boost enabled:

* 1 physical CPU active: 3.6 GHz, Median +- std dev: 11.8 ms +- 0.3 ms
* 2 physical CPU active: 3.4 GHz, Median +- std dev: 12.4 ms +- 0.1 ms

**The maximum performance boost is 19% faster** (14.6 ms => 11.8 ms), the
minimum boost if 15% faster (14.6 ms => 12.4 ms).

Hum, I don't think that Turbo Boost can explain the bug.


Impact of the CPU temperature on benchmarks
===========================================

The CPU temperature is mentionned in Intel Turbo Boost documentation as a
factor used to decide which P-state will be used. I always wanted to check how
the CPU temperature impacts its performance.

Burn the CPU of my desktop PC
-----------------------------

CPU of my desktop PC: "Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz".

I used my `system_load.py script
<https://github.com/vstinner/misc/blob/master/bin/system_load.py>`_ to generate a
system load higher than 10.

When the fan is cooling correctly the CPU, all CPU run at 3.4 GHz (Turbo Boost
was disabled) and the CPU temperature is 66°C.

I used a simple sheet of paper to block the fan of my CPU. Yeah, I really
wanted to `burn my CPU <https://www.youtube.com/watch?v=Xf0VuRG7MN4>`_! More
seriously, I checked the CPU temperature every second using the ``sensors``
command and was prepared to unblock the fan if sometimes gone wrong.

.. image:: {static}/images/paper_blocks_cpu_fan.jpg
   :alt: Sheet of paper blocking the CPU fan

After one minute, the CPU reached 97°C. I expected a system crash, smoke or
something worse, but I was disappointed. **At 97°C, I was still able to use my
computer as everything was fine. The CPU was slowly down automatically to the
minimum CPU frequency: 1533 MHz** according to turbostat (the minimum frequency
of this CPU is 1.6 GHz).

When I unblocked the fan, the temperature decreased quickly to go back to its
previous state (62°C) and the CPU frequency quickly increased to 3.4 GHz as
well.

My Intel CPU is really impressive! I didn't expect such very efficient
protection against overheating!


Burn my laptop CPU
------------------

I used my system_load.py script to get a system load over 200. I also opened 4
tabs in Firefox playing Youtube videos to stress also the GPU which is
integrated into the CPU (IGP) on such laptop.

.. image:: {static}/images/burn_cpu_firefox.jpg
   :alt: Stress test playing Youtube videos in Firefox, CPU at 102°

With such crazy stress test, the CPU temperature was "only" 83°C.

Using a simple tissue, I closed the air hole used by the CPU fan. **When the
CPU temperature increased from 100°C to 101°C, the CPU frequency started slowly
to decrease from 3391 MHz to 3077 MHz** (with steps between 10 MHz and 50 MHz
every second, or something like that).

When pushing hard the tissue and waiting longer than 5 minutes, the CPU
temperature increased up to 102°C, but the CPU frequency was only decreased
from 3.4 GHz (Turbo Mode with 4 active logical CPUs) to 3.1 GHz.

The maximum frequency is 2.9 GHz. Frequencies higher than 2.9 GHz means that
the Turbo Mode was enabled! It means that **even with overheating, the CPU is
still fine and able to "overclock" itself!**

Again, I was disapointed. With a CPU at 102°C, my laptop was still super fast
and reactive.  It seems like mobile CPUs handle even better overheating than
desktop CPUs (which is not something suprising at all).


Impact of the CPU frequency on benchmarks
=========================================

I ran the bm_call_simple.py microbenchmark (CPU-bound) of performance 0.2.2
on my desktop PC.

Command to set the frequency of CPU 0 to the minimum frequency (1.6 GHz)::

    $ cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq|sudo tee  /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
    1600000

Command to set the frequency of CPU 0 to the maximum frequency (3.4 GHz)::

    $ cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq|sudo tee  /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
    3400000

* CPU running at 1.6 GHz (min freq): Median +- std dev: 27.7 ms +- 0.7 ms
* CPU running at 3.4 GHz (min freq): Median +- std dev: 12.9 ms +- 0.2 ms

The impact of the CPU frequency is quite obvious: **when the CPU frequency is
doubled, the performance is also doubled**. The benchmark is 53% faster (27.7
ms => 12.9 ms).


Bug reproduced and then identified in the Linux CPU driver
==========================================================

Two days ago, I ran a very simple "timeit" microbenchmark to try to bisect a
performance regression in Python 3.6 on ``functools.partial``. Again, suddenly,
the microbenchmark became 2x faster!

But this time, I found something: I noticed that running or stopping ``cpupower
monitor`` and/or ``turbostat`` can "enable" or "disable" the bug.

After a lot of tests, I understood that running the benchmark with turbostat
"disables" the bug, whereas running "cpupower monitor" while running a
benchmark enables the bug.

I reported the bug in the Fedora bug tracker, on the component kernel:
`intel_pstate C0 bug on isolated CPUs with the performance governor and
NOHZ_FULL <https://bugzilla.redhat.com/show_bug.cgi?id=1378529>`_.

It seems like the bug is related to CPU isolation and NOHZ_FULL. The NOHZ_FULL
option is able to fully disable the scheduler clock interruption  on isolated
CPUs. I understood the the ``intel_pstate`` driver uses a callback on the
scheduler to update the Pstate of the CPU. According to an Intel engineer, the
``intel_pstate`` driver was never tested with CPU isolation.

The issue is not fully analyzed yet, but at least I succeeded to write a list
of commands to reproduce it with a success rate of 100% :-) Moreover, the Intel
engineer suggested to add an extra parameter to the Linux kernel command
(``rcu_nocbs=3,7``) line which works around the issue.


Conclusion
==========

This article describes how I found and then identified a bug in the Linux
driver of my CPU.

Summary:

* The maximum speedup of Turbo Boost is 20%
* Overheating on a dekstop PC can decrease the CPU frequency to its minimum
  (half of the maximum in my case) which imply a slowdown of 50%
* A bug in the Linux CPU driver changes suddenly the CPU frequency from its
  minimum to maximum (or the opposite) which means a speedup of 50%
  (or slowdown of 50%)

**To get stable benchmarks, the safest fix for all these issues is probably to
set the CPU frequency of the CPUs used by benchmarks to the minimum.**
It seems like nothing can reduce the frequency of a CPU below its minimum.

**When running benchmarks, raw timings and CPU performance don't matter. Only
comparisons between benchmark results and stable performances matter.**
