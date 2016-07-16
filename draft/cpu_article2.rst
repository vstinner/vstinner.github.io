Turbo Boost
===========

Test on my laptop: 2 physical cores, 2 logical cores (Hyper threading
disabled). Base reference: 2.9 GHz, Turbo Boost: 3.6 GHz with 1 active core,
3.4 GHz with 2 active cores.

Benchmark: pybench -b TryExcept.

1 active core
-------------

* CPU frequency: 3.6 GHz (arond 3580 MHz)
* pybench: Median +- std dev: 12.5 ns +- 0.1 ns

2 active cores
--------------

* CPU frequency: 3.4 GHz (exactly!)
* pybench: Median +- std dev: 12.9 ns +- 0.0 ns

Turbo Mode disabled
-------------------

Disable Turbo Boost in the intel_pstate driver::

    selma$ echo 1|sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

With the benchmark, the CPU frequency peak is 2.9 GHz, the base frequency. It's
no more 3.4 GHz or 3.6 GHz.

pybench: Median +- std dev: 15.1 ns +- 0.2 ns

Compare
-------

* Turbo Boost 1 active core (3.6 GHz) => Turbo Boost 2 active cores (3.4 GHz): 3% slower (12.5 ns => 12.9 ns)
* Turbo Boost 1 active core (3.6 GHz) => no Turbo Boost (2.9 GHz): 21% slower (12.5 ns => 15.1 ns)


Burn CPU to disable Turbo Mode: fail
====================================

Turbo Mode has a documented constrain: temperature. I ran

* a benchmark on 1 core
* system_load.py 20
* open 3 youtube videos with 1 in full screen

I closed the hole of the CPU fan on my laptop.

The CPU temperature reached 100°C. It was unable to get more than 100°C.

The CPU frequency was still 3.4 GHz even with the temperature of 100°C!

Maybe my i7-3520M CPU (Ivy Bridge) doesn't have the temperature constrain?


powertop
========

powertop has a very bad effect on the stability of benchmarks. It looks like
the CPU frequency changes a lot when powertop is running.

* Maximum: 3.6 GHz (Turbo Boost, 1 active core), benchmark: 1.72 us
* Minimum: 1.2 GHz, benchmark: 5.11 us (3x slower!)


MISC: CPU tools
===============

Get info, monitor:

* powertop

Configure:

* chcpu
* taskset

Linux:

* /proc/cpuinfo
* /sys/devices/cpu/
* /sys/devices/system/cpu/



