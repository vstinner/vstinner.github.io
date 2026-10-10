++++++++++++++++++++++++++++++++++++++++++
Convert C functions to PyBytesWriter C API
++++++++++++++++++++++++++++++++++++++++++

:date: 2027-10-10 19:00
:tags: c-api, cpython
:category: cpython
:slug: convert-to-pybyteswriter-c-api
:authors: Victor Stinner

This article describes my recent work on ``PyBytesWriter`` and
``PyUnicodeWriter``, bugfixes, optimizations, documentation changes, with some
references to older work.

``PyBytesWriter`` is now **1.28x faster** on a micro-benchmark creating the
string ``b'abc'``.  ``PyUnicodeWriter`` can now avoid memory copies in some
cases.

In debug mode, ``PyBytesWriter`` and ``PyUnicodeWriter`` can now detect buffer
overflows, and Python checks if singletons have been modified by mistake at
exit (detect silent memory corruption).

``PyBytesWriter`` has been fixed to handle properly memory allocation failure.

I also made documentation and tests enhancements.

See also the previous article: `PEP 782 – Add PyBytesWriter C API
<{filename}/pep-782-pybyteswriter.rst>`_.

Convert to PyBytesWriter
========================

Recently, I modified the following code to use ``PyBytesWriter``:

* ``CJK codecs``
* ``PySSL_RAND()``
* ``Python/assemble.c``
* ``_Py_strhex_impl()``
* ``_zstd.finalize_dict()``
* ``_zstd.train_dict()``
* ``bytes.translate()``
* ``codecs``
* ``codeobject.c``
* ``io _textiowrapper_writeflush()``
* ``winconsoleio.c``
* ``xml.etree``

In the current main branch, excluding tests and doc, there are:

* 82 calls to ``PyBytesWriter_Create()``.
* 23 calls to soft deprecated ``PyBytes_FromStringAndSize(NULL, size)``
* 18 calls to soft deprecated ``_PyBytes_Resize()``

So the majority of functions creating ``bytes`` objects now use the new
``PyBytesWriter_Create()`` API.

The UTF-32 keeps a code path using ``PyBytes_FromStringAndSize(NULL, size)``:
fast path if the input string kind is UCS-1.

When I modified the UTF-7 encoder, I had some concerns about performance, but
hopefully I found `optimization opportunities
<https://github.com/python/cpython/pull/139253>`_ making the encoder **1.13x
faster** in average.

In two cases, ``PyBytes_FromStringAndSize(NULL, size)`` was replaced with
``PyMem_Malloc()`` since no Python ``bytes`` object is needed:
``decode_unicode_with_escapes()`` and ``memoryview.hex()``.

See also `issue gh-139156 <https://github.com/python/cpython/issues/139156>`_
(September 2025) where I converted most Unicode encoders to ``PyBytesWriter``.


Documentation
=============

I added the following note to `PyBytesObject documentation
<https://docs.python.org/dev/c-api/bytes.html#bytes-objects>`_:

    **CPython implementation detail:** The internal buffer of PyBytesObject
    always includes an **extra trailing null byte** for compatibility with null
    terminated C strings. This extra byte is not counted in PyBytes_Size() nor
    in the various length and size arguments of the functions below.

Thanks to this change, **Nathan Goldbaum** noticed that RustPython doesn't
implement this trailing null byte and `reported the issue to RustPython
<https://github.com/RustPython/RustPython/issues/8685>`_.

I added a `similar note to Unicode objects <https://docs.python.org/dev/c-api/unicode.html#unicode-objects>`_.


Detect bugs
===========

Check if a bytes object is mutable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A ``bytes`` object is immutable in Python. But in C, it can be mutated under
some strict conditions. I added ``_PyBytes_IsMutable()`` assertion to check
that:

.. code-block:: c

   // Make sure that a bytes object can still be mutated.
   //
   // Usage: assert(_PyBytes_IsMutable(obj)).
   int
   _PyBytes_IsMutable(PyObject *self)
   {
       assert(PyBytes_Check(self));
       // Do not use _PyObject_IsUniquelyReferenced(): this function is called
       // by bytearray and PyBytesWriter which can be used by multiple threads.
       assert(Py_REFCNT(self) == 1);
       assert(!_Py_IsImmortal(self));

       // Check that the object is not a singleton
       Py_ssize_t size = PyBytes_GET_SIZE(self);
       if (size == 0) {
           assert(self != bytes_get_empty());
       }
       else if (size == 1) {
           unsigned char ch = PyBytes_AS_STRING(self)[0];
           assert(self != (PyObject*)CHARACTER(ch));
       }

       // gh-158219: The hash value must not be cached yet. Otherwise, it means
       // that the bytes object was already used in Python somehow (ex: as a
       // dictionary key).
       assert(get_ob_shash((PyBytesObject *)self) == -1);

       return 1;
   }

