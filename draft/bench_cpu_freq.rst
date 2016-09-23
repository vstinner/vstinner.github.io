+++++++++++++++++++++++
Impact of CPU frequency
+++++++++++++++++++++++

Desktop.

- cpu_model_name: Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
- perf_version: 0.7.12
- python_version: 3.5.1 (64-bit)
- cpu_config: 3=driver:intel_pstate, intel_pstate:no turbo, governor:performance, nohz_full, isolated
- cpu_count: 8  # 8 logical, 4 physical

Start
=====

- cpu_freq: 3=3400 MHz

Median +- std dev: 12.9 ms +- 0.2 ms


Min frequency
=============

Force frequency to min frequency, 1.6 GHz::

    $ cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq|sudo tee  /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
    1600000

1.6 GHz

Median +- std dev: 27.7 ms +- 0.7 ms


Max frequency
=============

::

    $ cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq|sudo tee  /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
    3400000

3.4 GHz.

Median +- std dev: 12.9 ms +- 0.2 ms


Impact of CPU frequency
=======================

* 1.6 GHz instead of 3.4 GHz: 53% slower (27.7 ms => 12.9 ms)

