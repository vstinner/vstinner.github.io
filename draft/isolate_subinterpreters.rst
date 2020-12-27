++++++++++++++++++++++
Python Subinterpreters
++++++++++++++++++++++

:date: 2020-12-27 12:00
:tags: cpython, subinterpreters
:category: cpython
:slug: isolate-subinterpreters
:authors: Victor Stinner

This article is about the work done in Python in 2019 and 2020 to better
isolate subinterpreters. The final goal is to be able run multiple interpreters
in parallel, like one interpreter per CPU, each interpreter would run in its
own thread of the same process. The principle is the same than the
multiprocessing module and has the same limitations: no Python object can be
shared directly between two interpreters. Later, we can imagine helpers to
share Python mutable objects using proxies which would prevent race conditions.


Why isolating subinterpreters?
==============================

The work on subinterpreter requires to modify many functions and extension
modules and it will benefit to Python in different ways.

Converting static types to heap types and convert extension modules to the
multiphase initialization API (PEP 489) makes extension modules implemented in
C to behave closer to modules implemented in Python, which is good for the `PEP
399 -- Pure Python/C Accelerator Module Compatibility Requirements
<https://www.python.org/dev/peps/pep-0399/>`__. So this work also helps
Python implementations other than CPython, like PyPy.

These changes also allow to release memory at Python exit which matters when
Python is embedded in an application. Python should be "state less", especially
release all memory at exit. This work slowly fix the `bpo-163574: Py_Finalize()
doesn't clear all Python objects at exit
<https://bugs.python.org/issue1635741>`__. Python leaks less and less Python
objects at exit.


Proof-of-concept in May 2020
============================

In May 2020, I wrote a proof-of-concept to prove the feasability of the project
and to prove that it is faster than sequential execution: `PoC: Subinterpreters
4x faster than sequential execution or threads on CPU-bound workaround
<https://mail.python.org/archives/list/python-dev@python.org/thread/S5GZZCEREZLA2PEMTVFBCDM52H4JSENR/#RIK75U3ROEHWZL4VENQSQECB4F4GDELV>`_.
The performance of subintepreters is basically the same than multiprocessing.

After this PoC, I added a ``--with-experimental-isolated-subinterpreters``
option to ``./configure`` in `bpo-40514 <https://bugs.python.org/issue40514>`_
which defines the ``EXPERIMENTAL_ISOLATED_SUBINTERPRETERS`` macro, and I
disabled some code if the macro is enabled:

* Make the GIL per-interpreter.
* Add a TSS for tstate.
* Disable GC in subinterpreters since some objects are still shared.
* Disable the type attribute lookup cache (shared by all interpreters).
* Disable the fast pymalloc memory allocator (shared by all interpreters).


Convert static types to heap types
==================================

Types declared in Python (``class MyTypes: ...``) are always "heap types":
types dynamically allocated on the heap memory. Historically, types declared in
C were all declared as "static types": defined statically at build type.

Static types are referenced directly. For example, the Python ``str`` type is
``&PyUnicode_Type`` in C. These types are declared statically as
``PyTypeObject``, whereas C APIs require a ``PyTypeObject*`` pointer, and so a
reference to the type is needed using ``&``: it is ``&PyUnicode_Type``, and not
``PyUnicode_Type``.

Static types are referenced directly (``&``), and not copied. All interpreters
share the same static types. Types are also regular objects (``PyTypeObject``
inherits from ``PyObject``) and have a reference count, whereas
``PyObject.ob_refcnt`` is not atomic and so must not be modified in parallel.
Static types must not be shared. There are other problems:

* A type ``__mro__`` tuple (``PyTypeObject.tp_mro`` member) has also the
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
206 types. TODO: convert the remaining 117 static types: see `bpo-40077
<https://bugs.python.org/issue40077>`__.


Multiphase initialization API
=============================

Historically, extension modules are declared with the ``PyModule_Create()``
function. Usually, such extension can be instanciated exactly once. It is
stored in an internal ``PyInterpreterState.modules_by_index`` list, and the
module unique index is stored in ``PyModuleDef.m_base.m_index``. Usually,
such extension use static global variables.

Such "static" extension causes multiple issues:

* The extension cannot be unloaded: memory is not released at Python exit. It
  is an issue when Python is embedded in an application.
