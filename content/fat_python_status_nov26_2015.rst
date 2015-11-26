+++++++++++++++++++++++++++++++++++++++++++++++++++
Status of the FAT Python project, November 26, 2015
+++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2015-11-26 17:30
:tags: optimization
:category: python
:slug: fat-python-status-nov26-2015
:authors: Victor Stinner
:summary: Status of the FAT Python project, November 26, 2015

Previous status: [python-dev] `Second milestone of FAT Python
<https://mail.python.org/pipermail/python-dev/2015-November/142113.html>`_
(Nov 4, 2015).


Documentation
=============

I combined the documentation of various optimizations projects into a single
documentation: `Faster CPython <http://faster-cpython.readthedocs.org/>`_.
My previous optimizations projects:

* `"old" astoptimizer
  <http://faster-cpython.readthedocs.org/old_ast_optimizer.html>`_ (now
  replaced with a "new" astoptimizer included in the FAT Python, see below)
* `registervm <http://faster-cpython.readthedocs.org/registervm.html>`_
* `read-only Python <http://faster-cpython.readthedocs.org/readonly.html>`_

The FAT Python project has its own page: `FAT Python project
<http://faster-cpython.readthedocs.org/fat_python.html>`_.


Copy builtins to constants optimization
=======================================

xxx


Loop unrolling optimization
===========================

xxx


Lot of enhancements of the AST optimizer
========================================

New optimizations helped to find bugs in the AST optimizer. Many fixes and
various enhancements were done in the AST optimizer.

The number of lines of code more than doubled: 500 to 1200 lines.

Optimization: ``copy.deepcopy()`` is no more used to duplicate a full tree. The
new ``NodeTransformer`` class now only copies a single node, if at least one
field is modified.

The ``VariableVisitor`` class which detects local and global variables was
heavily modified. It handles much more AST nodes: ``For``, ``AugAssign``,
``AsyncFunctionDef``, ``ClassDef``, etc. It now also detects non-local
variables (``nonlocal`` keyword). The scope is now limited to the current
function, it doesn't enter inside nested ``DictComp``, ``FunctionDef``,
``Lambda``, ...: these node create a new separated namespace.

The optimizer is now able to optimize without guards: it's need for loop
unrolling of a loop using a tuple.


Known bugs
==========

See the `TODO.rst file
<https://hg.python.org/sandbox/fatpython/file/0d30dba5fa64/TODO.rst>`_ for
known bugs.

Wrong Line Numbers (and Tracebacks)
-----------------------------------

AST nodes have ``lineno`` and ``col_offset`` fields, so an AST optimizer is not
"supposed" to break line numbers. In practice, line numbers and so traceback
are completly wrong in FAT mode. The problem is probably that AST optimizer
can copy and move instructions, line numbers are no more motononic. CPython
probably don't handle this case. It should be possible to fix it.


exec(code, dict)
----------------

In FAT mode, some optimizations require guards on the global namespace.
If ``exec()`` if called with a Python ``dict`` for globals, an exception
is raised beacuse ``func.specialize()`` requires a ``fat.verdict`` for
globals.

This bug will go avoid if the versionning feature is moved directly into
the builtin ``dict`` type.
