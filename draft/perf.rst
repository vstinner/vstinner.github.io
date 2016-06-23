telco.py
========

It looks like the first 5 samples must be treated as warmup. The difference
between each run is low::

    $ python3 telco.py --json-file=telco.json
    .........................
    Average: 26.9 ms +- 0.1 ms (25 runs x 3 samples)

    $ python3 -m perf -v telco.json
    Metadata:
    - aslr: enabled
    - cpu_count: 4
    - cpu_model_name: Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
    - date: 2016-06-09T16:07:45
    - platform: Linux-4.4.9-300.fc23.x86_64-x86_64-with-fedora-23-Twenty_Three
    - python_executable: /usr/bin/python3
    - python_implementation: cpython
    - python_version: 3.4.3

    Run 1/25: warmup (5): 44.4 ms, 36.4 ms, 31.9 ms, 28.9 ms, 26.8 ms; samples (3): 26.6 ms, 26.5 ms, 26.6 ms
    Run 2/25: warmup (5): 44.7 ms, 36.9 ms, 32.2 ms, 29.1 ms, 27.0 ms; samples (3): 27.0 ms, 26.9 ms, 26.9 ms
    Run 3/25: warmup (5): 40.4 ms, 31.6 ms, 28.5 ms, 26.8 ms, 26.7 ms; samples (3): 26.9 ms, 26.9 ms, 26.8 ms
    Run 4/25: warmup (5): 42.8 ms, 35.6 ms, 31.5 ms, 28.4 ms, 26.8 ms; samples (3): 26.9 ms, 26.8 ms, 26.8 ms
    Run 5/25: warmup (5): 44.2 ms, 33.7 ms, 29.7 ms, 27.3 ms, 26.8 ms; samples (3): 26.8 ms, 26.8 ms, 26.8 ms
    Run 6/25: warmup (5): 42.7 ms, 33.5 ms, 28.7 ms, 26.8 ms, 26.8 ms; samples (3): 26.9 ms, 26.8 ms, 26.8 ms
    Run 7/25: warmup (5): 40.7 ms, 31.3 ms, 28.4 ms, 26.8 ms, 26.8 ms; samples (3): 26.8 ms, 26.9 ms, 26.9 ms
    Run 8/25: warmup (5): 37.4 ms, 31.0 ms, 27.8 ms, 26.9 ms, 27.0 ms; samples (3): 26.9 ms, 27.0 ms, 27.0 ms
    Run 9/25: warmup (5): 37.9 ms, 30.9 ms, 28.0 ms, 26.9 ms, 27.0 ms; samples (3): 27.0 ms, 27.0 ms, 26.8 ms
    Run 10/25: warmup (5): 42.7 ms, 31.8 ms, 29.1 ms, 27.0 ms, 26.7 ms; samples (3): 27.0 ms, 26.9 ms, 26.9 ms
    Run 11/25: warmup (5): 27.1 ms, 26.9 ms, 26.9 ms, 27.0 ms, 27.0 ms; samples (3): 26.9 ms, 26.8 ms, 27.0 ms
    Run 12/25: warmup (5): 44.5 ms, 34.7 ms, 30.7 ms, 27.8 ms, 26.7 ms; samples (3): 26.9 ms, 26.9 ms, 26.9 ms
    Run 13/25: warmup (5): 41.7 ms, 32.2 ms, 28.8 ms, 26.9 ms, 26.8 ms; samples (3): 26.8 ms, 26.8 ms, 26.8 ms
    Run 14/25: warmup (5): 43.1 ms, 33.3 ms, 29.7 ms, 27.5 ms, 27.0 ms; samples (3): 26.9 ms, 27.0 ms, 26.9 ms
    Run 15/25: warmup (5): 41.7 ms, 31.5 ms, 28.4 ms, 26.9 ms, 26.9 ms; samples (3): 26.7 ms, 26.9 ms, 26.8 ms
    Run 16/25: warmup (5): 46.5 ms, 38.4 ms, 33.2 ms, 29.8 ms, 27.4 ms; samples (3): 27.0 ms, 26.9 ms, 27.0 ms
    Run 17/25: warmup (5): 44.8 ms, 34.4 ms, 30.6 ms, 27.9 ms, 27.1 ms; samples (3): 27.0 ms, 27.0 ms, 27.0 ms
    Run 18/25: warmup (5): 44.0 ms, 36.3 ms, 31.5 ms, 28.6 ms, 27.0 ms; samples (3): 26.9 ms, 26.8 ms, 26.9 ms
    Run 19/25: warmup (5): 38.5 ms, 28.2 ms, 26.8 ms, 26.8 ms, 26.9 ms; samples (3): 26.9 ms, 26.7 ms, 26.9 ms
    Run 20/25: warmup (5): 35.5 ms, 30.0 ms, 27.9 ms, 27.4 ms, 27.3 ms; samples (3): 27.2 ms, 27.3 ms, 27.3 ms
    Run 21/25: warmup (5): 41.4 ms, 34.1 ms, 30.9 ms, 28.0 ms, 26.8 ms; samples (3): 26.8 ms, 26.8 ms, 26.9 ms
    Run 22/25: warmup (5): 27.3 ms, 26.9 ms, 26.9 ms, 26.6 ms, 26.9 ms; samples (3): 26.8 ms, 26.8 ms, 26.6 ms
    Run 23/25: warmup (5): 34.6 ms, 30.0 ms, 27.5 ms, 26.8 ms, 26.8 ms; samples (3): 26.7 ms, 26.7 ms, 26.7 ms
    Run 24/25: warmup (5): 46.2 ms, 38.2 ms, 33.0 ms, 29.5 ms, 27.2 ms; samples (3): 26.8 ms, 26.7 ms, 26.7 ms
    Run 25/25: warmup (5): 44.8 ms, 35.6 ms, 31.2 ms, 28.3 ms, 26.7 ms; samples (3): 26.9 ms, 26.7 ms, 26.8 ms

    Average: 26.9 ms +- 0.1 ms (min: 26.5 ms, max: 27.3 ms) (25 runs x 3 samples; 5 warmups)


