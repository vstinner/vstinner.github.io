++++++++++++++++++
Benchmark glitches
++++++++++++++++++

BUG REPORT: https://bugzilla.redhat.com/show_bug.cgi?id=1378529

JSON
====

* CPU speed: 2.7 GHz => 3.4 GHz

Start date: 2016-09-15T22:34:39
*   cpu_freq: 1=3400 MHz, 2=2226 MHz, 3=2740 MHz, 5=2440 MHz, 6=2221 MHz, 7=2549 MHz

CPU speed changed at 2016-09-16T16:28:57

*  cpu_freq: 1-3,5=3400 MHz, 6=3365 MHz, 7=3360 MHz

Bug seen at 2016-09-16T22:03:38

* CPU 2: fast, 11.0 ms
  cpu_freq: 2=3400 MHz
* CPU 3: slow, 20.3 ms
  cpu_freq: 3=3400 MHz


Temperature
===========

pgo_1.json .. xx: between 69°C and 72°C
pgo_seed_5.json:
  Run 1..105: between 69°C and 72°C
  Run 106..400: 69°C => 58°C

Cpu bug: ~54°C


Glitch 1
========

When trying to understand the impact of PGO on benchmarking, I noticed a major glitch.
My test was:

* compile Python with PGO
* train Python PGO using bm_call_simple.py
* run bm_call_simple.py

The test was repeated 5 times to check if the benchmarks were stable or not.

First I used 120 samples for bm_call_simple: the benchmark took 1 minute.
After my 3rd change, I chose to run the benchmark lager: 1200 samples which takes 10 minutes.

* Try 1
* Try 2: unset MAKEFLAGS
* Try 3: isolated process used to train the compiler
* Try 4: 1200 samples instead of only 120
* Try 5: LTO <=== GLITCH occurred here!

Config:

* PGO compilation
* 6 CPUs isolated (total: 8 logical CPUs)
* NOHZ full configured on these CPUs

Once, a benchmark becomes 2x FASTER. WTF? ::

    $ python3 -m perf show pgo_seed_[1-5].json|grep ms
    Median +- std dev: 20.6 ms +- 0.1 ms
    Median +- std dev: 20.5 ms +- 0.1 ms
    Median +- std dev: 19.9 ms +- 0.1 ms
    Median +- std dev: 20.4 ms +- 0.1 ms
    Median +- std dev: 11.0 ms +- 4.1 ms

Analyze of the 5th compilation::

    $ python3 -m perf dump pgo_seed_5.json --quiet|less
    Run 1: samples (3): 20.4 ms (+86%), 20.4 ms (+86%), 20.4 ms (+86%)
    Run 2: samples (3): 20.7 ms (+88%), 20.7 ms (+88%), 20.7 ms (+88%)
    Run 3: samples (3): 20.3 ms (+85%), 20.3 ms (+85%), 20.3 ms (+85%)
    Run 4: samples (3): 20.3 ms (+85%), 20.3 ms (+85%), 20.3 ms (+85%)
    ... (similar timings)
    Run 103: samples (3): 20.3 ms (+85%), 20.3 ms (+85%), 20.3 ms (+85%)
    Run 104: samples (3): 20.3 ms (+85%), 20.3 ms (+85%), 20.3 ms (+85%)
    Run 105: samples (3): 20.3 ms (+85%), 20.3 ms (+85%), 20.3 ms (+85%)
    Run 106: samples (3): 11.0 ms, 11.0 ms, 11.0 ms
    Run 107: samples (3): 11.2 ms, 11.2 ms, 11.2 ms
    Run 108: samples (3): 11.1 ms, 11.1 ms, 11.1 ms
    ... (similar timings)
    Run 398: samples (3): 11.0 ms, 11.0 ms, 11.0 ms
    Run 399: samples (3): 10.9 ms, 10.8 ms, 10.9 ms
    Run 400: samples (3): 10.8 ms, 10.8 ms, 10.8 ms

