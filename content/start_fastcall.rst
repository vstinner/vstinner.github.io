+++++++++++++++++++++++++++++++++
The start of the FASTCALL project
+++++++++++++++++++++++++++++++++

:date: 2017-02-16 17:00
:tags: fastcall, optimization, cpython
:category: python
:slug: start-fastcall-project
:authors: Victor Stinner

False start
===========

In April 2016, I experimented a Python change to avoid temporary tuple to call
functions. Builtin functions were between 20 and 50% faster!

Sadly, some benchmarks were randomy slower. It will take me four months to
understand why!

Work on benchmarks
==================

During four months, I worked on making benchmarks more stable. See my previous
blog posts:

* `My journey to stable benchmark, part 1 (system)
  <{filename}/stable_benchmark_system.rst>`_ (May 21, 2016)
* `My journey to stable benchmark, part 2 (deadcode)
  <{filename}/stable_benchmark_deadcode.rst>`_ (May 22, 2016)
* `My journey to stable benchmark, part 3 (average)
  <{filename}/stable_benchmark_average.rst>`_ (May 23, 2016)
* `Visualize the system noise using perf and CPU isolation
  <{filename}/perf_visualize_system_noise.rst>`_ (June 16, 2016)
* `Intel CPUs: P-state, C-state, Turbo Boost, CPU frequency, etc.
  <{filename}/intel_cpus.rst>`_ (July 15, 2015)
* `Intel CPUs (part 2): Turbo Boost, temperature, frequency and Pstate C0 bug
  <{filename}/intel_cpus_part2.rst>`_
  (September 23, 2016)
* `Analysis of a Python performance issue
  <{filename}/analysis_python_performance_issue.rst>`_
  (November 19, 2016)
* ...

See my talk `How to run a stable benchmark
<https://fosdem.org/2017/schedule/event/python_stable_benchmark/>`_ that I gave
at FOSDEM 2017 (Brussels, Belgium): slides + video. I listed all the issues
that I had to get reliable benchmarks.


Ask for permission
==================

August 2016, I
confirmed that my change didn't introduce any slowndown. So I asked for the
permission on the python-dev mailing list to start pushing changes: `New
calling convention to avoid temporarily tuples when calling functions
<https://mail.python.org/pipermail/python-dev/2016-August/145793.html>`_.

Guido van Rossum asked me for benchmark results:

    But is there a performance improvement?

Benchmark results
=================

On micro-benchmarks, FASTCALL is much faster:

* ``getattr(1, "real")`` becomes **44%** faster
* ``list(filter(lambda x: x, list(range(1000))))`` becomes **31%** faster
* ``namedtuple.attr`` (read the attribute) becomes **23%** faster
* ...

Full results:

* `FASTCALL compared to Python 3.6 (default branch)
  <https://bugs.python.org/issue26814#msg263999>`_
* `2.7 / 3.4 / 3.5 / 3.6 / 3.6 FASTCALL comparison
  <https://bugs.python.org/issue26814#msg264003>`_

On the `CPython benchmark suite
<https://bugs.python.org/issue26814#msg266359>`_, I also saw many faster
benchmarks:

* pickle_list: **1.29x faster**
* etree_generate: **1.22x faster**
* pickle_dict: **1.19x faster**
* etree_process: **1.16x faster**
* mako_v2: **1.13x faster**
* telco: **1.09x faster**
* ...

Replies to my email
===================

I got two very positive replies, so I understood that it was ok.

Brett Canon:

    I just wanted to say I'm excited about this and I'm glad someone is taking
    advantage of what Argument Clinic allows for and what I know Larry had
    initially hoped AC would make happen!

Yury Selivanov:

    Exceptional results, congrats Victor. Will be happy to help with code
    review.


Real start
==========

That's how the FASTCALL began for real! I started to push a long serie of
patches adding new private functions and then modify code to call these new
functions.
