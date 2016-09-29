+++++++++++++++++++++++++++++++
Intel P-state and NOHZ_FULL bug
+++++++++++++++++++++++++++++++

General
=======

Bug 1
=====

When a single process (thread) runs on a CPU, the interruption of the scheduler
clock is no more sent to the process. As a side effect, the scheduler doesn't
call the cpufreq callback anymore, whereas the intel_pstate driver requires
to be called when the workload changes to update the P-state of the CPU.

The frequency of CPUs using NOHZ_FULL doesn't depend on their workload, but
on the workload of other CPUs! Example with the default CPU scaling governor "powersave":

* Idle system
* Start a benchmark 1 on CPU 7 using NOHZ_FULL
* Start a benchmark 2 on CPU 0 (not using NOHZ_FULL)
* Suddenly, the benchmark 1 "becomes 2x faster"
* Stop the benchmark 2: benchmark 1 becomes slower again

When the system is idle, all CPUs use a low P-state (so low performance). When
the benchmark 2 starts, intel_pstate updates the P-state to use the highest
P-state.


Bug 2
=====

On a CPU using NOHZ_FULL, the intel_idle driver doesn't update properly C-state
of CPUs. Sometimes, two logical cores using NOHZ_FULL of the same physical core
using HyperThreading are "stuck" in the C0 ("POLL") state. On such case,
the performance of a single logical core is 2x slower than the nominal
performance.

Moreover, this bug can be trigger without NOHZ_FULL if the intel_idle driver
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


Bug 3
=====

Similar to the bug 2, but different. Again, because of NOHZ_FULL, intel_idle
doesn't update properly C-state. On this bug, CPUs are not stuck in the highest
C-state C0 (aka "POLL"), but stay in a deep C-state and not awaken.

XXX