Something occurred at run 106! Let's see metadata::

    $ python3 -m perf dump pgo_seed_5.json --verbose|less

    Metadata:
      aslr: Full randomization
      cpu_affinity: 1-3,5-7 (isolated)
      cpu_config: 1-3,5-7=driver:intel_pstate, intel_pstate:no turbo, governor:performance
      cpu_count: 8
      cpu_model_name: Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
      description: Test the performance of simple Python-to-Python function calls
      hostname: smithers
      inner_loops: 20
      loops: 1
      name: call_simple
      perf_version: 0.7.9
      platform: Linux-4.7.2-201.fc24.x86_64-x86_64-with-fedora-24-Twenty_Four
      python_cflags: -Wno-unused-result -Wsign-compare -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes
      python_executable: /home/haypo/prog/python/ref_bench/python
      python_hash_seed: 0
      python_implementation: cpython
      python_version: 3.7.0a0 (64-bit)
      timer: clock_gettime(CLOCK_MONOTONIC), resolution: 1.00 ns

    (...)
    Run 105: warmup (1): 20.3 ms (+85%); samples (3): 20.3 ms (+85%), 20.3 ms (+85%), 20.3 ms (+85%)
      cpu_freq: 1,7=3400 MHz, 2=2855 MHz, 3=2772 MHz, 5=3136 MHz, 6=2868 MHz
      cpu_temp: coretemp:Physical id 0=71 C, coretemp:Core 0=66 C, coretemp:Core 1=71 C, coretemp:Core 2=67 C, coretemp:Core 3=68 C
      date: 2016-09-16T16:28:56
      duration: 1.6 sec
      load_avg_1min: 1.58
      mem_max_rss: 11.1 MB
      runnable_threads: 1
    Run 106: warmup (1): 13.3 ms (+22%); samples (3): 11.0 ms, 11.0 ms, 11.0 ms
      cpu_freq: 1-3,5=3400 MHz, 6=3365 MHz, 7=3360 MHz
      cpu_temp: coretemp:Physical id 0=68 C, coretemp:Core 0=62 C, coretemp:Core 1=68 C, coretemp:Core 2=59 C, coretemp:Core 3=59 C
      date: 2016-09-16T16:28:57
      duration: 930 ms
      load_avg_1min: 1.58
      mem_max_rss: 11.2 MB
      runnable_threads: 1
    (...)

By analyzing more data, I noticed that load_avg_1min changed::

    $ python3 -m perf dump pgo_seed_5.json -v|grep load_avg|less
      load_avg_1min: 1.25
      (...)
      load_avg_1min: 1.15
      (...)
      load_avg_1min: 1.07
      (...)
  load_avg_1min: 1.10
(...)
  load_avg_1min: 1.31
(...)
  load_avg_1min: 1.30
  load_avg_1min: 1.35
  load_avg_1min: 1.35
  load_avg_1min: 1.35
  load_avg_1min: 1.65
  load_avg_1min: 1.65
  load_avg_1min: 1.65
  load_avg_1min: 1.59
  load_avg_1min: 1.59
  load_avg_1min: 1.55
  load_avg_1min: 1.55
  load_avg_1min: 1.55
  load_avg_1min: 1.58
  load_avg_1min: 1.58
  load_avg_1min: 1.58
  load_avg_1min: 1.58
  load_avg_1min: 1.62
  load_avg_1min: 1.62
  load_avg_1min: 1.62
  load_avg_1min: 1.62
  load_avg_1min: 1.62
  load_avg_1min: 1.62
  load_avg_1min: 1.57
  load_avg_1min: 1.57
  load_avg_1min: 1.57
  load_avg_1min: 1.57
  load_avg_1min: 1.57
  load_avg_1min: 1.52
  load_avg_1min: 1.52
  load_avg_1min: 1.52
  load_avg_1min: 1.52
  load_avg_1min: 1.52
  load_avg_1min: 1.48
  load_avg_1min: 1.48
  load_avg_1min: 1.48
  load_avg_1min: 1.48
(...)
  load_avg_1min: 1.41
  load_avg_1min: 1.37
  load_avg_1min: 1.37
  load_avg_1min: 1.37
  load_avg_1min: 1.37
  load_avg_1min: 1.37
  load_avg_1min: 1.34
  load_avg_1min: 1.34
  load_avg_1min: 1.34
  load_avg_1min: 1.34
  load_avg_1min: 1.34
  load_avg_1min: 1.34
  load_avg_1min: 1.31
  load_avg_1min: 1.31
  load_avg_1min: 1.31
  load_avg_1min: 1.31
  load_avg_1min: 1.31
  load_avg_1min: 1.29
  load_avg_1min: 1.29
  load_avg_1min: 1.29
  load_avg_1min: 1.29
  load_avg_1min: 1.29
  load_avg_1min: 1.27
  load_avg_1min: 1.27
  load_avg_1min: 1.27
  load_avg_1min: 1.27
  load_avg_1min: 1.27
  load_avg_1min: 1.27
  load_avg_1min: 1.24
  load_avg_1min: 1.24
  load_avg_1min: 1.24
  load_avg_1min: 1.24
  load_avg_1min: 1.24
