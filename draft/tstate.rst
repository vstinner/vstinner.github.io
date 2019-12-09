+++++++++++
Pass tstate
+++++++++++

:date: 2019-12-09 12:00
:tags: cpython
:category: python
:slug: cpython-pass-tstate
:authors: Victor Stinner

* `Pass _PyRuntimeState as an argument rather than using the _PyRuntime global
  variable
  <https://bugs.python.org/issue36710>`_
* `GC operates out of global runtime state.
  <https://bugs.python.org/issue36854>`_
* `new_interpreter() should reuse more Py_InitializeFromConfig() code
  <https://bugs.python.org/issue38858>`_
* `Pass explicitly tstate to function calls
  <https://bugs.python.org/issue38644>`_


Thread: `python-dev: Pass the Python thread state to internal C functions
<https://mail.python.org/archives/list/python-dev@python.org/thread/PQBGECVGVYFTVDLBYURLCXA3T7IPEHHO/#Q4IPXMQIM5YRLZLHADUGSUT4ZLXQ6MYY>`_.

subinterpreters:


* `PEP 554: Multiple Interpreters in the Stdlib
  <https://www.python.org/dev/peps/pep-0554/>`_
* Eric Snow's fork: `multi-core-python
  <https://github.com/ericsnowcurrently/multi-core-python/>`_. Eric also
  uses this project bug tracker to track the progress of the subinterpreters
  project.
* My notes: `Reorganize Python “runtime”
  <https://pythoncapi.readthedocs.io/runtime.html>`_

See also:

* `Replace Py_FatalError() with regular Python exceptions
  <https://bugs.python.org/issue38631>`_
