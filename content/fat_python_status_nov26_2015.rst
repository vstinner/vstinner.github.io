.. _fat-status-nov26-2015:

+++++++++++++++++++++++++++++++++++++++++++++++++++
Status of the FAT Python project, November 26, 2015
+++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2015-11-26 17:30
:tags: optimization, fatpython
:category: python
:slug: fat-python-status-nov26-2015
:authors: Victor Stinner
:summary: Status of the FAT Python project, November 26, 2015

.. image:: {static}/images/fat_python.jpg
   :alt: FAT Python project
   :align: right
   :target: http://faster-cpython.readthedocs.org/fat_python.html

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
  replaced with a "new" astoptimizer included in the FAT Python)
* `registervm <http://faster-cpython.readthedocs.org/registervm.html>`_
* `read-only Python <http://faster-cpython.readthedocs.org/readonly.html>`_

The FAT Python project has its own page: `FAT Python project
<http://faster-cpython.readthedocs.org/fat_python.html>`_.


Copy builtins to constants optimization
=======================================

The ``LOAD_GLOBAL`` instruction is used to load a builtin function.  The
instruction requires two dictionary lookup: one in the global namespace (which
almost always fail) and then in the builtin namespaces.

It's rare to replace builtins, so the idea here is to replace the dynamic
``LOAD_GLOBAL`` instruction with a static ``LOAD_CONST`` instruction which
loads the function from a C array, a fast O(1) lookup.

It is not possible to inject a builtin function during the compilation. Python
code objects are serialized by the marshal module which only support simple
types like integers, strings and tuples, not functions. The trick is to modify
the constants at runtime when the module is loaded. I added a new
``patch_constants()`` method to functions.

Example::

    def log(message):
        print(message)

This function is specialized to::

    def log(message):
        'LOAD_GLOBAL print'(message)
    log.patch_constants({'LOAD_GLOBAL print': print})

The specialized bytecode uses two guards on builtin and global namespaces to
disable the optimization if the builtin function is replaced.

See `Copy builtin functions to constants
<https://faster-cpython.readthedocs.org/fat_python.html#copy-builtin-functions-to-constants>`_
for more information.


Loop unrolling optimization
===========================

A simple optimization is to "unroll" a loop to reduce the cost of loops. The
optimization generates assignement statements (for the loop index variable)
and duplicates the loop body.

Example with a ``range()`` iterator::

    def func():
        for i in (1, 2, 3):
            print(i)

The function is specialized to::

    def func():
        i = 1
        print(i)

        i = 2
        print(i)

        i = 3
        print(i)

If the iterator uses the builtin ``range`` function, two guards are
required on builtin and global namespaces.

The optimization also handles tuple iterator. No guard is needed in this case
(the code is always optimized).

See `Loop unrolling
<https://faster-cpython.readthedocs.org/fat_python.html#loop-unrolling>`_
for more information.


Lot of enhancements of the AST optimizer
========================================

New optimizations helped to find bugs in the `AST optimizer
<https://faster-cpython.readthedocs.org/new_ast_optimizer.html>`_. Many fixes
and various enhancements were done in the AST optimizer.

The number of lines of code more than doubled: 500 to 1200 lines.

Optimization: ``copy.deepcopy()`` is no more used to duplicate a full tree. The
new ``NodeTransformer`` class now only copies a single node, if at least one
field is modified.

The ``VariableVisitor`` class which detects local and global variables was
heavily modified. It understands much more kinds of AST node: ``For``, ``AugAssign``,
``AsyncFunctionDef``, ``ClassDef``, etc. It now also detects non-local
variables (``nonlocal`` keyword). The scope is now limited to the current
function, it doesn't enter inside nested ``DictComp``, ``FunctionDef``,
``Lambda``, etc. These nodes create a new separated namespace.

The optimizer is now able to optimize a function without guards: it's needed to
unroll a loop using a tuple as iterator.


Known bugs
==========

See the `TODO.rst file
<https://hg.python.org/sandbox/fatpython/file/0d30dba5fa64/TODO.rst>`_ for
known bugs.

Wrong Line Numbers (and Tracebacks)
-----------------------------------

AST nodes have ``lineno`` and ``col_offset`` fields, so an AST optimizer is not
"supposed" to break line numbers. In practice, line numbers, and so tracebacks,
are completly wrong in FAT mode. The problem is probably that AST optimizer can
copy and move instructions. Line numbers are no more motononic. CPython
probably don't handle this case (negative line delta).

It should be possible to fix it, but right now I prefer to focus on new
optimizations and fix other bugs.


exec(code, dict)
----------------

In FAT mode, some optimizations require guards on the global namespace.
If ``exec()`` if called with a Python ``dict`` for globals, an exception
is raised because ``func.specialize()`` requires a ``fat.verdict`` for
globals.

It's not possible to convert implicitly the ``dict`` to a ``fat.verdict``,
because the ``dict`` is expected to be mutated, and the guards be will on
``fat.verdict`` not on the original ``dict``.

I worked around the bug by creating manually a ``fat.verdict`` in FAT mode,
instead of a ``dict``.

This bug will go avoid if the versionning feature is moved directly into
the builtin ``dict`` type (and the ``fat.verdict`` type is removed).
