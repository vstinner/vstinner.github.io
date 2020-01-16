+++++++++++++++++++++++++++
Python 3.7 Development Mode
+++++++++++++++++++++++++++

:date: 2020-01-16 12:00
:tags: cpython
:category: python
:slug: python37-dev-mode
:authors: Victor Stinner

This article describes the discussion on the design of the `development mode
(-X dev) <https://docs.python.org/dev/using/cmdline.html#id5>`_ that I **added
to Python 3.7** and how it has been implemented.

The development mode enables runtime checks which are too expensive to be
enabled by default. It can be enabled by ``python3 -X dev`` command line option
or by ``PYTHONDEVMODE=1`` environment variable.  It helps developers to spot
bugs in their code and helps them to be prepared for future Python changes.

.. image:: {static}/images/ready_to_race.jpg
   :alt: Ready to race
   :target: https://twitter.com/guinoir/status/1217146968029331456

*Ready to race, by Guillaume Singelin.*


Email sent to python-ideas
==========================

In March 2016, I proposed `Add a developer mode to Python: -X dev command line
option
<https://mail.python.org/pipermail/python-ideas/2016-March/039314.html>`__ on
the python-ideas list:

    When I develop on CPython, I'm always building Python in debug mode
    using ``./configure --with-pydebug``. This mode enables a **lot** of extra
    checks which helps me to detect bugs earlier. The debug mode makes Python
    much slower and so is not enabled by default.

    I propose to add a "development mode" to Python, to get a few checks
    to detect bugs earlier: a new ``-X dev`` command line option. Example::

       python3.6 -X dev script.py

    I propose to enable:

    * Show ``DeprecationWarning`` and ``ResourceWarning warnings``: ``python -Wd``
    * Show ``BytesWarning`` warning: ``python -b``
    * Enable Python assertions (``assert``) and set ``__debug__`` to True:
      remove (or just ignore) ``-O`` or ``-OO`` command line arguments
    * faulthandler to get a Python traceback on segfault and fatal errors:
      ``python -X faulthandler``
    * Debug hooks on Python memory allocators: ``PYTHONMALLOC=debug``

I wrote an implementation of this development mode using ``exec()``. **Ronald
Oussoren** `commented my patch <https://bugs.python.org/issue26670#msg262659>`_:

    Why does this patch execv() the interpreter to set options? I'd expect it
    to be possible to get the same result by updating the argument parsing code
    in Py_Main.

More on that later :-) **Marc-Andre Lemburg** `didn't buy the idea
<https://mail.python.org/pipermail/python-ideas/2016-March/039325.html>`_:

    **I'm not sure whether this would make things easier for the
    majority of developers**, e.g. someone not writing C extensions
    would likely not be interested in debugging memory allocations
    or segfaults, someone spending more time on numerics wouldn't
    bother with bytes warnings, etc.

Opinion shared by **Ethan Furman**, so I gave up at this point, closed my issue
and my PR.


async keyword, DeprecationWarning and PEP 565
=============================================

At November 1, 2017, Ned Deily, the Python 3.7 release release,
sent an email to python-dev: `Reminder: 12 weeks to 3.7 feature code cutoff
<https://mail.python.org/pipermail/python-dev/2017-November/150061.html>`_.

A discussion started on ``async`` and ``await`` becoming keywords and how this
incompatible change was conducted. Read LWN article `Who should see Python
deprecation warnings?  <https://lwn.net/Articles/740804/>`_ (December 2017) by
Jonathan Corbet for the whole story:

     In early November, one sub-thread of a big discussion on preparing for the
     Python 3.7 release focused on the await and async identifiers. They will
     become keywords in 3.7, meaning that any code using those names for any
     other purpose will break. Nick Coghlan observed that **Python 3.6 does not
     warn** about the use of those names, calling it "a fairly major
     oversight/bug". **In truth, though, Python 3.6 does emit warnings in that
     case — but users rarely see them.**

The question is who should see ``DeprecationWarning``. Long time ago, it has
been decided to hide them by default to not bother users. Users are not able to
fix them, and so it is only a source of annoyance.

If the warning is displayed by default, developers can be annoyed by warnings
coming from code that they cannot easily fix, like third-party dependencies.

At November 12, 2017, Nick Coghlan proposed `PEP 565: Show DeprecationWarning
in __main__ <https://www.python.org/dev/peps/pep-0565/>`_ as a compromise:

    This change will mean that code entered at the interactive prompt and code
    in single file scripts will revert to reporting these warnings by default,
    while they will **continue to be silenced by default for packaged code**
    distributed as part of an importable module.

