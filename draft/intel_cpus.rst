++++++++++
Intel CPUs
++++++++++

:date: 2016-07-15 12:00
:tags: optimization, benchmark
:category: benchmark
:slug: intel-cpus
:authors: Victor Stinner
:summary: Intel CPUs

Ten years ago, most computers were desktop computers and their CPU frequency
was fixed. Nowadays, most devices are embedded and use `low power consumption
<https://en.wikipedia.org/wiki/Low-power_electronics>`_ processors like ARM
CPUs. The `Thermal design power (TDP)
<https://en.wikipedia.org/wiki/Thermal_design_power>`_ now matters more than
raw performances.

Intel CPUs evolved from a single core to multiple physical cores in the same
`package <https://en.wikipedia.org/wiki/CPU_socket>`_ and got new features:
`Hyper-threading <https://en.wikipedia.org/wiki/Hyper-threading>`_ to run two
threads on the same physical core and `Turbo Boost
<https://en.wikipedia.org/wiki/Intel_Turbo_Boost>`_ to maximum performances.
CPU cores can be completely turned off (CPU HALT, frequency of 0) temporary to
reduce the power consumption, and the frequency of cores changes regulary
depending on many factors like the workload and temperature.


Installation on Fedora 24
=========================

``dnf install -y util-linux``:

* lscpu

``dnf install -y kernel-tools``:

* cpupower
* turbostat

``sudo dnf install -y msr-tools``:

* rdmsr
* wrmsr

Other tools, not tested in this article: i7z (no more
maintained), lshw, dmidecode.


Example of Intel CPUs
=====================

My laptop CPU: /proc/cpuinfo
----------------------------

On Linux, the most common way to retrieve information on the CPU is to read
``/proc/cpuinfo``. Example on my laptop::

    selma$ cat /proc/cpuinfo
    processor  : 0
    vendor_id  : GenuineIntel
    model name : Intel(R) Core(TM) i7-3520M CPU @ 2.90GHz
    cpu MHz    : 1200.214
    ...

    processor  : 1
    vendor_id  : GenuineIntel
    model name : Intel(R) Core(TM) i7-3520M CPU @ 2.90GHz
    cpu MHz    : 3299.882
    ...

"i7-3520M" CPU is a model designed for Mobile Platforms (see the "M" suffix).
It was built in 2012 and is the third generation of the Intel i7
microarchitecture: `Ivy Bridge
<https://en.wikipedia.org/wiki/Ivy_Bridge_(microarchitecture)>`_.

The CPU has two physical cores, I disabled HyperThreading in the BIOS.

The first strange thing is that the CPU announces "2.90 GHz" but Linux reports
1.2 GHz on the first core, and 3.3 GHz on the second core. 3.3 GHz is greater
than 2.9 GHz!

My desktop CPU: lscpu
---------------------

According to ``/proc/cpuinfo``, the CPU model is "Intel(R) Core(TM) i7-2600 CPU
@ 3.40GHz" and there are 8 logical cores, but only 4 physical cores::

    smithers$ cat /proc/cpuinfo
    processor   : 0
    physical id : 0
    core id     : 0
    ...
    model name  : Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
    cpu cores   : 4
    ...

    processor   : 1
    physical id : 0
    core id     : 1
    ...

    (...)

    processor   : 7
    physical id : 0
    core id     : 3
    ...

The ``lscpu`` renders a short table which helps to understand the CPU topology::

    smithers$ lscpu -a -e
    CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE MAXMHZ    MINMHZ
    0   0    0      0    0:0:0:0       yes    3800.0000 1600.0000
    1   0    0      1    1:1:1:0       yes    3800.0000 1600.0000
    2   0    0      2    2:2:2:0       yes    3800.0000 1600.0000
    3   0    0      3    3:3:3:0       yes    3800.0000 1600.0000
    4   0    0      0    0:0:0:0       yes    3800.0000 1600.0000
    5   0    0      1    1:1:1:0       yes    3800.0000 1600.0000
    6   0    0      2    2:2:2:0       yes    3800.0000 1600.0000
    7   0    0      3    3:3:3:0       yes    3800.0000 1600.0000

