++++++++++++++++++++++++++++++++++++++
My contributions to CPython in 2015 Q4
++++++++++++++++++++++++++++++++++++++

:date: 2016-02-17 01:30
:tags: cpython
:category: python
:slug: contrib-cpython-2015q4
:authors: Victor Stinner
:summary: My contributions to CPython in 2015 Q4

My contributions to CPython in 2015 Q4 (october, november, december)::

    hg log --no-merge -u Stinner -r 'date("2015-10-01"):date("2015-12-31")'

As usual, I pushed changes of various contributors and helped them to polish
their change.

I focus on optimizing the bytes type during this quarter. It started with the
issue #24870 opened by INADA Naoki who works on PyMySQL: decoding bytes
using the surrogateescape error handler was slow. For me, it was an opportunity
for a new attempt to implement a fast "bytes writer API".

Funny bugs:

* Issue #25274: test_recursionlimit_recovery() of test_sys now checks
  sys.gettrace() when the test is executed, not when the module is loaded.
  sys.settrace() may be after after the test is loaded.
  Bug found while working on XXX.
* Issue #25274: sys.setrecursionlimit() now raises a RecursionError if the new
  recursion limit is too low depending at the current recursion depth. Modify
  also the "lower-water mark" formula to make it monotonic. This mark is used
  to decide when the overflowed flag of the thread state is reset.

Optimizations:

As usual for performance, Serhiy Storchaka was very helpful on reviews, to run
independant benchmarks, etc.

* Issue #25318: Add _PyBytesWriter API. Add a new private API to optimize
  Unicode encoders. It uses a small buffer allocated on the stack and supports
  overallocation.
* Use _PyBytesWriter API for UCS1 (ASCII and Latin1) and UTF-8 encoders. Enable
  overallocation for the UTF-8 encoder with error handlers.
* unicode_encode_ucs1(): initialize collend to collstart+1 to not check the
  current character twice, we already know that it is not ASCII.
* Issue #25267: The UTF-8 encoder is now up to 75 times as fast for error
  handlers: ``ignore``, ``replace``, ``surrogateescape``, ``surrogatepass``.
  Patch co-written with Serhiy Storchaka.
* Issue #25301: The UTF-8 decoder is now up to 15 times as fast for error
  handlers: ``ignore``, ``replace`` and ``surrogateescape``.
* Issue #25318: Optimize backslashreplace and xmlcharrefreplace error handlers
  in UTF-8 encoder. Optimize also backslashreplace error handler for ASCII and
  Latin1 encoders.
* Issue #25349: Optimize bytes % args using the new private _PyBytesWriter API
* Optimize error handlers of ASCII and Latin1 encoders when the replacement
  string is pure ASCII: use _PyBytesWriter_WriteBytes(), don't check individual
  character.
* Issue #25349: Optimize bytes % int. Formatting is between 30% and 50% faster
  on a microbenchmark.
* Issue #25357: Add an optional newline paramer to binascii.b2a_base64().
  base64.b64encode() uses it to avoid a memory copy.
* Issue #25353: Optimize unicode escape and raw unicode escape encoders to use
  the new _PyBytesWriter API.
* Rewrite PyBytes_FromFormatV() using _PyBytesWriter API
* Issue #25399: Optimize bytearray % args. Most formatting operations are now
  between 2.5 and 5 times faster.
* Optimize bytes.fromhex() and bytearray.fromhex(). Issue #25401: Optimize
  bytes.fromhex() and bytearray.fromhex(): they are now between 2x and 3.5x
  faster.

Changes:

* Issue #25003: On Solaris 11.3 or newer, os.urandom() now uses the getrandom()
  function instead of the getentropy() function. The getentropy() function is
  blocking to generate very good quality entropy, os.urandom() doesn't need
  such high-quality entropy.
* Issue #22806: Add ``python -m test --list-tests`` command to list tests.
* Issue #25670: Remove duplicate getattr() in ast.NodeTransformer
* Issue #25557: Refactor _PyDict_LoadGlobal(). Don't fallback to
  PyDict_GetItemWithError() if the hash is unknown: compute the hash instead.
  Add also comments to explain the optimization a little bit.
* Issue #25868: Try to make test_eintr.test_sigwaitinfo() more reliable
  especially on slow buildbots

Changes specific to Python 2.7:

* Closes #25742: locale.setlocale() now accepts a Unicode string for its second
  parameter.

Bugfixes:

* Fix regrtest --coverage on Windows
* Fix pytime on OpenBSD
* More fixes for test_eintr on FreeBSD
* Close #25373: Fix regrtest --slow with interrupted test
* Issue #25555: Fix parser and AST: fill lineno and col_offset of "arg" node
  when compiling AST from Python objects. First contribution related
  to FAT Python ;-)
* Issue #25696: Fix installation of Python on UNIX with make -j9.
