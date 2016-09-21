TODO
====

* Explain direct link between CPU frequency and performance: set manually the
  CPU frequency

Burning the CPU
===============

When the CPU fan is blocked by a sheet of paper, the CPU temperate goes up to
97°C. But the CPU doesn't burn, its frequency decreases from 3.4 GHz (max when
Turbo Boost is disabled) to 1.6 GHz (minimum).


Snapshot::

    $ sensors
    coretemp-isa-0000
    Adapter: ISA adapter
    Physical id 0:  +97.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 0:         +97.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 1:         +97.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 2:         +96.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 3:         +97.0°C  (high = +80.0°C, crit = +98.0°C)

    $ sudo turbostat sleep 3
    3.001563 sec
         CPU Avg_MHz   Busy% Bzy_MHz TSC_MHz
           -    1343   87.56    1527    3414
           0    1534   99.96    1527    3417
           4    1534   99.96    1527    3417
           1    1534   99.96    1527    3416
           5    1533   99.96    1527    3415
           2    1533   99.96    1527    3413
           6    1532   99.96    1527    3412
           3    1532   99.96    1527    3411
           7      10    0.67    1536    3411


CPU fan not blocked
===================

System heavily loaded (system load higher than 10), all CPU run at 3.4 GHz, the
CPU temperature is 66°C.

Snapshot::

    $ sensors
    coretemp-isa-0000
    Adapter: ISA adapter
    Physical id 0:  +66.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 0:         +62.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 1:         +66.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 2:         +62.0°C  (high = +80.0°C, crit = +98.0°C)
    Core 3:         +63.0°C  (high = +80.0°C, crit = +98.0°C)

    $ sudo turbostat sleep 3
    3.000748 sec
         CPU Avg_MHz   Busy% Bzy_MHz TSC_MHz
           -    2988   87.51    3400    3414
           0    3417  100.00    3400    3417
           4    3417  100.00    3400    3417
           1    3416  100.00    3400    3416
           5    3415  100.00    3400    3415
           2    3413  100.00    3400    3413
           6    3412  100.00    3400    3412
           3    3411  100.00    3400    3411
           7       1    0.02    3400    3411

Laptop
======

Using a tissue, I closed the hole used by the CPU fan. The CPU temperature
increased up to 102°C, but the CPU frequency was only decreased from 3.4 GHz
(Turbo Mode with 4 active logical CPUs) to 3.1 GHz.

When the CPU temperature ("Physical id 0" sensor) switched from 100°C to 101°C,
the CPU frequency started slowly to decrease from 3391 MHz to 3077 MHz with
steps of 10 MHz

Beginning of the test::

    $ sensors
    coretemp-isa-0000
    Adapter: ISA adapter
    Physical id 0:  +83.0°C  (high = +87.0°C, crit = +105.0°C)
    Core 0:         +78.0°C  (high = +87.0°C, crit = +105.0°C)
    Core 1:         +83.0°C  (high = +87.0°C, crit = +105.0°C)

    $ sudo turbostat sleep 3
    3.001621 sec
         CPU Avg_MHz   Busy% Bzy_MHz TSC_MHz
           -    3393  100.00    3400    2894
           0    3394  100.00    3400    2895
           1    3394  100.00    3400    2895
           2    3393  100.00    3400    2894
           3    3392  100.00    3400    2893

Hotest::

    $ sensors
    coretemp-isa-0000
    Adapter: ISA adapter
    Physical id 0: +102.0°C  (high = +87.0°C, crit = +105.0°C)
    Core 0:         +97.0°C  (high = +87.0°C, crit = +105.0°C)
    Core 1:        +102.0°C  (high = +87.0°C, crit = +105.0°C)

    $ sudo turbostat sleep 3
    3.002816 sec
         CPU Avg_MHz   Busy% Bzy_MHz TSC_MHz
           -    3160   99.92    3169    2894
           0    3160   99.92    3169    2894
           1    3160   99.92    3169    2894
           2    3160   99.92    3169    2894
           3    3159   99.92    3169    2893

