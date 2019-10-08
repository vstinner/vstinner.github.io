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

The first change (commit 626bff856840f471e98ec627043f780c111a063d) added ``_PyObject_ASSERT(obj, exprt`` macro which is similar
to ``assert(expr)``, but dumps a Python object if the assertion fails.


    commit 626bff856840f471e98ec627043f780c111a063d
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Thu Oct 25 17:31:10 2018 +0200

        bpo-9263: Dump Python object on GC assertion failure (GH-10062)



_PyObject_ASSERT


_PyObject_ASSERT
_Py_NegativeRefcount
gcmodule.c
Py_FatalError()
visit_decref()
_PyObject_Dump()
_PyObject_IsFreed()
_PyObject_CheckConsistency(): function currently unused

Experimental issues:

* gc.enable_object_debugger()

Python 3.6: xxx
Python 3.7: xxx
Python 3.8: Debug build is ABI compatible with release build, no need to recompile
Python 3.9: visit_decref(), Py GC Track