There are 8 logical CPUs (``CPU 0..7``), all on the same node (``NODE 0``) and
the same socket (``SOCKET 0``).  There are only 4 physical cores (``CORE
0..3``). For example, the physical core ``2`` is made of the two logical CPUs:
``2`` and ``6``.

Using the ``L1d:L1i:L2:L3`` column, we can see that each pair of two logical
cores share the same physical core caches for levels 1 (L1 data, L1
instruction) and 2 (L2).  All physical cores share the same L3 cache.


P-states
========

A new CPU driver ``intel_pstate`` was added to the Linux kernel 3.9. First, it
only supported SandyBridge CPUs, Linux 3.10 extended it to Ivybridge generation
CPUs, etc. It is possible to force the legacy CPU driver (``acpi_cpufreq``)
using ``intel_pstate=disable`` option in the kernel command line.

This driver supports recent features and thermal control of modern Intel CPUs.
Its name comes from P-states:

    "The processor P-state is the capability of running the processor at
    different voltage and/or frequency levels. Generally, P0 is the highest
    state resulting in maximum performance, while P1, P2, and so on, will save
    power but at some penalty to CPU performance."

For more information on P-states, read:

* `Arjan van de Ven's article
  <https://plus.google.com/+ArjanvandeVen/posts/dLn9T4ehywL>`_ on Google+
* `Balancing Power and Performance in the Linux Kernel
  <https://events.linuxfoundation.org/sites/events/files/slides/LinuxConEurope_2015.pdf>`_
  talk at LinuxCon Europe 2015 by Kristen Accardi (Intel).
* `What exactly is a P-state? (Pt. 1)
  <https://software.intel.com/en-us/blogs/2008/05/29/what-exactly-is-a-p-state-pt-1>`_
  (2008) by Taylor K. (Intel)


Idle states: C-states
=====================

Quick summary:

    "C-states are idle power saving states, in contrast to P-states, which are
    execution power saving states."

    "During a P-state, the processor is still executing instructions, whereas
    during a C-state (other than C0), the processor is idle, meaning that
    nothing is executing."

For more information, see `Power Management States: P-States, C-States, and
Package C-States
<https://software.intel.com/en-us/articles/power-management-states-p-states-c-states-and-package-c-states>`_.

C-states:

* C0 is the operational state, meaning that the CPU is doing useful work
* C1 is the first idle state
* C2 is the second idle state: The external I/O Controller Hub blocks
  interrupts to the processor.
* etc.

The ``cpupower idle-info`` command lists C-state supported by your Intel CPU::

    selma$ cpupower idle-info
    CPUidle driver: intel_idle
    CPUidle governor: menu
    analyzing CPU 0:

    Number of idle states: 6
    Available idle states: POLL C1-IVB C1E-IVB C3-IVB C6-IVB C7-IVB
    ...

When a logical processor is idle (C state except of C0), its frequency is
typically 0 (HALT).


Coprocessor
===========

Computers with Intel vPro technology includes `Intel Active Management
Technology (AMT)
<https://en.wikipedia.org/wiki/Intel_Active_Management_Technology>`_: "hardware
and firmware technology for remote out-of-band management of personal
computers". Hardware part: `Management Engine (ME)
<https://en.wikipedia.org/wiki/Intel_Active_Management_Technology#Hardware>`_:
an isolated and protected coprocessor, embedded as a non-optional part in all
current (as of 2015) Intel chipsets. The coprocessor is a special 32-bit ARC
microprocessor (RISC architecture) that's physically located inside the PCH
chipset (or MCH on older chipsets). The coprocessor can for example be found on
Intel MCH Chipsets Q35 and Q45.

AMT also handles power management.

See `Intel x86s hide another CPU that can take over your machine (you can't audit it)
<https://boingboing.net/2016/06/15/intel-x86-processors-ship-with.html>`_.

More recently, the Intel Xeon Phi CPU (released in 2016) includes a coprocessor
for power management.


Turbo Boost
===========

