++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Fast call: A new calling convention for the Python C API (history)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-12-15 16:00
:tags: optimization, python
:category: python
:slug: python-fast-call-history
:authors: Victor Stinner


Caching tuples for function calls
=================================

Globally, CPython has a basic design: compile source to bytecode, very basic
optimizations on the bytecode, run the bytecode. But CPython is full of
efficient and interesting optimizations.

To call a function, the C API of Python requires a Python tuple object to pass
positional arguments, and a Python dictionary object for keyword parameters (if
any).


pickle (1997)
=============

Caching a tuple for arguments is a very old optimization technic. It was first
used in 1997, Python 1.5, by Guido van Rossum in the newly created cPickle
module (`commit fd3626511dad
<https://hg.python.org/cpython/rev/fd3626511dad>`_).

The tuple is cached in a pickler object::

    typedef struct
    {
      PyObject_HEAD
      ...
      PyObject *arg;
      ...
    } Picklerobject;

Example showing how *arg* is used in ``write_other()`` (simplified code)::

  UNLESS(self->arg)
    UNLESS(self->arg = PyTuple_New(1))
    { ... }

  if (PyTuple_SetItem(self->arg, 0, py_str) == -1)
  { ... }

  Py_INCREF(py_str);
  UNLESS(junk = PyObject_CallObject(self->write, self->arg))
  { ...  }

where ``UNLESS()`` is the following macro::

    #define UNLESS(E) if (!(E))

A tuple of 1 element is created if ``self->arg`` is not set yet (``NULL``).
Then, the element of the tuple is replaced. The tuple is used to pass arguments
when calling the ``self->write`` function.


3.0 comment
-----------

In Python 3.0, the code was deeply refactored (`commit 0ae50aa7d97c
<https://hg.python.org/cpython/rev/0ae50aa7d97c>`_). A new helper function was
added with an interesting comment::

    /* A temporary cleaner API for fast single argument function call.

       XXX: Does caching the argument tuple provides any real performance benefits?

       A quick benchmark, on a 2.0GHz Athlon64 3200+ running Linux 2.6.24 with
       glibc 2.7, tells me that it takes roughly 20,000,000 PyTuple_New(1) calls
       when the tuple is retrieved from the freelist (i.e, call PyTuple_New() then
       immediately DECREF it) and 1,200,000 calls when allocating brand new tuples
       (i.e, call PyTuple_New() and store the returned value in an array), to save
       one second (wall clock time). Either ways, the loading time a pickle stream
       large enough to generate this number of calls would be massively
       overwhelmed by other factors, like I/O throughput, the GC traversal and
       object allocation overhead. So, I really doubt these functions provide any
       real benefits.

       On the other hand, oprofile reports that pickle spends a lot of time in
       these functions. But, that is probably more related to the function call
       overhead, than the argument tuple allocation.

       XXX: And, what is the reference behavior of these? Steal, borrow? At first
       glance, it seems to steal the reference of 'arg' and borrow the reference
       of 'func'. */
    static PyObject *
    _Pickler_FastCall(PicklerObject *self, PyObject *func, PyObject *arg)
    { ... }


itertools (2003)
================

In Python 2.3.0 (released in 2003), Raymond Hettinger added a new new itertools
module. The implementation of the module used a cached tuple for the
itertools.izip() generator. The optimization was also added to the enumerate()
generator.

When the itertools module was merged into Python 2.3, in the development
branch, it used a cached tuple for itertools.imap() generator, but the cache
was removed before 2.3.0 in the `commit 59ae41e04ffb
<https://hg.python.org/cpython/rev/59ae41e04ffb>`_: "Eliminated tuple re-use in
imap(). Doing it correctly made the code too hard to read."

In Python 2.7, the itertools uses a cached tuple for the following generators:

* itertools.combinations()
* itertools.combinations_with_replacement()
* itertools.izip()
* itertools.permutations()
* itertools.product()


Pycon US 2014
=============

In 2014 during a lunch at Pycon, Larry Hasting told me that he would like to
get rid of temporary tuples to call functions in Python. In Python, positional
arguments are passed as a tuple to C functions: ``PyObject *args``.

Larry wrote `Argument Clinic <https://docs.python.org/dev/howto/clinic.html>`_
which gives more control on how C functions are called. But I guess that Larry
didn't have time to finish his implementation, since he didn't publish a patch.


Issues with cached tuples
=========================

If the cached tuple is not cleared after the function call, the object is
kept alive longer than expected.

If items of the cached tuple are set to ``NULL``, ``gc.get_objects()`` can
expose the private tuple and manipulating the special tuple can crash.

A workaround is to untrack the tuple from the garbage collector.


pickle: fast-call removed from Python 3.4
-----------------------------------------

The optimization was removed from Python 3.4 by the `commit dd51b72cfb52
<https://hg.python.org/cpython/rev/dd51b72cfb52>`_. Commit message::

    Remove the tuple reuse optimization in _Pickle_FastCall.

    I have noticed a race-condition occurring on one of the buildbots because of
    this optimization. The function called may release the GIL which means
    multiple threads may end up accessing the shared tuple. I could fix it up by
    storing the tuple to the Pickler and Unipickler object again, but honestly it
    really not worth the trouble.

    I ran many benchmarks and the only time the optimization helps is when using a
    fin-memory file, like io.BytesIO on which reads are super cheap, combined with
    pickle protocol less than 4. Even in this contrived case, the speedup is a
    about 5%. For everything else, this optimization does not provide any
    noticable improvements.

property get issues
-------------------

At the end of 2014, Joe Jevnik created the `cnamedtuple
<https://pypi.python.org/pypi/cnamedtuple>`_ project: collections.namedtuple
implemented in C. At 2015-04-10, he opened the issue `C implementation of
namedtuple (WIP) <http://bugs.python.org/issue23910>`_ to propose to merge his
C code into the stdlib.

Raymond Hettinger moved the discussion to the performance of getting an
attribute from a namedtuple. The discussion moved to optimizing
property_descr_get(), and then it became even more specific about the tuple
used to pass arguments to PyObject_CallFunctionObjArgs().

Raymond proposed to cache a tuple of one element before calls to avoid the cost
of the tuple creation (and then destruction).

Raymond suggested to ensure that the reference counter is 1.

At 2015-04-10, Joe Jevnik proposed to optimize property_descr_get() by caching
the tuple of 1 item in a static C variable: issue: `property_descr_get reuse
argument tuple <http://bugs.python.org/issue23910>`_, `commit 661cdbd617b8
<https://hg.python.org/cpython/rev/661cdbd617b8>`_.

2015-05-24: `Correct reuse argument tuple in property descriptor
<http://bugs.python.org/issue24276>`_. Bug found while working on the C
implementation of functools.lru_cache. First fix.

2016-04-21: `Crash when iterating on gc.get_objects()
<http://bugs.python.org/issue26811>`_. Second fix.

