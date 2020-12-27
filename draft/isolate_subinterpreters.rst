++++++++++++++++++++++
Python Subinterpreters
++++++++++++++++++++++

:date: 2020-12-27 12:00
:tags: cpython, subinterpreters
:category: cpython
:slug: isolate-subinterpreters
:authors: Victor Stinner

This article is about the work done in Python in 2019 and 2020 to better
isolate subinterpreters. Static types are converted to heap types, extension
modules are converted to use the new multiphase initialization API (PEP 489),
caches, states, singletons and free lists are made per-interpreter, many bugs
have been fixed, etc.

Running multiple interpreters in parallel with one "GIL" per interpreter cannot
be done yet, but a lot of complex technical challenges have been solved.

.. image:: {static}/images/christmas-gift.jpg
   :alt: Christmas gift.


Why isolating subinterpreters?
==============================

The final goal is to be able run multiple interpreters in parallel in the same
process, like one interpreter per CPU, each interpreter would run in its own
thread. The principle is the same than the multiprocessing module and has the
same limitations: no Python object can be shared directly between two
interpreters. Later, we can imagine helpers to share Python mutable objects
using proxies which would prevent race conditions.

The work on subinterpreter requires to modify many functions and extension
modules. It will benefit to Python in different ways.

Converting static types to heap types and convert extension modules to the
multiphase initialization API (PEP 489) makes extension modules implemented in
C to behave closer to modules implemented in Python, which is good for the `PEP
399 -- Pure Python/C Accelerator Module Compatibility Requirements
<https://www.python.org/dev/peps/pep-0399/>`__. So **this work also helps
Python implementations other than CPython, like PyPy**.

These changes also destroy more Python objects and release more memory at
Python exit which matters **when Python is embedded in an application**. Python
should be "state less", especially release all memory at exit. This work slowly
fix the `bpo-163574: Py_Finalize() doesn't clear all Python objects at exit
<https://bugs.python.org/issue1635741>`__. Python leaks less and less Python
objects at exit.


Proof-of-concept in May 2020
============================

In May 2020, I wrote a proof-of-concept to prove the feasability of the project
and to prove that it is faster than sequential execution: `PoC: Subinterpreters
4x faster than sequential execution or threads on CPU-bound workaround
<https://mail.python.org/archives/list/python-dev@python.org/thread/S5GZZCEREZLA2PEMTVFBCDM52H4JSENR/#RIK75U3ROEHWZL4VENQSQECB4F4GDELV>`_.
Benchmark on 4 CPUs:

* Sequential: 1.99 sec +- 0.01 sec
* Threads: 3.15 sec +- 0.97 sec (1.5x **slower**)
* Multiprocessing: 560 ms +- 12 ms (3.6x **faster**)
* Subinterpreters: 583 ms +- 7 ms (3.4x **faster**)

The performance of subintepreters is basically the same speed than
multiprocessing on this benchmark which is promising.


Experimental isolated subintepreters
====================================

To write this PoC, I added a ``--with-experimental-isolated-subinterpreters``
option to ``./configure`` in `bpo-40514 <https://bugs.python.org/issue40514>`_
which defines the ``EXPERIMENTAL_ISOLATED_SUBINTERPRETERS`` macro. Effects of
this special build:

* Make the GIL per-interpreter.
* ``_xxsubinterpreters.run_string()`` releases the GIL when running the
  subinterpreter.
* Add a thread local storage for the Python thread state ("tstate").
* Disable the garbage collector in subinterpreters.
* Disable the type attribute lookup cache.
* Disable free lists: frame, list, tuple, type attribute lookup cache.
* Disable singletons: latin1 characters.
* Disable interned strings.
* Disable the fast pymalloc memory allocator (force libc malloc memory
  allocator).

Features are disabled because their implementation is currently not compatible
with multiple interpreters running in parallel.

This special build is designed to be temporary. It should ease the development
of isolated subinterpreters. It will be removed once subinterpreters will be
fully isolated (once each interpreter will have its own GIL).


Convert static types to heap types
==================================

Types declared in Python (``class MyType: ...``) are always "heap types":
types dynamically allocated on the heap memory. Historically, all types
declared in C were declared as "static types": defined statically at build
time.

In C, static types are referenced directly using the using ``&`` operator to
get their address, they are not copied. For example, the Python ``str`` type is
referenced as ``&PyUnicode_Type`` in C.

Types are also regular objects (``PyTypeObject`` inherits from ``PyObject``)
and have a reference count, whereas the ``PyObject.ob_refcnt`` member is not
atomic and so must not be modified in parallel. Problem: all interpreters share
the same static types.  Static types have other problems:

