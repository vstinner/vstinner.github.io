+++++++++++++++++++++++++++++++++++++++
Pass the Python thread state explicitly
+++++++++++++++++++++++++++++++++++++++

:date: 2020-01-08 15:00
:tags: cpython
:category: python
:slug: cpython-pass-tstate
:authors: Victor Stinner

Keeping Python competitive
==========================

I'm trying to find ways to make Python more efficient for many years, see for
example my discussion at the Language Summit during Pycon US 2017: `Keeping
Python competitive <https://lwn.net/Articles/723949/>`_ (LWN article); `slides
<https://github.com/vstinner/talks/blob/master/2017-PyconUS/summit.pdf>`_.
At EuroPython 2019 (Basel), I gave the keynote "Python Performance: Past,
Present and Future": `slides
<https://github.com/vstinner/talks/blob/master/2019-EuroPython/python_performance.pdf>`__
and `video
<https://www.youtube.com/watch?v=T6vC_LOHBJ4&feature=youtu.be&t=1875>`__.  I
gave my vision on the Python performance and listed 3 projects to speedup
Python that I consider as realistic:

* subinterpreters: see Eric Snow's `multi-core-python
  <https://github.com/ericsnowcurrently/multi-core-python/>`_ project
* better C API: see `HPy (new C API) <https://github.com/pyhandle/hpy>`_
  and `pythoncapi.readthedocs.io <https://pythoncapi.readthedocs.io/>`_
* tracing garbage collector for CPython

.. image:: {static}/images/capi.jpg
   :alt: Python C API

This article is about **subinterpreters**.

Subinterpreters
===============

Eric Snow is working on subinterpreters since 2015, see his first blog post
published in September 2016: `Solving Multi-Core Python
<http://ericsnowcurrently.blogspot.com/2016/09/solving-mutli-core-python.html>`_.
See Eric Snow's `multi-core-python project wiki
<https://github.com/ericsnowcurrently/multi-core-python/wiki>`_ for the whole
history.

In September 2017, he wrote a concrete proposal: `PEP 554: Multiple
Interpreters in the Stdlib <https://www.python.org/dev/peps/pep-0554/>`_.

Eric mentions the `PEP 432: Simplifying the CPython startup sequence
<https://www.python.org/dev/peps/pep-0432/>`_ as one blocker issue. I fixed
this issue (at least for the subinterpreters case) with my `PEP 587: Python
Initialization Configuration <https://www.python.org/dev/peps/pep-0587/>`_ that
I implemented in Python 3.8.

Sadly, implementing subinterpreters in the 30 years old CPython project is hard
since a lot of code has to be updated. CPython is made of not less than **603K
lines of C code** (and 815K lines of Python code)!

In May 2018, at CPython sprint during Pycon US, I discussed subinterpreters
with Eric Snow and Nick Coghlan. I draw an overview of Python internals and the
different "states" on a whiteboard:

.. image:: {static}/images/subinterpreters2.jpg
   :alt: Python states

Python and Python subinterpreter lifecycles (creation and finalization):

.. image:: {static}/images/subinterpreters1.jpg
   :alt: Python subinterpreter lifecycle

As a follow-up of this meeting, I wrote down the current state and what should
be done: `Reorganize Python “runtime”
<https://pythoncapi.readthedocs.io/runtime.html>`_.

Getting the current Python thread state
=======================================

In the current master branch of Python, getting the current Python thread state
is done using these two macros::

    #define _PyRuntimeState_GetThreadState(runtime) \
        ((PyThreadState*)_Py_atomic_load_relaxed(&(runtime)->gilstate.tstate_current))

    #define _PyThreadState_GET() _PyRuntimeState_GetThreadState(&_PyRuntime)

These macros depend on the global ``_PyRuntime`` variable: instance of the
``_PyRuntimeState`` structure. There is exactly one instance of
``_PyRuntimeState``: data shared by all interpreters on purpose (more info
about ``_PyRuntimeState`` below).

