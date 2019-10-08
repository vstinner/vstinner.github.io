+++++++++++++++++++++++++++++++++++++
Better debugging experience in Python
+++++++++++++++++++++++++++++++++++++

Usually, debugging a Python program in done in pure Python and they are plently
of cool debuggers and tools to help with that. This article is about bugs in C
extensions and bugs in CPython internals (CPython itself).

``python-gdb.py`` is a cool gdb extension provided by gdb which provides gdb
commands to inspect Python internals: get the Python traceback, display the
content of a variable, display Python variables, etc.

In general, I manage to find a way to debug C extensions. But bugs in the
garbage collector (GC) are the worst, especially crash in the
``visit_decref()`` function. When a crash occurs in ``visit_decref()``, it is
bad because the object passed as an argument is usually corrupted. A Python
object can be corrupted for different reasons:

* Issue with the reference counting: missing ``Py_INCREF()`` or ``Py_DECREF()``
* Buffer underflow or overflow in a memory block
* Memory write into freed memory, the memory can be reused by a new object,
  or not
* Another unknown reason to be discovered

Objects tracked by the GC
=========================

Not all Python objects are tracked by the garbage collector. For example,
simple immutable types like ``int`` or ``str`` are not tracked. Containers
like ``list`` and ``dict`` are tracked. Example::

    $ python3
    >>> import gc
    >>> a=1
    >>> b="string"
    >>> gc.is_tracked(a)
    False
    >>> gc.is_tracked(b)
    False

    >>> x=[a, b]
    >>> gc.is_tracked(x)
    True

In general, objects which can contain other objects are tracked by the GC.
Otherwise, they should not be tracked.

There are special cases and optimizations. For example in Python 3.7, a
dictionary is not tracked by default. It is tracked once a new item is inserted
if the key or the value is tracked. ::

    vstinner@apu$ python3
    >>> d={}
    >>> import gc; gc.is_tracked(d)
    False

    >>> d[1]=2; gc.is_tracked(d)
    False

    >>> d[2]=[]; gc.is_tracked(d)
    True

tp_traverse() method
====================

Types tracked by the GC must implement the internal ``tp_traverse()`` method.
This method takes a callback which is called on each object contained in the
parent (traversed) object. For example, for the list ``[1, 2]``, calling
``tp_traverse(my_function)`` calls ``my_function(1)`` and ``my_function(2)``.

visit_decref() traverse function
================================

The Python GC frequently check if objects tracked by the GC are still
"reachable". Unreachable objects are destroyed.

In fact, it's not only about objects directly tracked by the GC, but also
objects referenced by tracked GC thanks to the ``tp_traverse()`` mechanism.

The ``visit_decref()`` is used with ``tp_traverse()`` as part of the function
checking if objects are still "reachable" or not.

Simplified but incorrect explanation: ``visit_decref()`` is called on every
single Python object.

If an object is corrupted, it is likely that the GC which crash while
inspecting it using ``visit_decref()``.

For a more accurate and more details explanation on how the GC decides which
objects are unreachable, see `Time to take out the rubbish: garbage collector -
PyCon 2019 <https://www.youtube.com/watch?v=CLW5Lyc1FN8?t=505>`_ talk by Pablo
Galindo Salgado at PyCon US 2019: the link points to "2. The algorithm".

New _PyObject_ASSERT() function
===============================

In 2010, Dave Malcolm wrote a change to enhance assertions errors in the
garbage collector when Python is compiled in debug mode. He wrote a
``_PyObject_AssertFailed()`` function which is called on an assertion error:
it dumps a Python object before calling ``abort()``. He also added a few
macros to easily use this new function.

This change was maintained downstream at Red Hat in Fedora and RHEL for 8
years. Last year, while I looked at our downstream patches at Red Hat (in
Fedora), I found this change and I pushed it upstream, to reduce our
maintenance burden, but also to share these nice enhancements with everybody.

The first change (`commit 626bff85
<https://github.com/python/cpython/commit/626bff856840f471e98ec627043f780c111a063d>`__)
adds the ``_PyObject_AssertFailed()`` function, and a ``_PyObject_ASSERT(obj,
expr)`` macro which is similar to ``assert(expr)``, but dumps a Python object
if the assertion fails. ::

    commit 626bff856840f471e98ec627043f780c111a063d
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Thu Oct 25 17:31:10 2018 +0200

        bpo-9263: Dump Python object on GC assertion failure (GH-10062)