* A type ``__mro__`` tuple (``PyTypeObject.tp_mro`` member) has the same
  problem of non-atomic reference count.
* When a subtype is created, it is stored in the ``PyTypeObject.tp_subclasses``
  dictionary member (accessible in Python with the ``__subclasses__()``
  method), whereas Python dictionaries are not thread-safe.
* Static types behave differently than regular Python types. For example,
  usually it is not possible to add an arbitrary attribute or override
  an attribute. It goes against the `PEP 399 -- Pure Python/C Accelerator
  Module Compatibility Requirements
  <https://www.python.org/dev/peps/pep-0399/>`__ principles.
* etc.

Right now, **43% (89/206)** of types are declared as heap types on a total of
206 types. For comparison, in Python 3.8, only 9% (15/172) of types were
declared as heap types: **74 types** have been converted in the meanwhile.

TODO: convert the remaining 117 static types: see `bpo-40077
<https://bugs.python.org/issue40077>`__.


Multiphase initialization API
=============================

Historically, extension modules are declared with the ``PyModule_Create()``
function. Usually, such extension can be instanciated exactly once. It is
stored in an internal ``PyInterpreterState.modules_by_index`` list; an unique
index is assigned to the module and stored in ``PyModuleDef.m_base.m_index``.
Usually, such extension use static global variables.

Such "static" extension has multiple issues:

* The extension cannot be unloaded: its memory is not released at Python exit.
  It is an issue when Python is embedded in an application.
* The extension behaves differently than modules defined in Python. When an
  extension is reimported, its namespace (``module.__dict__``) is duplicated,
  but mutable objects and static global variables are still shared. It goes
  against the `PEP 399 -- Pure Python/C Accelerator Module Compatibility
  Requirements <https://www.python.org/dev/peps/pep-0399/>`__ principles.
* etc.

In 2013, **Petr Viktorin**, **Stefan Behnel** and **Nick Coghlan** wrote the
`PEP 489 -- Multi-phase extension module initialization
<https://www.python.org/dev/peps/pep-0489/>`_ which has been approved and
implemented in Python 3.5. For example, the ``_abc`` module initialization
function is now just a call to the new ``PyModuleDef_Init()`` function::

    PyMODINIT_FUNC
    PyInit__abc(void)
    {
        return PyModuleDef_Init(&_abcmodule);
    }

An extension module can have a module state, if ``PyModuleDef.m_size`` is
greater than zero. Example::

    typedef struct {
        PyTypeObject *_abc_data_type;
        unsigned long long abc_invalidation_counter;
    } _abcmodule_state;

    static struct PyModuleDef _abcmodule = {
        ...
        .m_size = sizeof(_abcmodule_state),  // <=== HERE ===
    };

The ``PyModule_GetState()`` can be used to retrieve the module state. Example::

    static inline _abcmodule_state*
    get_abc_state(PyObject *module)
    {
        void *state = PyModule_GetState(module);
        assert(state != NULL);
        return (_abcmodule_state *)state;
    }

    static PyObject *
    _abc__abc_init(PyObject *module, PyObject *self)
    {
        _abcmodule_state *state = get_abc_state(module);
        ...
        data = abc_data_new(state->_abc_data_type, NULL, NULL);
        ...
    }

Right now, **77% (102/132)** of extension modules use the new multiphase
initialization API (PEP 489) on a total of 132 extension modules.  For
comparison, in Python 3.8, only 23% (27/118) of extensions used the new
multiphase initialization API: **75 extensions** have been converted in the
meanwhile.

TODO: convert the remaining 30 extension modules (`bpo-163574
<https://bugs.python.org/issue1635741>`__).


Module states
=============

Some modules have a state which should be stored in the interpreter to share
its state between multiple instances of the module, and also to give access to
the state in functions of the public C API (ex: ``PyAST_Check()``).

States made per-interpreter:

* 2019-05-10: **warnings**
  (`bpo-36737 <https://bugs.python.org/issue36737>`__,
  `commit <https://github.com/python/cpython/commit/86ea58149c3e83f402cecd17e6a536865fb06ce1>`__ by **Eric Snow**)
* 2019-11-07: **parser**
  (`bpo-36876 <https://bugs.python.org/issue36876>`__,
  `commit <https://github.com/python/cpython/commit/9def81aa52adc3cc89554156e40742cf17312825>`__ by **Vinay Sajip**)
