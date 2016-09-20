Laptop.

Benchmark
=========

* CPU: Intel(R) Core(TM) i7-3520M CPU @ 2.90GHz
* perf version 0.7.11
* Linux kernel 4.6.3
* Benchmark: bm_call_simple.py of performance 0.2.2

::

    $ sudo cpupower frequency-info
      ...
      boost state support:
        Supported: yes
        Active: yes
        3400 MHz max turbo 4 active cores
        3400 MHz max turbo 3 active cores
        3400 MHz max turbo 2 active cores
        3600 MHz max turbo 1 active cores


Turbo Boost Disabled
====================

* 1 physical CPU active: 2.9 GHz, Median +- std dev: 14.6 ms +- 0.3 ms
* 2 physical CPU active: 2.9 GHz, Median +- std dev: 14.7 ms +- 0.5 ms


Turbo Boost Enabled
===================

2 physical CPU active: 3.4 GHz, Median +- std dev: 12.4 ms +- 0.1 ms
1 physical CPU active: 3.6 GHz, Median +- std dev: 11.8 ms +- 0.3 ms

Impact on benchmark
===================

Turbo Boost:

* min boost (2 physical CPU active): 15% faster
* max boost (1 physical CPU active): 19% faster

