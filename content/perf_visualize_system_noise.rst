+++++++++++++++++++++++++++++++++++++++++++++++++++++++
Visualize the system noise using perf and CPU isolation
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-06-16 13:30
:tags: benchmark
:category: benchmark
:slug: perf-visualize-system-noise-with-cpu-isolation
:authors: Victor Stinner

I developed a new `perf module <http://perf.readthedocs.io/>`_ designed to run
stable benchmarks, give fine control on benchmark parameters and compute
statistics on results. With such tool, it becomes simple to *visualize*
sources of noise. The CPU isolation will be used to visualize the system noise.
Running a benchmark on isolated CPUs isolates it from the system noise.


Isolate CPUs
============

My computer has 4 physical CPU cores. I isolated half of them using
``isolcpus=2,3`` parameter of the Linux kernel. I modified manually the command
line in GRUB to add this parameter.

Check that CPUs are isolated::

    $ cat /sys/devices/system/cpu/isolated
    2-3

The CPU supports HyperThreading, but I disabled it in the BIOS.


Run a benchmark
===============

The ``perf`` module automatically detects and uses isolated CPU cores. I will
use the ``--affinity=0,1`` option to force running the benchmark on the CPUs
which are not isolated.

Microbenchmark with and without CPU isolation::

    $ python3 -m perf.timeit --json-file=timeit_isolcpus.json --verbose -s 'x=1; y=2' 'x+y'
    Pin process to isolated CPUs: 2-3
    .........................
    Median +- std dev: 36.6 ns +- 0.1 ns (25 runs x 3 samples x 10^7 loops; 1 warmup)

    $ python3 -m perf.timeit --affinity=0,1 --json-file=timeit_no_isolcpus.json --verbose -s 'x=1; y=2' 'x+y'
    Pin process to CPUs: 0-1
    .........................
    Median +- std dev: 36.7 ns +- 1.3 ns (25 runs x 3 samples x 10^7 loops; 1 warmup)

My computer was not 100% idle, I was using it while the benchmarks were
running.

The median is almost the same (36.6 ns and 36.7 ns). The first major difference
is the standard deviation: it is much larger without CPU isolation: 0.1 ns =>
1.3 ns (13x larger).

Just in case, check manually CPU affinity in metadata::

    $ python3 -m perf show timeit_isolcpus.json --metadata | grep cpu
    - cpu_affinity: 2-3 (isolated)
    - cpu_count: 4
    - cpu_model_name: Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz

    $ python3 -m perf show timeit_no_isolcpus.json --metadata | grep cpu_affinity
    - cpu_affinity: 0-1


Statistics
==========

The ``perf stats`` command computes statistics on the distribution of samples::

    $ python3 -m perf stats timeit_isolcpus.json
    Number of samples: 75

    Minimum: 36.5 ns (-0.1%)
    Median +- std dev: 36.6 ns +- 0.1 ns (36.5 ns .. 36.7 ns)
    Maximum: 36.7 ns (+0.4%)

    $ python3 -m perf stats timeit_no_isolcpus.json
    Number of samples: 75

    Minimum: 36.5 ns (-0.5%)
    Median +- std dev: 36.7 ns +- 1.3 ns (35.4 ns .. 38.0 ns)
    Maximum: 43.0 ns (+17.0%)

The minimum is the same. The second major difference is the maximum: it is much
larger without CPU isolation: 36.7 ns (+0.4%) => 43.0 ns (+17.0%).

The difference between the maximum and the median is 63x larger without CPU
isolation: 0.1 ns (``36.7 - 36.6``) => 6.3 ns (``43.0 - 36.7``).

Depending on the system load, a single sample of the microbenchmark is up to
17% slower (maximum of 43.0 ns with a median of 36.7 ns) without CPU isolation.
The difference is smaller with CPU isolation: only 0.4% slower (for the
maximum, and 0.1% faster for the minimum).


Histogram
=========

Another way to analyze the distribution of samples is to render an histogram::

    $ python3 -m perf hist --bins=8 timeit_isolcpus.json timeit_no_isolcpus.json
    [ timeit_isolcpus ]
    36.1 ns: 75 ################################################
    36.9 ns:  0 |
    37.7 ns:  0 |
    38.5 ns:  0 |
    39.3 ns:  0 |
    40.1 ns:  0 |
    40.9 ns:  0 |
    41.7 ns:  0 |
    42.5 ns:  0 |

    [ timeit_no_isolcpus ]
    36.1 ns: 52 ################################################
    36.9 ns: 13 ############
    37.7 ns:  1 #
    38.5 ns:  4 ####
    39.3 ns:  2 ##
    40.1 ns:  0 |
    40.9 ns:  1 #
    41.7 ns:  0 |
    42.5 ns:  2 ##

I choose the number of bars to get a small histogram and to get all samples of
the first benchmark on the same bar. With 8 bars, each bar is a range of 0.8
ns.

The last major difference is the shape of these histogram. Without CPU
isolation, there is a "long tail" at the right of the median: `outliers
<https://en.wikipedia.org/wiki/Outlier>`_ in the range [37.7 ns; 42.5 ns].
The outliers come from the "noise" caused by the multitasking system.


Conclusion
==========

The ``perf`` module provides multiple tools to analyze the distribution of
benchmark samples. Three tools show a major difference without CPU isolation
compared to results with CPU isolation:

* Standard deviation: 13x larger without isolation
* Maximum: difference to median 63x larger without isolation
* Shape of the histogram: long tail at the right of the median

It explains why CPU isolation helps to make benchmarks more stable.
