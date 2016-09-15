Benchmark on PGO

Test: ``./configure && make profile-opt && ./python bm_call_simple.py``

* 5 runs: PGO compilation
* 5 runs: unset MAKEFLAGS (previously MAKEFLAGS=-j9)
* 5 runs: unset MAKEFLAGS, taskset_isolcpus.py (pin to 6 isolated CPUs)

Hardware:

* Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
* 4 physical cores, 8 logical cores: 3 physical cores are isolated
* NOHZ full on the isolated CPUs
* Python revision b6ca2d734f8e
* Python makefile: PROFILE_TASK=bm_call_simple.py --worker -w 3 -n 2500 -v
* GCC 6.1.1, Linux kernel 4.7.2, Fedora 24

Total: 15 runs.

Sorted timings::

    Median +- std dev: 18.2 ms +- 0.4 ms
    Median +- std dev: 18.5 ms +- 0.8 ms
    Median +- std dev: 18.6 ms +- 0.5 ms
    Median +- std dev: 18.6 ms +- 0.5 ms
    Median +- std dev: 18.8 ms +- 0.4 ms
    Median +- std dev: 18.8 ms +- 0.5 ms
    Median +- std dev: 18.8 ms +- 0.7 ms
    Median +- std dev: 18.8 ms +- 0.9 ms
    Median +- std dev: 19.0 ms +- 0.5 ms
    Median +- std dev: 19.0 ms +- 0.7 ms
    Median +- std dev: 19.0 ms +- 0.7 ms
    Median +- std dev: 19.2 ms +- 0.5 ms
    Median +- std dev: 19.2 ms +- 0.6 ms
    Median +- std dev: 19.3 ms +- 0.6 ms
    Median +- std dev: 19.5 ms +- 0.9 ms

Stats::

    >>> samples
    [18.2, 18.5, 18.6, 18.6, 18.8, 18.8, 18.8, 18.8, 19.0, 19.0, 19.0, 19.2, 19.2, 19.3, 19.5]
    >>> len(samples)
    15
    >>> import statistics
    >>> statistics.stdev(samples)
    0.3377798663260408
    >>> statistics.mean(samples)
    18.886666666666667

Median +- std dev of the 15 runs: 18.9 ms +- 0.3 ms
