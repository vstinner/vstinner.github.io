++++++++++++++++++++++++++++++++++++++
Split Include/ directory in Python 3.8
++++++++++++++++++++++++++++++++++++++

:date: 2019-06-19 12:00
:tags: python, c-api
:category: python
:slug: split-include-directory-python38
:authors: Victor Stinner

.. image:: {static}/images/private_way.jpg
   :alt: Private way. Trespassers and those disposing rubbish will be prosecuted.
   :target: https://www.flickr.com/photos/mortengade/2747989334/

In September 2017, during the CPython sprint at Facebook, I proposed my
idea to create `A New C API for CPython <{filename}/new_python_c_api.rst>`_.
I'm still working on the Python C API at: `pythoncapi.readthedocs.io
<http://pythoncapi.readthedocs.io/>`_.

My analysis is that the C API leaks too many implementation details which
prevent to optimize Python and make the implementation of PyPy (cpyext) more
painful.

In Python 3.8, I created ``Include/cpython/`` sub-directory to stop adding new
APIs to the stable API by mistake.

I moved more private functions into the internal C API: ``Include/internal/``
directory.

I also converted some macros like ``Py_INCREF()`` and ``Py_DECREF()`` to static
inline functions to have well defined parameter and return type, and to avoid
macro pitfals.

Finally, I removed 3 functions from the C API.


Include/internal/
=================

In Python 3.7, **Eric Snow** created ``Include/internal/`` sub-directory for
the CPython "internal C API": API which should not be used outside CPython code
base. In Python 3.6, these APIs were surrounded by::

    #ifdef Py_BUILD_CORE
    ...
    #endif

In Python 3.8, I continued this work by moving more private functions into
this directory: see `bpo-35081 <https://bugs.python.org/issue35081>`_.

I started a thread on python-dev: `[Python-Dev] Rename Include/internal/ to
Include/pycore/
<https://mail.python.org/pipermail/python-dev/2018-October/155587.html>`_. But
it was decided to keep ``Include/internal/`` name. It was decided that internal
header files must not be included implicitly by the generic ``#include
<Python.h>``, but included explicitly. For example, when I moved
``_PyObject_GC_TRACK()`` and ``_PyObject_GC_UNTRACK()`` to the internal C API,
I had to add ``#include "pycore_object.h"`` to 32 C files!

`I also modified make install <https://bugs.python.org/issue35296>`_ to install
this internal C API, so it can be used for specific needs like debuggers or
profilers which have to access CPython internals (access structure fields) but
cannot call functions. For example, **Eric Snow** moved the ``PyInterpreterState``
structure to the internal C API.

Installing the internal C API ease the migration of APIs to internal: if an API
is still needed after it's moved, it's now possible to opt-in to use it.

Using the internal C API requires to define ``Py_BUILD_CORE_MODULE`` macro and
use a different include, like ``#include "internal/pycore_pystate.h"``. It's
more complicated on purpose: ensure that it's not used by mistake.

Python 3.8 now provides 21 internal header files::

    pycore_accu.h       pycore_getopt.h      pycore_pyhash.h
    pycore_atomic.h     pycore_gil.h         pycore_pylifecycle.h
    pycore_ceval.h      pycore_hamt.h        pycore_pymem.h
    pycore_code.h       pycore_initconfig.h  pycore_pystate.h
    pycore_condvar.h    pycore_object.h      pycore_traceback.h
    pycore_context.h    pycore_pathconfig.h  pycore_tupleobject.h
    pycore_fileutils.h  pycore_pyerrors.h    pycore_warnings.h


Include/cpython/
================

The `PEP 384 "Defining a Stable ABI"
<https://www.python.org/dev/peps/pep-0384/>`_ introduced ``Py_LIMITED_API``
macro to exclude functions from the Python C API. The problem is when a new API
is added, it has to explicitly be excluded using ``#ifndef Py_LIMITED_API``.
If the author forgets it, the function is added to be stable API by mistake.

I proposed to move the API which should be excluded from the stable ABI to a
new subdirectory. I created a `poll on the sub-directory name
<https://discuss.python.org/t/poll-what-is-your-favorite-name-for-the-new-include-subdirectory/477>`_:

