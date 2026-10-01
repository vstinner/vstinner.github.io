++++++++++++++++++++++++++++++++++++
Convert C functions to PyBytesWriter
++++++++++++++++++++++++++++++++++++

https://vstinner.github.io/pep-782-pybyteswriter-c-api.html

Convert to PyBytesWriter
========================

Issue gh-155742:

* Use PyBytesWriter in CJK codecs (#155746)
* Use PyBytesWriter in CJK codecs (#157535)
* Use PyBytesWriter in PySSL_RAND() (#157731)
* Use PyBytesWriter in Python/assemble.c (#155747)
* Use PyBytesWriter in Python/assemble.c (#157349)
* Use PyBytesWriter in _Py_strhex_impl() (#157734)
* Use PyBytesWriter in _zstd.finalize_dict() (#157343)
* Use PyBytesWriter in _zstd.train_dict() (#155745)
* Use PyBytesWriter in bytes.translate() (#157346)
* Use PyBytesWriter in codecs (#155750)
* Use PyBytesWriter in codeobject.c (#157345)
* Use PyBytesWriter in io _textiowrapper_writeflush() (#155743)
* Use PyBytesWriter in winconsoleio.c (#157391)
* Use PyBytesWriter in xml.etree (#155749)

Special cases
=============

Use PyMem_Malloc():

* gh-155742: Use PyMem_Malloc() in decode_unicode_with_escapes() (#157587)
* memoryview.hex(): https://github.com/python/cpython/pull/158582

Documentation
=============

* gh-156939: Document that PyBytesObject ends with a NUL byte (#157236)

Detect bugs
===========

* gh-157242: Add _PyBytes_IsMutable() assertion (#157371)
* gh-156939: Detect buffer overflow in PyBytesWriter in debug mode (#156943)
* gh-156939: Detect PyBytesWriter buffer overflow earlier (#157385)
* gh-155742: Check singletons consistency at Python exit (#157572)
* gh-157242: Add byteswriter_check_consistency() (#157723)
* gh-156939: Clear newly allocated bytes in PyBytesWriter_Resize() (#157455)
* gh-156939: Detect buffer overflow in bytes and bytearray (#157529)

Unicode:

* gh-157710: Detect overflow in PyUnicodeWriter_Finish() (#157715)
* gh-157710: Add _PyUnicodeWriter_CanWrite() function (#157712)

Fixes
=====

* gh-155742: Get PyBytes_AS_STRING() as `const char*` (#155751)
* gh-156939: Fix struct.pack('0p', bytes) (#157071)
* gh-129813: Check size in PyBytesWriter_FinishWithSize() (#157226)
* gh-156939: Fix xmlcharrefreplace() buffer overflow (#157109)
* gh-157242: Fix PyBytesWriter_Resize() on MemoryError (#157243); Add _PyBytes_ResizeKeepOnError()
* gh-157242: Leave bytearray unchanged if resize() fails (#157340)
* gh-157242: Fix set_nomemory() on Py_TRACE_REFS build (#157351)
* gh-157242: Do not close io.BytesIO on MemoryError (#157344)

Tests
=====

* gh-155503: Add more PyType C API tests (#155505)
* gh-155742: Test PyBytesWriter_FinishWithSize() with negative size (#155783)
* gh-157242: Add more PyBytesWriter tests (#157352)
* gh-142217: Add tests on the deprecated _Py_Identifier C API (#157638)
* gh-155907: Complete PyMarshal C API tests (#157452)

Unicode:

* gh-157710: Add MemoryError tests to PyUnicodeWriter (#157853)
* gh-156939: Add tests on the PyUnicode C API (#157798)
* gh-156939: Document that PyUnicodeObject ends with null character (#157708)

Optimizations
=============

* gh-155742: Get singleton in PyBytesWriter_FinishWithSize() (#155795)
* gh-128509: Use bytes singletons in marshal (#157398)

Unicode:

* gh-157710: Defer allocation in PyUnicodeWriter_Create() (#157969)
* gh-157710: Enable read-only optimization in PyUnicodeWriter (#157861)
* gh-157710: Avoid resize in PyUnicodeWriter_Finish() for singleton (#157862)
