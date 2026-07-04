+++++++++++++++++++++++++++++++++++++
PEP 814: Add frozendict built-in type
+++++++++++++++++++++++++++++++++++++

:date: 2026-07-04 14:00
:tags: cpython
:category: cpython
:slug: pep-814-add-frozendict-builtin-type
:authors: Victor Stinner


PEP 416: Add a frozendict builtin type
======================================

In 2012, I was working actively on the `pysandbox project
<https://github.com/vstinner/pysandbox>`_. To implement this sandbox, I needed
read-only dictionaries and so I wrote `PEP 416 – Add a frozendict builtin type
<https://peps.python.org/pep-0416/>`_. Sadly, after 1 month of discussions,
Guido van Rossum (Python BDFL) rejected my PEP: read the `Rejection Notice
<https://peps.python.org/pep-0416/#rejection-notice>`_.

PEP 603: Adding a frozenmap type to collections
===============================================

In September 2019, Yury Selivanov wrote `PEP 603: Adding a frozenmap type to
collections <https://peps.python.org/pep-0603/>`_ and `started a discussion
<https://discuss.python.org/t/pep-603-adding-a-frozenmap-type-to-collections/2318>`_.
``frozenmap`` implementation is based on `Hash Array Mapped Trie (HAMT)
<https://en.wikipedia.org/wiki/Hash_array_mapped_trie>`_ data structure.
``frozenmap`` instances can be hashable just like ``tuple`` objects.
The API is similar to ``dict`` API, with additional methods:

* ``frozenmap.including(key, value)``
* ``frozenmap.excluding(key)``
* ``frozenmap.union(mapping=None, **kw)``
* ``frozenmap.mutating()``

Copying a ``frozenmap`` displays near O(1) performance for all benchmarked
dictionary sizes, whereas ``dict.copy()`` has O(n) complexity.

``frozenmap`` lookup time is ~30% slower than ``dict`` lookups on average.

``frozenmap`` doesn't preserve insertion order.

PEP 603 discussion got 215 messages, but it was submitted to the Steering
Council so far.

PEP 814 – Add frozendict built-in type
======================================

In November 2025, I wrote `PEP 814 – Add frozendict built-in type
<https://peps.python.org/pep-0814/>`_ with Donghee Na, and we `started a
discussion
<https://discuss.python.org/t/pep-814-add-frozendict-built-in-type/104854>`_.

Quickly, the PEP got updated to document that ``frozendict`` can be compared to
``dict``, the ``frozendict | frozendict`` union operation was documented,
copy was elaborated, more C API functions were added (like
``PyAnyDict_Check()`` and ``PyFrozenDict_New()``), and complexity of PEP 603
``frozenmap`` was clarified.

Adding a method to convert a ``dict`` to ``frozendict`` and type annotation
were added to Rejected Ideas.

The sentence "Using **immutable** values creates a hashable frozendict" was
replaced with "Using **hashable** values creates a hashable frozendict" to
clarify that hashable doesn't mean immutable.

In February 2026, the Steering Council accepted PEP 814, and also requested
some changes, like removing this paragraph:

    Immutable mappings can be used to safely share dictionaries across thread
    and asynchronous task boundaries. The immutability makes it easier to
    reason about threads and asynchronous tasks.

Implementation
==============

Reference Implementation of PEP 814 says:

* ``frozendict`` shares most of its code with the ``dict`` type.
* Add ``PyFrozenDictObject`` structure which inherits from ``PyDictObject`` and
  has an additional ``ma_hash`` member.

Most changes were done in `issue gh-141510
<https://github.com/python/cpython/issues/141510>`_.

In the current main branch, ``Objects/dictobject.c`` has around 8,500 lines.  A
coarse measurement is that only around 560 lines (7%) are specific to the
``frozendict`` implementation: most of the code is shared between ``dict`` and
``frozendict``!

Python 3.15 alpha 7 was the first release including ``frozendict``. Obviously,
many bugs have been quickly discovered! For example, ``frozendict.__init__()``
was implemented by mistake: this method allowed to modify an immutable
``frozendict`` which is wrong! The method has been simply removed.

Another example is that ``hash(frozendict)`` was modified to avoid creating a
temporary ``frozenset`` object, since the old implementation created surprising
error messages related to ``frozenset`` on a unhashable value. But the new hash
function has flaws, hash collisions were likely. The hash function was fixed to
compute hash of pairs.

``repr(frozendict)`` was modified to return ``frozendict()`` instead of
``frozendict({})`` for an empty dictionary.

Donghee Na optimized the ``frozendict`` implementation for Free Threading. For
example:

* ``len(frozendict)`` do no use atomic operation.
* Avoid locking whenever possible on ``repr(frozendict)``,
  ``frozenset.fromkeys()``, ``frozendict.copy()`` and
  ``frozendict | frozendict``.

