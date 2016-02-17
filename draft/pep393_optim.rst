++++++++++++++++++++++++++++++++++++++++++
Optimization of the PEP 393 implementation
++++++++++++++++++++++++++++++++++++++++++

:date: 2016-02-17 18:00
:tags: cpython, optimization
:category: python
:slug: pep393-optim
:authors: Victor Stinner
:summary: Optimization of the PEP 393 implementation

After presenting the PEP 393 design and its first implementation, let's
see how it was optimized in Python 3.3 and 3.4.

As any kind of a fresh code, the first implementation of the PEP 393 was
inefficient. Different people ran micro-benchmarks and noticed that the future
Python 3.3 was slower than Python 3.2, sometimes much slower. In 2010, Python 3
was less popular, and the inefficient implementation PEP 393 was likely to feed
the old troll against Python 3.

Since I strongly believed in Python 3, I spent between 6 months and 1 year
to optimize almost all C code handling strings, especially code building
strings.

While the PEP 393 is very complex, it has nice side-effect regarding
performances. For example, comparison between two strings doesn't need to
compare characters if the "kind" of the two strings is different: the
complexity is O(1) in this case.

I worked on different "areas":

* Optimizations on low-level Unicode functions: copy characters, convert
  strings from one kind to another kind, etc.
* Optimize codecs like ASCII and UTF-8
* Optimize str % args and str.format(args)


Functions specializations
=========================

Instead of using a singled function with a switch on the kind inside a loop,
each function has 4 versions:

* ASCII
* Py_UCS1: Latin1
* Py_UCS2: BMP
* Py_UCS4: non-BMP

To limit code duplication, header files (.h) in ``Objects/stringlib/``
directory are used as templates to instanciate 4 versions of the same code.

For some functions, the ASCII and/or Latin1 versions use a more optimized
version, since it's easier to optimize operations on bytes, than operations on
16-bit (Py_UCS2) or 32-bit (Py_UCS4) numbers.


Compute the maximum character of a string
=========================================

The PEP 393 requires to always find the most compact format of a string,
it's a strong requirement for different reasons.

This operation is very expensive because it requires to scan all characters
of a string. ``ucsNlib_find_max_char()`` functions were implemented.

Features:

* Hot-code work a ``unsigned long*`` pointer to process 8 bytes per iteration
  on 64-bit system (4 bytes on Windows and 32-bit systems)
* Use a bitmask (value & mask) rather than comparison between integers (value >
  max_char)
* The loop stops when the we reached the maximum possible character depending
  on the format. For example, when scanning a Py_UCS1 string, the loop stops
  as soon as a byte larger than 127 (0x7f) is found. In this case. For Py_UCS2,
  we stop at the first character larger than 255 (0xff). For Py_UCS4, we stop
  at the first character larger than 65,535 (0xffff)


Copy characters
===============

A core function for strings is to copy characters from one string to another
string. I expected a simple implementation like ``memcpy()``, but it's not
that simple. Since PEP 393 uses complex formats, an efficient implementation
requires to specialize the code when the kind of the input and output strings
are different:

* ASCII/UCS1 -> UCS1: most efficient code, simply use ``memcpy()``
* UCS1 -> ASCII: need to check maximum character of the substring, use ``memcpy()``
* UCS1 -> UCS2, UCS1 -> UCS4, UCS2 -> UCS4: need to convert characters
* big format -> smaller kind: slow-path, need to check maximum character.
  Implemented with a loop calling the slow macros PyUnicode_READ() and
  PyUnicode_WRITE()

A special version _PyUnicode_FastCopyCharacters() skips the code checking the
maximum character when the check was done earlier.


Resizing a string
=================

As copying characters, I first expected that changing the length of a string
would be simple. Sorry, it is not. The implementation is complex again :-/

There are 3 main implementations:

* if the string is not more "modifiable", a new string is created and
  characters are copied, complexity of ``O(n)``
* compact string: use ``realloc()`` which avoid to copy characters, complexifty of ``O(1)``, if the
  new length is smaller or when the memory allocator is able to grow the
  memory block without moving it. Otherwise, the resize has a cost of ``O(n)``.
* legacy string: again, use ``realloc()``.


PyUnicode_Join
==============

Use memcpy() if possible.


Compare
=======

PyUnicode_Compare() uses ``memcmp()`` for UCS1-UCS1 and use ``wmemcmp()`` for
UCS4-UCS4 if wchar_t is 32-bit long.

unicode_compare_eq() uses ``memcmp()``.

PyUnicode_CompareWithASCIIString() uses ``memcmp()`` for UCS1 string.


Py_UNICODE
==========

The code to handle the backward compatibility is boring or awful. I prefer to
not talk about it :-)


PyUnicode_Append
================

PyUnicode_Append(left, right) appends inplace if left is modifiable, if
PyUnicode_KIND(right) <= PyUnicode_KIND(left), but not for ascii += latin1.
It uses ``realloc()`` to try to avoid copying left characters.


Optimzations for Py_UCS1
========================

* Fill with a character (ex: padding in ``str % args`` like
  ``'%10s' % 'abc'``): use ``memset()``
* ``'x' * int`` uses ``memset()``
* Search a character in a string (``c`` in ``abc'``): ``memchr()``.
  When available, ``memrchr()`` is used for reverse search.


Optimzations for ASCII
======================

For optimization, a very nice attribute of Unicode string is the "ascii" flag.
We know if a Unicode string only contains ASCII characters.

Encoding a ASCII string to UTF-8 is as simple as ``memcpy()``, or even use a
pointer to ASCII characters when it's possible to use a direct pointer. Since
UTF-8 is the default encoding in Python 3 (ex: ``'hello'.encode()``), it's nice
to have this optimization!

lower/upper: use _Py_bytes_upper() and _Py_bytes_lower() which use precomputed
tables, O(1) lookup.

strip(): use _Py_ascii_whitespace precomputed table, O(1) lookup.

The private ``_PyUnicode_FromASCII()`` function was added to build a Unicode
string when we are 100% sure that the input bytes string is ASCII-encoded.
For example, it is used to:

* build a substring of an ASCII string
* format a floating point number to a string
* format an integer number to a string
* format an pointer to a string
* copy strings in PyUnicode_FromFormatV(), since the format string must
  be encoded to ASCII


Optimizations of codecs
=======================

Serhiy, me and others spent a lot of time to optimize the most common codecs,
especially ASCII, Latin1 (ISO 8859-1), UTF-8 and UTF-16. The UTF-16 is
important on Windows, it's used by all "wide" functions of the Windows API (C
``wchar_t*`` strings).

The most annoying were CJK codecs. Their implement is based on many low-level
C macros.


Optimize string formating
=========================

I optimized ``str % args`` and ``str.format(args)`` with a new private
``_PyUnicodeWriter`` API. This API is design to optimize code producing strings
when the ouput size is not known in advance. For the PEP 393, it also helps
when the maximum character is not known in advance.

I will elaborate this in a different article.
