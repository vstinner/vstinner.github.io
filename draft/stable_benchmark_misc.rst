+++++++++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part 4 (misc)
+++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-05-31 17:00
:tags: optimization, benchmark
:category: python
:slug: journey-to-stable-benchmark-misc
:authors: Victor Stinner
:summary: My journey to stable benchmark, part 4 (misc)

A bit of history, CPU power consumption
=======================================

In 2016, Intel CPU vendor stopped to only be focused on pure performances. The
market of desktop PCs is decreasing, today computers are small and have no more
power cable, but a battery. If we exagerate, the power consumption matters more
than performance. It would be hard to sell a smartphone which requires to be
plugged to a power cable more frequently than every nights: one day is still
strict minimum for the autonomy.

ARM CPUs are commonly used in smartphones, tablets and other kinds of
"embedded" devices. Intel developped technologies to reduce the power
consumption to not loose markets, starting with laptops. It started with
`SpeedStep <https://en.wikipedia.org/wiki/SpeedStep>`_ in 2005. Later Intel
introduced `Turbo Boost <https://en.wikipedia.org/wiki/Intel_Turbo_Boost>`_ in
2008. With the latest generation, Skylake now runs the power
management directly in the CPU.

The `Thermal design power (TDP)
<https://en.wikipedia.org/wiki/Thermal_design_power`_ matters!


Impact of power consumption on benchmarks
=========================================

In short, the speed of today Intel CPUs is no more constant. It changes a lot.
It can change multiple times per minute depend many factors.

The Turbo Mode makes the CPU faster if the CPU temperature is lower than
a threshold. The Turbo Mode can be detected with a different CPU speed, the
difference can be a single MHz.

The result of a benchmark with and without Turbo Mode is huge.

Linux uses a power manager to change dynamically the speed of the CPU. The
default governor is usually "powersave"::

    $ cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
    powersave

See the driver::

    $ cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver
    intel_pstate

Other driver: acpi_xxx.

Available governors::

    $ cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors
    performance powersave

Changing the CPU speed takes a few milliseconds. The performance governor
tries to limit the number of speed changes, whereas the powersave governor
tries to reduce the power consumption and so tries to use the lowest
CPU speed, without killing performances.


CPU Turbo Boost
===============

If your system is using the intel_pstate frequency scaling driver::

    $ cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_driver
    intel_pstate
    ...
    intel_pstate

Then you can inquire as to the turbo enabled or disabled status::

    $ cat /sys/devices/system/cpu/intel_pstate/no_turbo
    0

Check if Turbo Boost is enabled::

    sudo rdmsr -f 38:38 0x1a0

* ``1`` means disabled (no turbo)
* ``0`` means enabled

Use the ``wrmsr`` to set the Turbo Boost, or go into your BIOS/EFI.

Fedora: ``dnf install -u msr-tools``.



Linux
=====

* Linux documentation

  * `Linux CPUFreq: CPUFreq Governors
    <https://www.kernel.org/doc/Documentation/cpu-freq/governors.txt>`_
  * `Linux CPUFreq User Guide
    <https://www.kernel.org/doc/Documentation/cpu-freq/user-guide.txt>`_



Intel power states
==================

`Power Management States: P-States, C-States, and Package C-States
<https://software.intel.com/en-us/articles/power-management-states-p-states-c-states-and-package-c-states>`_.

C0...C6 states:

* C0: CPU fully turned on
* C6: Deep Power Down

* `Everything You Need to Know About the CPU C-States Power Saving Modes
  <http://www.hardwaresecrets.com/everything-you-need-to-know-about-the-cpu-c-states-power-saving-modes/>`_


HyperThreading
==============

xxx


===

* https://lwn.net/Articles/534735/ Rethinking optimization for size
