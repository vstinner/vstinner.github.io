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
Guido van Rossum (Python former `BDFL
<https://en.wikipedia.org/wiki/Benevolent_dictator_for_life>`_) rejected my
PEP: read the `Rejection Notice
<https://peps.python.org/pep-0416/#rejection-notice>`_.

Note: In 2013, I announced the `failure of the pysandbox project
<https://lwn.net/Articles/574215/>`_.

PEP 603: Adding a frozenmap type to collections
===============================================

In September 2019, Yury Selivanov wrote `PEP 603: Adding a frozenmap type to
collections <https://peps.python.org/pep-0603/>`_ and `started a discussion
<https://discuss.python.org/t/pep-603-adding-a-frozenmap-type-to-collections/2318>`_.
``frozenmap`` implementation is based on `Hash Array Mapped Trie (HAMT)
<https://en.wikipedia.org/wiki/Hash_array_mapped_trie>`_ data structure.
``frozenmap`` instances can be hashable just like ``tuple`` objects.
The API is similar to ``dict`` API, with additional methods:

* ``including(key, value)``
* ``excluding(key)``
* ``union(mapping=None, **kw)``
* ``mutating()``

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
the copy was elaborated, more C API functions were added (like
``PyAnyDict_Check()`` and ``PyFrozenDict_New()``), and complexity of PEP 603
``frozenmap`` was clarified.

Adding a method to convert a ``dict`` to ``frozendict`` and type annotation
were added to `Deferred Ideas
<https://peps.python.org/pep-0814/#deferred-ideas>`_.

The sentence "Using **immutable** values creates a hashable frozendict" was
replaced with "Using **hashable** values creates a hashable frozendict" to
clarify that hashable doesn't mean immutable.

In February 2026, the Steering Council `accepted PEP 814
<https://discuss.python.org/t/pep-814-add-frozendict-built-in-type/104854/121>`_,
but also requested some changes, like removing this paragraph:

    Immutable mappings can be used to safely share dictionaries across thread
    and asynchronous task boundaries. The immutability makes it easier to
    reason about threads and asynchronous tasks.

Implementation
==============

The Reference Implementation section of PEP 814 says:

* ``frozendict`` shares most of its code with the ``dict`` type.
* Add ``PyFrozenDictObject`` structure which inherits from ``PyDictObject`` and
  has an additional ``ma_hash`` member.

In the current main branch, ``Objects/dictobject.c`` has around 8,500 lines.  A
coarse measurement is that only around 560 lines (7%) are specific to the
``frozendict`` implementation: so most of the ``dict`` code is shared with
``frozendict``!

Most changes were done in the `issue gh-141510
<https://github.com/python/cpython/issues/141510>`_.

Python 3.15 alpha 7 was the first release including ``frozendict``. Obviously,
many bugs have been quickly discovered! For example, the
``frozendict.__init__()`` method was implemented by mistake: this method
allowed to modify an immutable ``frozendict`` which is plain wrong! The method
has been simply removed.

I `fixed
<https://github.com/python/cpython/commit/244300162d2e863a0588d1754e224d68931ada37>`_
``hash(frozendict)``, the old implementation created too many hash collision.
The new code now computes hash of ``(key, value)`` pairs

``repr(frozendict)`` was modified to return ``'frozendict()'`` instead of
``'frozendict({})'`` for an empty dictionary.

Donghee Na optimized the ``frozendict`` implementation for Free Threading. For
example:

* ``len(frozendict)`` do no use atomic operation.
* Avoid locking whenever possible on ``repr(frozendict)``,
  ``frozenset.fromkeys()``, ``frozendict.copy()`` and
  ``frozendict | frozendict``.

Donghee also modified ``BINARY_OP_SUBSCR_DICT`` and ``CONTAINS_OP_DICT``
bytecode specialization to support ``frozendict``.

The helper function ``can_modify_dict()`` was added to debug mode to make sure
that a ``frozendict`` is only modified when it's not visible in Python. It must
not be tracked by the garbage collector and it must have a reference count of
``1``.

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

New functions have beend added to Python 3.15 C API:

* ``PyAnyDict_Check()``, ``PyAnyDict_CheckExact()``
* ``PyFrozenDict_Check()``, ``PyFrozenDict_CheckExact()``
* ``PyFrozenDict_New()``

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

All ``PyDict`` functions reading a dictionary accept a ``frozendict``. So
existing C extensions using these functions don't need to be updated to accept
``frozendict``.

Note: ``PyDict_Clear()`` is kind of special: it does nothing if the argument is
not a ``dict`` or a ``dict`` subclass.

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
that the ``PyDict_Copy()`` result type can now be ``frozendict``. Moreover,
copying a ``frozendict`` is expected to return the same object unchanged, since
it's immutable. At the end, it was decided to reject ``frozendict`` in
``PyDict_Copy()``.

Note: I added an internal ``_PyDict_CopyAsDict()`` function to copy a ``dict``
or a ``frozendict`` as a new (mutable) ``dict``.


Use frozendict in the Standard Library
======================================

``eval()`` and ``exec()`` accept ``frozendict`` for globals, and ``type()`` and
``str.maketrans()`` accept ``frozendict`` for dict.

Modules modified to accept ``frozendict``:

* ``copy``
* ``decimal`` (to set context flags)
* ``json``
* ``marshal`` (version increased to 6)
* ``pickle``
* ``plistlib`` (only for serialization)
* ``pprint``
* ``xml.etree.ElementTree``

