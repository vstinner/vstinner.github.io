++++++++++++++++++++++++++++++++++++++++
My journey to stable benchmark, part xxx
++++++++++++++++++++++++++++++++++++++++

:date: 2016-05-23 23:50
:tags: optimization, benchmark
:category: python
:slug: journey-to-stable-benchmark-xxx
:authors: Victor Stinner
:summary: My journey to stable benchmark, part xxx

Sources of "noise" when running a Python microbenchmark
=======================================================

Tools:

* timeit => broken
* perf => partially broken
* isolcpus.py: configure Linux

Sources of noise:

* Use the minimum: this is just plain wrong. It's not easy to explain,
  but using the minimum can only lead to false conclusion about the performance
  of a patched Python. Use the average *and* check the standard deviation
  (stdev).

* Random minor difference between two runs:
  PYTHONHASHSEED, already handled by perf.py. Easy to reproduce using two
  different PYTHONHASHSEED values.

* Random temporary performance slow-down:
  CPU Turbo Mode (maybe also HyperThreading)

* Environment variables, command line, current working directory, etc.
  Any tiny change in the environment changes the "memory layout", the exact
  address of objects. On microbenchmarks, it has a real impact, and the effect
  is constant.