The PEP has been approved and implemented in Python 3.7. For example,
``DeprecationWarning`` is now displayed by default when running a script and in
the REPL::

    $ cat example.py
    import imp

    $ python3 example.py
    example.py:1: DeprecationWarning: the imp module is deprecated ...
      import imp

    $ python3
    Python 3.7.6 (default, Dec 19 2019, 22:52:49)
    >>> import imp
    __main__:1: DeprecationWarning: the imp module is deprecated ...


Development mode proposed on python-dev
=======================================

I was not convinced that only displaying warnings in the ``__main__`` module is
enough to help developers to fix issues in their code. A project is way larger
than just this module.

I came back with my idea, now on the python-dev list: `Add a developer mode to
Python: -X dev command line option
<https://mail.python.org/pipermail/python-dev/2017-November/150514.html>`__.

This mode shows ``DeprecationWarning`` and ``ResourceWarning`` is all modules,
not only in the ``__main__`` module.  In my opinion, having an opt-in mode for
developers is the best option. Python should not spam users with warnings which
are targeting developers.

**In the context of Python 3.7 incompatible changes, the feedback was way better
this time.**


Issues with the Python initialization
=====================================

When I proposed the idea, my plan was to call exec() to replace the current
process with a new process. But when I tried to implement it, it was more
tricky than expected. My first blocker issue was to remove ``-O`` option from
the command line. I hate having to parse the command line: it is very fragile
and it's too easy to make mistake.

So I tried to write a clean implementation: configure Python properly in
"development mode". The first blocker issue was to implement
``PYTHONMALLOC=debug``.  The C code to read and apply the Python configuration
used Python objects before the Python initialization even started. For example,
``-W`` and ``-X`` options were stored as Python lists. It means that the Python
memory allocator was used before Python would be able to parse ``PYTHONMALLOC``
environment variable.

Moreover, the Python configuration is quite complex. Many options are
inter-dependent. For example, the ``-E`` command line option ignores
environment variables with a name staring with ``PYTHON``: like
``PYTHONMALLOC``! Python has to parse the command line before being able to
handle ``PYTHONMALLOC``.

Python lists depends on the memory allocator which depends on ``PYTHONMALLOC``
environment variable which depends on the ``-E`` command line option which
depends on Python lists...

In short, **it wasn't possible to write a clean implementation of the
development mode without refactoring the Python initialization code**.


Refactoring main.c
==================

For all these reasons, I refactored Python initialization code in ``main.c``,
with `bpo-32030 <https://bugs.python.org/issue32030>`__ with two **large**
changes:

* `commit f7e5b56c
  <https://github.com/python/cpython/commit/f7e5b56c37eb859e225e886c79c5d742c567ee95>`__:
  bpo-32030: Split Py_Main() into subfunctions
* `commit a7368ac6
  <https://github.com/python/cpython/commit/a7368ac6360246b1ef7f8f152963c2362d272183>`__:
  bpo-32030: Enhance Py_Main()

Add -X dev option
=================

Since I got enough approval by my peers (core developers), I pushed `commit
ccb0442a
<https://github.com/python/cpython/commit/ccb0442a338066bf40fe417455e5a374e5238afb>`__
of `bpo-32043 <https://bugs.python.org/issue32043>`__ to add the ``-X dev``
command line option. Thanks to the previous refactoring, the implementation is
less intrusive.

Effects of the development mode:

* Add ``default`` warnings option. For example, display ``DeprecationWarning``
  and ``ResourceWarning`` warnings.
* Install `debug hooks on memory allocators
  <https://docs.python.org/dev/c-api/memory.html#c.PyMem_SetupDebugHooks>`_ as if
  ``PYTHONMALLOC`` is set to ``debug``.
* Enable my `faulthandler
  <https://docs.python.org/dev/library/faulthandler.html>`_ module to dump the
  Python traceback on a crash.


Add PYTHONDEVMODE environment variable
======================================

In a PR review, Antoine Pitrou `proposed
<https://github.com/python/cpython/pull/4478#pullrequestreview-77874230>`_:

    Speaking of which, perhaps it would be nice to set those environment
    variables so that child processes launched using subprocess inherit them?

I created `bpo-32101 <https://bugs.python.org/issue32101>`__ to add
``PYTHONDEVMODE`` environment variable: `commit 5e3806f8
<https://github.com/python/cpython/commit/5e3806f8cfd84722fc55d4299dc018ad9b0f8401>`__.

Setting ``PYTHONDEVMODE=1`` allows to also enable the development mode in
Python child processes, without having to touch their command line.


Enable asyncio debug mode
=========================

I created `bpo-32047: asyncio: enable debug mode when -X dev is used
<https://bugs.python.org/issue32047>`_ and `asked in the -X dev thread on
python-dev
<https://mail.python.org/pipermail/python-dev/2017-November/150572.html>`_:

    What do you think? Is it ok to include asyncio in the global "developer mode"?

