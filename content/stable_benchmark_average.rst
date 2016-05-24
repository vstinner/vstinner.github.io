++++++++++++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part 3 (average)
++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-05-23 23:00
:tags: optimization, benchmark
:category: python
:slug: journey-to-stable-benchmark-average
:authors: Victor Stinner
:summary: My journey to stable benchmark, part 3 (average)

.. image:: images/fog.jpg
   :alt: Fog
   :target: https://www.flickr.com/photos/stanzim/11100202065/

*Stable benchmarks are so close, but ...*

Address Space Layout Randomization
==================================

When I started to work on removing the noise of the system, I was told that
disabling `Address Space Layout Randomization (ASLR)
<https://en.wikipedia.org/wiki/Address_space_layout_randomization>`_ makes
benchmarks more stable.

I followed this advice without trying to understand it. We will see in this
article that it was a bad idea, but I had to hit other issues to really
understand to root issue with disabling ASLR.

Example of command to see the effect of ASLR, the first number of the output is
the start address of the heap memory::

    $ python -c 'import os; os.system("grep heap /proc/%s/maps" % os.getpid())'
    55e6a716c000-55e6a7235000 rw-p 00000000 00:00 0                          [heap]

Heap address of 3 runs with ASLR enabled (random):

* 55e6a716c000
* 561c218eb000
* 55e6f628f000

Disable ASLR::

    sudo bash -c 'echo 0 >| /proc/sys/kernel/randomize_va_space'

Heap addresses of 3 runs with ASLR disabled (all the same):

* 555555756000
* 555555756000
* 555555756000

Note: To reenable ASLR, it's better to use the value 2, the value 1 only
partially enables the feature::

    sudo bash -c 'echo 2 >| /proc/sys/kernel/randomize_va_space'


Python randomized hash function
===============================

With `system tuning  (part 1) <{filename}/stable_benchmark_system.rst>`_, a
`Python compiled with PGO (part 2) <{filename}/stable_benchmark_deadcode.rst>`_
and ASLR disabled, I still I failed to get the same result when running
manually ``bm_call_simple.py``.

On Python 3, the hash function is now randomized by default: `issue #13703
<http://bugs.python.org/issue13703>`_. The problem is that for a
microbenchmark, the number of hash collisions of an "hot" dictionary has a
non-negligible impact on performances.

The ``PYTHONHASHSEED`` environment variable can be used to get a fixed hash
function. Example with the patch::

    $ PYTHONHASHSEED=1 taskset -c 1 ./python bm_call_simple.py -n 1
    0.198
    $ PYTHONHASHSEED=2 taskset -c 1 ./python bm_call_simple.py -n 1
    0.201
    $ PYTHONHASHSEED=3 taskset -c 1 ./python bm_call_simple.py -n 1
    0.207
    $ PYTHONHASHSEED=4 taskset -c 1 ./python bm_call_simple.py -n 1
    0.187
    $ PYTHONHASHSEED=5 taskset -c 1 ./python bm_call_simple.py -n 1
    0.180

Timings of the reference python::

    $ PYTHONHASHSEED=1 taskset -c 1 ./ref_python bm_call_simple.py -n 1
    0.204
    $ PYTHONHASHSEED=2 taskset -c 1 ./ref_python bm_call_simple.py -n 1
    0.206
    $ PYTHONHASHSEED=3 taskset -c 1 ./ref_python bm_call_simple.py -n 1
    0.195
    $ PYTHONHASHSEED=4 taskset -c 1 ./ref_python bm_call_simple.py -n 1
    0.192
    $ PYTHONHASHSEED=5 taskset -c 1 ./ref_python bm_call_simple.py -n 1
    0.187

The minimums is 180 ms for the reference and 186 ms for the patch. The patched
Python is 3% faster, yeah!

Wait. What if we only test PYTHONHASHSEED from 1 to 3? In this case, the
minimum is 195 ms for the reference and 198 ms for the patch. The patched
Python becomes 2% slower, oh no!

Faster? Slower? Who is right?

Maybe I should write a script to find a ``PYTHONHASHSEED`` value for which my
patch is always faster :-)


Command line and environment variables
======================================

Well, let's say that we will use a fixed PYTHONHASHSEED value. Anyway, my
patch doesn't touch at the hash function. So it doesn't matter.

While running benchmarks, I noticed differences when running the benchmark from
a different directory::

    $ cd /home/haypo/prog/python/fastcall
    $ PYTHONHASHSEED=3 taskset -c 1 pgo/python ../benchmarks/performance/bm_call_simple.py -n 1
    0.215

    $ cd /home/haypo/prog/python/benchmarks
    $ PYTHONHASHSEED=3 taskset -c 1 ../fastcall/pgo/python ../benchmarks/performance/bm_call_simple.py -n 1
    0.203

    $ cd /home/haypo/prog/python
    $ PYTHONHASHSEED=3 taskset -c 1 fastcall/pgo/python benchmarks/performance/bm_call_simple.py -n 1
    0.200