Slowly, I modified more and more files to use this new nice macro:

* ``gcmodule.c``
* ``object.c``
* ``dictobject.c``
* ``typeobject.c``
* ``unicodeobject.c``

Functions:

* ``_PyObject_GC_TRACK()``
* ``_PyObject_GC_UNTRACK()``
* ``Py_DECREF()`` through ``_Py_NegativeRefcount()``

Py_FatalError()
===============

The ``Py_FatalError()`` function is called when Python cannot recover from a
bug and it is safer to abort the process. This function should provide as much
information as possible about the bug to help users and developers to debug it.

I implemented the `faulthandler module
<https://docs.python.org/dev/library/faulthandler.html>`_ in Python 3.3. Once
it was implemented, it became easy to modify ``Py_FatalError()`` to dump the
Python traceback of all Python threads, when ``Py_FatalError()`` is not called
with an exception set (otherwise, the exception traceback is logged instead).

In Python 3.3, I modified the function to log the traceback of all Python
threads. After I implemented the faulthandler module

While debugging Python bugs, I fixed more and more bugs in ``Py_FatalError()``
to handle corner cases. In Python 3.5, I modified the function to avoid
crashing if it's called without holding the GIL.

In Python 3.6, I modified the function to detect reentrant call. For example,
when flushing ``sys.stdout`` causes a second fatal error like a recursion
error. I also enhanced how Python detects if the GIL is held or not.

In Python 3.7, I modified the Windows implementation to avoid a call to
``alloca()`` which depends on the length of the error message.
``Py_FatalError()`` can be called while the C stack is close to overflow.
The new implementation only uses 256 bytes of stack memory. In practice,
this issue is more theorical since error messages are usually short.

In Python 3.8, the function now dumps the "Python runtime state":
"preinitializing", "initialized", etc. It's related to the PEP 587
implementation.

_PyObject_IsFreed()
===================

bpo-9263: I added ``_PyObject_IsFreed()`` and ``_PyMem_IsFreed()``
functions to check if the memory of an object has been freed.
``_PyObject_IsFreed()`` function can be used to prevent reading freed memory.
In debug mode, Python installs a debug hook on memory allocators which fills
freed memory with a byte pattern. Pointers stored in PyObject becomes
0xDBDBDBDB: deferencing such point is likely to crash.

I added function tests to ensure that ``_PyObject_IsFreed()`` is able to
detect when a Python object has been freed. The test failed on Windows.
The reason was that the MSCRT also fills the freed memory with a pattern,
but a pattern different than Python: 0xDB. The invalid pointer 0xDBDBDBDB
becomes 0xDDDDDDDD in this case. I modified the Python byte patterns to match
the ones used by MSCRT:

* ``PYMEM_CLEANBYTE = 0xCD``: clean (newly allocated) memory
* ``PYMEM_DEADBYTE = 0xDD``: dead (newly freed) memory
* ``PYMEM_FORBIDDENBYTE = 0xFD``: untouchable bytes at each end of a block

Recently, I modified ``_PyMem_IsFreed(ptr)`` to also return 1 if ptr is NULL
(is equal to zero).

``_PyObject_IsFreed()`` is an heuristic. One the memory is freed, Python is
free to reallocate it and so override bytes. It should work to detect
uninitialized bytes. For freed bytes, it works until the memory is reallocated.


_PyObject_Dump()
================

_PyObject_Dump() function is mostly provided to be called directly in
debuggers. Only very few functions use it, and usually only in debug mode.

_PyObject_Dump() no longer displays the object content if it is detected as
been "freed".

_PyObject_Dump() now dumps all info *before* trying to render repr(object),
since repr() is likely to crash if the object is corrupted.

Experimental "object debugger"
==============================

Working PyObject_GC_Track() enhancement.

MISC
====

_PyObject_CheckConsistency(): function currently unused

Experimental issues:

* gc.enable_object_debugger()

Python 3.6: xxx
Python 3.7: xxx
Python 3.8: Debug build is ABI compatible with release build, no need to recompile
Python 3.9: visit_decref(), Py GC Track