* The extension behaves differently than modules defined in Python. When an
  extension is reimported, its namespace (``module.__dict__``) is duplicated,
  but mutable objects and static global variables are still shared. It goes
  against the `PEP 399 -- Pure Python/C Accelerator Module Compatibility
  Requirements <https://www.python.org/dev/peps/pep-0399/>`__ principles.
* etc.

In 2013, Petr Viktorin, Stefan Behnel and Nick Coghlan wrote the `PEP 489 --
Multi-phase extension module initialization
<https://www.python.org/dev/peps/pep-0489/>`_ which has been approved and
implemented in Python 3.5. For example, the ``_abc`` module initialization
function becomes just a call to the new ``PyModuleDef_Init()`` function::

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
        .m_size = sizeof(_abcmodule_state),
    };

Example to get the module state::

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
initialization API (PEP 489) on a total of 132 extension modules.
TODO: convert the remaining 30 extension modules
(`bpo-163574 <https://bugs.python.org/issue1635741>`__).


Module states
=============

* Per-interpreter states:

  * 2020-11-02: ast
    (`bpo-41796 <https://bugs.python.org/issue41796>`__,
    `commit <https://github.com/python/cpython/commit/5cf4782a2630629d0978bf4cf6b6340365f449b2>`__)
  * 2019-11-20: gc
    (`bpo-36854 <https://bugs.python.org/issue36854>`__,
    `commit <https://github.com/python/cpython/commit/7247407c35330f3f6292f1d40606b7ba6afd5700>`__)
  * parser
    (`bpo-36876 <https://bugs.python.org/issue36876>`__,
    `commit <https://github.com/python/cpython/commit/9def81aa52adc3cc89554156e40742cf17312825>`__ by **Vinay Sajip**)
  * warnings
    (`bpo-36737 <https://bugs.python.org/issue36737>`__,
    `commit <https://github.com/python/cpython/commit/86ea58149c3e83f402cecd17e6a536865fb06ce1>`__ by **Eric Snow**)

Singletons
==========

* Per-interpreter singletons (`bpo-40521 <https://bugs.python.org/issue40521>`__):

  * small integer ([-5; 256] range) (`bpo-38858 <https://bugs.python.org/issue38858>`__)
  * empty bytes string singleton
  * empty Unicode string singleton
  * empty tuple singleton
  * single byte character (``b'\x00'`` to ``b'\xFF'``)
  * single Unicode character (U+0000-U+00FF range)
  * Note: the empty frozenset singleton has been removed.

Free lists
==========

* Per-interpreter free lists (`bpo-40521 <https://bugs.python.org/issue40521>`__):

  * MemoryError
  * asynchronous generator
  * context
  * dict
  * float
  * frame
  * list
  * slice
  * tuple

Caches
======

* Per-interpreter slice cache (`bpo-40521 <https://bugs.python.org/issue40521>`__).
* Per-interpreter type attribute lookup cache (`bpo-42745 <https://bugs.python.org/issue42745>`__).

Strings
=======

* Per-interpreter interned strings (`bpo-40521 <https://bugs.python.org/issue40521>`__).
* Per-interpreter identifiers: ``_PyUnicode_FromId()`` (`bpo-39465 <https://bugs.python.org/issue39465>`__)

Misc
====

* Per-interpreter pending calls (`bpo-39984 <https://bugs.python.org/issue39984>`__).

Bugfixes
========

* Fix crashes with daemon threads: https://vstinner.github.io/gil-bugfixes-daemon-threads-python39.html
* Fix bugs related to heap types:

  * Fix the traverse function of heap types for GC collection
    (`bpo-40217 <https://bugs.python.org/issue40217>`__, `bpo-40149 <https://bugs.python.org/issue40149>`__)
  * Fix pickling heap types implemented in C with protocols 0 and 1 (`bpo-41052 <https://bugs.python.org/issue41052>`__)

Thanks
======

The work on subintepreters, multiphase init and heap type is a collaborative
work on-going since 2019. I would like to thank the following developers for
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

Since the work is scattered in multiple issues and pull requests, it's hard to
track who helped: sorry if I forget someone :-( (contact me and I will complete
the list)

What's Next?
============

* `bpo-40512: [subinterpreters] Meta issue: per-interpreter GIL
  <https://bugs.python.org/issue40512>`_
* `Python Subinterpreters
  <https://pythondev.readthedocs.io/subinterpreters.html>`_
