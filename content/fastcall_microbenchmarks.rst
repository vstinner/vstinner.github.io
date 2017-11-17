++++++++++++++++++++++++
FASTCALL microbenchmarks
++++++++++++++++++++++++

:date: 2017-02-24 22:00
:tags: fastcall, optimization, cpython
:category: python
:slug: fastcall-microbenchmarks
:authors: Victor Stinner

For my FASTCALL project (CPython optimization avoiding temporary tuples and
dictionaries to pass arguments), I wrote many short microbenchmarks. I grouped
them into a new Git repository: `pymicrobench
<https://github.com/vstinner/pymicrobench>`_.  Benchmark results are required by
CPython developers to prove that an optimization is worth it. It's not uncommon
that I abandon a change because the speedup is not significant, makes CPython
slower, or because the change is too complex. Last 12 months, I counted that I
abandonned 9 optimization issues, rejected for different reasons, on a total of
46 optimization issues.

This article gives Python 3.7 results of these microbenchmarks compared to
Python 3.5 (before FASTCALL). I ignored 3 microbenchmarks which are between 2%
and 5% slower: the code was not optimized and the result is not signifiant
(less than 10% on a *microbenchmark* is not significant).

On results below, the speedup is between 1.11x faster (-10%) and 1.92x faster
(-48%). It's not easy to isolate the speedup of only FASTCALL. Since Python
3.5, Python 3.7 got many other optimizations.

Using FASTCALL gives a speedup around 20 ns: measured on a patch to use
FASTCALL.  It's not a lot, but many builtin functions take less than 100 ns, so
20 ns is significant in practice! Avoiding a tuple to pass positional arguments
is interesting, but FASTCALL also allows further internal optimizations.

Microbenchmark on calling builtin functions:

+--------------------------------------------+---------+------------------------------+
| Benchmark                                  | 3.5     | 3.7                          |
+============================================+=========+==============================+
| struct.pack("i", 1)                        | 105 ns  | 77.6 ns: 1.36x faster (-26%) |
+--------------------------------------------+---------+------------------------------+
| getattr(1, "real")                         | 79.4 ns | 64.4 ns: 1.23x faster (-19%) |
+--------------------------------------------+---------+------------------------------+

Microbenchmark on calling methods of builtin types:

+--------------------------------------------+---------+------------------------------+
| Benchmark                                  | 3.5     | 3.7                          |
+============================================+=========+==============================+
| {1: 2}.get(7, None)                        | 84.9 ns | 61.6 ns: 1.38x faster (-27%) |
+--------------------------------------------+---------+------------------------------+
| collections.deque([None]).index(None)      | 116 ns  | 87.0 ns: 1.33x faster (-25%) |
+--------------------------------------------+---------+------------------------------+
| {1: 2}.get(1)                              | 79.4 ns | 59.6 ns: 1.33x faster (-25%) |
+--------------------------------------------+---------+------------------------------+
| "a".replace("x", "y")                      | 134 ns  | 101 ns: 1.33x faster (-25%)  |
+--------------------------------------------+---------+------------------------------+
| b"".decode()                               | 71.5 ns | 54.5 ns: 1.31x faster (-24%) |
+--------------------------------------------+---------+------------------------------+
| b"".decode("ascii")                        | 99.1 ns | 75.7 ns: 1.31x faster (-24%) |
+--------------------------------------------+---------+------------------------------+
| collections.deque.rotate(1)                | 106 ns  | 82.8 ns: 1.28x faster (-22%) |
+--------------------------------------------+---------+------------------------------+
| collections.deque.insert()                 | 778 ns  | 608 ns: 1.28x faster (-22%)  |
+--------------------------------------------+---------+------------------------------+
| b"".join((b"hello", b"world") * 100)       | 4.02 us | 3.32 us: 1.21x faster (-17%) |
+--------------------------------------------+---------+------------------------------+
| [0].count(0)                               | 53.9 ns | 46.3 ns: 1.16x faster (-14%) |
+--------------------------------------------+---------+------------------------------+
| collections.deque.rotate()                 | 72.6 ns | 63.1 ns: 1.15x faster (-13%) |
+--------------------------------------------+---------+------------------------------+
| b"".join((b"hello", b"world"))             | 102 ns  | 89.8 ns: 1.13x faster (-12%) |
+--------------------------------------------+---------+------------------------------+

Microbenchmark on builtin functions calling Python functions (callbacks):

+--------------------------------------------+---------+------------------------------+
| Benchmark                                  | 3.5     | 3.7                          |
+============================================+=========+==============================+
| map(lambda x: x, list(range(1000)))        | 76.1 us | 61.1 us: 1.25x faster (-20%) |
+--------------------------------------------+---------+------------------------------+
| sorted(list(range(1000)), key=lambda x: x) | 90.2 us | 78.2 us: 1.15x faster (-13%) |
+--------------------------------------------+---------+------------------------------+
| filter(lambda x: x, list(range(1000)))     | 81.8 us | 73.4 us: 1.11x faster (-10%) |
+--------------------------------------------+---------+------------------------------+

Microbenchmark on calling slots (``__getitem__``, ``__init__``, ``__int__``)
implemented in Python:

+--------------------------------------------+---------+------------------------------+
| Benchmark                                  | 3.5     | 3.7                          |
+============================================+=========+==============================+
| Python __getitem__: obj[0]                 | 167 ns  | 87.0 ns: 1.92x faster (-48%) |
+--------------------------------------------+---------+------------------------------+
| call_pyinit_kw1                            | 348 ns  | 240 ns: 1.45x faster (-31%)  |
+--------------------------------------------+---------+------------------------------+
| call_pyinit_kw5                            | 564 ns  | 401 ns: 1.41x faster (-29%)  |
+--------------------------------------------+---------+------------------------------+
| call_pyinit_kw10                           | 960 ns  | 734 ns: 1.31x faster (-24%)  |
+--------------------------------------------+---------+------------------------------+
| Python __int__: int(obj)                   | 241 ns  | 207 ns: 1.16x faster (-14%)  |
+--------------------------------------------+---------+------------------------------+

Microbenchmark on calling a method descriptor (static method):

+--------------------------------------------+---------+------------------------------+
| Benchmark                                  | 3.5     | 3.7                          |
+============================================+=========+==============================+
| int.to_bytes(1, 4, "little")               | 177 ns  | 103 ns: 1.72x faster (-42%)  |
+--------------------------------------------+---------+------------------------------+

Benchmarks were run on ``speed-python``, server used to run CPython benchmarks.

