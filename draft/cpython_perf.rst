+++++++++++++++++++
CPython performance
+++++++++++++++++++

perf module
===========

* new system module: replace my old isolcpus.py script. Better output, better
  error reporting, give advices, support acpi-cpufreq CPU driver
  (speed-python).
* use a pipe to return the benchmark suite to the master process, stdout and
  stderr are no more used.
* 0.8.3 optimization: run the Python profiler, remove the Metadata class, don't
  store timestamps as datetime.datetime objects but string. Conversion to
  datetime.datetime is now only done by the get_dates() method. Optimize
  add_run(): don't recompute common metadata at each call, but update existing
  common metadata

performance
===========

* Many issues with the venv command: all of them should be fixed now. The
  creation of the venv now ensures that the pip command works, or download
  and install pip if needed. Should help to support Linux distributions which
  don't provide ensurepip or provide a broken ensurepip module.
* Automatically switch between "pip" and "python -m pip"

speed.python.org
================

* peformance: new scripts/ directory with two fully automated scripts to run benchmarks:

  * tune the system
  * update the Mercurial repository
  * update the repository to the specified branch, or even revision
  * get the revision properties: branch, date
  * compile Python: PGO and LTO are configurable options
  * run benchmarks
  * store benchmark into a JSON, filename created with the date, branch,
    revision and an optional name.
  * upload results to speed.python.org

* First issue: python_startup slowdown, http://bugs.python.org/issue28637
  Fixed by modifying the site module to not import the re module: https://hg.python.org/cpython/rev/a822818ec74e

* regex_compile slowdown, http://bugs.python.org/issue28082#msg280836
  Median +- std dev: [71c1970f27b6] 388 ms +- 3 ms -> [3cf248d10bed] 470 ms +- 4 ms: 1.21x slower

* call_method: 70% slowdown, http://bugs.python.org/issue28618
  Hot functions marked with __attribute__((hot))

pymicrobench
============

xxx
