*********************************
PEP 782 – Add PyBytesWriter C API
*********************************

:date: 2025-10-17 13:00
:tags: c-api, cpython
:category: cpython
:slug: pep-782-pybyteswriter-c-api
:authors: Victor Stinner

.. image:: {static}/images/arrietty.jpg
   :alt: The Secret World of Arrietty
   :target: https://en.wikipedia.org/wiki/Arrietty

In the Python C API, I dislike APIs modifying immutable objects such as
``_PyBytes_Resize()``. I designed a whole new ``PyBytesWriter`` API to
replace this ``_PyBytes_Resize()`` function. As usual in Python, it took
multiple iterations and one year to design the API and to reach an
agreement.

Picture: *The Secret World of Arrietty by Hayao Miyazaki*.

Original private _PyBytesWriter API
===================================

In 2016 (Python 3.6), I designed a private ``_PyBytesWriter`` API to
create ``bytes`` objects in an efficient way, especially by
overallocating a buffer. See my article `Fast _PyAccu, _PyUnicodeWriter
and_PyBytesWriter APIs to produce strings in CPython
<https://vstinner.github.io/pybyteswriter.html>`_ about this API (and
other similar APIs).

In July 2023 (Python 3.13), I moved the private ``_PyBytesWriter`` API
to the internal C API. See the article `Remove private C API functions
<https://vstinner.github.io/remove-c-api-funcs-313.html>`_.

First public API attempt
========================

In June 2024, Marc-Andre Lemburg `asked
<https://github.com/capi-workgroup/problems/issues/70#issuecomment-2158541011>`_
to make the private ``_PyBytesWriter`` API public.

In July, I wrote a first public API attempt: `PR gh-121726
<https://github.com/python/cpython/pull/121726>`_. API:

.. code-block:: c

   PyBytesWriter* PyBytesWriter_Create(Py_ssize_t size, char **str)
   PyObject* PyBytesWriter_Finish(PyBytesWriter *writer, char *str)
   void PyBytesWriter_Discard(PyBytesWriter *writer)

   int PyBytesWriter_Prepare(PyBytesWriter *writer, char **str, Py_ssize_t size)
   int PyBytesWriter_WriteBytes(PyBytesWriter *writer, char **str, const void *bytes, Py_ssize_t size)

Example creating the string ``"abc"``:

.. code-block:: c

   PyObject*
   create_abc(void)
   {
       char *str;
       PyBytesWriter *writer = PyBytesWriter_Create(3, &str);
       if (writer == NULL) {
           return NULL;
       }

       memcpy(str, "abc", 3);
       str += 3;

       return PyBytesWriter_Finish(writer, str);
   }

With a ``PyBytesWriter_Prepare(writer, &str, size)`` to preallocate the
buffer.

The implementation was fully based on the private structure:

.. code-block:: c

   typedef struct {
       PyObject *buffer;
       Py_ssize_t allocated;
       Py_ssize_t min_size;
       int use_bytearray;
       int overallocate;
       int use_small_buffer;
       char small_buffer[512];
   } _PyBytesWriter;

In August, I created a `C API Working Group decision
<https://github.com/capi-workgroup/decisions/issues/39>`_. Sadly, this
API didn't convinced the C API WG which found the ``Prepare()`` API
confusing and the *str* variable hard to use.

In October, I closed the decision issue:

    It seems like this API is too low-level and too error-prone. I
    prefer to abandon promoting this API as a public API for now. We can
    revisit this API later if needed.

Second public API attempt
=========================

In February 2025, I gave a try to a second public API:
`issue gh-129813 <https://github.com/python/cpython/issues/129813>`_
and `PR gh-129814 <https://github.com/python/cpython/pull/129814>`_.
API:

.. code-block:: c

   void* PyBytesWriter_Create(PyBytesWriter **writer, Py_ssize_t alloc)
   void PyBytesWriter_Discard(PyBytesWriter *writer)
   PyObject* PyBytesWriter_Finish(PyBytesWriter *writer, void *buf)

   void* PyBytesWriter_Extend(PyBytesWriter *writer, void *buf, Py_ssize_t extend)
   void* PyBytesWriter_WriteBytes(PyBytesWriter *writer, void *buf, const void *bytes, Py_ssize_t size)
   void* PyBytesWriter_Format(PyBytesWriter *writer, void *buf, const char *format, ...)

The API now uses ``void*`` instead of ``char*`` for the buffer and I
added ``PyBytesWriter_Format()`` function.

Example creating the string ``"abc"``:

.. code-block:: c

   PyObject*
   create_abc(void)
   {
       PyBytesWriter *writer;
       char *buf = PyBytesWriter_Create(&writer, 3);
       if (buf == NULL) {
           return NULL;
       }

       memcpy(buf, "abc", 3);
       buf += 3;

       return PyBytesWriter_Finish(writer, buf);
   }

The API is similar to the first version, but ``PyBytesWriter_Create()``
now returns a ``void*`` instead of the ``PyBytesWriter*``.

With a ``buf = PyBytesWriter_Extend(writer, buf, str_size)`` API to
preallocate the bufer.