Donghee also modified ``BINARY_OP_SUBSCR_DICT`` and ``CONTAINS_OP_DICT``
bytecode specialization to support ``frozendict``.

The ``can_modify_dict()`` function was added to detect attempts to modify a
frozendict when it should not be possible. These checks are only run in a debug
build.

``frozendict.fromkeys()`` was fixed to copy the ``frozendict`` if the type
constructor returns a ``frozendict``.


Return the frozendict unchanged
===============================

Since a ``frozendict`` is immutable, it's possible to return the same
``frozendict`` on multiple operations. Examples:

.. code-block:: python

   $ python3.15
   >>> fd=frozendict(x=1, y=2)
   >>> fd.copy() is fd
   True

   >>> empty=frozendict()
   >>> (fd | empty) is fd
   True
   >>> (empty | fd) is fd
   True

    >>> import copy
    >>> copy.copy(fd) is fd
    True


C API
=====

New functions:

* ``PyAnyDict_Check()``, ``PyAnyDict_CheckExact()``
* ``PyFrozenDict_Check()``, ``PyFrozenDict_CheckExact()``
* ``PyFrozenDict_New()``

In many functions which already accept ``dict``, accepting ``frozendict`` can
be easily done by replacing ``PyDict_Check()`` with ``PyAnyDict_Check()``.

The C API was adjusted to decide when the ``frozendict`` type are accepted or
not. Examples:

* ``PyDict_Update()``, ``PyDict_Merge()`` and ``_PyDict_MergeEx()`` no longer
  accept frozendict.
* ``PyDict_Contains()`` and ``PyDict_ContainsString()`` now raise
  ``SystemError`` if the argument type is not accepted.
* ``PyDict_MergeFromSeq2()`` now fails with ``SystemError`` if the first
  argument is not a ``dict`` or a ``dict`` subclass.
* Don't accept ``frozendict`` in ``PyDict_Watch()`` and ``PyDict_Unwatch()``. A
  ``frozendict`` cannot be modified, so it's not useful to watch for
  modifications.

Functions accepting ``fronzendict``:

* ``PyAnyDict_Check()``, ``PyAnyDict_CheckExact()``
* ``PyFrozenDict_Check()``, ``PyFrozenDict_CheckExact()``
* ``PyDictProxy_New()``
* ``PyDict_Size()``
* ``PyDict_GetItemRef()``, ``PyDict_GetItemStringRef()``
* ``PyDict_GetItem()``, ``PyDict_GetItemString()``, ``PyDict_GetItemWithError()``
* ``PyDict_Contains()``, ``PyDict_ContainsString()``
* ``PyDict_Keys()``, ``PyDict_Values()`` and ``PyDict_Items()``
* ``PyDict_Next()``
* ``PyDict_Clear()``

All ``PyDict`` functions reading a dictionary accept a ``frozendict``.

Also, a new ``PyFrozenDict_New()`` function was added to create a
``frozendict`` from a mapping (ex: from a mutable ``dict``).

``PyDict_Clear()`` is kind of special: it does nothing if the argument
is not a ``dict`` or a ``dict`` subclass.

The following abstract methods have also been modified to accept ``frozendict``:

* ``PyMapping_GetOptionalItem()``
* ``PyMapping_Keys()``
* ``PyMapping_Values()``
* ``PyMapping_Items()``

Functions which don't accept ``frozendict``:

* ``PyDict_Check()``, ``PyDict_CheckExact()``
* ``PyDict_Copy()``
* ``PyDict_Update()``
* ``PyDict_Merge()``
* ``PyDict_MergeFromSeq2()``
* ``PyDict_DelItem()``, ``PyDict_DelItemString()``
* ``PyDict_SetItem()``, ``PyDict_SetItemString()``
* ``PyDict_SetDefault()``, ``PyDict_SetDefaultRef()``
* ``PyDict_Pop()``, ``PyDict_PopString()``

Functions modifying a dictionary don't accept ``frozendict``. If they are
called with a ``frozendict``, at least a nice error message is provided to
guide the developer. For example, ``PyDict_SetItem()`` raises
``TypeError("frozendict object does not support item assignment")``.

First, ``PyDict_Copy()`` was modified to return a ``frozendict`` if the
argument is a ``frozendict``. But it was too surprising in existing C code
that the ``PyDict_Copy()`` result type can now be ``frozendict``. Copying a
``frozendict`` is expected to return the same object unchanged, since it's
immutable. At the end, it was decided to reject ``frozendict`` in
``PyDict_Copy()``.

I added an internal ``_PyDict_CopyAsDict()`` function for functions creating a
modified ``frozendict`` copy.


Use frozendict in the Standard Library
======================================

``eval()`` and ``exec()`` accept ``frozendict`` for globals, and ``type()`` and
``str.maketrans()`` accept ``frozendict`` for dict.

