+++++++++++++++++++++++
A New C API for CPython
+++++++++++++++++++++++

:date: 2017-09-07 18:00
:tags: optimization, cpython
:category: python
:slug: new-python-c-api
:authors: Victor Stinner

I am currently at a CPython sprint 2017 at Facebook. We are discussing my idea
of writing a new C API for CPython hiding implementation details and replacing
macros with function calls.

.. image:: {static}/images/cpython_sprint_sept2017.jpg
   :alt: CPython sprint at Facebook, september 2017

This article tries to explain why the CPython C API needs to **evolve**.

C API prevents further optimizations
====================================

The CPython ``PyListObject`` type uses an array of ``PyObject*`` objects. PyPy
is able to use a C array of integers if the list only contains small integers.
CPython cannot because PyList_GET_ITEM(list, index) is implemented as a macro::

    #define PyList_GET_ITEM(op, i) ((PyListObject *)op)->ob_item[i]

The macro relies on the ``PyListObject`` structure::

    typedef struct {
        PyVarObject ob_base;
        PyObject **ob_item;   // <-- pointer to real data
        Py_ssize_t allocated;
    } PyListObject;

    typedef struct {
        PyObject ob_base;
        Py_ssize_t ob_size; /* Number of items in variable part */
    } PyVarObject;

    typedef struct _object {
        Py_ssize_t ob_refcnt;
        struct _typeobject *ob_type;
    } PyObject;


API and ABI
===========

Compiling C extension code using ``PyList_GET_ITEM()`` produces machine code
accessing ``PyListObject`` members. Something like (C pseudo code)::

    PyObject **items;
    PyObject *item;
    items = (PyObject **)(((char*)list) + 24);
    item = items[i];

The offset 24 is hardcoded in the C extension object file: the **API**
(**programming** interface) becomes the **ABI** (**binary** interface).

But debug builds use a different memory layout::

    typedef struct _object {
        struct _object *_ob_next;   // <--- two new fields are added
        struct _object *_ob_prev;   // <--- for debug purpose
        Py_ssize_t ob_refcnt;
        struct _typeobject *ob_type;
    } PyObject;

The machine code becomes something like::

    items = (PyObject **)(((char*)op) + 40);
    item = items[i];

The offset changes from 24 to 40 (+16, two pointers of 8 bytes).

C extensions have to be recompiled to work on Python compiled in debug mode.

Another example is Python 2.7 which uses a different ABI for UTF-16 and UCS-4
Unicode string: the ``--with-wide-unicode`` configure option.


Stable ABI
==========

If the machine code doesn't use the offset, it would be able to only compile C
extensions once.

A solution is to replace PyList_GET_ITEM() **macro** with a **function**::

    PyObject* PyList_GET_ITEM(PyObject *list, Py_ssize_t index);

defined as::

    PyObject* PyList_GET_ITEM(PyObject *list, Py_ssize_t index)
    {
        return ((PyListObject *)list)->ob_item[i];
    }

The machine code becomes a **function call**::

    PyObject *item;
    item = PyList_GET_ITEM(list, index);


Specialized list for small integers
===================================

If C extension objects don't access structure members anymore, it becomes
possible to modify the memory layout.

For example, it's possible to design a specialized implementation of
``PyListObject`` for small integers::

    typedef struct {
        PyVarObject ob_base;
        int use_small_int;
        PyObject **pyobject_array;
        int32_t *small_int_array;   // <-- new compact C array for integers
        Py_ssize_t allocated;
    } PyListObject;

    PyObject* PyList_GET_ITEM(PyObject *op, Py_ssize_t index)
    {
        PyListObject *list = (PyListObject *)op;
        if (list->use_small_int) {
            int32_t item = list->small_int_array[index];
            /* create a new object at each call */
            return PyLong_FromLong(item);
        }
        else {
            return list->pyobject_array[index];
        }
    }

It's just an example to show that it becomes possible to modify PyObject
structures. I'm not sure that it's useful in practice.


Multiple Python "runtimes"
==========================

Assuming that all used C extensions use the new stable ABI, we can now imagine
multiple specialized Python runtimes installed in parallel, instead of a single
runtime:

* python3.7: regular/legacy CPython, backward compatible
* python3.7-dbg: runtime checks to ease debug
* fasterpython3.7: use specialized list
* etc.

The ``python3`` runtime would remain **fully** compatible since it would use
the old C API with macros and full structures. So by default, everything will
continue to work.

But the other runtimes require that all imported C extensions were compiled
with the new C API.

``python3.7-dbg`` adds more checks tested at runtime. Example::

    PyObject* PyList_GET_ITEM(PyObject *list, Py_ssize_t index)
    {
        assert(PyList_Check(list));
        assert(0 <= index && index < Py_SIZE(list));
        return ((PyListObject *)list)->ob_item[i];
    }

Currently, some Linux distributions provide a ``python3-dbg`` binary, but may
not provide ``-dbg`` binary packages of all C extensions. So all C extensions
have to be recompiled manually which is quite painful (need to install build
dependencies, wait until everthing is recompiled, etc.).


Experiment optimizations
========================

With the new C API, it becomes possible to implement a new class of
optimizations.

Tagged pointer
--------------

Store small integers directly into the pointer value. Reduce the memory usage,
avoid expensive unboxing-boxing.

See `Wikipedia: Tagged pointer
<https://en.wikipedia.org/wiki/Tagged_pointer>`_.

No garbage collector (GC) at all
--------------------------------

Python runtime without GC at all. Remove the following header from objects
tracked by the GC::

    struct {
        union _gc_head *gc_next;
        union _gc_head *gc_prev;
        Py_ssize_t gc_refs;
    } PyGC_Head;

It would remove 24 bytes per object tracked by the GC.

For comparison, the smallest Python object is "object()" which only takes 16
bytes.

Tracing garbage collector without reference counting
----------------------------------------------------

This idea is really the most complex and most experimental idea, but IMHO it's
required to "unlock" Python performances.

* Write a new API to keep track of pointers:

  * Declare a variable storing a ``PyObject*`` object
  * Set a pointer
  * Maybe also read a pointer?

* Modify C extensions to use this new API
* Implement a tracing garbage collector which can move objects in memory
  to compact memory
* Remove reference counting

It even seems possible to implement a tracing garbage collector **and** use
reference counting. But I'm not an expert in this area, need to dig the topic.

Questions:

* Is it possible to fix all C extensions to use the new API? Should be an
  opt-in option in a first stage.
* Is it possible to emulate Py_INCREF/DECREF API, for backward compatibility,
  using an hash table which maintains a reference counter outside ``PyObject``?
* Do we need to fix all C extensions?

Read also `Wikipedia: Tracing garbage collection
<https://en.wikipedia.org/wiki/Tracing_garbage_collection>`_.

Gilectomy
---------

Abstracting the ABI allows to customize the runtime for Gilectomy needs, to be
able to reemove the GIL.

Removing reference counting would make Gilectomy much simpler.