The implementation now uses a new dedicated simpler structure (less
members):

.. code-block:: c

   struct PyBytesWriter {
       char small_buffer[256];
       PyObject *obj;
       Py_ssize_t size;
       int use_bytearray;
   };

This time, I followed **Petr Viktorin**'s advice and I created a
`discussion on Discourse
<https://discuss.python.org/t/add-pybyteswriter-public-c-api/81182>`_.
Again, the API was not liked by other developers who were confused by
the API.

In March, I gave up again, and closed my PR:

    It seems like most developers are confused by the API which requires
    to pass writer and buf to most functions. I abandon this API.

Third public API: PEP 782
=========================

Following **Antoine Pitrou**'s link, I had a look at `Arrow C++
BufferBuilder API
<https://github.com/apache/arrow/blob/b3d218c819283bafe973dc7deb5214324f4a68b2/cpp/src/arrow/buffer_builder.h#L176-L191>`_.
Antoine helped me to design a better API using size and without the
``void *buf`` parameter.

At the end of March, I wrote `PEP 782 – Add PyBytesWriter C API
<https://peps.python.org/pep-0782/>`_ and created a `new discussion on
the PEP
<https://discuss.python.org/t/pep-782-add-pybyteswriter-c-api/86617>`_.

Example creating the string ``"abc"``:

.. code-block:: c

   PyObject *
   create_abc(void)
   {
       PyBytesWriter *writer = PyBytesWriter_Create(3);
       if (writer == NULL) {
           return NULL;
       }

       char *buf = PyBytesWriter_GetData(writer);
       memcpy(buf, "abc", 3);

       return PyBytesWriter_Finish(writer);
   }

With a ``PyBytesWriter_Resize(writer, size)`` API to preallocate the
buffer. The *size* is now absolute, rather than being relative.

The mandatory ``void *buf`` parameter was replaced with
``PyBytesWriter_GetData()`` function.

In May, I submitted the PEP to the Steering Council. In September, the
Steering Council `approved PEP 782
<https://discuss.python.org/t/pep-782-add-pybyteswriter-c-api/86617/15>`_!
(Yeah, it took them 4 months to take a decision.)


Final API
=========

.. code-block:: c

   PyBytesWriter* PyBytesWriter_Create(Py_ssize_t size)
   void PyBytesWriter_Discard(PyBytesWriter *writer)
   PyObject* PyBytesWriter_Finish(PyBytesWriter *writer)
   PyObject* PyBytesWriter_FinishWithSize(PyBytesWriter *writer, Py_ssize_t size)
   PyObject* PyBytesWriter_FinishWithPointer(PyBytesWriter *writer, void *buf)

   void* PyBytesWriter_GetData(PyBytesWriter *writer)
   Py_ssize_t PyBytesWriter_GetSize(PyBytesWriter *writer)

   int PyBytesWriter_WriteBytes(PyBytesWriter *writer, const void *bytes, Py_ssize_t size)
   int) PyBytesWriter_Format(PyBytesWriter *writer, const char *format, ...)

   int PyBytesWriter_Resize(PyBytesWriter *writer, Py_ssize_t size)
   int PyBytesWriter_Grow(PyBytesWriter *writer, Py_ssize_t size)
   void* PyBytesWriter_GrowAndUpdatePointer(PyBytesWriter *writer, Py_ssize_t size, void *buf)

See the `documentation <https://docs.python.org/dev/c-api/bytes.html#pybyteswriter>`_.

Implementation
==============

In September, I implemented the ``PyBytesWriter`` API in the main branch
(future Python 3.15) with documentation and tests.

I also modified code using soft deprecated APIs,
``PyBytes_FromStringAndSize(NULL, size)`` and ``_PyBytes_Resize()``,  to
use the new ``PyBytesWriter`` API instead. When doing these conversions,
I ran benchmarks to check that there is no significant impact on
performance. Examples of benchmarks:

* `os.read(1)
  <https://github.com/python/cpython/pull/138829#issuecomment-3288634427>`_
* `io.FileIO.read(1)
  <https://github.com/python/cpython/pull/138955#issuecomment-3293995606>`_
* `io.BufferedReader.read1(1)
  <https://github.com/python/cpython/pull/138954#issuecomment-3293959389>`_
* `utf8_encoder()
  <https://github.com/python/cpython/pull/138874#issuecomment-3288721255>`_

For example, I abandonned these two changes:

* `bytes_concat: 1.4x slower
  <https://github.com/python/cpython/pull/138840#issuecomment-3288640248>`_
* `_json: 1.10x slower
  <https://github.com/python/cpython/pull/138957>`_

Later, other people joined the party and found other opportunity for
``PyBytesWriter`` with great optimizations:

* `zstd: 10-30% speedup for decompression
  <https://github.com/python/cpython/pull/139976>`_
* `Python parser, concatenate bytes strings: 4x faster
  <https://github.com/python/cpython/pull/140150>`_
* `io.RawIOBase.readall(): 4x faster
  <https://github.com/python/cpython/pull/140139>`_
