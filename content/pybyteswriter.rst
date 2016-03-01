+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Fast _PyAccu, _PyUnicodeWriter and_PyBytesWriter APIs to produce strings in CPython
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-03-01 16:00
:tags: cpython
:category: python
:slug: pybyteswriter
:authors: Victor Stinner
:summary: _PyBytesWriter API

This article described the _PyBytesWriter and _PyUnicodeWriter private APIs of
CPython. These APIs are design to optimize code producing strings when the
ouput size is not known in advance.

I created the _PyUnicodeWriter API to reply to complains that Python 3 was much
slower than Python 2, especially with the new Unicode implementation (PEP 393).


_PyAccu API
===========

Issue #12778: In 2011, Antoine Pitrou found a performance issue in the JSON
serializer when serializing many small objects: it used way too much memory for
temporary objects compared to the final output string.

The JSON serializer used a list of strings and joined all strings at the end of
create a final output string. Pseudocode::

    def serialize():
        pieces = [serialize(item) for item in self]
        return ''.join(pieces)

Antoine introduced an accumulator compacting the temporary list of "small"
strings and put the result in a second list of "large" strings. At the end, the
list of "large" strings was also compacted to build the final output string.
Pseudo-code::

    def serialize():
        small = []
        large = []
        for item in self:
            small.append(serialize(item))
            if len(small) > 10000:
                large.append(''.join(small))
                small.clear()
        if small
            large.append(''.join(small))
        return ''.join(large)

The threshold of 10,000  strings is justified by this comment::

    /* Each item in a list of unicode objects has an overhead (in 64-bit
     * builds) of:
     *   - 8 bytes for the list slot
     *   - 56 bytes for the header of the unicode object
     * that is, 64 bytes.  100000 such objects waste more than 6MB
     * compared to a single concatenated string.
     */

Issue #12911: Antoine Pitrou found a similar performance issue in repr(list),
and so proposed to convert its accumular code into a new private _PyAccu API.
He added the _PyAccu API to Python 2.7.5 and 3.2.3. Title of te repr(list)
change: "Fix memory consumption when calculating the repr() of huge tuples or
lists".


The _PyUnicodeWriter API
========================

Inefficient implementation of the PEP 393
-----------------------------------------

In 2010, Python 3.3 got a completly new Unicode implementation, the Python type
``str``, with the PEP 393. The implementation of the PEP was the topic of a
Google Summer of Code 2011 with the student Torsten Becker menthored by Martin
v. Löwis (author of the PEP). The project was successful: the PEP 393 was
implemented, it worked!

The first implementation of the PEP 393 used a lot of 32-bit character buffers
(``Py_UCS4``) which uses a lot of memory and requires expensive conversion to
8-bit (``Py_UCS1``, ASCII and Latin1) or 16-bit (``Py_UCS2``, BMP) characters.

The new internal structures for Unicode strings are now very complex and
require to be smart when building a new string to avoid memory copies. I
created the _PyUnicodeWriter API to try to reduce expensive memory copies, and
even completly avoid memory copies in best cases.


Design of the _PyUnicodeWriter API
----------------------------------

According to benchmarks, creating a ``Py_UCS1*`` buffer and then expand it
to ``Py_UCS2*`` or ``Py_UCS4*`` is more efficient, since ``Py_UCS1*`` is the
most common format.

Python ``str`` type is used for a wide range of usages. For example, it is used
for the name of variable names in the Python language itself. Variable names
are almost always ASCII.

The worst case for _PyUnicodeWriter is when a long ``Py_UCS1*`` buffer must be
converted to ``Py_UCS2*``, and then converted to ``Py_UCS4*``. Each conversion
is expensive: need to allocate a second memory block and convert characters to
the new format.

_PyUnicodeWriter features:

* Optional overallocation: overallocate the buffer by 25% on Windows and 50%
  on Linux. The ratio changes depending on the OS, it is a raw heuristic to get
  the best performances depending on the ``malloc()`` memory allocator.
* The buffer can be a shared read-only string if the buffer was only created
  from a single string. Micro-optimization for ``"%s" % str``.

The API allows to disable overallocation before the last write. For example,
``"%s%s" % ('abc', 'def')`` disables the overallocation before writing
``'def'``.

The _PyUnicodeWriter was introduced by the issue #14716 (change 7be716a47e9d):

    Close #14716: str.format() now uses the new "unicode writer" API instead
    of the PyAccu API. For example, it makes str.format() from 25% to 30%
    faster on Linux.


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
functions especially the code to format integers in bases 2 (binary), 8
(octal), 10 (decimal) and 16 (hexadecimal).

The function formatting an integer computes the exact size of the output,
requests a number of characters and then write characters. The characters are
written directly in the writer buffer. No temporary memory block is needed
anymore, and moreover no Py_UCS conversion is need: ``_PyLong_Format()`` writes
directly characters into the character format (PyUCS1, Py_UCS2 or Py_UCS4) of
the buffer.


