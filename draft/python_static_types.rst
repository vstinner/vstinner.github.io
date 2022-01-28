SC decision: Feb 2021
=====================

Jan 6, 2021, itertools: https://github.com/python/cpython/pull/24065#issuecomment-755251541

Victor: I prefer to close the PR for now. I'm working on a PEP with @corona10 to explain the rationale. We can wait until this (future) PEP is accepted before changing itertools.

Feb 8, 2021: https://github.com/python/cpython/pull/24481#issuecomment-775208079

Pablo: I would recommend waiting for #24065 (comment) before continuing with heap type changes

Feb 8, 2021: https://github.com/python/steering-council/blob/1d85eefdc5861a096c3859e9990dbc8527c5973b/updates/2021-02-steering-council-update.md

The Steering Council discussed the ongoing work on porting types in the standard library to heap-types and the subinterpreter-related changes. It was decided that through Pablo, the Steering Council will ask the core developers driving those changes to create an informational PEP and not to make any more changes in this area after beta 1, as per our general policy.

Full GC protocol
================

https://bugs.python.org/issue42972

A heap type must respect the following 3 conditions to collaborate with the GC:

* Py_TPFLAGS_HAVE_GC flag
* tp_traverse function
* Instances must be tracked by the GC

Mandatory tp_traverse
=====================


https://github.com/python/cpython/commit/ee7637596d8de25f54261bbeabc602d31e74f482 change::

    commit ee7637596d8de25f54261bbeabc602d31e74f482
    Author: Victor Stinner <vstinner@python.org>
    Date:   Tue Jun 1 23:37:12 2021 +0200

        bpo-44263: Py_TPFLAGS_HAVE_GC requires tp_traverse (GH-26463)

        The PyType_Ready() function now raises an error if a type is defined
        with the Py_TPFLAGS_HAVE_GC flag set but has no traverse function
        (PyTypeObject.tp_traverse).

* https://github.com/python/cpython/commit/8b55bc3f93a655bc803bff79725d5fe3f124e2f0
* https://github.com/python/cpython/commit/8b55bc3f93a655bc803bff79725d5fe3f124e2f0


Python 3.10 regressions
=======================

Mutable types
-------------

April, 2021: https://bugs.python.org/issue43908

Types became mutable: we had to add the immutable flag

Add a new Py_TPFLAGS_IMMUTABLETYPE type flag for creating immutable type objects: type attributes cannot be set nor deleted. (Contributed by Victor Stinner and Erlend E. Aasland in bpo-43908.)

https://bugs.python.org/issue43908

All static types are marked as immutable.

In Python 3.11, 68 heap types have the Py_TPFLAGS_IMMUTABLETYPE flag:

* _blake2.blake2b
* _blake2.blake2s
* _bz2.BZ2Compressor
* _bz2.BZ2Decompressor
* _csv.Dialect
* _csv.reader
* _csv.writer
* _dbm.dbm
* _gdbm.gdbm
* _hashlib.HASH
* _hashlib.HASHXOF
* _hashlib.HMAC
* _lsprof.Profiler
* _lzma.LZMACompressor
* _lzma.LZMADecompressor
* _md5.md5
* _multibytecodec.MultibyteCodec
* _multibytecodec.MultibyteIncrementalDecoder
* _multibytecodec.MultibyteIncrementalEncoder
* _multibytecodec.MultibyteStreamReader
* _multibytecodec.MultibyteStreamWriter
* _overlapped.Overlapped
* _queue.SimpleQueue
* _sha1.sha1
* _sha256.sha224
* _sha256.sha256
* _sha3.keccak_224
* _sha3.keccak_256
* _sha3.keccak_384
* _sha3.keccak_512
* _sha3.sha3_224
* _sha3.sha3_256
* _sha3.sha3_384
* _sha3.sha3_512
* _sha512.sha384
* _sha512.sha512
* _sre.SRE_Scanner
* _ssl.Certificate
* _ssl.MemoryBIO
* _ssl.SSLSession
* _ssl._SSLContext
* _ssl._SSLSocket
* ssl.SSLError
* _thread.RLock
* _thread._local
* _thread._localdummy
* _thread.lock
* _tokenize.TokenizerIter
* _winapi.Overlapped
* array.array
* array.arrayiterator
* functools.KeyWrapper
* functools._lru_cache_wrapper
* functools._lru_list_elem
* functools.partial
* mmap.mmap
* operator.attrgetter
* operator.itemgetter
* operator.methodcaller
* pyexpat.xmlparser
* re.Match
* re.Pattern
* sqlite3.Connection
* sqlite3.Cursor
* sqlite3.PrepareProtocol
* sqlite3.Row
* sqlite3.Statement
* unicodedata.UCD


