Mid-term goal: specialized compact PyListObject for lists only containing small
integers.

Long-term goal: experiment tracing garbage collector without reference
counting.

C API prevents further optimizations
====================================

Example: PyListObject uses an array of PyObject*. PyPy is able to use a C array
of int32 if the list only contains small integers. CPython cannot because
PyList_GET_ITEM(list, index) is implemented as a macro::

    #define PyList_GET_ITEM(op, i) (((PyListObject *)(op))->ob_item[i])

The macro relies on the PyListObject structure::

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

C extension using PyList_GET_ITEM() produces machine code accessing
PyListObject. Something like::

    PyObject **items;
    PyObject *item;
    items = (PyObject **)(((char*)list) + 24);
    item = items[i];

The offset 24 is hardcoded in the C extension object: the API (**programming**
interface) becomes the ABI (**binary** interface).

But debug build uses a different memory layout::

    typedef struct _object {
        struct _object *_ob_next;   // <---
        struct _object *_ob_prev;   // <---
        Py_ssize_t ob_refcnt;
        struct _typeobject *ob_type;
    } PyObject;

The machine code becomes::

    items = (PyObject **)(((char*)op) + 40);
    item = items[i];

The offset changes from 24 to 40 (+16, two pointers of 8 bytes).

=> need to recompile C extension for debug build

Note: Python 2.7 used a different ABI for UTF-16 and UCS-4 unicode,
--with-wide-unicode configure option.


Stable ABI
==========

It would be able to only compile C extensions once and use it on release
(offset 40) and debug (offset 24) builds if the machine code doesn't use the
offset.

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

Now it becomes possible to imagine a specialized implementation of PyListObject
for small integers::

    typedef struct {
        PyVarObject ob_base;
        int is_specialized;
        PyObject **pyobject_array;
        int32_t *small_int_array; /* compact C array */
        Py_ssize_t allocated;
    } PyListObject;

    PyObject* PyList_GET_ITEM(PyObject *op, Py_ssize_t index)
    {
        PyListObject *list = (PyListObject *)op;
        if (list->is_specialized) {
            int32_t item = list->small_int_array[index];
            /* create a new object at each call */
            return PyLong_FromLong(item);
        }
        else {
            return list->pyobject_array[index];
        }
    }


Multiple Python "runtimes"
==========================

Assuming that all used C extensions use the new stable ABI, we can now imagine
multiple specialized Python runtimes installed in parallel, instead of a single
"python3" (/urs/bin/python3):

* python3: regular/legacy CPython, backward compatible
* python3-dbg: runtime checks to ease debug
* faster-python3: use specialized list
* etc.

python3-dbg adds more checks, tested at runtime::

    PyObject* PyList_GET_ITEM(PyObject *list, Py_ssize_t index)
    {
        assert(PyList_Check(list));
        assert(0 <= index && index < Py_SIZE(list));
        return ((PyListObject *)list)->ob_item[i];
    }

Currently, python3-dbg exists but requires to recompile all C extensions and so
is painful to use in practice.

python3 remains the default and is backward compatible.

Other runtimes require that all imported C extensions were compiled with the
new C API which doesn't leak any implementation detail and so use the stable
ABI.


Experiment optimizations
========================

No GC at all
------------

Python runtime without GC at all. Remove the following header from objects
tracked by the GC::

    struct {
        union _gc_head *gc_next;
        union _gc_head *gc_prev;
        Py_ssize_t gc_refs;
    } PyGC_Head;

Remove 24 bytes per object tracked by the GC.

For comparison, the small Python object is "object()" and only takes 16 bytes.

Tagged pointer
--------------

Store small integers directly in the pointer. Reduce the memory usage, avoid
expensive unboxing-boxing.

Tracing garbage collector without reference counting
----------------------------------------------------

Most experimental idea:

* write a new API to declare variables storing PyObject* and setting the value
  of PyObject* pointers, to track all pointers to objects
* modify C extensions to use this new API
* implement a tracing garbage collector which can move objects in memory
  to compact memory
* remove reference counting

Questions:

* Is it possible to fix all C extensions to use the new API?
* Is it possible to emulate Py_INCREF/DECREF using an hash table which
  maintains a reference counter outside PyObject?
* Do we need to fix all C extensions?

Gilectomy
---------

Abstracting the ABI allows to customize the runtime for Gilectomy needs, to be
able to reemove the GIL.