call_simple
===========

CPU isolation helps: 3 samples have the same timing. But each run has a
different performance because of ASLR and Python randomized hash::

    $ python3 performance/bm_call_simple.py --json-file=call_simple.json
    .........................
    Average: 329 ms +- 3 ms (25 runs x 3 samples x 20 loops)

    $ python3 -m perf -v call_simple.json
    Metadata:
    - aslr: enabled
    - cpu_count: 4
    - cpu_model_name: Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
    - date: 2016-06-09T16:54:53
    - platform: Linux-4.4.9-300.fc23.x86_64-x86_64-with-fedora-23-Twenty_Three
    - python_executable: /usr/bin/python3
    - python_implementation: cpython
    - python_version: 3.4.3

    Run 1/25: warmup (1): 335 ms; samples (3): 328 ms, 328 ms, 328 ms
    Run 2/25: warmup (1): 356 ms; samples (3): 330 ms, 330 ms, 330 ms
    Run 3/25: warmup (1): 356 ms; samples (3): 328 ms, 328 ms, 328 ms
    Run 4/25: warmup (1): 349 ms; samples (3): 327 ms, 327 ms, 327 ms
    Run 5/25: warmup (1): 340 ms; samples (3): 330 ms, 330 ms, 330 ms
    Run 6/25: warmup (1): 360 ms; samples (3): 327 ms, 327 ms, 327 ms
    Run 7/25: warmup (1): 359 ms; samples (3): 327 ms, 327 ms, 327 ms
    Run 8/25: warmup (1): 349 ms; samples (3): 326 ms, 326 ms, 326 ms
    Run 9/25: warmup (1): 347 ms; samples (3): 329 ms, 329 ms, 329 ms
    Run 10/25: warmup (1): 347 ms; samples (3): 327 ms, 327 ms, 327 ms
    Run 11/25: warmup (1): 346 ms; samples (3): 329 ms, 328 ms, 328 ms
    Run 12/25: warmup (1): 335 ms; samples (3): 327 ms, 327 ms, 327 ms
    Run 13/25: warmup (1): 336 ms; samples (3): 327 ms, 327 ms, 327 ms
    Run 14/25: warmup (1): 338 ms; samples (3): 329 ms, 329 ms, 329 ms
    Run 15/25: warmup (1): 330 ms; samples (3): 327 ms, 327 ms, 327 ms
    Run 16/25: warmup (1): 337 ms; samples (3): 330 ms, 330 ms, 330 ms
    Run 17/25: warmup (1): 342 ms; samples (3): 329 ms, 329 ms, 329 ms
    Run 18/25: warmup (1): 358 ms; samples (3): 333 ms, 333 ms, 333 ms
    Run 19/25: warmup (1): 343 ms; samples (3): 328 ms, 328 ms, 328 ms
    Run 20/25: warmup (1): 336 ms; samples (3): 328 ms, 328 ms, 328 ms
    Run 21/25: warmup (1): 364 ms; samples (3): 338 ms, 338 ms, 338 ms
    Run 22/25: warmup (1): 356 ms; samples (3): 331 ms, 331 ms, 331 ms
    Run 23/25: warmup (1): 354 ms; samples (3): 326 ms, 326 ms, 326 ms
    Run 24/25: warmup (1): 345 ms; samples (3): 328 ms, 328 ms, 328 ms
    Run 25/25: warmup (1): 355 ms; samples (3): 330 ms, 330 ms, 330 ms

    Average: 329 ms +- 3 ms (min: 326 ms, max: 338 ms) (25 runs x 3 samples x 20 loops; 1 warmup)




Effect of ASLR and hash randomization
=====================================

::

    haypo@smithers$ python3 performance/bm_call_simple.py -w 2 -n 1 -p 100 --json-file=json
    ....................................................................................................
    Average: 330 ms +- 6 ms (100 runs x 1 sample x 20 loops)


    $ python3
    Python 3.4.3 (default, Mar 31 2016, 20:42:37)
    >>> import perf, collections
    >>> result = perf.Results.from_json(open("json").read())

    Statistics on first sample:

    >>> collections.Counter([int(run.samples[0]*1e3) for run in result.runs])
    Counter({326: 22, 327: 17, 325: 15, 329: 10, 328: 9, 336: 7, 330: 5, 337: 4, 338: 3, 341: 3, 352: 2, 340: 1, 344: 1, 345: 1})

    >>> samples=[]
    >>> for run in result.runs: samples.extend(run.samples)
    ...
    >>> perf.mean(samples)*1e3
    330.1833630000101
    >>> perf.stdev(samples)*1e3
    5.852616629494851
    >>> statistics.variance(samples)*1e3
    0.034253121411839664
