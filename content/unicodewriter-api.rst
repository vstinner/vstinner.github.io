+++++++++++++++++++++++++
Add PyUnicodeWriter C API
+++++++++++++++++++++++++

:date: 2024-07-04 18:00
:tags: c-api, cpython
:category: cpython
:slug: pyunicodewriter-c-api
:authors: Victor Stinner


.. image:: {static}/images/matisse_la_danse.jpg
   :alt: La Danse - Matisse

In May, I designed a new C API to build a Python str object: the
`PyUnicodeWriter API
<https://docs.python.org/dev/c-api/unicode.html#pyunicodewriter>`__.
Many people were involved in the design and the discussion
was quite long. The C API Working Group helped to design a better and more
convenient API. It took me basically a whole month to get the design done
and fully implement the API.

Painting: `La Danse <https://en.wikipedia.org/wiki/Dance_(Matisse)>`_ by
Matisse (1910).

Initial API
===========

Building a Python ``str`` object in C is not easy. I wrote the private
``_PyUnicodeWriter`` C API 9 years ago (see `my previous article
<{filename}/pybyteswriter.rst>`__), but it's not usable outside Python since
it's a private API. So I proposed to make it public.

On May 19, I create `an issue
<https://github.com/python/cpython/issues/119182>`_ and `a pull request
<https://github.com/python/cpython/pull/119184>`_ to discuss the API. The
initial API was:

.. code-block:: c

   typedef struct PyUnicodeWriter PyUnicodeWriter;

   PyAPI_FUNC(PyUnicodeWriter*) PyUnicodeWriter_Create(void);
   PyAPI_FUNC(void) PyUnicodeWriter_Free(PyUnicodeWriter *writer);
   PyAPI_FUNC(PyObject*) PyUnicodeWriter_Finish(PyUnicodeWriter *writer);
   PyAPI_FUNC(void) PyUnicodeWriter_SetOverallocate(
       PyUnicodeWriter *writer,
       int overallocate);

   PyAPI_FUNC(int) PyUnicodeWriter_WriteChar(
       PyUnicodeWriter *writer,
       Py_UCS4 ch);
   PyAPI_FUNC(int) PyUnicodeWriter_WriteStr(
       PyUnicodeWriter *writer,
       PyObject *str);
   PyAPI_FUNC(int) PyUnicodeWriter_WriteSubstring(
       PyUnicodeWriter *writer,
       PyObject *str,
       Py_ssize_t start,
       Py_ssize_t stop);
   PyAPI_FUNC(int) PyUnicodeWriter_WriteASCIIString(
       PyUnicodeWriter *writer,
       const char *ascii,
       Py_ssize_t len);

API changes
===========

PyUnicodeWriter_WriteUTF8()
---------------------------

My first implementation made the assumption that the caller would only pass
ASCII characters to ``PyUnicodeWriter_WriteASCIIString()`` which is a bold
assumption.  It would crash if non-ASCII characters would be passed by
mistake. UTF-8 is more common and Python has a fast UTF-8 decoder. The first
change was to replace ``PyUnicodeWriter_WriteASCIIString()`` with
``PyUnicodeWriter_WriteUTF8()``.

PyUnicodeWriter_WriteStr()
--------------------------

I really wanted ``PyUnicodeWriter_WriteStr()`` to only accept a Python str
object. Others insisted to accept any Python object and write ``str(obj)``
instead. I changed ``PyUnicodeWriter_WriteStr()`` to implement that.

PyUnicodeWriter_WriteRepr()
---------------------------

Since ``str(obj)`` was there, ``repr(obj)`` becomes the next question: should
we added it? It was decided to add ``PyUnicodeWriter_WriteRepr(obj)`` to write
``repr(obj)``. It's convenient to use.

PyUnicodeWriter_Format()
------------------------

While discussing, it was proposed to add many functions to write various
formats.  I proposed to add ``PyUnicodeWriter_FromFormat(format, ...)``
similiar to ``PyUnicode_FromFormat()``. It was decided to add it under the name:
``PyUnicodeWriter_Format()``. Its implementation is efficient since multiple
formats write directly into the writer, without having to create a temporary
string object.

PyUnicodeWriter_Create()
------------------------

The initial version of ``PyUnicodeWriter_Create()`` had no argument. It was
asked to add a size parameter to preallocate the internal buffer:
``PyUnicodeWriter_Create(size)``.

Remove PyUnicodeWriter_SetOverallocate()
----------------------------------------

I tried to justify that calling ``PyUnicodeWriter_SetOverallocate(0)`` before
the last write was a killer feature for performance, but it looked too
complicated to others and it was decided to simply remove this API.


C API Working Group discussion
==============================

On May 24, once most of the API was stable, I created a `decision issue
<https://github.com/capi-workgroup/decisions/issues/27>`_ for the API to the C
API Working Group.

On June 7, the API was approved by a majority vote.

On June 10, Marc-Andre Lemburg reopened the issue since he had concerns about
the incomplete UTF-8 Decoder API and the fact that the functions were not
atomic: on error, the behavior was undefined.

I modified my implementation to make all functions atomic: either the whole
string is written, or nothing is written (restore the writer to its previous
state).

I also proposed to extend the ``PyUnicodeWriter`` API once we agreed on an
minimum API.

On June 17, issue was closed again and I merged my implementation.

Extensions
==========

PyUnicodeWriter_WriteWideChar()
-------------------------------

I added a function to write wide strings (``wchar_t*``) which are common on
Windows.

PyUnicodeWriter_DecodeUTF8Stateful()
------------------------------------

I added a stateful UTF-8 decoder as an answer to Marc-Andre's request. API::

    int PyUnicodeWriter_DecodeUTF8Stateful(
        PyUnicodeWriter *writer,
        const char *string,
        Py_ssize_t length,
        const char *errors,
        Py_ssize_t *consumed);

PyUnicodeWriter_WriteUCS4()
---------------------------

While less common, UCS-4 strings are convenient to manipulate Unicode code
points. I added an API to support natively this string format.

Documentation
=============

Read the `PyUnicodeWriter API documentation
<https://docs.python.org/dev/c-api/unicode.html#pyunicodewriter>`__.

Example of contextvar_tp_repr()
===============================

Simplified code:

.. code-block:: c

   static PyObject *
   contextvar_tp_repr(PyContextVar *self)
   {
       // "<ContextVar name='a' at 0x1234567812345678>"
       Py_ssize_t estimate = 43;
       PyUnicodeWriter *writer = PyUnicodeWriter_Create(estimate);
       if (writer == NULL) {
           return NULL;
       }

       if (PyUnicodeWriter_WriteUTF8(writer, "<ContextVar name=", 17) < 0) {
           goto error;
       }
       if (PyUnicodeWriter_WriteRepr(writer, self->var_name) < 0) {
           goto error;
       }
       if (PyUnicodeWriter_Format(writer, " at %p>", self) < 0) {
           goto error;
       }
       return PyUnicodeWriter_Finish(writer);

   error:
       PyUnicodeWriter_Discard(writer);
       return NULL;
   }


Conclusion
==========

Thanks for great discussions, the final ``PyUnicodeWriter`` API is better, more
convenient, less error-prone, and maybe even a little bit more efficient!

Thanks to everyone who was involved in these discussions!
