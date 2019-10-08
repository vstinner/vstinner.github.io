_PyObject_ASSERT
_Py_NegativeRefcount
gcmodule.c
Py_FatalError()
visit_decref()
_PyObject_Dump()
_PyObject_IsFreed()
_PyObject_CheckConsistency(): function currently unused

Experimental issues:

* gc.enable_object_debugger()

Python 3.6: xxx
Python 3.7: xxx
Python 3.8: Debug build is ABI compatible with release build, no need to recompile
Python 3.9: visit_decref(), Py GC Track
