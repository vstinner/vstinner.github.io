+++++++++++++++++++++++++++++++++++++++++++++++
Status of the Python Limited C API (March 2024)
+++++++++++++++++++++++++++++++++++++++++++++++

:date: 2024-03-20 17:00
:tags: c-api, cpython
:category: cpython
:slug: status-limited-c-api-march-2024
:authors: Victor Stinner

.. image:: {static}/images/ghibli-spyrited-away.jpg
   :alt: Ghibli - Spirited Away
   :target: https://danielazconegui.com/en/prints/ghibli-spyrited-away.html

In Python 3.13, I made multiple enhancements to make the limited C API more
usable:

* Add 14 functions to the limited C API.
* Make the special debug build ``Py_TRACE_REFS`` compatible with the limited
  C API.
* Enhance Argument Clinic to generate C code using the limited C API.
* Add an convenient API to format a type fully qualified name using the limited
  C API (PEP 737).
* Add ``_testlimitedcapi`` extension.
* Convert 16 stdlib extensions to the limited C API.

What's Next?

* PEP 741: Python Configuration C API.
* Py_GetConstant().
* Cython and PyO3.

*Drawing: Ghibli - Spirited Away by Daniel Azconegui.*

New Functions
=============

I added 14 functions to the limited C API:

* ``PyDict_GetItemRef()``
* ``PyDict_GetItemStringRef()``
* ``PyImport_AddModuleRef()``
* ``PyLong_AsInt()``
* ``PyMem_RawCalloc()``
* ``PyMem_RawFree()``
* ``PyMem_RawMalloc()``
* ``PyMem_RawRealloc()``
* ``PySys_Audit()``
* ``PySys_AuditTuple()``
* ``PyType_GetFullyQualifiedName()``
* ``PyType_GetModuleName()``
* ``PyWeakref_GetRef()``
* ``Py_IsFinalizing()``

It makes code using these functions **compatible with the limited C API**.


Py_TRACE_REFS
=============

I modified the special debug build ``Py_TRACE_REFS``. Instead of adding two
members to ``PyObject`` to create a double linked list of all objects, I added
an hash table to track all objects.

Since the ``PyObject`` structure is no longer modified, this special debug
build is now **ABI compatible** with the **release build**! Moreover, it also
becomes compatible with the **limited C API**!


Argument Clinic
===============

I modified Argument Clinic (AC) to generate C code compatible with the limited
C API.

First, I moved private functions used by Argument Clinic to the internal C API
and modified Argument Clinic to generate ``#include`` to get these functions.
Then I modified Argument Clinic to use only the limited C API and to not
generate these ``#include``.

At the beginning, only some converteres were supported and only the slower
``METH_VARARGS`` calling convention was supported.

Now, more and more converters and formats are supported, and the regular
efficient ``METH_FASTCALL`` calling convention is used.

Example
-------

