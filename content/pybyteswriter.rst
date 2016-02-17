++++++++++++++++++
_PyBytesWriter API
++++++++++++++++++

:date: 2016-02-17 02:00
:tags: cpython
:category: python
:slug: pybyteswriter
:authors: Victor Stinner
:summary: _PyBytesWriter API

The "bytes writer" (_PyBytesWriter) is an API designed to reduce the number of
memory reallocations when the output size is unknown. This article explains its
history.

During 2015 Q4, I focused my work on optimizing the bytes type. For me, it was
an opportunity for a new attempt to implement a fast "bytes writer API".


The _PyUnicodeWriter API
========================

Inefficient implementation of the PEP 393
-----------------------------------------

The core type str (Unicode) was reimplemented in Python 3.3 by the `PEP 393 --
Flexible String Representation <https://www.python.org/dev/peps/pep-0393/>`_ to
use less memory. The new internal structure is now very complex and require
to be smart when building a new string to avoid memory copies. I created
the _PyUnicodeWriter API to start to avoid expensive memory copies.

The first implementation of the PEP 393 used a lot of ``Py_UCS4*`` buffer which
used a lot of memory and required expensive conversion to ``Py_UCS1*`` (ASCII,
Latin1) or ``Py_UCS2*`` buffers.

Design of the API
-----------------

According to benchmarks, creating a ``Py_UCS1*`` buffer and then expand it
to ``Py_UCS2*`` or ``Py_UCS4*`` is more efficient, since ``Py_UCS1*`` is the
most common format.

Python ``str`` type is used for a wide range of usages. For example, it is
used for the name of variable names in the Python language itself. In practice,
variable names are pure ASCII in most cases.

The worst case for _PyUnicodeWriter is when a long ``Py_UCS1*`` buffer must be
converted ``Py_UCS2*`` and then to ``Py_UCS4*``. Each conversion is expensive:
need to allocate a second memory block, inefficient loop, etc.

Features:

* Optional overallocation: overallocate the buffer by 25% on Windows and 50%
  on Linux. The ratio changes depending on the OS, it is a raw heuristic to get
  the best performances depending on the system memory allocator
  (``malloc()``).
* Buffer can be a shared read-only buffer if the buffer was only created from
  a single string. Micro-optimization for ``"%s" % str``.

The API allows to disable overallocate before the last write. For example,
``"%s%s" % ('abc', 'def')`` disables the overallocation before writing
``'def'``.

Fast-path for ASCII
-------------------

The cool and *unexpected* side-effect of the _PyUnicodeWriter is that many
intermediate operations got a fast-path for ``Py_UCS1*``, especially for ASCII
strings. For example, padding a number with spaces on ``'%10i' % 123`` is
implemented with ``memset()``.

Formating a floating point number uses the ``PyOS_double_to_string()`` function
which creates an ASCII buffer. If the writer buffer uses Py_UCS1, a
``memcpy()`` is enough to copy the formatted number.


Avoid temporary buffers
-----------------------

Since the beginning, I had the idea of avoiding temporary buffers thanks
to an unified API to handle a "Unicode buffer". Slowly, I spread my changes
to all functions producing Unicode strings.

The obvious target were ``str % args`` and ``str.format(args)``. Both
instructions use very different code, but it was possible to share a few
functions especially the code to format integers.

The function formatting an integer computes the exact size of the output,
requested a number of characters and then write characters. The characters are
written directly in the writer buffer. Not only not temporary memory block is
allocated, but better: no Py_UCS conversion is need. ``_PyLong_Format()``
writes directly characters into the right format.


Speed?
------

The PEP 393 uses a complex storage for strings, so the exact performances
now depends on the character set used in the benchmark. For tests using
something else than ASCII, the result are more tricky to understand.

To compare performances with Python 2, I focused my benchmarks on ASCII.  I
compared Python 3 str with Python 2 unicode, but also sometimes to Python 2 str
(bytes). On ASCII, Python 3.3 was as fast as Python 2, or even faster on some
very specific cases, but most of them are probably artificial and never seen in
real applications.