For example, the check is used in ``_PyBytes_Resize()`` to make sure that it's
safe to resize an object in-place. It's also used by ``PyBytesWriter`` to check
that we are not modifying a singleton.

I added a similar ``_PyUnicodeWriter_CanWrite()`` for ``PyUnicodeWriter``. For
example, it checks that the internal buffer is not read-only.


Detect buffer overflow in PyBytesWriter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

I modified ``PyBytesWriter`` to detect buffer overflow in debug mode. It writes
a canary byte (``0xDD``) at the end of the buffer, and checks if this byte has
been overwritten. When the buffer uses a ``bytes`` or ``bytearray`` object,
use the trailing null byte as the canary byte.

Previously, debug hooks on Python memory allocators already reported buffer
overflow, but not when the trailing null byte was overwritten.

The new ``byteswriter_check_consistency()`` assertion checks the canary, but
also that the buffer object can be mutated.

I added a similar buffer overflow check to ``PyUnicodeWriter_Finish()``.

Detect Python singleton corruptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In debug mode at Python exit, check if immutable singleton objects have been
modified by mistake to detect bugs in C extensions: `commit
<https://github.com/python/cpython/commit/8bcbcf8cfc73844154f87c29b37ebb51cd8cb9b7>`__.
Add tests corrupting bytes, str, bool and int singleton objects.

I wrote this new generic debug feature after I saw a bug report from Serhiy
**Storchaka** where `sqlite3 corrupts a bytes singleton object
<https://github.com/python/cpython/issues/155702>`_. Such memory corruption
is silent and can remain unnoticed for a long time. The checks that I added
make sure that the corruption is detected at Python exit.


Fix MemoryError handling
========================

There was also a tricky bug in ``PyBytesWriter_Resize()`` on ``MemoryError``. I
added ``_PyBytes_ResizeKeepOnError()`` which leaves the bytes object unchanged
on memory allocation failure; ``PyBytesWriter_Resize()`` now calls it.

Other similar fixes:

* Leave ``bytearray`` unchanged if ``resize()`` fails (``MemoryError``).
* Do not close ``io.BytesIO`` on ``MemoryError``.

Bug fixes
=========

* Check size in ``PyBytesWriter_FinishWithSize()``.
* Fix ``struct.pack('0p', bytes)`` and  ``xmlcharrefreplace()``: don't write
  a null byte outside the buffer.
* Fix ``set_nomemory()``, so it can be run on ``Py_TRACE_REFS`` builds
  (`commit <https://github.com/python/cpython/commit/051b168e63af80872222a2d91d43af4de16980b1>`__).
* Use ``const char*`` for ``PyBytes_AS_STRING()`` since ``bytes`` is immutable.

Optimizations
=============

``PyBytesWriter``
^^^^^^^^^^^^^^^^^

``PyBytesWriter_FinishWithSize()`` now returns a single byte singleton
when a ``bytes`` was allocated.

I also `optimized mashal
<https://github.com/python/cpython/commit/658612ae770aac8e1e5e060922d3364a4be7e547>`_
to return bytes singletons. It makes the code shorter and easier to understand!

I also made multiple changes to optimize ``PyBytesWriter`` to reduce its
overhead compated to ``PyBytes_FromStringAndSize(NULL, size)``. I ran a
`benchmark creating the string b'abc'
<https://github.com/python/cpython/issues/158585#issuecomment-5986531617>`__ to
compare Python 3.15 to Python 3.16:

``Mean +- std dev: [py315] 41.6 ns +- 1.0 ns -> [py316] 32.5 ns +- 0.6 ns: 1.28x faster``

The `PyBytesWriter` API is now **1.28x faster** (**-9.1 ns**)!


``PyUnicodeWriter``
^^^^^^^^^^^^^^^^^^^

``PyUnicodeWriter_Create(size)`` no longer allocates immediately a buffer: the
buffer is now allocated at the first write.

If no buffer is allocated yet, ``PyUnicodeWriter_WriteStr()`` stores the
``str`` object as a read-only buffer to avoid memory copy. In the same way,
``PyUnicodeWriter_WriteChar()`` stores a single character singleton for
characters in range U+0000-U+00ff (ASCII and Latin1 characters).


Tests
=====

I added more tests on the C API:

* Add tests on the ``PyType`` C API
* Test ``PyBytesWriter_FinishWithSize()`` with negative size
* Add more ``PyBytesWriter`` tests
* Add tests on the deprecated ``_Py_Identifier`` (Unicode) C API
* Complete ``PyMarshal`` C API tests
* Add ``MemoryError`` tests to ``PyUnicodeWriter``
* Add more tests on the PyUnicode C API
