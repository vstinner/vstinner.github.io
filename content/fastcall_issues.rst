+++++++++++++++
FASTCALL issues
+++++++++++++++

:date: 2017-02-25 00:00
:tags: fastcall, optimization, cpython
:category: python
:slug: fastcall-issues
:authors: Victor Stinner

Here is the raw list of the 46 CPython issues I opended between 2016-04-21 and
2017-02-10 to implement my FASTCALL optimization. Most issues created in 2016
are already part of Python 3.6.0, some are already merged into the future
Python 3.7, the few remaining issues are still open.

27 FASTCALL issues
==================

* 2016-04-21: `[WIP] Add a new _PyObject_FastCall() function which avoids the creation of a tuple or dict for arguments <http://bugs.python.org/issue26814>`_
* 2016-05-26: `Add _PyObject_FastCall() <http://bugs.python.org/issue27128>`_
* 2016-08-20: `Add _PyFunction_FastCallDict(): fast call with keyword arguments as a dict <http://bugs.python.org/issue27809>`_
* 2016-08-20: `Add METH_FASTCALL: new calling convention for C functions <http://bugs.python.org/issue27810>`_
* 2016-08-22: `Add _PyObject_FastCallKeywords(): avoid the creation of a temporary dictionary for keyword arguments <http://bugs.python.org/issue27830>`_
* 2016-08-23: `functools.partial: don't copy keywoard arguments in partial_call()? <http://bugs.python.org/issue27840>`_ [**REJECTED**]
* 2016-08-23: `Use fast call in method_call() and slot_tp_new() <http://bugs.python.org/issue27841>`_
* 2016-08-23: `Optimize update_keyword_args() function <http://bugs.python.org/issue27845>`_
* 2016-11-22: `Update python-gdb.py for fastcalls <http://bugs.python.org/issue28770>`_
* 2016-11-30: `_PyFunction_FastCallDict(): replace PyTuple_New() with PyMem_Malloc() <http://bugs.python.org/issue28839>`_ [**REJECTED**]
* 2016-12-02: `Compiler warnings in _PyObject_CallArg1() <http://bugs.python.org/issue28855>`_
* 2016-12-02: `Fastcall uses more C stack <http://bugs.python.org/issue28858>`_
* 2016-12-09: `Modify PyObject_CallFunction() to use fast call internally <http://bugs.python.org/issue28915>`_
* 2017-01-10: `Reduce C stack consumption in function calls <http://bugs.python.org/issue29227>`_
* 2017-01-10: `call_method(): call _PyObject_FastCall() rather than _PyObject_VaCallFunctionObjArgs() <http://bugs.python.org/issue29233>`_
* 2017-01-11: `Disable inlining of _PyStack_AsTuple() to reduce the stack consumption <http://bugs.python.org/issue29234>`_
* 2017-01-13: `Add tp_fastcall to PyTypeObject: support FASTCALL calling convention for all callable objects <http://bugs.python.org/issue29259>`_ [**REJECTED**]
* 2017-01-13: `Implement LOAD_METHOD/CALL_METHOD for C functions <http://bugs.python.org/issue29263>`_
* 2017-01-18: `Check usage of Py_EnterRecursiveCall() and Py_LeaveRecursiveCall() in new FASTCALL functions <http://bugs.python.org/issue29306>`_
* 2017-01-19: `Optimize _PyFunction_FastCallDict() for **kwargs <http://bugs.python.org/issue29318>`_ [**REJECTED**]
* 2017-01-24: `Add tp_fastnew and tp_fastinit to PyTypeObject, 15-20% faster object instanciation <http://bugs.python.org/issue29358>`_ [**REJECTED**]
* 2017-01-24: `_PyStack_AsDict(): Don't check if all keys are strings nor if keys are unique <http://bugs.python.org/issue29360>`_
* 2017-01-25: `python-gdb: display wrapper_call() <http://bugs.python.org/issue29367>`_
* 2017-02-05: `Use _PyArg_Parser for _PyArg_ParseStack(): support positional only arguments <http://bugs.python.org/issue29451>`_
* 2017-02-06: `Modify _PyObject_FastCall() to reduce stack consumption <http://bugs.python.org/issue29465>`_
* 2017-02-09: `Use FASTCALL in call_method() to avoid temporary tuple <http://bugs.python.org/issue29507>`_
* 2017-02-10: `Move functions to call objects into a new Objects/call.c file <http://bugs.python.org/issue29524>`_

3 issues converting functions to FASTCALL
=========================================

* 2017-01-16: `Use METH_FASTCALL in str methods <http://bugs.python.org/issue29286>`_
* 2017-01-18: `Use FASTCALL in dict.update() <http://bugs.python.org/issue29312>`_ [**REJECTED**]
* 2017-02-05: `Use FASTCALL for collections.deque methods: index, insert, rotate <http://bugs.python.org/issue29452>`_

6 Argument Clinic issues
========================

Converting code to Argument Clinic converts METH_VARARGS methods to
METH_FASTCALL.

* 2017-01-16: `Convert OrderedDict methods to Argument Clinic <http://bugs.python.org/issue29289>`_
* 2017-01-17: `Argument Clinic: Fix signature of optional positional-only arguments <http://bugs.python.org/issue29299>`_
* 2017-01-17: `Modify the _struct module to use FASTCALL and Argument Clinic <http://bugs.python.org/issue29300>`_
* 2017-01-17: `decimal: Use FASTCALL and/or Argument Clinic <http://bugs.python.org/issue29301>`_
* 2017-01-18: `Argument Clinic: convert dict methods <http://bugs.python.org/issue29311>`_
* 2017-02-02: `Argument Clinic: inline PyArg_UnpackTuple and PyArg_ParseStack(AndKeyword)? <http://bugs.python.org/issue29419>`_

10 other optimization issues
============================

* 2016-08-24: `C function calls: use Py_ssize_t rather than C int for number of arguments <http://bugs.python.org/issue27848>`_
* 2016-09-07: `Optimize bytes.join(sequence) <http://bugs.python.org/issue28004>`_ [**REJECTED**]
* 2016-11-05: `Decorate hot functions using __attribute__((hot)) to optimize Python <http://bugs.python.org/issue28618>`_
* 2016-11-07: `Python startup performance regression <http://bugs.python.org/issue28637>`_
* 2016-11-25: `Add RETURN_NONE bytecode instruction <http://bugs.python.org/issue28800>`_ [**REJECTED**]
* 2016-11-25: `Drop CALL_PROFILE special build? <http://bugs.python.org/issue28799>`_
* 2016-12-09: `Inline PyEval_EvalFrameEx() in callers <http://bugs.python.org/issue28924>`_ [**REJECTED**]
* 2016-12-15: `Document PyObject_CallFunction() special case more explicitly <http://bugs.python.org/issue28977>`_
* 2017-02-06: `Experiment usage of likely/unlikely in CPython core <http://bugs.python.org/issue29461>`_
* 2017-02-08: `Should PyObject_Call() call the profiler on C functions, use C_TRACE() macro? <http://bugs.python.org/issue29502>`_

