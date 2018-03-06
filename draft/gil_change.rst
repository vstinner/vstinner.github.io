+++++++++++++++++++++++++
The Python 3.7 GIL change
+++++++++++++++++++++++++

:date: 2018-03-06 16:00
:tags: cpython
:category: python
:slug: python37-gil-change
:authors: Victor Stinner


GIL change
==========

In March 2014, Steve Dower reported a bug when a "C thread" uses the Python C
API: "In Python 3.4rc3, calling PyGILState_Ensure() from a thread that was not
created by Python and without any calls to PyEval_InitThreads() will cause a
fatal exit: (...)".

I commented "IMO it's a bug in PyEval_InitThreads()."

In March 2016, I wrote a short C program to reproduce the bug and a fix.

In november 2017, Marcin Kasperski asked "Is this fix released? I can't find it
in the changelog…". Oops, I forgot to apply my fix.

Not only I applied my fix, but I also wrote an unit test.

    Ok, the bug is now fixed in Python 2.7, 3.6 and master (future 3.7). On 3.6
    and master, the fix comes with an unit test.

The fix::

    bpo-20891: Fix PyGILState_Ensure() (#4650)

    When PyGILState_Ensure() is called in a non-Python thread before
    PyEval_InitThreads(), only call PyEval_InitThreads() after calling
    PyThreadState_New() to fix a crash.

    Add an unit test in test_embed.

Everything was fine... until december 2017, when **random** failures were
spotted on macOS buildbots::

    macbook:master haypo$ while true; do ./Programs/_testembed bpo20891 ||break; date; done
    Lun  4 déc 2017 12:46:34 CET
    Lun  4 déc 2017 12:46:34 CET
    Lun  4 déc 2017 12:46:34 CET
    Fatal Python error: PyEval_SaveThread: NULL tstate

    Current thread 0x00007fffa5dff3c0 (most recent call first):
    Abort trap: 6

My analysis:

    I found a working fix: call PyEval_InitThreads() in
    PyThread_start_new_thread(). So the GIL is created as soon as a second
    thread is spawned. The GIL cannot be created anymore while two threads are
    running. At least, with the "python" binary. It doesn't fix the issue if a
    thread is not spawned by Python, but this thread calls PyGILState_Ensure().

Antoine Pitrou commented:

    Why not *always* call PyEval_InitThreads() at interpreter initialization?
    Are there any downsides?

I found the origin of the code creating the GIL "on demand"::

    commit 1984f1e1c6306d4e8073c28d2395638f80ea509b
    Author: Guido van Rossum <guido@python.org>
    Date:   Tue Aug 4 12:41:02 1992 +0000

        * Makefile adapted to changes below.
        * split pythonmain.c in two: most stuff goes to pythonrun.c, in the library.
        * new optional built-in threadmodule.c, build upon Sjoerd's thread.{c,h}.
        * new module from Sjoerd: mmmodule.c (dynamically loaded).
        * new module from Sjoerd: sv (svgen.py, svmodule.c.proto).
        * new files thread.{c,h} (from Sjoerd).
        * new xxmodule.c (example only).
        * myselect.h: bzero -> memset
        * select.c: bzero -> memset; removed global variable

    (...)

    +void
    +init_save_thread()
    +{
    +#ifdef USE_THREAD
    +       if (interpreter_lock)
    +               fatal("2nd call to init_save_thread");
    +       interpreter_lock = allocate_lock();
    +       acquire_lock(interpreter_lock, 1);
    +#endif
    +}
    +#endif

"I guess that the intent of dynamically created GIL is to reduce the "overhead"
of the GIL when 100% of the code is run in single thread."

Guido van Rossum:

    Yeah, the original reasoning was that threads were something esoteric and
    not used by most code, and at the time we definitely felt that always using
    the GIL would cause a (tiny) slowdown and increase the risk of crashes due
    to bugs in the GIL code. I'd be happy to learn that we no longer need to
    worry about this and can just always initialize it.

    (Note: I haven't read the entire thread, just the first and last message.)

Nick Coghlan:

    Victor, could you run your patch through the performance benchmarks?

I ran pyperformance on my PR 4700. Differences of at least 5%::

    haypo@speed-python$ python3 -m perf compare_to ~/json/uploaded/2017-12-18_12-29-master-bd6ec4d79e85.json.gz /home/haypo/json/patch/2017-12-18_12-29-master-bd6ec4d79e85-patch-4700.json.gz --table --min-speed=5

    +----------------------+--------------------------------------+-------------------------------------------------+
    | Benchmark            | 2017-12-18_12-29-master-bd6ec4d79e85 | 2017-12-18_12-29-master-bd6ec4d79e85-patch-4700 |
    +======================+======================================+=================================================+
    | pathlib              | 41.8 ms                              | 44.3 ms: 1.06x slower (+6%)                     |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | scimark_monte_carlo  | 197 ms                               | 210 ms: 1.07x slower (+7%)                      |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | spectral_norm        | 243 ms                               | 269 ms: 1.11x slower (+11%)                     |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | sqlite_synth         | 7.30 us                              | 8.13 us: 1.11x slower (+11%)                    |
    +----------------------+--------------------------------------+-------------------------------------------------+
    | unpickle_pure_python | 707 us                               | 796 us: 1.13x slower (+13%)                     |
    +----------------------+--------------------------------------+-------------------------------------------------+

    Not significant (55): 2to3; chameleon; chaos; (...)

I decided to skip the test which was failing randomly before going to holiday,
I didn't want to stress myself with having to take such major decision before
leaving. Modifying one of the most important key feature of Python (GIL) before
leaving is not a good idea.

At the end of january 2018, "I tested again these 5 benchmarks were Python was
slower with my PR. I ran these benchmarks manually on my laptop using CPU
isolation. Result::

    vstinner@apu$ python3 -m perf compare_to ref.json patch.json --table
    Not significant (5): unpickle_pure_python; sqlite_synth; spectral_norm; pathlib; scimark_monte_carlo

Ok, that was expected: no significant difference.

So I pushed the fix to master::

    New changeset 2914bb32e2adf8dff77c0ca58b33201bc94e398c by Victor Stinner in branch 'master':
    bpo-20891: Py_Initialize() now creates the GIL (#4700)
    https://github.com/python/cpython/commit/2914bb32e2adf8dff77c0ca58b33201bc94e398c

Antoine Pitrou considers that my PR 5421 for Python 3.6 should not be merged:

    I don't think so. People can already call PyEval_InitThreads.

I reenabled test_embed.test_bpo20891() on master but removed it from Python
3.6.

::

    bpo-20891: Skip test_embed.test_bpo20891() (#4967)

    Skip the test failing randomly because of known race condition.

    Skip the test to fix macOS buildbots until a decision is made on the
    proper fix for the race condition.

Note: Python 2.7 doesn't have test_embed.test_bpo20891() since it was more
complex to write such test for Python 2.7.



