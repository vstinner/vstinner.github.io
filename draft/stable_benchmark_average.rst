++++++++++++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part 3 (average)
++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-05-22 16:50
:tags: optimization, benchmark
:category: python
:slug: journey-to-stable-benchmark-average
:authors: Victor Stinner
:summary: My journey to stable benchmark, part 3 (average)

Python randomized hash function
===============================

On Python 3, the hash function is now randomized by default: `issue #13703
<http://bugs.python.org/issue13703>`_. The problem is that for a
microbenchmark, the number of hash collisions of an "hot" dictionary can cause
a non negligible difference in the benchmark

The ``PYTHONHASHSEED`` environment variable can be used to use a fixed hash
function. Example with different hash functions on the patched Python::

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

Result of the reference Python::

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

Note: I ran this microbenchmark with `system tuning
<{filename}/stable_benchmark_system.rst> (part 1)`_ on a `Python compiled with
PGO <{filename}/stable_benchmark_system.rst> (part 2)`_.

Minimums: ref=180 ms, patched=186 ms. The patched Python is 3% faster, yeah!

Wait. What is we only test PYTHONHASHSEED from 1 to 3? Minimums: patched=198
ms, ref=195 ms. The patched Python is now 2% slower.

Faster? Slower? Who is right?

Maybe we should write an algorithm to find a ``PYTHONHASHSEED`` value for which
our program is always faster? Would it be fair? Probably not ;-)


ASLR
====

When I started to work on removing the noise of the system, I read the advice:
disable `Address Space Layout Randomization (ASLR)
<https://en.wikipedia.org/wiki/Address_space_layout_randomization>`_.

I followed this advice without trying to understand it.

Example of command to see the effect of ASLR, the first number is the start
address of the heap memory::

    $ python -c 'import os; os.system("grep heap /proc/%s/maps" % os.getpid())'
    55e6a716c000-55e6a7235000 rw-p 00000000 00:00 0                          [heap]

Let's see the result of 6 runs:

* 55e6a716c000
* 561c218eb000
* 55e6f628f000
* 5617d2d89000
* 55faa3fc8000
* 555fbb16e000

Disable ASLR::

    sudo bash -c 'echo 0 >| /proc/sys/kernel/randomize_va_space'

When ASLR is disabled ::

    $ python -c 'import os; os.system("grep heap /proc/%s/maps" % os.getpid())'
    555555756000-55555581f000 rw-p 00000000 00:00 0                          [heap]
    $ python -c 'import os; os.system("grep heap /proc/%s/maps" % os.getpid())'
    555555756000-55555581f000 rw-p 00000000 00:00 0                          [heap]
    $ python -c 'import os; os.system("grep heap /proc/%s/maps" % os.getpid())'
    555555756000-55555581f000 rw-p 00000000 00:00 0                          [heap]

Note: To reenable ASLR, it's better to use the value 2::

    sudo bash -c 'echo 2 >| /proc/sys/kernel/randomize_va_space'


ASLR issue
==========

Ok, ASLR is disabled. Python hash function is now fixed. Great! The performance
is now perfect, right?

I noticed something very strange. The benchmark result depends on the current
directory::

    $ cd /home/haypo/prog/python/fastcall/pgo
    $ PYTHONHASHSEED=3 taskset -c 1 ./python  ../../benchmarks/performance/bm_call_simple.py -n 1
    0.214

    $ cd /home/haypo/prog/python/fastcall/pgo
    $ PYTHONHASHSEED=3 taskset -c 1 ./python  ../../benchmarks/performance/bm_call_simple.py -n 1
    0.214

    $ cd /home/haypo/prog/python/fastcall
    $ PYTHONHASHSEED=3 taskset -c 1 pgo/python  ../benchmarks/performance/bm_call_simple.py -n 1
    0.215

    $ cd /home/haypo/prog/python/benchmarks
    $ PYTHONHASHSEED=3 taskset -c 1 ../fastcall/pgo/python  ../benchmarks/performance/bm_call_simple.py -n 1
    0.203

    $ cd /home/haypo/prog/python
    $ PYTHONHASHSEED=3 taskset -c 1 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1
    0.200

The benchmark also depends on the environment variables::

    $ PYTHONHASHSEED=3 taskset -c 1 env -i fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1
    0.193
    $ PYTHONHASHSEED=3 taskset -c 1 env -i VAR1=1 VAR2=2 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1
    0.202
    $ PYTHONHASHSEED=3 taskset -c 1 env -i VAR1=1 VAR2=2 VAR3=3 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1
    0.214
    $ PYTHONHASHSEED=3 taskset -c 1 env -i VAR1=1 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1
    0.196

The benchmark also depends on the command line::

    $ PYTHONHASHSEED=3 taskset -c 1 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1
    0.201
    $ PYTHONHASHSEED=3 taskset -c 1 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1 arg1
    0.198
    $ PYTHONHASHSEED=3 taskset -c 1 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1 arg1 arg2 arg3
    0.203
    $ PYTHONHASHSEED=3 taskset -c 1 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1 arg1 arg2 arg3 arg4 arg5
    0.206
    $ PYTHONHASHSEED=3 taskset -c 1 fastcall/pgo/python  benchmarks/performance/bm_call_simple.py -n 1 arg1 arg2 arg3 arg4 arg5 arg6
    0.210

Note: the script ignores command line arguments.

Using ``strace`` and ``ltrace``, I saw the memory addresses are different.

But later I got *very* strange issues. I noticed that the output of the
benchmark depends on the command line!



Average and standard deviation
==============================

In fact, the problem is much more generic than just the hash function. They are
many other sources of noise which cannot be controlled.

Average: 195 ms, standard deviation: 11 ms.
