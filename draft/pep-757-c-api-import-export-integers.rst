************************************************
PEP 757 – C API to import-export Python integers
************************************************

Issue
=====

July 4, 2023. Mark Shannon.

Issue #102471: The C-API for Python to C integer conversion is, to be frank, a mess.

Python 3.13 alpha 1 removes _PyLong_New()
=========================================

August 2023.

Pull request gh-106320: Remove private _PyLong_New() function.

Release 3.13.0 alpha 1: Friday, 2023-10-13

The private function has been restored in 3.13 alpha 2.

Issue
=====

October 28, 2023. Sergey B Kirpichev.

Consider restoring _PyLong_New() function as public
https://github.com/python/cpython/issues/111415

Add public function PyLong_GetDigits()
======================================

July 2024. Sergey B Kirpichev.

Pull request #121339
====================

July 3, 2024.

Pull request #121339

C API Working Group decision issue #35
======================================

July 14, 2024.

https://github.com/capi-workgroup/decisions/issues/35

PEP 757
=======

September 2024.

PEP 757 – C API to import-export Python integers
https://peps.python.org/pep-0757/

Discourse: PEP 757 – C API to import-export Python integers
===========================================================

September 2024.

https://discuss.python.org/t/pep-757-c-api-to-import-export-python-integers/63895

Benchmarks
==========

xxx

Open Questions
==============

* Should we add digits_order and endian members to sys.int_info and
  remove PyLong_GetNativeLayout()? The PyLong_GetNativeLayout() function
  returns a C structure which is more convenient to use in C than
  sys.int_info which uses Python objects.
* Anonymous union.

Vote on PEP 757 – C API to import-export Python integers #45
============================================================

https://github.com/capi-workgroup/decisions/issues/45

November 28, 2024: I mark the PEP as Accepted and close the issue.

Acceptance immediately reverted...

Steering Council
================

https://github.com/python/steering-council/issues/264

December 8, 2024: The steering council has decided to accept PEP 757.

Implementation
==============

xxx

