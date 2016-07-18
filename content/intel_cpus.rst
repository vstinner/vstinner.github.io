++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Intel CPUs: P-state, C-state, Turbo Boost, CPU frequency, etc.
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-07-15 12:00
:tags: optimization, benchmark
:category: benchmark
:slug: intel-cpus
:authors: Victor Stinner
:summary: Intel CPUs: Hyper-threading, Turbo Boost, CPU frequency, etc.


Ten years ago, most computers were desktop computers designed for best
performances and their CPU frequency was fixed. Nowadays, most devices are
embedded and use `low power consumption
<https://en.wikipedia.org/wiki/Low-power_electronics>`_ processors like ARM
CPUs. The power consumption now matters more than performance peaks.

Intel CPUs evolved from a single core to multiple physical cores in the same
`package <https://en.wikipedia.org/wiki/CPU_socket>`_ and got new features:
`Hyper-threading <https://en.wikipedia.org/wiki/Hyper-threading>`_ to run two
threads on the same physical core and `Turbo Boost
<https://en.wikipedia.org/wiki/Intel_Turbo_Boost>`_ to maximum performances.
CPU cores can be completely turned off (CPU HALT, frequency of 0) temporarily to
reduce the power consumption, and the frequency of cores changes regulary
depending on many factors like the workload and temperature. The power
consumption is now an important part in the design of modern CPUs.

Warning! This article is a summary of what I learnt last weeks from random
articles. It may be full of mistakes, don't hesitate to report them, so I can
enhance the article! It's hard to find simple articles explaining performances
of modern Intel CPUs, so I tried to write mine.


Tools used in this article
==========================

This article mentions various tools. Commands to install them on Fedora 24:

``dnf install -y util-linux``:

* lscpu

``dnf install -y kernel-tools``:

* `cpupower <http://linux.die.net/man/1/cpupower>`_
* turbostat

``sudo dnf install -y msr-tools``:

* rdmsr
* wrmsr

Other interesting tools, not used in this article: i7z (sadly no more
maintained), lshw, dmidecode, sensors.

The sensors tool is supposed to report the current CPU voltage, but it doesn't
provide this information on my computers. At least, it gives the temperature of
different components, but also the speed of fans.


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

My desktop CPU: CPU topology with lscpu
---------------------------------------

cpuinfo::

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

The CPU i7-2600 is the 2nd generation: `Sandy Bridge microarchitecture
<https://en.wikipedia.org/wiki/Sandy_Bridge>`_. There are 8 logical cores and 4
physical cores (so with Hyper-threading).

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
instruction) and 2 (L2).  All physical cores share the same cache level 3 (L3).


P-states
========

A new CPU driver ``intel_pstate`` was added to the Linux kernel 3.9 (April
2009). First, it only supported SandyBridge CPUs (2nd generation), Linux 3.10
extended it to Ivybridge generation CPUs (3rd gen), and so on and so forth.

This driver supports recent features and thermal control of modern Intel CPUs.
Its name comes from P-states.

The processor P-state is the capability of running the processor at different
voltage and/or frequency levels. Generally, P0 is the highest state resulting
in maximum performance, while P1, P2, and so on, will save power but at some
penalty to CPU performance.

It is possible to force the legacy CPU driver (``acpi_cpufreq``) using
``intel_pstate=disable`` option in the kernel command line.

See also:

* `Documentation of the intel-pstate driver
  <https://www.kernel.org/doc/Documentation/cpu-freq/intel-pstate.txt>`_
* `Some basics on CPU P states on Intel processors
  <https://plus.google.com/+ArjanvandeVen/posts/dLn9T4ehywL>`_ (2013) by Arjan
  van de Ven (Intel)
* `Balancing Power and Performance in the Linux Kernel
  <https://events.linuxfoundation.org/sites/events/files/slides/LinuxConEurope_2015.pdf>`_
  talk at LinuxCon Europe 2015 by Kristen Accardi (Intel)