It's now possible to pass ``object_hook=frozendict`` to the JSON decoder to
create ``frozendict`` dictionaries:

.. code-block:: python

   >>> json.loads('{"x": 1}', object_hook=frozendict)
   frozendict({'x': 1})

Methods:

* ``dataclasses.field``: ``Field.metadata`` becomes a empty ``frozendict``
  if there is no metadata.
* ``email.headerregistry.ParameterizedMIMEHeader.params`` type is now
  ``frozendict`` instead of ``MappingProxyType``.

Private variables and variables of private modules converted to ``frozendict``:

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

PEP 814 planned to convert more dictionares to ``frozendict`` in the standard
library, but the Steering Council asked:

    Stdlib adoption should happen with each module maintainer’s approval, not
    as a mechanical sweep.

The ``errno.errorcode`` change (`PR gh-144906
<https://github.com/python/cpython/pull/144906>`_) was rejected by the module
maintainer (Thomas Wouters), since there are legit use cases to modify
the ``errno.errorcode`` dictionary.

Converting the 3 ``_opcode_metadata`` dictionaries to ``frozendict`` broke the
Cinder project. Because of the rejected ``errno`` change and the Cinder
regression, it was decided to not convert more stdlib dictionaries to
``frozendict``.


Frozendict special cases
========================

Only the frozendict mapping is immutable. Values can still be mutable. Example:

.. code-block:: python

   >>> fd=frozendict(x=[1])
   >>> fd['x'].append(2)
   >>> fd
   frozendict({'x': [1, 2]})

A frozendict is only hashable if all values are hashtable. Example:

.. code-block:: python

   >>> hash(frozendict(x=1, y=2))  # hashable values
   -3593417788644647096
   >>> hash(frozendict(x=1, y=[]))  # not hashable values
   TypeError: unhashable type: 'list'

I `had to fix a corner case
<https://github.com/python/cpython/commit/646bd86e3b2f4f484129bd4a926cf73fafc9f874>`_
in ``copy.deepcopy()`` when copying a ``frozendict`` which... contains itself!
Example of such dictionary:

.. code-block:: python

   # recursive frozendict
   fd = frozendict(foo=[])
   fd['foo'].append(fd)


Bugs involving the garbage collector
====================================

`Issue gh-151722 <https://github.com/python/cpython/issues/151722>`_ was
created to report a bug using ``gc.get_objects()``: it was possible to see a
``frozendict`` being modified in Python!

While ``frozendict`` are immutable in Python, the C implementation creates
an empty ``frozendict``, set items and then return the new ``frozendict`` to
Python. The problem is that it was possible to see the internal ``frozendict``
being modified using ``gc.get_objects()``.

The issue was fixed by only tracking ``frozendict`` in the garbage collector
once it's fully initialized, instead of tracking it as soon as it's created
(empty). Multiple C functions creating ``frozendict`` had to be fixed for this
issue.

Later, Donghee discovered (and fixed) a similar issue in ``frozenset``: `issue
gh-152235 <https://github.com/python/cpython/issues/152235>`_.


Update your code for frozendict
===============================

Python code
-----------

Code checking for ``dict`` type using ``isinstance(arg, dict)`` can be updated
to ``isinstance(arg, (dict, frozendict))`` to accept also the ``frozendict``
type, or to ``isinstance(arg, collections.abc.Mapping)`` to accept also other
mapping types such as ``types.MappingProxyType``.

C code
------

In many functions which already accept ``dict``, accepting ``frozendict`` can
be easily done by replacing ``PyDict_Check()`` with ``PyAnyDict_Check()``.

C code which only reads dictionaries with functions like
``PyDict_GetItemRef()`` don't need to be updated to accept ``frozendict``.


Options on Python 3.14 and older
================================

Python 3.15 final is `scheduled for October 2026
<https://peps.python.org/pep-0790/>`_. Until that, there are different options
to use an immutable dictionary on Python 3.14 and older.

MappingProxyType
----------------

When the PEP 416 got rejected, I added ``types.MappingProxyType`` to Python
3.3. It can be used to create a read-only proxy of a dictionary. It's not
possible to modify the proxy, but if the underlying dictionary is modified, the
proxy is updated as well.

Example:

.. code-block:: python

   $ python3.14
   >>> import types
   >>> private = {'key': 'value'}

   >>> proxy = types.MappingProxyType(private)
   >>> proxy['key']
   'value'
   >>> proxy['key'] = 'value2'
   TypeError: 'mappingproxy' object does not support item assignment

   >>> private['key'] = 'value2'
   >>> proxy['key']
   'value2'

Note: there are ways to access the internal mutable dictionary. Example using
the ``gc`` module:

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
provides a ``frozendict`` type with is similar API to Python 3.15 built-in
``frozendict`` type, but with additional methods:

* ``set(key, value)``
* ``delete(key)``
* ``setdefault(key[, default])``
* ``key([index])``
* ``value([index])``
* ``item([index])``

On Python 3.6 to 3.10, it uses a C implementation. On other Python versions,
the ``frozendict.frozendict`` type is implemented in Python (it inherits from
the ``dict`` type).

There are multiple other PyPI projects providing ``frozendict``, sometimes
under a different name, such as ``immutabledict``.

namedtuple
----------

While ``collections.namedtuple`` doesn't implement the mapping protocol, it is
sometimes used to create immutable objects.
