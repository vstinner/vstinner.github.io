Benchmark on PGO

Test: ``./configure && make profile-opt && ./python bm_call_simple.py``

Hardware
========

* Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
* 4 physical cores, 8 logical cores: 3 physical cores are isolated
* NOHZ full on the isolated CPUs
* Python revision b6ca2d734f8e
* Python makefile: PROFILE_TASK=bm_call_simple.py --worker -w 3 -n 2500 -v
* GCC 6.1.1, Linux kernel 4.7.2, Fedora 24


Try 1
=====

PGO compilation, make -j9, 5 compilations::

    Median +- std dev: 18.8 ms +- 0.7 ms
    Median +- std dev: 18.6 ms +- 0.5 ms
    Median +- std dev: 19.5 ms +- 0.9 ms
    Median +- std dev: 19.2 ms +- 0.6 ms
    Median +- std dev: 18.8 ms +- 0.4 ms

Not really the expected result, each compilation seems to be a different speed.
Well, the difference is *very* small, especially if you take in the account the
standard deviation.


Try 2
=====

Oh, I forgot that my ``~/.bashrc`` contains::

    export MAKEFLAGS=$(python -c "import os; print('-j%s' % (os.sysconf('SC_NPROCESSORS_ONLN') + 1))")

And so make uses ``-j9`` by default! Running jobs in parallel doesn't help to
get reproductible builds. Let's retry without the ``MAKEFLAGS`` environment
variable.

PGO compilation (make without -j), 5 compilations::

    Median +- std dev: 19.2 ms +- 0.5 ms
    Median +- std dev: 19.0 ms +- 0.5 ms
    Median +- std dev: 18.6 ms +- 0.5 ms
    Median +- std dev: 18.8 ms +- 0.9 ms
    Median +- std dev: 18.5 ms +- 0.8 ms


Try 3
=====

There is still a tiny difference. Maybe PGO depends on exact timings, so ``make
profile-opt`` step should be pinning on isolated CPUs as well? New try on
isolated CPUs without ``MAKEFLAGS``.

PGO compilation pinned on isolated CPUs, (make without -j), 5 compilations::

    Median +- std dev: 19.3 ms +- 0.6 ms
    Median +- std dev: 19.0 ms +- 0.7 ms
    Median +- std dev: 19.0 ms +- 0.7 ms
    Median +- std dev: 18.2 ms +- 0.4 ms
    Median +- std dev: 18.8 ms +- 0.5 ms


Try 4
=====

1200 samples (400 runs x 3 samples)::

    ./python bm_call_simple.py -p 100 --inherit-environ=PYTHONPATH -o pgo_many_$run.json
    ./python bm_call_simple.py -p 100 --inherit-environ=PYTHONPATH --append pgo_many_$run.json
    ./python bm_call_simple.py -p 100 --inherit-environ=PYTHONPATH --append pgo_many_$run.json
    ./python bm_call_simple.py -p 100 --inherit-environ=PYTHONPATH --append pgo_many_$run.json

Result of 5 compilations::

    Median +- std dev: 18.2 ms +- 0.8 ms
    Median +- std dev: 18.7 ms +- 0.5 ms
    Median +- std dev: 18.9 ms +- 0.8 ms
    Median +- std dev: 18.5 ms +- 0.7 ms
    Median +- std dev: 18.8 ms +- 0.5 ms


Single compilation, multiple runs
=================================

Compile once, run the benchmark 5 times::

    Median +- std dev: 19.1 ms +- 0.8 ms
    Median +- std dev: 19.0 ms +- 0.5 ms
    Median +- std dev: 19.2 ms +- 0.5 ms
    Median +- std dev: 18.8 ms +- 0.7 ms
    Median +- std dev: 18.8 ms +- 0.6 ms


Statistics
==========

Timings of the total 15 compilations, sorted::

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


Without PGO
===========

For comparison, 5 compilations without PGO. 1 run per compilation::

    Median +- std dev: 22.9 ms +- 0.4 ms
    Median +- std dev: 23.0 ms +- 0.6 ms
    Median +- std dev: 22.9 ms +- 0.4 ms
    Median +- std dev: 22.9 ms +- 0.4 ms
    Median +- std dev: 22.9 ms +- 0.5 ms

Timings are *very* close: the difference on the median is only 0.1 ms: 0.4%!
Moreover, there is not difference if you take in account the standard deviation
;-)

But PGO is much faster: 18.8 ms instead of 22.9 ms, 17.5% faster!