Code checking for ``dict`` type using ``isinstance(arg, dict)`` can be updated
to ``isinstance(arg, (dict, frozendict))`` to accept also the ``frozendict``
type, or to ``isinstance(arg, collections.abc.Mapping)`` to accept also other
mapping types such as ``types.MappingProxyType``.

Modules:

* ``copy``
* ``decimal`` (to set context flags)
* ``json``
* ``marshal`` (version increased to 6)
* ``pickle``
* ``plistlib`` (only for serialization)
* ``pprint``
* ``xml.etree.ElementTree``

It's now possible to pass ``object_hook=frozendict`` to the JSON decoder to
create ``frozendict`` instead of ``dict``:

.. code-block:: python

   >>> json.loads('{"x": 1}', object_hook=frozendict)
   frozendict({'x': 1})

I `had to fix a corner case
<https://github.com/python/cpython/commit/646bd86e3b2f4f484129bd4a926cf73fafc9f874>`_
in ``copy.deepcopy()`` when copying a ``frozendict`` which... contains itself!

Methods:

* ``dataclasses.field``: ``Field.metadata`` becomes a empty ``frozendict``
  if there is no metadata.
* ``email.headerregistry.ParameterizedMIMEHeader.params`` type is now
  ``frozendict`` instead of ``MappingProxyType``.

Private variables or variables of private modules:

* ``functools._convert``
* ``gettext._binary_ops``
* ``gettext._c2py_ops``
* ``json.decoder._CONSTANTS``
* ``json.tool._group_to_theme_color``
* ``opcode._cache_format``
* ``opcode._inline_cache_entries``
* ``optparse._builtin_cvt``
* ``platform._ver_stages``
* ``platform._default_architecture``
* ``plistlib._BINARY_FORMAT``
* ``_ssl._PROTOCOL_NAMES``
* ``symtable._scopes_value_to_name``
* ``tarball._NAMED_FILTERS``
* ``_opcode_metadata._specializations``
* ``_opcode_metadata._specialized_opmap``
* ``_opcode_metadata.opmap``

Rejected changes:

* ``errno.errorcode`` (`PR gh-144906 <https://github.com/python/cpython/pull/144906>`_)

Bugs involving the garbage collector
====================================

`Issue gh-151722 <https://github.com/python/cpython/issues/151722>`_ was
created to report a bug using ``gc.get_objects()``: it was possible to see a
``frozendict`` being modified in Python!

While ``frozendict`` are immutable in Python, the C implementation creates
an empty ``frozendict``, set items and then return the new ``frozendict`` to
Python. The problem is that it's possible to see the internal ``frozendict``
using ``gc.get_objects()``.

The issue was fixed by only tracking ``frozendict`` once it's fully
initialized, instead of tracking it when it's created (empty). Multiple C
functions creating ``frozendict`` have been fixed for this issue.

Later, a similar issue has been discovered in ``frozenset``:
`issue gh-152235 <https://github.com/python/cpython/issues/152235>`_.


Options on Python 3.14 and older
================================

Python 3.15 final is `scheduled for October 2026
<https://peps.python.org/pep-0790/>`_. Until that, there are different options
to use an immutable dictionary on Python 3.14 and older.

MappingProxyType
----------------

First, ``types.MappingProxyType`` is available since Python 3.3. It can be
used to get a read-only proxy on a dictionary. It's not possible to modify
the private, but if the underlying dictionary is modified, the proxy is updated
as well.

Example:

.. code-block:: python

   $ python3.14
   >>> import types
   >>> private={'key': 'value'}

   >>> public=types.MappingProxyType(private)
   >>> public['key']
   'value'
   >>> public['key']='value2'
   TypeError: 'mappingproxy' object does not support item assignment

   >>> private['key']='value2'
   >>> public['key']
   'value2'

Moreover, it's possible to access the internal mutable dictionary.
Example using the ``gc`` module:

.. code-block:: python

   $ python3.14
   >>> import types, gc
   >>> mapping = types.MappingProxyType({'secret': 'dict'})
   >>> internal_dict = gc.get_referents(mapping)[0]
   >>> internal_dict['secret'] = 'not so secret'
   >>> mapping
   mappingproxy({'secret': 'not so secret'})

frozendict on PyPI
------------------

The `frozendict project <https://pypi.org/project/frozendict/>`_ by Marco Sulla
provides a ``frozendict`` type with is similar to Python 3.15 built-in
``frozendict`` type, but with additional methods:

* ``set(key, value)``
* ``delete(key)``
* ``setdefault(key[, default])``
* ``key([index])``
* ``value([index])``
* ``item([index])``

On Python 3.6 to 3.10, it uses a C implementation. On other Python versions,
the ``frozendict`` type is implemented in Python (it inherits from the ``dict``
type).

namedtuple
----------

While ``collections.namedtuple`` doesn't implement the mapping protocol, it is
sometimes used when an immutable object is needed.