``_Py_atomic_load_relaxed()`` uses an atomic operation which may become an
performance issue if Python is modified to get the Python thread state in more
places. I tried to check if it uses a slow atomic read instruction, but it
seems like only a write uses an explicit memory fence operation: read seems to
be "free" (it's a regular efficient ``MOV`` instruction). I only checked the
x86-64 machine code, it may be different on other architectures.


GIL state
=========

Currently, the ``_PyRuntimeState`` structure has a ``gilstate`` field which is
shared between all subinterpreters. The long term goal of the PEP 554
(subinterpreters) is to **have one GIL per subinterpeters** to **execute
multiple interpreters in parallel**. Currently, only one interpreter can be
executed at the same time: there is no parallelism, except if a thread releases
the GIL which is not the common case.

It's tracked by these two issues:

* `Make the PyGILState API compatible with multiple interpreters
  <https://bugs.python.org/issue10915>`_
* `Support subinterpreters in the GIL state API
  <https://bugs.python.org/issue15751>`_

I expect that fixing this issue may require to add a lock somewhere which **can
hurt performances**, depending on how the GIL state is accessed.


Passing a state to internal function calls
==========================================

To avoid any risk of performance penality with incoming Python internal changes
for subinterpreters, but also to make things more explicit, I proposed to
**pass explicitly "a state" to internal C function calls**.

First, it wasn't obvious which "state" should be passed: ``_PyRuntimeState``,
``PyThreadState``, a structure containing both, or something else?

Moreover, it was unclear how to get the runtime from ``PyThreadState``, and how
to get ``PyThreadState`` from runtime?

I started to **pass runtime to some functions** (``_PyRuntimeState``): `Pass
_PyRuntimeState as an argument rather than using the _PyRuntime global variable
<https://bugs.python.org/issue36710>`_.

Then I pushed more changes to **pass tstate to some other functions**
(``PyThreadState``): `Pass explicitly tstate to function calls
<https://bugs.python.org/issue38644>`_.

I added ``PyInterpreterState.runtime`` so getting ``_PyRuntimeState`` from
``PyThreadState`` is now done using: ``tstate->interp->runtime``. It's no
longer needed to pass ``runtime`` **and** ``tstate`` to internal functions:
``tstate`` is enough.

Slowly, I modified the internals to only pass ``tstate`` to internal functions:
**tstate should become the root object to access all Python states**.

I ended with a thread on the python-dev mailing list to summarize this work:
`Pass the Python thread state to internal C functions
<https://mail.python.org/archives/list/python-dev@python.org/thread/PQBGECVGVYFTVDLBYURLCXA3T7IPEHHO/#Q4IPXMQIM5YRLZLHADUGSUT4ZLXQ6MYY>`_.
The feedback was quite positive, most core developers agreed that passing
explicitly tstate is a good practice and the work should be continued.


_PyRuntimeState and PyInterpreterState
======================================

Currently, some ``_PyRuntimeState`` fields are shared by all interperters,
whereas they should be moved into ``PyInterpreterState``: it's still a work in
progress.

For example, I continued the work started by Eric Snow to move the garbage
collector state from ``_PyRuntimeState`` to ``PyInterpreterState``: `GC
operates out of global runtime state.  <https://bugs.python.org/issue36854>`_.

As explained above, another example is ``gilstate`` that should also be moved
to ``PyInterpreterState``, but that's a complex change that should be well
prepared to not break anything.


More subinterpreter work
========================

Implementing subinterpreters also requires to cleanup various parts of Python
internals.

For example, I modified Python so Py_NewInterpreter() and Py_EndInterpreter()
(create and finalize a subinterpreter) share more code with Py_Initialize()
and Py_Finalize() (create and finalize the **main** interpreter):
`new_interpreter() should reuse more Py_InitializeFromConfig() code
<https://bugs.python.org/issue38858>`_.

They are still many issues to be fixed: **it's moving slowly but steadily!**