Turbo Boost allows to run one or many CPU cores to higher P-states than usual.
The maximum P-state depends on the workload, the temperature of CPUs, the
number of active cores, etc. Example on my laptop::

    selma$ cat /proc/cpuinfo
    model name : Intel(R) Core(TM) i7-3520M CPU @ 2.90GHz
    ...

    selma$ sudo cpupower frequency-info
    analyzing CPU 0:
      driver: intel_pstate
      ...
      boost state support:
        Supported: yes
        Active: yes
        3400 MHz max turbo 4 active cores
        3400 MHz max turbo 3 active cores
        3400 MHz max turbo 2 active cores
        3600 MHz max turbo 1 active cores

The CPU base frequency is 2.9 GHz. If only 1 physical core is "active" (busy),
the active core can run at up to 3.6 GHz.  If more physical cores are active,
the maximum frequency is limited to 3.4 GHz.

Turbo Boost is supported and active.


Turbo Boost MSR
---------------

The bit 38 of the `Model-specific register
(MSR) <https://en.wikipedia.org/wiki/Model-specific_register>`_ ``0x1a0`` can
be used to check if the Turbo Boost is enabled::

    selma$ sudo rdmsr -f 38:38 0x1a0
    0

``0`` means that Turbo Boost is enabled, whereas ``1`` means disabled (no
turbo). ``-f 38:38`` option asks to only display the bit 38.

If the command doesn't work, you may have to load the ``msr`` kernel module::

    sudo modprobe msr

.. note::
   Command to install rdmsr on Fedora 24: ``sudo dnf install -y msr-tools``.

.. warning::
   I'm not sure that the command works on all Intel CPUs.


intel_state/no_turbo
--------------------

The following file can be read to check if Turbo Boost is allowed or not in the
``intel_pstate`` driver::

    selma$ cat /sys/devices/system/cpu/intel_pstate/no_turbo
    0

Where ``0`` means that it is allowed. Write ``1`` into this file to deny Turbo
Boost::

    selma$ echo 1|sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

See also the ``ida`` (Intel Dynamic Acceleration) of CPU flags in
``/proc/cpuinfo``.


Read the CPU frequency
======================

General information using ``cpupower frequency-info``::

    selma$ cpupower -c 0 frequency-info
    analyzing CPU 0:
      driver: intel_pstate
      CPUs which run at the same hardware frequency: 0
      CPUs which need to have their frequency coordinated by software: 0
      hardware limits: 1.20 GHz - 3.60 GHz
      current policy: frequency should be within 1.20 GHz and 3.60 GHz.
                      The governor "performance" may decide which speed to use
                      within this range.
    ...

The frequency is between 1.2 GHz and 3.6 GHz.


Get the frequency of CPUs
-------------------------

Kernel message, the ``tsc`` clock source logs the CPU frequency::

    selma$ dmesg|grep 'MHz processor'
    [    0.000000] tsc: Detected 2893.331 MHz processor

cpuinfo::

    selma$ grep MHz /proc/cpuinfo
    cpu MHz : 1372.289
    cpu MHz : 3401.042

cpupower frequency-info::

    selma$ for core in $(seq 0 1); do sudo cpupower -c $core frequency-info|grep 'current CPU'; done
      current CPU frequency: 3.48 GHz (asserted by call to hardware)
      current CPU frequency: 3.40 GHz (asserted by call to hardware)

cpupower monitor::

    selma$ sudo cpupower monitor -m 'Mperf'
        |Mperf
    CPU | C0   | Cx   | Freq
       0|  4.77| 95.23|  1924
       1|  0.01| 99.99|  1751

turbostat::

    selma$ sudo turbostat
         CPU Avg_MHz   Busy% Bzy_MHz TSC_MHz
           -     224    7.80    2878    2893
           0     448   15.59    2878    2893
           1       0    0.01    2762    2893
         CPU Avg_MHz   Busy% Bzy_MHz TSC_MHz
           -     139    5.65    2469    2893
           0     278   11.29    2469    2893
           1       0    0.01    2686    2893
        ...

* ``Avg_MHz``: average frequency read from APERF
* ``Busy%``: CPU usage in percent
* ``Bzy_MHz``: busy frequency, read by MPERF (?)
* ``TSC_MHz``: fixed frequency