* `What exactly is a P-state? (Pt. 1)
  <https://software.intel.com/en-us/blogs/2008/05/29/what-exactly-is-a-p-state-pt-1>`_
  (2008) by Taylor K. (Intel)


Idle states: C-states
=====================

C-states are idle power saving states, in contrast to P-states, which are
execution power saving states.

During a P-state, the processor is still executing instructions, whereas during
a C-state (other than C0), the processor is idle, meaning that nothing is
executing.

C-states:

* C0 is the operational state, meaning that the CPU is doing useful work
* C1 is the first idle state
* C2 is the second idle state: The external I/O Controller Hub blocks
  interrupts to the processor.
* etc.

When a logical processor is idle (C-state except of C0), its frequency is
typically 0 (HALT).

The ``cpupower idle-info`` command lists supported C-states::

    selma$ cpupower idle-info
    CPUidle driver: intel_idle
    CPUidle governor: menu
    analyzing CPU 0:

    Number of idle states: 6
    Available idle states: POLL C1-IVB C1E-IVB C3-IVB C6-IVB C7-IVB
    ...

The ``cpupower monitor`` shows statistics on C-states::

    smithers$ sudo cpupower monitor -m Idle_Stats
        |Idle_Stats
    CPU | POLL | C1-S | C1E- | C3-S | C6-S
       0|  0,00|  0,19|  0,09|  0,58| 96,23
       4|  0,00|  0,00|  0,00|  0,00| 99,90
       1|  0,00|  2,34|  0,00|  0,00| 97,63
       5|  0,00|  0,00|  0,17|  0,00| 98,02
       2|  0,00|  0,00|  0,00|  0,00|  0,00
       6|  0,00|  0,00|  0,00|  0,00|  0,00
       3|  0,00|  0,00|  0,00|  0,00|  0,00
       7|  0,00|  0,00|  0,00|  0,00| 49,97

See also: `Power Management States: P-States, C-States, and Package C-States
<https://software.intel.com/en-us/articles/power-management-states-p-states-c-states-and-package-c-states>`_.


Turbo Boost
===========

In 2005, Intel introduced `SpeedStep
<https://en.wikipedia.org/wiki/SpeedStep>`_, a serie of dynamic frequency
scaling technologies to reduce the power consumption of laptop CPUs. Turbo
Boost is an enhancement of these technologies, now also used on desktop and
server CPUs.

Turbo Boost allows to run one or many CPU cores to higher P-states than usual.
The maximum P-state is constrained by the following factors:

- The number of active cores (in C0 or C1 state)
- The estimated current consumption of the processor (Imax)
- The estimated power consumption (TDP - Thermal Design Power) of processor
- The temperature of the processor

Example on my laptop::

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

The CPU base frequency is 2.9 GHz. If more than one physical cores is "active"
(busy), their frequency can be increased up to 3.4 GHz. If only 1 physical core
is active, its frequency can be increased up to 3.6 GHz.

In this example, Turbo Boost is supported and active.

See also the `Linux cpu-freq documentation on CPU boost
<https://www.kernel.org/doc/Documentation/cpu-freq/boost.txt>`_.


Turbo Boost MSR
---------------

The bit 38 of the `Model-specific register
(MSR) <https://en.wikipedia.org/wiki/Model-specific_register>`_ ``0x1a0`` can
be used to check if the Turbo Boost is enabled::

    selma$ sudo rdmsr -f 38:38 0x1a0
    0

``0`` means that Turbo Boost is enabled, whereas ``1`` means disabled (no
turbo). (The ``-f 38:38`` option asks to only display the bit 38.)

If the command doesn't work, you may have to load the ``msr`` kernel module::

    sudo modprobe msr

Note: I'm not sure that all Intel CPU uses the same MSR.


intel_state/no_turbo
--------------------

Turbo Boost can also be disabled at runtime in the ``intel_pstate`` driver.

Check if Turbo Boost is enabled::

    selma$ cat /sys/devices/system/cpu/intel_pstate/no_turbo
    0