(...)
  load_avg_1min: 1.17
  load_avg_1min: 1.16
  load_avg_1min: 1.16
  load_avg_1min: 1.16
  load_avg_1min: 1.16
  load_avg_1min: 1.16
  load_avg_1min: 1.15
  load_avg_1min: 1.15
  load_avg_1min: 1.15
  load_avg_1min: 1.15
  load_avg_1min: 1.15
  load_avg_1min: 1.13
  load_avg_1min: 1.13
  load_avg_1min: 1.13
  load_avg_1min: 1.13
  load_avg_1min: 1.13
(...)
  load_avg_1min: 1.01
  load_avg_1min: 1.01
  load_avg_1min: 1.01
  load_avg_1min: 1.01
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.00
  load_avg_1min: 1.08
  load_avg_1min: 1.08
  load_avg_1min: 1.08
  load_avg_1min: 1.08
  load_avg_1min: 1.08
  load_avg_1min: 1.08
  load_avg_1min: 1.08
  load_avg_1min: 1.08
  load_avg_1min: 1.08





For the first 100 runs, the temparature of the CPU package was between 69°C and
71°C, but mostly at least 70°C. For some reasons, the temperature decreased to 68°C at the run 106 and
then slowly decreased until 57°C (last run, run 400).

I noticed that one CPU was 2x slower::

    $ python3 -m perf show cpu_bug2.json
    Median +- std dev: 11.0 ms +- 0.2 ms
    $ python3 -m perf show cpu_bug3.json
    Median +- std dev: 20.3 ms +- 0.2 ms

Full metadata::

    haypo@smithers$ python3 -m perf show --metadata cpu_bug2.json
    Metadata:
    - aslr: Full randomization
    - cpu_affinity: 2 (isolated)
    - cpu_config: 2=driver:intel_pstate, intel_pstate:no turbo, governor:performance, nohz_full
    - cpu_count: 8
    - cpu_freq: 2=3400 MHz
    - cpu_model_name: Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
    - description: Test the performance of simple Python-to-Python function calls
    - hostname: smithers
    - inner_loops: 20
    - loops: 1
    - name: call_simple
    - perf_version: 0.7.9
    - platform: Linux-4.7.2-201.fc24.x86_64-x86_64-with-fedora-24-Twenty_Four
    - python_cflags: -Wno-unused-result -Wsign-compare -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes
    - python_executable: /home/haypo/prog/python/ref_bench/python
    - python_hash_seed: 0
    - python_implementation: cpython
    - python_version: 3.7.0a0 (64-bit)
    - runnable_threads: 1
    - timer: clock_gettime(CLOCK_MONOTONIC), resolution: 1.00 ns

    Median +- std dev: 11.0 ms +- 0.2 ms

    haypo@smithers$ python3 -m perf show --metadata cpu_bug3.json
    Metadata:
    - aslr: Full randomization
    - cpu_affinity: 3 (isolated)
    - cpu_config: 3=driver:intel_pstate, intel_pstate:no turbo, governor:performance, nohz_full
    - cpu_count: 8
    - cpu_freq: 3=3400 MHz
    - cpu_model_name: Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz
    - description: Test the performance of simple Python-to-Python function calls
    - hostname: smithers
    - inner_loops: 20
    - loops: 1
    - name: call_simple
    - perf_version: 0.7.9
    - platform: Linux-4.7.2-201.fc24.x86_64-x86_64-with-fedora-24-Twenty_Four
    - python_cflags: -Wno-unused-result -Wsign-compare -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes
    - python_executable: /home/haypo/prog/python/ref_bench/python
    - python_hash_seed: 0
    - python_implementation: cpython
    - python_version: 3.7.0a0 (64-bit)
    - runnable_threads: 1
    - timer: clock_gettime(CLOCK_MONOTONIC), resolution: 1.00 ns

    Median +- std dev: 20.3 ms +- 0.2 ms

