+++++++++++++++++++++++++++++++++++++++
My contributions to Python: August 2023
+++++++++++++++++++++++++++++++++++++++

138 commits from 2023-08-16 to 2023-09-09

PyDict_GetItemRef
=================

API added XXX, no complain, start to use it.

* f5559f38d9 gh-108308: Replace PyDict_GetItem() with PyDict_GetItemRef() (#108309)
* ec3527d196 gh-108308: config_dict_get() uses PyDict_GetItemRef() (#108371)
* 4890f65ecf gh-108308: Use PyDict_GetItemRef() in moduleobject.c (#108381)
* 4dc9f48930 gh-108308: Replace _PyDict_GetItemStringWithError() (#108372)
* 52c6a6e48a gh-108308: Remove _PyDict_GetItemStringWithError() function (#108426)

C API removal
=============

Plan published at XXX: XXX

* 615f6e946d gh-106320: Remove _PyDict_GetItemStringWithError() function (#108313)
* c55e73112c gh-106320: Remove private PyLong C API functions (#108429)
* 773b803c02 gh-106320: Remove private _PyManagedBuffer_Type (#108431)
* bbbe1faf7b gh-106320: Remove private float C API functions (#108430)
* 480a337366 gh-106320: Remove private _PyContext_NewHamtForTests() (#108434)
* c494fb333b gh-106320: Remove private _PyEval function (#108433)
* c3d580b238 gh-106320: Remove private _PyList functions (#108451)
* 26893016a7 gh-106320: Remove private _PyDict functions (#108449)
* a071ecb4d1 gh-106320: Remove private _PySys functions (#108452)
* 546cab8444 gh-106320: Remove private _PyTraceback functions (#108453)
* 713afb8804 gh-106320: Remove private _PyLong converter functions (#108499)
* 6353c21b78 gh-106320: Remove private _PyLong_FileDescriptor_Converter() (#108503)
* 8ba4714611 gh-106320: Remove private AC converter functions (#108505)
* 4fb96a11db gh-106320: Remove private _Py_Identifier API (#108593)
* 301eb7e607 gh-106320: Remove _PyAnextAwaitable_Type from the public C API (#108597)
* 15c5a50797 gh-106320: Remove private pythonrun API (#108599)
* 8d8bf0b514 gh-106320: Remove private _Py_UniversalNewlineFgetsWithSize() (#108602)
* 07cf33ef24 gh-106320: Remove private _PyThread_at_fork_reinit() function (#108601)
* 21a7420190 gh-106320: Remove private _PyGILState_GetInterpreterStateUnsafe() (#108603)
* 921eb8ebf6 gh-106320: Remove private _PyLong_New() function (#108604)
* c9eefc77a7 gh-106320: Remove private _PyErr_SetKeyError() (#108607)
* fadc2dc7df gh-106320: Remove private _PyOS_IsMainThread() function (#108605)
* b6de2850f2 gh-106320: Remove private _PyObject_GetState() (#108606)
* 24b9bdd6ea gh-106320: Remove private _Py_ForgetReference() (#108664)
* 79823c103b gh-106320: Remove private _PyErr_ChainExceptions() (#108713)
* 3edcf743e8 gh-106320: Remove private _PyLong_Sign() (#108743)
* 676593859e gh-106320: Remove private _PyErr_WriteUnraisableMsg() (#108863)
* dd32611f4f gh-106320: winconsoleio.c includes pycore_pyerrors.h (#108720)
* c780698e9b gh-106320: Fix test_peg_generator: _Py_UniversalNewlineFgetsWithSize() (#108609)

C API: don't export internal functions
======================================

Follow-up of the API removal.

* 18fc543b37 gh-107211: No longer export pycore_strhex.h functions (#108229)
* 3f7e93be51 gh-107211: No longer export PyTime internal functions (#108422)
* ea871c9b0f gh-107211: No longer export internal functions (6) (#108424)
* f1ae706ca5 gh-107211: No longer export internal functions (7) (#108425)
* b7808820b1 gh-107211: No longer export internal functions (5) (#108423)
* 19eddb515a gh-107211: No longer export internal _PyLong_FromUid() (#109037)

* fb8fe377c4 gh-107211: Fix select extension build on Solaris (#108012)
* fa6933e035 gh-107211: Fix test_peg_generator (#108435)

* 194c6fb85e gh-106320: Don't export _Py_ForgetReference() function (#108712)

Cleanup C API header files
==========================

Try to make the C API as small as possible: minimize side effects and names.

* 0dd3fc2a64 gh-108216: Cleanup #include in internal header files (#108228)

* 45b9e6a61f gh-108765: Move standard includes to Python.h (#108769)
* 4ba18099b7 gh-108765: Python.h no longer includes <ieeefp.h> (#108781)
* 594b00057e gh-108765: Python.h no longer includes <unistd.h> (#108783)
* e7de0c5901 gh-108765: Python.h no longer includes <sys/time.h> (#108775)
* 03c4080c71 gh-108765: Python.h no longer includes <ctype.h> (#108831)
* b298b395e8 gh-108765: Cleanup #include in Python/*.c files (#108977)
* 1f3e797dc0 gh-108765: Remove old prototypes from pyport.h (#108782)
* 44fc378b59 gh-108765: Move export code from pyport.h to exports.h (#108855)
* c2ec174d24 gh-108765: Move stat() fiddling from pyport.h to fileutils.h (#108854)
* 5948f562e0 gh-108765: Reformat Include/osdefs.h (#108766)
* 03c5a68568 gh-108765: Reformat Include/pymacconfig.h (#108764)
* 578ebc5d5f gh-108767: Replace ctype.h functions with pyctype.h functions (#108772)
* bac1e6d695 gh-108765: multiprocessing.h includes <unistd.h> (#108823)
* a52213bf83 gh-108765: pystrhex: Replace stdlib.h abs() with Py_ABS() (#108830)
* fd5989bda1 gh-108753: _Py_PrintSpecializationStats() uses Py_hexdigits (#109040)

* 0e6d582b3b gh-63760: Don't declare gethostname() on Solaris (#108817)

Clean C API
===========

* 21c0844742 gh-108220: Internal header files require Py_BUILD_CORE to be defined (#108221)
* c2941cba7a gh-107298: Fix C API Buffer documentation (#108011)
* 9c03215a3e gh-107149: Make PyUnstable_ExecutableKinds public (#108440)
* b0edf3b98e GH-91079: Rename C_RECURSION_LIMIT to Py_C_RECURSION_LIMIT (#108507)
* 0b6a4cb0df gh-107149: Rename _PyUnstable_GetUnaryIntrinsicName() function (#108441)

Public C API
============

* be436e08b8 gh-108444: Add PyLong_AsInt() public function (#108445)
* 4e5a7284ee gh-108444: Argument Clinic uses PyLong_AsInt() (#108458)
* b32d4cad15 gh-108444: Replace _PyLong_AsInt() with PyLong_AsInt() (#108459)
* e59a95238b gh-108444: Remove _PyLong_AsInt() function (#108461)

* 3ff5ef2ad3 gh-108014: Add Py_IsFinalizing() function (#108032)

* 6726626646 gh-108314: Add PyDict_ContainsString() function (#108323)

Limited C API
=============

Prepare the limited C API to be usable by stdlib extensions.

* c6d56135e1 gh-108638: Fix tests when _stat extension is missing (#108689)
* 1dd9510977 gh-108494: Argument Clinic partial supports of Limited C API (#108495)
* 5c68cba268 gh-108494: Build _testclinic_limited on Windows (#108589)
* bf08131e0a gh-108494: Don't build _testclinic_limited with TraceRefs (#108608)

* 13a00078b8 gh-108634: Py_TRACE_REFS uses a hash table (#108663)
* b936cf4fe0 gh-108634: PyInterpreterState_New() no longer calls Py_FatalError() (#108748)

* 86bc9e35c4 gh-108494: AC supports pos-only args in limited C API (#108498)
* e675e515ae gh-108494: Argument Clinic: fix option group for Limited C API (#108574)
* 2928e5dc65 gh-108494: Argument Clinic: Document how to generate code that uses the limited C API (#108584)

* 73d33c1a30 gh-107603: Argument Clinic can emit includes (#108486)
* ad73674283 gh-107603: Argument Clinic: Only include pycore_gc.h if needed (#108726)

* b62a76043e gh-108638: Fix stat.filemode() when _stat is missing (#108639)

regrtest
========

Maintenance became painful. Need new features.

* 4f9b706c6f gh-108794: doctest counts skipped tests (#108795)

* 174e9da083 gh-108388: regrtest splits test_asyncio package (#108393)
* d4e534cbb3 regrtest computes statistics (#108793)
* f5ddbeeab7 gh-108822: Add Changelog entry for regrtest statistics (#108821)
* 31c2945f14 gh-108834: regrtest reruns failed tests in subprocesses (#108839)
* 1170d5a292 gh-108834: regrtest --fail-rerun exits with code 5 (#108896)
* 489ca0acf0 gh-109162: Refactor Regrtest.action_run_tests() (#109170)
* a56c928756 gh-109162: Refactor libregrtest WorkerJob (#109171)
* e9e2ca7a7b gh-109162: Refactor libregrtest.runtest (#109172)
* b78950d0d9 gh-109162: Refactor libregrtest.RunTests
* 5b7303e265 gh-109162: Refactor Regrtest.main() (#109163)
* ac8409b38b gh-109162: Regrtest copies 'ns' attributes (#109168)

Tests
=====

* 83e191ba76 test_sys: remove debug print() (#108642)
* 23f54c1200 Make test_fcntl quiet (#108758)

* 531930f47f Fix test_generators: save/restore warnings filters (#108246)
* e35c722d22 gh-106659: Fix test_embed.test_forced_io_encoding() on Windows (#108010)
* a8cae4071c gh-107219: Fix concurrent.futures terminate_broken() (#108974)
* 8ff1142578 gh-108851: Fix tomllib recursion tests (#108853)
* fa626b8ca0 gh-107178: Remove _testcapi.test_dict_capi() (#108436)
* f59c66e8c8 gh-108297: Remove test_crashers (#108690)
* babdced23f test.pythoninfo logs freedesktop_os_release() (#109057)
* 2fafc3d5c6 gh-108996: Skip broken test_msvcrt for now (#109169)
* 9173b2bbe1 gh-105776: Fix test_cppext when CC contains -std=c11 option (#108343)
* 7a6cc3eb66 test_peg_generator and test_freeze require cpu (#108386)
* 995f4c48e1 gh-80527: Change support.requires_legacy_unicode_capi() (#108438)

Split tests
===========

* aa9a359ca2 gh-108388: Split test_multiprocessing_spawn (#108396)
* aa6f787faa gh-108388: Convert test_concurrent_futures to package (#108401)

See: Serhiy's change to skip 'cpu' resource.

Move test files
===============

* adfc118fda gh-106016: Add Lib/test/test_module/ directory (#108293)
* 21dda09600 gh-108303: Add Lib/test/test_cppext/ sub-directory (#108325)
* 14d6e197cc gh-108303: Create Lib/test/test_dataclasses/ directory (#108978)
* d2879f2095 gh-108303: Remove unused Lib/test/sgml_input.html (#108305)

Sanitizers
==========

Because ??? (Gregory ???), I had a look at sanitizers.

* 58f9c63500 Fix test_faulthandler for sanitizers (#108245)
* a541e01537 gh-90791: Enable test___all__ on ASAN build (#108286)
* 3a1ac87f8f gh-90791: test.pythoninfo logs ASAN_OPTIONS env var (#108289)

nogil
=====

I started to have a look Sam Gross's work, see PEP xxx.

* 5afe0c17ca gh-108223: test.pythoninfo and libregrtest log Py_NOGIL (#108238)
* 2bd960b579 gh-108337: Add pyatomic.h header (#108701)
* 1f7e42131d gh-109054: configure checks if libatomic is needed (#109101)

Build system
============

Fix a race condition which affected me when I modified Argument Clinic
to support the limited C API.

* bd58389cdd Run make regen-global-objects (#108714)
* db1ee6a19a gh-108740: Fix "make regen-all" race condition (#108741)

FreeBSD
=======

Removal of the two FreeBSD buildbot workers maintained by koobs.

* fbce43a251 gh-91960: Skip test_gdb if gdb cannot retrive Python frames (#108999)
* cd2ef21b07 gh-108962: Skip test_tempfile.test_flags() if not supported (#108964)
* 15d659f929 gh-91960: FreeBSD Cirrus CI runs configure separately (#109127)
* a52a350977 gh-109015: Add test.support.socket_helper.tcp_blackhole() (#109016)

Fedora work
===========

Fedora bug: XXX

* 5a79d2ae57 Revert "gh-46376: Return existing pointer when possible in ctypes (#1… (#108688)

_socket capsule leak
====================

* 513c89d012 gh-108240: Add _PyCapsule_SetTraverse() internal function (#108339)
* a35d48d4bd gh-108240: _PyCapsule_SetTraverse() rejects NULL callbacks (#108417)
* 39506ee565 gh-108240: Add pycore_capsule.h internal header file (#108596)

ssl regression
==============

Fix major Python ssl vulnerability: xxx.

* 64f9935035 gh-108342: Break ref cycle in SSLSocket._create() exc (#108344)
* 592bacb6fc gh-108342: Make ssl TestPreHandshakeClose more reliable (#108370)

Fix race conditions
===================

Serhiy's saw XXX, I had a look.

* f63d37877a gh-104690: thread_run() checks for tstate dangling pointer (#109056)

Documentation
=============

On Discord, minimum Tkinter version was asked. I added it to the doc.

* e012cf771b Document Python build requirements (#108646)

Misc
====

* c965cf6dd1 Define _Py_NULL as nullptr on C23 and newer (#108244)
* 6541fe4ad7 Ignore _Py_write_noraise() result: cast to (void) (#108291)
* c1c9cd61da gh-89745: Remove commented code in getpath.c (#108307)
* a0773b89df gh-108753: Enhance pystats (#108754)