* 2019-11-20: **gc**
  (`bpo-36854 <https://bugs.python.org/issue36854>`__,
  `commit <https://github.com/python/cpython/commit/7247407c35330f3f6292f1d40606b7ba6afd5700>`__ by me)
* 2020-11-02: **ast**
  (`bpo-41796 <https://bugs.python.org/issue41796>`__,
  `commit <https://github.com/python/cpython/commit/5cf4782a2630629d0978bf4cf6b6340365f449b2>`__ by me)

Singletons
==========

Singletons must not be shared between interpreters.

Singletons made per-interpreter.

`bpo-38858 <https://bugs.python.org/issue38858>`__:

* 2019-12-17: small **integer**, the [-5; 256] range
  (`commit <https://github.com/python/cpython/commit/630c8df5cf126594f8c1c4579c1888ca80a29d59>`__ by me)

`bpo-40521 <https://bugs.python.org/issue40521>`__:

* 2020-06-04: empty **tuple** singleton
  (`commit <https://github.com/python/cpython/commit/69ac6e58fd98de339c013fe64cd1cf763e4f9bca>`__ by me)
* 2020-06-23: empty **bytes** string singleton and single byte character
  (``b'\x00'`` to ``b'\xFF'``) singletons
  (`commit <https://github.com/python/cpython/commit/c41eed1a874e2f22bde45c3c89418414b7a37f46>`__ by me)
* 2020-06-23: empty **Unicode** string singleton
  (`commit <https://github.com/python/cpython/commit/f363d0a6e9cfa50677a6de203735fbc0d06c2f49>`__ by me)
* 2020-06-23: empty **frozenset** singleton
  (`commit <https://github.com/python/cpython/commit/261cfedf7657a515e04428bba58eba2a9bb88208>`__ by me);
  later removed.
* 2020-06-24: single **Unicode** character (U+0000-U+00FF range)
  (`commit <https://github.com/python/cpython/commit/2f9ada96e0d420fed0d09a032b37197f08ef167a>`__ by me)

I also micro-optimized the code: most singletons are now always created at
startup, it's no longer needed to check if it is created at each function call.
Moreover, an assertion now ensures that singletons are no longer used after
they are deleted.


Free lists
==========

A free list is a micro-optimization on memory allocations. The memory of
recently destroyed objects is not freed to be able to reuse it for new objects.
Free lists must not be shared between interpreters.

Free lists made per-interpreter (`bpo-40521 <https://bugs.python.org/issue40521>`__):

* 2020-06-04: **slice**
  (`commit <https://github.com/python/cpython/commit/7daba6f221e713f7f60c613b246459b07d179f91>`__ by me)
* 2020-06-04: **tuple**
  (`commit <https://github.com/python/cpython/commit/69ac6e58fd98de339c013fe64cd1cf763e4f9bca>`__ by me)
* 2020-06-04: **float**
  (`commit <https://github.com/python/cpython/commit/2ba59370c3dda2ac229c14510e53a05074b133d1>`__ by me)
* 2020-06-04: **frame**
  (`commit <https://github.com/python/cpython/commit/3744ed2c9c0b3905947602fc375de49533790cb9>`__ by me)
* 2020-06-05: **async generator**
  (`commit <https://github.com/python/cpython/commit/78a02c2568714562e23e885b6dc5730601f35226>`__ by me)
* 2020-06-05: **context**
  (`commit <https://github.com/python/cpython/commit/e005ead49b1ee2b1507ceea94e6f89c28ecf1f81>`__ by me)
* 2020-06-05: **list**
  (`commit <https://github.com/python/cpython/commit/88ec9190105c9b03f49aaef601ce02b242a75273>`__ by me)
* 2020-06-23: **dict**
  (`commit <https://github.com/python/cpython/commit/b4e85cadfbc2b1b24ec5f3159e351dbacedaa5e0>`__ by me)
* 2020-06-23: **MemoryError**
  (`commit <https://github.com/python/cpython/commit/281cce1106568ef9fec17e3c72d289416fac02a5>`__ by me)


Caches
======

Caches made per interpreter:

* 2020-06-04: **slice** cache
  (`bpo-40521 <https://bugs.python.org/issue40521>`__,
  `commit <https://github.com/python/cpython/commit/7daba6f221e713f7f60c613b246459b07d179f91>`__ by me)
* 2020-12-26: **type** attribute lookup cache
  (`bpo-42745 <https://bugs.python.org/issue42745>`__,
  `commit <https://github.com/python/cpython/commit/41010184880151d6ae02a226dbacc796e5c90d11>`__ by me)


Interned strings and identifiers
================================

