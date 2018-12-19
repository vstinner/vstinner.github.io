+++++++++++++++++++++++++++++++++++++++++
New Python C API: Report of November 2018
+++++++++++++++++++++++++++++++++++++++++

I am working on a new C API for Python to be able to get ride of mistakes of
the past which prevent us to move on. My main target is to make "Python"
faster, for example by making C extensions run faster on PyPy (using cpyext).

I would like to work directly on CPython upstream to ensure that every can play
with the new API and report issues. It would also help to have a wider
adoption. The new API would be an opt-in compilation mode to developers wanting
to check if their C extensions are compatible.

My `pythoncapi.readthedocs.io <https://pythoncapi.readthedocs.io/>`_ website
elaborates the rationale and proposed changes.

This article describes changes made in Python last months.

Private API moved to Include/internal/
======================================

Issue: `bpo-35081 <https://bugs.python.org/issue35081>`_.

The CPython code base is splitted into multiple C files. To be able to use a
function defined in one file from other files, function prototypes are defined
in the ``Include/`` subdirectory using ``#ifdef Py_BUILD_CORE``. Example from
Python 3.6::

   #ifdef Py_BUILD_CORE
   PyAPI_DATA(_Py_atomic_address) _PyThreadState_Current;
   #  define PyThreadState_GET() \
                ((PyThreadState*)_Py_atomic_load_relaxed(&_PyThreadState_Current))
   #else
   #  define PyThreadState_GET() PyThreadState_Get()
   #endif

When building Python core, ``PyThreadState_GET()`` directly access the atomic
variable ``_PyThreadState_Current``. Otherwise, the macro becomes an alias to
``PyThreadState_Get()``.

These APIs should not be used outside Python code. Eric Snow started to move
``#ifdef Py_BUILD_CORE`` from ``Include/*.h`` to new  ``Include/internal/*.h``
header files in Python 3.7. I finished this migration in the future Python 3.8.

I renamed internal header files to add a ``pycore_`` prefix. Previously,
``Include/internal/pystate.h`` used ``#include "pytstate.h"`` but this include
had no effect, since the C compiler included ``Include/internal/pystate.h``
instead of ``Include/pystate.h`` (and the second include does nothing).

I moved all code surrounded by ``#ifdef Py_BUILD_CORE`` to
``Include/internal/``. I created multiple header files.

I added ``Include/internal/`` to the header search path (gcc ``-I`` option), so
it's now possible to write::

    #include "pycore_pymem.h"
    #include "pycore_pystate.h"
    #include "pycore_tupleobject.h"

Right now, ``Include/internal/`` contains:

* ``pycore_accu.h``
* ``pycore_atomic.h``
* ``pycore_ceval.h``
* ``pycore_condvar.h``
* ``pycore_context.h``
* ``pycore_fileutils.h``
* ``pycore_getopt.h``
* ``pycore_gil.h``
* ``pycore_hamt.h``
* ``pycore_object.h``
* ``pycore_pathconfig.h``
* ``pycore_pyhash.h``
* ``pycore_pylifecycle.h``
* ``pycore_pymem.h``
* ``pycore_pystate.h``
* ``pycore_tupleobject.h``
* ``pycore_warnings.h``

Chosing the name of the ``Include/internal/`` directory (I proposed to rename
it) and chosing the ``pycore_`` prefix took time :-) It has been decided to
**not** include directly ``pycore_xxx.h`` header from ``Include/xxx.h`` header,
but instead requires to explicitly include ``pycore_xxx.h`` in each C file.

I had to add ``#include "pycore_object.h"`` to not less than 32 C files for
``_PyObject_GC_TRACK()`` and ``_PyObject_GC_UNTRACK()``!


"CPython API" is moving to Include/cpython/
===========================================

Issue: `bpo-35134 <https://bugs.python.org/issue35134>`_.

When the `PEP 384 "Defining a Stable ABI"
<https://www.python.org/dev/peps/pep-0384/>`_ has been implemented, ``#ifndef
Py_LIMITED_API`` has been added around "unstable API". API has to opt-out from
stable ABI which caused new APIs to be added to be stable API by mistake.

To prevent new errors and to clarify what are the "stable API" and what are the
"unstable API", I create a new ``Include/cpython/`` directory where I moved
the code previously surrounded by ``#ifndef Py_LIMITED_API``. From the user
perspective, there is no change, since the new header files are included from
other header files. For example, ``Include/objimpl.h`` contains::

   #ifndef Py_LIMITED_API
   #  define Py_CPYTHON_OBJIMPL_H
   #  include  "cpython/objimpl.h"
   #  undef Py_CPYTHON_OBJIMPL_H
   #endif

By the way, ``Include/cpython/*.h`` header files must not be included directly.

``Include/*.h`` should be the "portable Python API", whereas
``Include/cpython/*.h`` should be the "CPython API": CPython implementation
details.


Convert macros to static inline functions
=========================================

Issue: `bpo-35059 <https://bugs.python.org/issue35059>`_.

C macros are very convenient to avoid to copy/paste code manually. They are
kinds of "templates", but working at the "text level" rather than the "language
level". It is very common to introduce subtle bugs when C macros are not
written "carefully", see `GCC Macro Pitfals
<https://gcc.gnu.org/onlinedocs/cpp/Macro-Pitfalls.html>`_.

I converted the following macros to static inline functions:

* ``Py_INCREF()``, ``Py_DECREF()``
* ``Py_XINCREF()``, ``Py_XDECREF()``
* ``PyObject_INIT()``, ``PyObject_INIT_VAR()``
* ``_Py_NewReference()``, ``_Py_ForgetReference()``
* ``_Py_Dealloc()``
* ``_PyObject_GC_TRACK()``, ``_PyObject_GC_UNTRACK()``

There is no significant impact on performance. It wasn't the intent of my
change. Python 3.7 uses ugly macros for comma and semicolon... Example::

   #define _Py_REF_DEBUG_COMMA ,
   #define _Py_CHECK_REFCNT(OP) /* a semicolon */;

   #define _Py_NewReference(op) (                          \
       _Py_INC_TPALLOCS(op) _Py_COUNT_ALLOCS_COMMA         \
       _Py_INC_REFTOTAL  _Py_REF_DEBUG_COMMA               \
       Py_REFCNT(op) = 1)

Static inline functions as regular C functions have a return type and their
arguments have a type as well. They are better defined than macros which
require to read their source code to check their exact semantics.

