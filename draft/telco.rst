+++++++++++++++++++++++++++++++++++++++++++
Analyze why the telco benchmark is unstable
+++++++++++++++++++++++++++++++++++++++++++

I started to work on stabilizing benchmarks when people started to complain
that Python benchmarks are not reliable in the `Python Issue 21955#: ceval.c:
implement fast path for integers with a single digit
<https://bugs.python.org/issue21955>`.

I really decided to stop writing optimization patches when I worked on my
FASTCALL branch: `[WIP] Add a new _PyObject_FastCall() function which avoids
the creation of a tuple or dict for arguments
<http://bugs.python.org/issue26814>`_. I completely failed to get reliable
benchmark results and so I was no more able to decide if my patch makes Python
faster or slower. In short, benchmark results said: both, faster *and* slower!

I chose to analyze the telco benchmark because it is less trivial than
microbenchmarks like call_simple. telco is a benchmark for the Python `decimal
module <https://docs.python.org/dev/library/decimal.html>`_ ("Decimal fixed
point and floating point arithmetic").

All benchmarks will be run using CPU isolation in this article.


Original benchmark
==================

xxx

Unstable.


Analyze hash randomization
==========================

xxx

No effect.

ASLR
====

xxx

The telco benchmark result is impacted by the exact memory addresses. From the
point of view of a benchmark, ASLR allows to hide the "noise" of the memory
layout.

The problem with the memory layout is that as a programmer, it's hard to
control it. The compiler link order is not really deterministic, but LTO
helps.

PGO compilation duplicates hot functions to move them in a special ELF section,
but keep a regular version of the functions called "cold".

The memory address of data also depends on many parameters like the command
line, environment variables, etc.