Antoine Pitrou didn't like the idea because asyncio debug mode was "quite
expensive", but Yury Selivanov (one of the asyncio maintainers) and Barry
Warsaw liked the idea, so I merged my PR: `commit 44862df2
<https://github.com/python/cpython/commit/44862df2eeec62adea20672b0fe2a5d3e160569e>`__.

Antoine Pitrou created `bpo-31970: asyncio debug mode is very slow
<https://bugs.python.org/issue31970>`_. Hopefully, he found a way to make
asyncio debug mode more efficient by truncating tracebacks to 10 frames
(`commit 921e9432
<https://github.com/python/cpython/commit/921e9432a1461bbf312c9c6dcc2b916be6c05fa0>`__).


Fix warnings filters
====================

While checking warnings filters, I noticed that the development mode was hiding
some ResourceWarning warnings. I completed the documentation and fixed warnings
filters in `bpo-32089 <https://bugs.python.org/issue32089>`__.


Python 3.8 logs close() exception
=================================

By default, Python ignores silently ``EBADF`` error (bad file descriptor) which
can lead to a **severe crash** , `bpo-18748
<https://bugs.python.org/issue18748>`_ (simplified gdb traceback)::

    Program received signal SIGABRT, Aborted.
    [Switching to Thread 0xb7b0eb70 (LWP 17152)]
    0xb7fe1424 in __kernel_vsyscall ()
    (gdb) bt
    #0  0xb7fe1424 in __kernel_vsyscall ()
    #1  0xb7e4e941 in *__GI_raise (sig=6)
    #2  0xb7e51d72 in *__GI_abort ()
    #3  0xb7e8ae15 in __libc_message (do_abort=1, fmt=0xb7f606f5 "%s")
    #4  0xb7e8af44 in *__GI___libc_fatal (message=0xb7fc75ec
        "libgcc_s.so.1 must be installed for pthread_cancel to work\n")
    #5  0xb7fc4ffa in pthread_cancel_init ()
    #6  0xb7fc509d in _Unwind_ForcedUnwind (...)
    #7  0xb7fc2b98 in *__GI___pthread_unwind (buf=<optimized out>)
    #8  0xb7fbcce0 in __do_cancel () at pthreadP.h:265
    #9  __pthread_exit (value=0x0) at pthread_exit.c:30
    ...

Notice the ``"libgcc_s.so.1 must be installed for pthread_cancel to work"`` error
message: the glibc loads dynamically ``libgcc_s.so.1`` library when a thread
completes, but another thread closed its file descriptor!

The worst is that **the crash is not deterministic**: it's a **race condition**
which requires to try many times, even with an example designed to trigger the
crash!

Since the ``EBADF`` error is silently ignored, it is hard to notice or to debug
such issue. I modified the development mode in Python 3.8 to **log close()
exceptions in io.IOBase destructor**.

It was not accepted to always log the ``close()`` exception. So having an
opt-in development mode is a good practical compromise!


Python 3.9 checks encoding and errors
=====================================

In June 2019, my colleague **Miro Hrončok** reported `bpo-37388
<https://bugs.python.org/issue37388>`_:

    I was just bit by specifying an nonexisitng error handler for
    bytes.decode() without noticing.

    Consider this code::

        >>> 'a'.encode('cp1250').decode('utf-8', errors='Boom, Shaka Laka, Boom!')
        'a'

I modified the development mode in Python 3.9, to also check *encoding* and
*errors* arguments on string encoding and decoding operations, like
``bytes.decode()`` or ``str.encode()``.

By default, for best performance, the *errors* argument is only checked at the
first encoding/decoding error and the *encoding* argument is sometimes ignored
for empty strings.

Having an opt-in development mode allows to enable additional debug checks at
runtime, without having to care too much about the performance overhead.

Note: I love the choice of the example, "Boom, Shaka Laka, Boom!"
from the game Gruntz :-D


Development Mode Example
========================

Even in the ``__main__`` module with PEP 565, ``ResourceWarning`` is still not
displayed by default (PEP 565 only shows ``DeprecationWarning``)::

    $ python3 -c 'print(len(open("README.rst").readlines()))'
    39

The development mode shows the warning::

    $ python3 -X dev -c 'print(len(open("README.rst").readlines()))'
    -c:1: ResourceWarning: unclosed file <_io.TextIOWrapper name='README.rst' mode='r' encoding='UTF-8'>
    ResourceWarning: Enable tracemalloc to get the object allocation traceback
    39

Not closing a resource explicitly can leave a resource open for way longer than
expected. It can cause severe issues at Python exit. It is bad in CPython, but
it is even worse in PyPy. **Closing resources explicitly makes an application
more deterministic and more reliable.**

If one of the development mode effect causes an issue, it is still possible to
override most options. For example,
``PYTHONMALLOC=default python3 -X dev ...`` command enables the development
mode without installing debug hooks on memory allocators.