Example from the ``grp`` extension::

    /*[clinic input]
    grp.getgrgid

        id: object

    Return the group database entry for the given numeric group ID.

Python 3.12 uses the **private** ``_PyArg_UnpackKeywords()`` functions::

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 1, 1, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    id = args[0];
    return_value = grp_getgrgid_impl(module, id);

Python 3.13 now uses the public ``PyArg_ParseTupleAndKeywords()`` function of
the **limited C API**::

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O:getgrgid", _keywords,
        &id))
        goto exit;
    return_value = grp_getgrgid_impl(module, id);


PEP 737: Format Type Name
=========================

One issue that I had with Argument Clinic was to **format an error message**
with the limited C API. I cannot use the private ``_PyArg_BadArgument()``
function, nor access to ``PyTypeObject.tp_name`` (opaque structure in the
limited C API) to format a type name. While the limited C API provides
``PyType_GetName()`` and ``PyType_GetQualName()``, it's still different than
how Python formats type names in error messages.

I proposed different APIs but there was no agreement. So I decided to write
`PEP 737 <https://peps.python.org/pep-0737/>`_ "C API to format a type fully
qualified name".

After four months of discussions, the **Steering Council** decided to accept it
in Python 3.13.

Changes:

* Add ``PyType_GetFullyQualifiedName()`` function.
* Add ``PyType_GetModuleName()`` function.
* Add ``%T``, ``%#T``, ``%N`` and ``%#N`` formats to
  ``PyUnicode_FromFormat()``.

I also proposed adding a new ``type.__fully_qualified_name__`` attribute, and a
few methods to format a the fully qualified name of type in Python. But the
Steering Council was not convinced and asked me to **remove these Python
changes** until someone comes with a strong use case for this attribute and
methods.

In **2018**, I made a **first attempt**: I made a similar change, but I had to
revert it. I created a discussion on the python-dev mailing list, but we failed
to reach a consensus.

In **2011**, I already asked to stop the **cargo cult** of truncating type
names, but I didn't implement my idea by proactively stop truncating type
names.

Example
-------

Example of the code generating an error message in the ``pwd`` extension.

Python 3.12 uses the **private** ``_PyArg_BadArgument()`` private::

    _PyArg_BadArgument("getpwnam", "argument", "str", arg);

Python 3.13 now uses the new ``%T`` format (PEP 737) of the **limited C API**::

    PyErr_Format(PyExc_TypeError,
                 "getpwnam() argument must be str, not %T",
                 arg);


Add _testlimitedcapi extension
==============================

In Python 3.12, C API tests are splitted in two categories:

* ``_testcapi``: public C API
* ``_testinternalcapi``: internal C API (``Py_BUILD_CORE``)

I added a third ``_testlimitedcapi`` extension to test the limited C API
(``Py_LIMITED_API``). I moved tests using the limited C C API from
``_testcapi`` to ``_testlimitedcapi``.

The difference between ``_testcapi`` and ``_testlimitedcapi`` is that the
``_testlimitedcapi`` extension is built with the ``Py_LIMITED_API`` macro
defined, and so can only access the internal C API.


Convert stdlib extensions to the limited C API
==============================================

At August 2023, I proposed to:
`Use the limited C API for some of our stdlib C extensions
<https://discuss.python.org/t/use-the-limited-c-api-for-some-of-our-stdlib-c-extensions/32465>`_.

In March 2024, there are now **16** C extensions built with the limited C API:

* ``_ctypes_test``
* ``_multiprocessing.posixshmem``
* ``_scproxy``
* ``_stat``
* ``_statistics``
* ``_testimportmultiple``
* ``_testlimitedcapi``
* ``_uuid``
* ``errno``
* ``fcntl``
* ``grp``
* ``md5``
* ``pwd``
* ``resource``
* ``termios``
* ``winsound``

Other stdlib C extensions use the internal C API for various reasons or are
using functions which are missing in the limited C API. Remaining issues should
be analyzed on a case by case basis.

This work shows that non-trivial C extensions can be written using only the
limited C API version 3.13.


What's Next?
============

PEP 741: Python Configuration C API
-----------------------------------

In Python 3.8, I added the ``PyConfig`` API to configure the Python
initialization. Problem: it has no stable ABI and is excluded from the limited
C API.

Recently, I proposed `PEP 741: Python Configuration C API
<https://peps.python.org/pep-0741/>`_ which is built on top of the
``PyConfig``, provides a stable ABI, and is compatible with the limited C API. I
submitted PEP 741 to the Steering Council.

Py_GetConstant()
----------------

Accessing constants reads private ABI symbols. For example, ``Py_None`` API
reads the private ``_Py_NoneStruct`` symbol at the stable ABI level.

I `proposed <https://github.com/python/cpython/pull/116883>`_ to change the
constant implementations to use function calls instead.  For example, reading
``Py_None`` would call ``Py_GetConstant(Py_CONSTANT_NONE)``.  The advantage is
that it adds 5 more constants: zero, one, empty string, empty bytes string, and
empty tuple. For example, ``Py_GetConstant(Py_CONSTANT_ZERO)`` gives the number
``0`` and the function cannot fail.

Cython and PyO3
---------------

Cython and PyO3 projects are two big consumers of the C API.

While Cython has an experimental build mode for the limited C API, it's still
incomplete. It would be nice to complete it to cover more use cases and more
APIs.

PyO3 can use the limited API but can still use the non-limited API for some use
cases. It would be interersting to only use the limited C API. The PEP 741 to
embed Python in Rust would be interesting for that.