* ``Include/cpython/``
* ``Include/board/``
* ``Include/impl/``
* ``Include/pycapi/`` (the name that I proposed initially)
* ``Include/unstable/``
* other (add comment)

The ``Include/cpython/`` name won with 100% of the 3 votes (and a few more
supports in the python-dev discussion and in the bug tracker) :-)

I created `bpo-35134: Add a new Include/cpython/ subdirectory for the "CPython
API" with implementation details <https://bugs.python.org/issue35134>`_.

My initial description of the directory content:

    The new subdirectory will contain ``#ifndef Py_LIMITED_API`` code, not the
    “Stable ABI” of `PEP 384 <https://www.python.org/dev/peps/pep-0384/>`__, but
    more “implementation details” of CPython.

The change is backward compatible: ``#include <Python.h>`` will still provide
exactly the same API. For example, ``object.h`` automatically includes
``cpython/object.h``. But ``Include/cpython/`` headers must not be included
directly (it would fail with a compilation error).

For example, ``Include/object.h`` now ends with::

    #ifndef Py_LIMITED_API
    #  define Py_CPYTHON_OBJECT_H
    #  include  "cpython/object.h"
    #  undef Py_CPYTHON_OBJECT_H
    #endif

``Include/cpython/object.h`` structure (content replaced with ``...``)::

    #ifndef Py_CPYTHON_OBJECT_H
    #  error "this header file must not be included directly"
    #endif

    #ifdef __cplusplus
    extern "C" {
    #endif

    ...

    #ifdef __cplusplus
    }
    #endif

In Python 3.8, the work is not complete. I tried to double- or even
triple-check my changes to ensure that I don't remove an API by mistake. This
work is still on-going in Python 3.9.

Summary of Include/ directories
===============================

The header files have been reorganized to better separate the different kinds
of APIs:

* ``Include/*.h`` should be the portable public stable C API.
* ``Include/cpython/*.h`` should be the unstable C API specific to CPython;
  public API, with some private API prefixed by ``_Py`` or ``_PY``.
* ``Include/internal/*.h`` is the private internal C API very specific to
  CPython. This API comes with no backward compatibility warranty and should
  not be used outside CPython. It is only exposed for very specific needs
  like debuggers and profiles which has to access to CPython internals
  without calling functions. This API is now installed by ``make install``.


Convert macros to static inline functions
=========================================

In `bpo-35059 <https://bugs.python.org/issue35059>`_, I converted some macros
to static inline functions:

* ``Py_INCREF()``, ``Py_DECREF()``
* ``Py_XINCREF()``, ``Py_XDECREF()``
* ``PyObject_INIT()``, ``PyObject_INIT_VAR()``
* Private functions: ``_PyObject_GC_TRACK()``, ``_PyObject_GC_UNTRACK()``,
  ``_Py_Dealloc()``

Compared to macros, static inline functions have multiple advantages:

* Parameter types and return type are well defined;
* They don't have issues specific to macros: see `GCC Macro Pitfals
  <https://gcc.gnu.org/onlinedocs/cpp/Macro-Pitfalls.html>`_;
* Variables have a well defined local scope.

Python 3.7 uses ugly macros with comma and semicolon. Example::

   #define _Py_REF_DEBUG_COMMA ,
   #define _Py_CHECK_REFCNT(OP) /* a semicolon */;

   #define _Py_NewReference(op) (                          \
       _Py_INC_TPALLOCS(op) _Py_COUNT_ALLOCS_COMMA         \
       _Py_INC_REFTOTAL  _Py_REF_DEBUG_COMMA               \
       Py_REFCNT(op) = 1)

`Python 3.6 requires C99 standard of the C dialect
<https://www.python.org/dev/peps/pep-0007/#c-dialect>`_. It was time to start
to use it :-)


Removed functions
=================


`bpo-35713 <https://bugs.python.org/issue35713>`_: I removed
``PyByteArray_Init()`` and ``PyByteArray_Fini()`` functions. They did nothing
since Python 2.7.4 and Python 3.2.0, were excluded from the limited API (stable
ABI), and were not documented.

`bpo-36728 <https://bugs.python.org/issue36728>`_: I also removed
``PyEval_ReInitThreads()`` function. It should not be called explicitly: use
``PyOS_AfterFork_Child()`` instead.
