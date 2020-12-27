+++++++++++++++++++++++
Isolate subinterpreters
+++++++++++++++++++++++

:date: 2020-03-20 23:00
:tags: subinterpreters, capi
:category: cpython
:slug: isolate-subinterpreters
:authors: Victor Stinner

Opaque PyInterpreterState
=========================

Change in Python 3.8.

2019-02-02: Eric Snow creates https://bugs.python.org/issue35886

`commit <https://github.com/python/cpython/commit/be3b295838547bba267eb08434b418ef0df87ee0>`__::

    bpo-35886: Make PyInterpreterState an opaque type in the public API. (GH-11731)

Moved PyInterpreterState structure from Include/cpython/pystate.h to Include/internal/pycore_pystate.h.

Long thread on python-dev: https://mail.python.org/pipermail/python-dev/2019-February/156344.html

cffi fix, include internal ``pycore_pystate.h``: https://bitbucket.org/cffi/cffi/commits/07d1803cb17b

Only 3 projects are known to be broken by this change:

* cffi (which indirectly broke brotlipy and httpbin)
* Blender
* FreeBSD

These projects have already been fixed. Usually, the code is easy to be
updated:

* Replace ``interp->modules`` with ``PyImport_GetModuleDict()``
* Replace ``interp->builtins`` with ``PyEval_GetBuiltins()``