tp_new
------

https://bugs.python.org/issue43916

It became possible again to instanciate types which was not possible before: we had to add a new "do not instanciate" flag.

Add a new Py_TPFLAGS_DISALLOW_INSTANTIATION type flag to disallow creating type instances. (Contributed by Victor Stinner in bpo-43916.)

Types declared with ``tp_new=NULL`` gets the
``Py_TPFLAGS_DISALLOW_INSTANTIATION`` flag.

In Python 3.11, 41 types are declared explicitly with the
``Py_TPFLAGS_DISALLOW_INSTANTIATION`` flag:

* _curses_panel.panel
* _dbm.dbm
* _gdbm.gdbm
* _hashlib.HASH
* _hashlib.HASHXOF
* _hashlib.HMAC
* _md5.md5
* _multibytecodec.MultibyteCodec
* _sha1.sha1
* _sha256.sha224
* _sha256.sha256
* _sha512.sha384
* _sha512.sha512
* _sre.SRE_Scanner
* _ssl.Certificate
* _thread._localdummy
* _thread.lock
* _tkinter.Tcl_Obj
* _tkinter.tkapp
* _tkinter.tktimertoken
* _winapi.Overlapped
* _xxsubinterpreters.ChannelID
* array.arrayiterator
* curses.ncurses_version
* functools.KeyWrapper
* functools._lru_list_elem
* os.DirEntry
* os.ScandirIterator
* pyexpat.xmlparser
* re.Match
* re.Pattern
* select.devpoll
* select.poll
* sqlite3.Statement
* stderrprinter
* sys.flags
* sys.getwindowsversion
* sys.version_info
* unicodedata.UCD
* zlib.Compress
* zlib.Decompress


GC bug
------

Major GC bug: fixed by adding many traverse function, add the GC flag, etc.

https://bugs.python.org/issue40217 "The garbage collector doesn't take in account that objects of heap allocated types hold a strong reference to their type"

Origin in Python 3.8:

    https://bugs.python.org/issue35810 "Object Initialization does not incref Heap-allocated Types"

    https://github.com/python/cpython/commit/364f0b0f19cc3f0d5e63f571ec9163cf41c62958

    tp_new must Py_INCREF(type) and tp_dealloc must Py_DECREF(type)


Problem: a type creates a reference cycle. MRO and methods for example contain a reference to the type.

GC fails to break the cycle:

    threading example: https://bugs.python.org/issue40149

    https://vstinner.github.io/subinterpreter-leaks.html Leaks discovered by subinterpreters (Dec 2020)

    Fix wrong fix: https://github.com/python/cpython/commit/0169d3003be3d072751dd14a5c84748ab63a249f

    Better fix: add Py_VISIT(Py_TYPE(self)) in traverse functions

    Problem: many heap types didn't implement the traverse function nor the GC protocol!


Approved PEPs
=============

* PEP 384 "Stable ABI" (approved in 2009): add an API to declare heap types, https://www.python.org/dev/peps/pep-0384/#type-objects
* PEP 573 "Module State Access from C Extension Methods" (approved in 2016): the whole PEP is about heap types
* PEP 630 "Isolating Extension Modules" (informal, not "approved"): https://www.python.org/dev/peps/pep-0630/#heap-types


May 2021, Language Summit talk
==============================

https://github.com/vstinner/talks/blob/main/2021-PyconUS/subinterpreters.pdf

Benchmark: no significant impact on perf.


Misc concerns
=============

* Performance issue
* _functools optimization: https://github.com/python/cpython/commit/139c232f3851b393798d0ea4e65f1298bfbcd9cf
* _PyType_GetModuleByDef() optimization... is incorrect? https://bugs.python.org/issue46433
* Private C API: _PyType_GetModuleByDef()