In the best case, Python 3 str (Unicode) was faster than Python 2 bytes.


_PyBytesWriter API: first try, big fail
=======================================

Since Python was *much* faster with _PyUnicodeWriter, I expected to get good
speedup with a similar API for bytes. The graal would be to share code for
bytes and Unicode (spoiler: I reached this goal, but for a single function:
formatting an integer to decimal).

My first attempt of a _PyBytesWriter API was in 2013: `issue #17742:
https://bugs.python.org/issue17742 <Add _PyBytesWriter API>`_. I spent
hours to understand why GCC produced less efficient machine code. When
I started to dig the "strict aliasing" optimization issue, I realized that
I reached a deadend.

Extract of the structure::

    typedef struct {
        /* Current position in the buffer */
        char *str;

        /* Start of the buffer */
        char *start;

        /* End of the buffer */
        char *end;

        ...
    } _PyBytesWriter ;

https://bugs.python.org/issue17742#msg187595

Machine code is less efficient, new code::

    while (collstart++<collend)
        *writer.str++ = '?';

"For the "writer.str++" instruction, the new pointer value is written
immediatly in the structure. The pointer value is also read again at
each iteration. So we have 1 load and 1 store per iteration."

original code::

    while (collstart++<collend)
        *str++ = '?';

"GCC emits better code: str is stored in a register and the new value
of str is only written once, at the end of loop (instead of writing it
at each iteration). The pointer value is read before the loop. So we
have 0 load and 0 store (related to the pointer value) in the body of
the loop."

"It may be an aliasing issue, but I didn't find how to say to GCC that
the new value of writer.str can be written only once at the end of the
loop. I tried to add __restrict__ keyword: the load (get the pointer
value) is moved out of the loop. But the store is still in the body of
the loop."

I wrote to gcc-help: `Missed optimization when using a structure
<https://gcc.gnu.org/ml/gcc-help/2013-04/msg00192.html>`_, but I didn't get any
reply.


_PyBytesWriter API: new try, the good one
=========================================

https://bugs.python.org/issue25318

The new _PyBytesWriter doesn't contain the ``char*`` pointers anymore: they are
now local variables in functions. Instead, the API uses a ``char*`` parameter.
Example::

    PyObject * _PyBytesWriter_Finish(_PyBytesWriter *writer, char *str)

The idea is to keep ``char*`` pointers is function to keep the most efficient
machine code. The compiler doesn't have to compute complex aliasing rules
to decide if a CPU register can be used or not.

Features:

* Optional overallocation: overallocate the buffer by 25% on Windows and 50%
  on Linux. Same idea nd than _PyUnicodeWriter.
* Support ``bytes`` and ``bytearray`` type as output format.
* Small buffer of 512 bytes allocated on the stack to avoid completly the need
  of a buffer allocated on the heap before creating the final
  ``bytes``/``bytearray`` object.

A _PyBytesWriter structure must always be allocated on the stack.

While _PyUnicodeWriter has a 5 functions and 1 macro to write a single
character, write strings, write a substring, etc. _PyBytesWriter has a single
_PyBytesWriter_WriteBytes() function to write a string, since all other writes
are done directly with regular C code on ``char*`` pointers.

The API itself doesn't make the code faster, especially maybe some corner cases
like overallocation disabled on the last write, or the usage of the small
buffer allocated on the stack.

In Python 3.6, I optimized error handlers on various codecs: ASCII, Latin1
and UTF-8. For example, the UTF-8 encoder is now up to 75 times as fast for
error handlers: ``ignore``, ``replace``, ``surrogateescape``,
``surrogatepass``. ``bytes % int`` became between 30% and 50% faster on a
microbenchmark.

Later, I replaced ``char*`` type with ``void*`` to avoid compiler warnings
in functions using ``Py_UCS1*`` or ``unsigned char*``, unsigned types.