where ``0`` means that Turbo Boost is enabled. Disable Turbo Boost::

    selma$ echo 1|sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo


CPU flag "ida"
--------------

It looks like the Turbo Boost status (supported or not) can also be read by the
CPUID(6): "Thermal/Power Management". It gives access to the flag `Intel
Dynamic Acceleration (IDA)
<https://en.wikipedia.org/wiki/Intel_Dynamic_Acceleration>`_.

The ``ida`` flag can also be seen in CPU flags of ``/proc/cpuinfo``.


Read the CPU frequency
======================

General information using ``cpupower frequency-info``::

    selma$ cpupower -c 0 frequency-info
    analyzing CPU 0:
      driver: intel_pstate
      ...
      hardware limits: 1.20 GHz - 3.60 GHz
      ...

The frequency of CPUs is between 1.2 GHz and 3.6 GHz (the base frequency is
2.9 GHz on this CPU).


Get the frequency of CPUs: turbostat
------------------------------------

It looks like the most reliable way to get a relialistic estimation of the CPUs
frequency is to use the tool ``turbostat``::

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

* ``Avg_MHz``: average frequency, based on APERF
* ``Busy%``: CPU usage in percent
* ``Bzy_MHz``: busy frequency, based on MPERF
* ``TSC_MHz``: fixed frequency, TSC stands for `Time Stamp Counter
  <https://en.wikipedia.org/wiki/Time_Stamp_Counter>`_

APERF (average) and MPERF (maximum) are MSR registers that can provide feedback
on current CPU frequency.


Other tools to get the CPU frequency
------------------------------------

It looks like the following tools are less reliable to estimate the CPU
frequency.

cpuinfo::

    selma$ grep MHz /proc/cpuinfo
    cpu MHz : 1372.289
    cpu MHz : 3401.042

In April 2016, Len Brown proposed a patch modifying cpuinfo to use APERF and
MPERF MSR to estimate the CPU frequency: `x86: Calculate MHz using APERF/MPERF
for cpuinfo and scaling_cur_freq <https://lkml.org/lkml/2016/4/1/7>`_.

The ``tsc`` clock source logs the CPU frequency in kernel logs::

    selma$ dmesg|grep 'MHz processor'
    [    0.000000] tsc: Detected 2893.331 MHz processor

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


Conclusion
==========

Modern Intel CPUs use various technologies to provide best performances without
killing the power consumption. It became harder to monitor and understand CPU
performances, than with older CPUs, since the performance now depends on much
more factors.

It also becomes common to get an integrated graphics processor (IGP) in the
same package, which makes the exact performance even more complex to predict,
since the IGP produces heat and so has an impact on the CPU P-state.

I should also explain that P-state are "voted" between CPU cores, but I didn't
understand this part. I'm not sure that understanding the exact algorithm
matters much. I tried to not give too much information.


Annex: AMT and the ME (power management coprocessor)
====================================================

Computers with Intel vPro technology includes `Intel Active Management
Technology (AMT)
<https://en.wikipedia.org/wiki/Intel_Active_Management_Technology>`_: "hardware
and firmware technology for remote out-of-band management of personal
computers". AMT has many features which includes power management.

`Management Engine (ME)
<https://en.wikipedia.org/wiki/Intel_Active_Management_Technology#Hardware>`_
is the hardware part: an isolated and protected coprocessor, embedded as a
non-optional part in all current (as of 2015) Intel chipsets. The coprocessor
is a special 32-bit ARC microprocessor (RISC architecture) that's physically
located inside the PCH chipset (or MCH on older chipsets). The coprocessor can
for example be found on Intel MCH chipsets Q35 and Q45.

See `Intel x86s hide another CPU that can take over your machine (you can't
audit it)
<https://boingboing.net/2016/06/15/intel-x86-processors-ship-with.html>`_ for
more information on the coprocessor.

More recently, the Intel Xeon Phi CPU (2016) also includes a coprocessor for
power management. I didn't understand if it is the same coprocessor or not.
