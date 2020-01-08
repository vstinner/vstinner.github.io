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
Python competitive <https://lwn.net/Articles/723752/#723949>`_ (LWN article).

At EuroPython 2019, Basel, I gave a keynote "Python Performance: Past, Present
and Future": `slides
<https://github.com/vstinner/talks/blob/master/2019-EuroPython/python_performance.pdf>`__
and `video
<https://www.youtube.com/watch?v=T6vC_LOHBJ4&feature=youtu.be&t=1875>`__.  I
gave my vision on the Python performance and lists 3 projects to speedup Python:

* subinterpreters: see Eric Snow's `multi-core-python
  <https://github.com/ericsnowcurrently/multi-core-python/>`_ project
* better C API: see `HPy (new C API) <https://github.com/pyhandle/hpy>`_
  and `pythoncapi.readthedocs.io <https://pythoncapi.readthedocs.io/>`_
* tracing garbage collector for CPython

This article is about the first project: subinterpreters.

Subinterpreters
===============

Eric Snow is working on subinterpreters since 2015, see his first blog post
published in September 2016: `Solving Multi-Core Python
<http://ericsnowcurrently.blogspot.com/2016/09/solving-mutli-core-python.html>`_.
See Eric Snow's `multi-core-python project wiki
<https://github.com/ericsnowcurrently/multi-core-python/wiki>_` for the whole
history.

In September 2017, he wrote a concrete proposal: `PEP 554: Multiple
Interpreters in the Stdlib <https://www.python.org/dev/peps/pep-0554/>`_.

Eric mentions the `PEP 432: Simplifying the CPython startup sequence
<https://www.python.org/dev/peps/pep-0432/>`_ as one blocker issue. I fixed
this issue (at least for the subinterpreters case) with my `PEP 587: Python
Initialization Configuration <https://www.python.org/dev/peps/pep-0587/>`_ that
I implemented in Python 3.8.

Sadly, implementing subinterpreters in the 30 years old CPython project is hard
since a lot of code has to be updated. CPython is 605K lines of C code and 818K
lines of Python code.

At a sprint during Pycon US 2018, I discussed with Eric Snow and Nick Coghlan
about subinterpreters. I draw an overview of Python internals and the different
"states":

.. image:: {static}/images/subinterpreters1.jpg
   :alt: Python Subinterpreters

Creation and finalization of Python and a subinterpreter:

.. image:: {static}/images/subinterpreters2.jpg
   :alt: Python Subinterpreters

I wrote `Reorganize Python “runtime”
<https://pythoncapi.readthedocs.io/runtime.html>`_ as a follow-up of this
meeting to write down the current state and what should be done.

Getting the current Python thread state
=======================================

In the current master branch of Python, getting the current Python thread state
is done using these two macros::

    #define _PyRuntimeState_GetThreadState(runtime) \
        ((PyThreadState*)_Py_atomic_load_relaxed(&(runtime)->gilstate.tstate_current))

    #define _PyThreadState_GET() _PyRuntimeState_GetThreadState(&_PyRuntime)

These macros depend on the global ``_PyRuntime`` variable: instance of the
``_PyRuntimeState`` structure.

``_Py_atomic_load_relaxed()`` uses an atomic operation which can be an issue in
term of efficiency. I tried to check if it uses an atomic read instruction, but
it seems like only a write uses an explicit memory fence operation: read seems
to be "free". I checked the x86-64 machine code. Maybe it's different on other
architectures.

GIL state
=========

Currently, the ``_PyRuntimeState`` structure has a ``gilstate`` field which is
shared between all subinterpreters. The long term goal of the PEP 554
(subinterpreters) is to have one GIL per subinterpeters to execute multiple
interpreters in **parallel**. Currently, only one interpreter can be at the
same time: there is no parallelism, except if a thread releases the GIL.

It is an old issue, tracked by:

* `Make the PyGILState API compatible with multiple interpreters
  <https://bugs.python.org/issue10915>`_
* `Support subinterpreters in the GIL state API
  <https://bugs.python.org/issue15751>`_

I expect that fixing this issue will require to add a lock somewhere which can
hurt performances, depending on how the GIL state is accessed. At least,
APIs and some structures have to be changed.

Passing a state to internal function calls
==========================================

To avoid any risk of performance penality but also to make things more
explicitly, I proposed to pass explicitly a "state" to internal C function
calls.

It seems like everybody agreed that Python internal functions should depend
less on an implicit global state, but the state should be passed as a parameter
instead. But first, we didn't agree on which state should be passed:
_PyRuntimeState, PyThreadState, a structure or something else?

It was unclear how to get the runtime from PyThreadState, or how to get runtime
from PyThreadState.

I started to pass _PyRuntimeState to some functions: `Pass _PyRuntimeState as
an argument rather than using the _PyRuntime global variable
<https://bugs.python.org/issue36710>`_.

Then to pass PyThreadState to some other functions: `Pass explicitly tstate to
function calls <https://bugs.python.org/issue38644>`_.

Thread: `python-dev: Pass the Python thread state to internal C functions
<https://mail.python.org/archives/list/python-dev@python.org/thread/PQBGECVGVYFTVDLBYURLCXA3T7IPEHHO/#Q4IPXMQIM5YRLZLHADUGSUT4ZLXQ6MYY>`_.

Related work
============

* `GC operates out of global runtime state.
  <https://bugs.python.org/issue36854>`_
* `new_interpreter() should reuse more Py_InitializeFromConfig() code
  <https://bugs.python.org/issue38858>`_
* `Replace Py_FatalError() with regular Python exceptions
  <https://bugs.python.org/issue38631>`_
