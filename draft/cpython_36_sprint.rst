CPython Core Dev Sprint at Facebook, Sept 5-9 (5 days)
======================================================

My contributions.


* Issue #27350: I reviewed and pushed the "compact dict" implementation which makes Python
  dict ordered (by insertion order) by default. Patch by ..., design by ...,
  .... It reduces the memory usage of dictionaries betwen 20% and 25%.

  Patch written by INADA Naoki, design by Raymond Hettinger, CPython
  implementation based on the PyPy implementation.

* "Fast calls": Python 3.6 has a new private C API which allows the creation of
  temporary tuples and dictionaries to pass positional (tuple) and keyword
  (dict) arguments. It makes Python xxx% faster.

  - Add METH_FASTCALL
  - Add _PyArg_ParseStack()
  - Add _PyCFunction_FastCallKeywords() -- issue #27810
  - Add _PyObject_FastCallKeywords() -- issue #27830

* I reviewed and pushed: Issue #27213: Rework CALL_FUNCTION* opcodes to produce
  shorter and more efficient bytecode. Patch by Demur Rumed, design by Serhiy
  Storchaka, reviewed by Serhiy Storchaka and Victor Stinner.

* PEP 509: Add a new private version to the builtin dict type. I pushed
  the implementation of my PEP. Guido approved the PEP during the sprint.

* I reviewed and pushed the isue #16334: "Optimize unicode_escape and
  raw_unicode_escape", patch written by Serhiy Storchaka.

* PEP 524. I pushed the implementation of my PEP, "os.urandom() now blocks on
  Linux". Issue #27776: The os.urandom() function does now block on Linux 3.17
  and newer until the system urandom entropy pool is initialized to increase
  the security. This change is part of the PEP 524.

* Add os.getrandom(). Issue #27778: Expose the Linux getrandom() syscall as a
  new os.getrandom() function. This change is part of the PEP 524.

* I review the two giant patches of Yury Selivanov for his two PEPs:

  - PEP 525: Asynchronous Generators
  - PEP 530: Asynchronous Comprehensions

  I happily found many issues including a major one: regular list-comprehension
  were completely broken :-) Another minor issue: SyntaxError didn't reported
  the correct line number in a specific case.

--

* Issue #27938: Add a fast-path for us-ascii encoding

Cleanup on function calls.