In fact, a different command line is enough so get different results (added
arguments are ignored)::

    $ PYTHONHASHSEED=3 taskset -c 1 ./python bm_call_simple.py -n 1
    0.201
    $ PYTHONHASHSEED=3 taskset -c 1 ./python bm_call_simple.py -n 1 arg1
    0.198
    $ PYTHONHASHSEED=3 taskset -c 1 ./python bm_call_simple.py -n 1 arg1 arg2 arg3
    0.203
    $ PYTHONHASHSEED=3 taskset -c 1 ./python bm_call_simple.py -n 1 arg1 arg2 arg3 arg4 arg5
    0.206
    $ PYTHONHASHSEED=3 taskset -c 1 ./python bm_call_simple.py -n 1 arg1 arg2 arg3 arg4 arg5 arg6
    0.210

I also noticed minor differences when the environment changes (added variables
are ignored)::

    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py -n 1
    0.201
    $ taskset -c 1 env -i PYTHONHASHSEED=3 VAR1=1 VAR2=2 VAR3=3 VAR4=4 ./python bm_call_simple.py -n 1
    0.202
    $ taskset -c 1 env -i PYTHONHASHSEED=3 VAR1=1 VAR2=2 VAR3=3 VAR4=4 VAR5=5 ./python bm_call_simple.py -n 1
    0.198

Using ``strace`` and ``ltrace``, I saw the memory addresses are different when
something (command line, env var, etc.) changes.


Average and standard deviation
==============================

Basically, it looks like a lot of "external factors" have an impact on the
exact memory addresses, even if ASRL is disabled and PYTHONHASHSEED is set. I
started to think how to get get *exactly* the same command line, the same
environment (easy), the same current directory (easy), etc. The problem is that
it's just not possible to control all external factors (having an effect on the
exact memory addresses).

Maybe I was plain wrong from the beginning and ASLR must be enabled,
as the default on Linux::

    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.198
    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.202
    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.199
    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.207
    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.200
    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.201

These results look "random". Yes, they are. It's exactly the purpose of ASLR.

But how can we compare performances if results are random? Take the minimum?

No! You must never (ever again) use the minimum for benchmarking! Compute the
average and some statistics like the standard deviation::

    $ python3
    Python 3.4.3
    >>> timings=[0.198, 0.202, 0.199, 0.207, 0.200, 0.201]
    >>> import statistics
    >>> statistics.mean(timings)
    0.2011666666666667
    >>> statistics.stdev(timings)
    0.0031885210782848245

On this example, the average is 201 ms +/- 3 ms. IMHO the standard deviation is
quite small (reliable) which means that my benchmark is stable. To get a good
distribution, it's better to have many samples. It looks like at least 25
processes are needed. Each process tests a different memory layout and a
different hash function.

Result of 5 runs, each run uses 25 processes (ASLR enabled, random hash
function):

* Average: 205.2 ms +/- 3.0 ms (min: 201.1 ms, max: 214.9 ms)
* Average: 205.6 ms +/- 3.3 ms (min: 201.4 ms, max: 216.5 ms)
* Average: 206.0 ms +/- 3.9 ms (min: 201.1 ms, max: 215.3 ms)
* Average: 205.7 ms +/- 3.6 ms (min: 201.5 ms, max: 217.8 ms)
* Average: 206.4 ms +/- 3.5 ms (min: 201.9 ms, max: 214.9 ms)

While memory layout and hash functions are random again, the result looks
*less* random, and so more reliable, than before!

With ASLR enabled, the effect of the environment variables, command line and
current directory is negligible on the (average) result.


The average solves issues with uniform random noises
====================================================

The user will run the application with default system settings which means
ASLR enabled and Python hash function randomized. Running a benchmark in one
specific environment is a mistake because it is not representative of the
performance in practice.

Computing the average and standard deviation "fixes" the issue with hash
randomization. It's much better to use random hash functions and compute the
average, than using a fixed hash function (setting ``PYTHONHASHSEED`` variable
to a value).

Oh wow, already 3 big articles explaing how to get stable benchmarks. Please
tell me that it was the last one!  Nope, more is coming...


Annex: why only -n1?
====================

In this article, I ran ``bm_call_simple.py`` with ``-n 1`` with only run one
iteration.

Usually, a single iteration is not reliable at all, at least 50 iterations are
needed. But thanks to system tuning, compilation with PGO, ASRL disabled and
``PYTHONHASHSEED`` set, a single iteration is enough.

Example of 3 runs, each with 3 iterations::

    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.201
    0.201
    0.201
    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.201
    0.201
    0.201
    $ taskset -c 1 env -i PYTHONHASHSEED=3 ./python bm_call_simple.py
    0.201
    0.201
    0.201

Always the same timing!