* 2020-12-25: Per-interpreter identifiers: ``_PyUnicode_FromId()``
  (`bpo-39465 <https://bugs.python.org/issue39465>`__,
  `commit <https://github.com/python/cpython/commit/ba3d67c2fb04a7842741b1b6da5d67f22c579f33>`__ by me)
* 2020-12-26: Per-interpreter interned strings: ``PyUnicode_InternInPlace()``
  (`bpo-40521 <https://bugs.python.org/issue40521>`__,
  `commit <https://github.com/python/cpython/commit/ea251806b8dffff11b30d2182af1e589caf88acf>`__ by me)

For ``_PyUnicode_FromId()``, I added the ``pycore_atomic_funcs.h`` header file
(`commit
<https://github.com/python/cpython/commit/52a327c1cbb86c7f2f5c460645889b23615261bf>`__)
which adds functions for atomic memory accesses (to variables of type
``Py_ssize_t``). It uses ``__atomic_load_n()`` and ``__atomic_store_n()`` on GCC
and clang, or ``_InterlockedCompareExchange64()`` and
``_InterlockedExchange64()`` on MSC (Windows).

First, I tried to use the ``_Py_hashtable`` type: `PR 20048
<https://github.com/python/cpython/pull/20048>`_. Using ``_Py_hashtable``,
``_PyUnicode_FromId()`` took 15.5 ns +- 0.1 ns.  I optimized ``_Py_hashtable``:
``_PyUnicode_FromId()`` took 6.65 ns +- 0.09 ns. But it was still slower than
the reference code: 2.38 ns +- 0.00 ns.

The merged implementation uses an array. An unique index is assigned, index in
this array. The array is made larger on demand. The final change adds 1 ns
per function call::

    [ref] 2.42 ns +- 0.00 ns -> [atomic] 3.39 ns +- 0.00 ns: 1.40x slower


Misc
====

* 2020-03-19: Per-interpreter pending calls
  (`bpo-39984 <https://bugs.python.org/issue39984>`__,
  `commit <https://github.com/python/cpython/commit/50e6e991781db761c496561a995541ca8d83ff87>`__ by me).

Bugfixes
========

* `GIL bugfixes for daemon threads in Python 3.9
  <{filename}/gil-bugfixes-daemon-threads-python39.rst>`_
* Fix many `leaks discovered by subinterpreters
  <{filename}/subinterpreter-leaks.rst>`_
* Fix pickling heap types implemented in C with protocols 0 and 1
  (`bpo-41052 <https://bugs.python.org/issue41052>`__)


Thanks
======

The work on subintepreters, multiphase init and heap types is a collaborative
work on-going for 2 years. I would like to thank the following developers for
helping on this large task:

* **Christian Heimes**
* **Dong-hee Na**
* **Eric Snow**
* **Erlend Egeberg Aasland**
* **Hai Shi**
* **Mohamed Koubaa**
* **Nick Coghlan**
* **Paulo Henrique Silva**
* **Vinay Sajip**

Note: Since the work is scattered in many issues and pull requests, it's hard
to track who helped: sorry if I forgot someone! (Please contact me and I
will complete the list.)

What's Next?
============

There are still multiple interesting technical challenges:

* `bpo-39511: Per-interpreter singletons (None, True, False, etc.)
  <https://bugs.python.org/issue39511>`_
* `bpo-40601: Hide static types from the C API
  <https://bugs.python.org/issue40601>`_
* Make pymalloc allocator compatible with subinterpreters.
* Make the GIL per interpreter. Maybe even give the choice to share or not
  the GIL when a subinterpreter is created.
* Make the ``_PyArg_Parser`` (``parser_init()``) function compatible with
  subinterpreters. Maybe use a per-interpreter array, similar solution than
  ``_PyUnicode_FromId()``.
* `bpo-15751: Make the PyGILState API compatible with subinterpreters
  <https://bugs.python.org/issue15751>`_ (issue created in 2012!)
* `bpo-40522: Get the current Python interpreter state from Thread Local
  Storage (autoTSSkey)
  <https://bugs.python.org/issue40522>`_

Also, there are still many static types to convert to heap types (`bpo-40077
<https://bugs.python.org/issue40077>`__) and many extension modules to convert
to the multiphase initialization API (`bpo-163574
<https://bugs.python.org/issue1635741>`__).

I'm tracking the work in my `Python Subinterpreters
<https://pythondev.readthedocs.io/subinterpreters.html>`_ page
and in the `bpo-40512: Meta issue: per-interpreter GIL
<https://bugs.python.org/issue40512>`_.