Performance compared to Python 2
--------------------------------

The PEP 393 uses a complex storage for strings, so the exact performances
now depends on the character set used in the benchmark. For benchmarks using
a character set different than ASCII, the result are more tricky to understand.

To compare performances with Python 2, I focused my benchmarks on ASCII.  I
compared Python 3 str with Python 2 unicode, but also sometimes to Python 2 str
(bytes). On ASCII, Python 3.3 was as fast as Python 2, or even faster on some
very specific cases, but these cases are probably artificial and never seen in
real applications.

In the best case, Python 3 str (Unicode) was faster than Python 2 bytes.


_PyBytesWriter API: first try, big fail
=======================================

Since Python was *much* faster with _PyUnicodeWriter, I expected to get good
speedup with a similar API for bytes. The graal would be to share code for
bytes and Unicode (Spoiler alert! I reached this goal, but only for a single
function: format an integer to decimal).

My first attempt of a _PyBytesWriter API was in 2013: `Issue #17742: Add
_PyBytesWriter API <https://bugs.python.org/issue17742>`_. But quickly, I
noticed with microbenchmarks that my change made Python slower! I spent hours
to understand why GCC produced less efficient machine code. When I started to
dig the "strict aliasing" optimization issue, I realized that I reached a
deadend.

Extract of the _PyBytesWriter structure::

    typedef struct {
        /* Current position in the buffer */
        char *str;

        /* Start of the buffer */
        char *start;

        /* End of the buffer */
        char *end;

        ...
    } _PyBytesWriter;

The problem is that GCC emited less efficient machine code for the C code (see
my `msg187595 <https://bugs.python.org/issue17742#msg187595>`_)::

    while (collstart++<collend)
        *writer.str++ = '?';

For the ``writer.str++`` instruction, the new pointer value is written
immediatly in the structure. The pointer value is read again at each iteration.
So we have 1 LOAD and 1 STORE per iteration.

GCC emits better code for the original C code::

    while (collstart++<collend)
        *str++ = '?';

The ``str`` variable is stored in a register and the new value of ``str`` is
only written *once*, at the end of loop (instead of writing it at each
iteration). The pointer value is *only read once* before the loop. So we have 0
LOAD and 0 STORE (related to the pointer value) in the loop body.

It looks like an aliasing issue, but I didn't find how to say to GCC that the
new value of ``writer.str`` can be written only once at the end of the loop. I
tried the ``__restrict__`` keyword: the LOAD (get the pointer value) was moved
out of the loop. But the STORE was still in the loop body.

I wrote to gcc-help: `Missed optimization when using a structure
<https://gcc.gnu.org/ml/gcc-help/2013-04/msg00192.html>`_, but I didn't get any
reply. I just gave up.


_PyBytesWriter API: new try, the good one
=========================================

In 2015, I created the `Issue #25318: Add _PyBytesWriter API to optimize
Unicode encoders <https://bugs.python.org/issue25318>`_. I redesigned the API
to avoid the aliasing issue.

The new _PyBytesWriter doesn't contain the ``char*`` pointers anymore: they are
now local variables in functions. Instead, functions of API requires two
parameters: the bytes writer and a ``char*`` parameter. Example::

    PyObject * _PyBytesWriter_Finish(_PyBytesWriter *writer, char *str)

The idea is to keep ``char*`` pointers in functions to keep the most efficient
machine code in loops. The compiler doesn't have to compute complex aliasing
rules to decide if a CPU register can be used or not.

_PyBytesWriter features:

* Optional overallocation: overallocate the buffer by 25% on Windows and 50%
  on Linux. Same idea than _PyUnicodeWriter.
* Support ``bytes`` and ``bytearray`` type as output format to avoid an expensive
  memory copy from ``bytes`` to ``bytearray``.
* Small buffer of 512 bytes allocated on the stack to avoid the need of a
  buffer allocated on the heap, before creating the final
  ``bytes``/``bytearray`` object.

A _PyBytesWriter structure must always be allocated on the stack (to get fast
memory allocation of the smaller buffer).

While _PyUnicodeWriter has a 5 functions and 1 macro to write a single
character, write strings, write a substring, etc. _PyBytesWriter has a single
_PyBytesWriter_WriteBytes() function to write a string, since all other writes
are done directly with regular C code on ``char*`` pointers.

The API itself doesn't make the code faster. Disabling overallocation on the
last write and the usage of the small buffer allocated on the stack may be
faster.

In Python 3.6, I optimized error handlers on various codecs: ASCII, Latin1
and UTF-8. For example, the UTF-8 encoder is now up to 75 times as fast for
error handlers: ``ignore``, ``replace``, ``surrogateescape``,
``surrogatepass``. The ``bytes % int`` instruction became between 30% and 50%
faster on a microbenchmark.

Later, I replaced ``char*`` type with ``void*`` to avoid compiler warnings
in functions using ``Py_UCS1*`` or ``unsigned char*``, unsigned types.
