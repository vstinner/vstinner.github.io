++++++++++++++++++++++
Python Subinterpreters
++++++++++++++++++++++

:date: 2020-12-23 14:00
:tags: cpython, subinterpreters
:category: cpython
:slug: isolate-subinterpreters
:authors: Victor Stinner

Multiphase initialization and heap types
========================================

* Multiphase: **64% (76/118)**. At 2020-10-06, 76 extensions on a total of 118
  use the new multi-phase initialization API. There are 42 remaining extensions
  using the old API (`bpo-163574 <https://bugs.python.org/issue1635741>`__).
* Heap types: **35% (69/200)**. At 2020-11-01, 69 types are defined as heap
  types on a total of 200 types. There are 131 remaining static types
  (`bpo-40077 <https://bugs.python.org/issue40077>`__).

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
