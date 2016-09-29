+++++++++++++++++++++++++++++++
Intel P-state and NOHZ_FULL bug
+++++++++++++++++++++++++++++++

General
=======

Bug 1: Slow P-state while a benchmark is running
================================================

When a single process (thread) runs on a CPU, the interruption of the scheduler
clock is no more sent to the process. As a side effect, the scheduler doesn't
call the cpufreq callback anymore, whereas the intel_pstate driver requires
to be called when the workload changes to update the P-state of the CPU.

The frequency of CPUs using NOHZ_FULL doesn't depend on their workload, but on
the workload of other CPUs! Example with the default CPU scaling governor
"powersave":

* Idle system
* Start a benchmark 1 on CPU 7 using NOHZ_FULL
* Start a benchmark 2 on CPU 0 (not using NOHZ_FULL)
* Suddenly, the benchmark 1 "becomes 2x faster"
* Stop the benchmark 2: benchmark 1 becomes slow again

In fact, when the system is idle, performance on CPU using NOHZ_FULL is half of
the nominal speed.

When the system is idle, all CPUs use a low P-state (so half performance). When
the benchmark 2 starts, intel_pstate updates the P-state to use the highest
P-state and so benchmark on all CPU have the nominal performance.


Bug 2: two CPU threads stuck in the C0 state
============================================

On a CPU using NOHZ_FULL, the intel_idle driver doesn't update properly C-state
of CPUs. Sometimes, two logical cores using NOHZ_FULL of the same physical core
using HyperThreading are "stuck" in the C0 ("POLL") state. On such case,
the performance of a single logical core is 2x slower than the nominal
performance.

Moreover, this bug can be triggered without NOHZ_FULL if the intel_idle driver
is tuned to stay in C0:

* Example: as root, write 0 into /dev/cpu_dma_latency and keep the device open

Example with the Linux cmdline ``... nohz_full=3,7``:

* Run a benchmark::

    Speed 100

* Open python3 as root, type::

    import strict
    f = open("/dev/cpu_dma_latency", "wb", 0)
    f.write(struct.pack('I', 0))
    # keep the device open

* Check the C-state of CPUs::

    cpupower monitor
    # CPU 3 and 7 are 100% in C0
    # or turbostat --debug

* Run again the benchmark::

    Speed 50

* Close the device

* Run again the benchmark::

    Speed 100

See also: `PM Quality Of Service Interface
<https://kernel.org/doc/Documentation/power/pm_qos_interface.txt>`_ (PM: Power
Management).


Bug 3: Slow C-state while a benchmark is running
================================================

Similar to the bug 2, but different. Again, because of NOHZ_FULL, intel_idle
doesn't update properly C-state. On this bug, CPUs are not stuck in the highest
C-state C0 (aka "POLL"), but stay in a deep C-state and not awaken.

XXX


Bug 4: Running turbostat to monitor hides or fixes bugs
=======================================================

Debugging issues on P-state and C-state of a CPU is difficult because these
states are not directly exposed in /proc/cpuinfo nor common tool. Moreover,
the effective state changes anytime. Tools can only estimate the percentage of
time the CPU spent in one specific state... For example, the last second,
the CPU 7 was 80% is C0, 10% in C1 and 10% in C1-E.

P-state and C-state can be read by different tools

* cpupower monitor
* turbostat
* perf stat -a -e "cstate_pkg/c2-residency/,cstate_pkg/c3-residency/,cstate_pkg/c6-residency/,cstate_pkg/c7-residency/" sleep 1

These tool can be used as "wrapper": run a command and monitor performances
while the command is running.  Example: "turbostat sleep 1" runs "sleep 1"
command and then displays statistics.

The problem was that running turbostat seems to "fix" the issues that I saw,
whereas I wanted to run this tool to analyze what is happening...

I read the source code (it's part of the Linux kernel) and used strace on it.
It reads MSR registers of CPUs using ``/dev/cpu/ID/msr`` where ``ID`` is the
CPU identifier, but the process is moved to the analyzed CPU using
``sched_setaffinity()``.

I was told that reading MSR can only be done from the CPU itself. Reading
``/dev/cpu/ID/msr`` file and running the ``rdmsr`` command use a trick: if the
requested CPU is not the current CPU, it sends an interruption to the requested
CPU to read the MSR value!

My problem is that the bugs that I found with NOHZ_FULL only occur when the LOC
interruption (scheduler clock) is no more sent to the CPUs using NOHZ_FULL.  If
a benchmark and turbostat are running "at the same time", we have more than 1
process running on the CPU and so NOHZ_FULL cannot disable the LOC interruption
anymore. Disabling the interruption wakes up intel_pstate and/or intel_idle
which update P-strace and C-strace, and so the bug is fixed immediatly.
