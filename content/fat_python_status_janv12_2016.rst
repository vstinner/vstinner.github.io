++++++++++++++++++++++++++++++++++++++++++++++++++
Status of the FAT Python project, January 12, 2016
++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-01-12 13:42
:tags: optimization
:category: python
:slug: fat-python-status-janv12-2016
:authors: Victor Stinner
:summary: Status of the FAT Python project, January 12, 2016

.. image:: images/fat_python.jpg
   :alt: FAT Python project
   :align: right
   :target: http://faster-cpython.readthedocs.org/fat_python.html

Previous status: `Status of the FAT Python project, November 26, 2015
<{filename}/fat_python_status_nov26_2015.rst>`_.

Summary
=======

* New optimizations implemented:

  * constant propagation
  * constant folding
  * dead code elimination
  * simplify iterable
  * replace builtin __debug__ variable with its value

* Major API refactoring to make the API more generic and reusable by other
  projects, and maybe different use case.

* Work on 3 different Python Enhancement Proposals (PEP): API for pluggable
  static optimizers and function specialization

The two previously known major bugs, "Wrong Line Numbers (and Tracebacks)" and
"exec(code, dict)", are now fixed.


Python Enhancement Proposals (PEP)
==================================

I proposed an API for to support function specialization and static optimizers.
I splitted changes in 3 different Python Enhancement Proposals (PEP):

* `PEP 509 - Add a private version to dict
  <https://www.python.org/dev/peps/pep-0509/>`_: "Add a new private version to
  builtin ``dict`` type, incremented at each change, to implement fast guards
  on namespaces."
* `PEP 510 - Specialize functions
  <https://www.python.org/dev/peps/pep-0510/>`_: "Add functions to the Python C
  API to specialize pure Python functions: add specialized codes with guards.
  It allows to implement static optimizers respecting the Python semantics."
* `PEP 511 - API for AST transformers
  <https://faster-cpython.readthedocs.org/pep_ast.html>`_: "Propose an API to
  support AST transformers."

The PEP 509 was sent to the python-ideas mailing list for a first round, and
then to python-dev mailing list.  The PEP 510 was sent to python-ideas to a
first round. The last PEP was not published yet, I'm still working on it.


Major API refactor
==================

The API has been deeply refactored to write the Python Enhancement Proposals.

First set of changes for function specialization (PEP 510):

* astoptimizer now adds ``import fat`` to optimized code when specialization is
  used
* Remove the function subtype: add directly the ``specialize()`` method to
  functions
* Add support of any callable object to ``func.specialize()``, not only code
  object (bytecode)
* Create guard objects:

  * fat.Guard
  * fat.GuardArgType
  * fat.GuardBuiltins
  * fat.GuardDict
  * fat.GuardFunc

* Add functions to create guards:

  * fat.GuardGlobals
  * fat.GuardTypeDict

* Move code.replace_consts() to the fat.replace_consts()


Second set of changes for AST transformers (PEP 511):

* Add sys.implementation.ast_transformers and sys.implementation.optim_tag
* Rename sys.asthook to sys.ast_transformers
* Add -X fat command line option to enable the FAT mode: register the
  astoptimizer in AST transformers
* Replace -F command line option with -o OPTIM_TAG
* Remove sys.flags.fat (Python flag) and Py_FatPython (C variable)
* Rewrite how an AST transformer is registered
* importlib skips .py if optim_tag is not 'opt' and required AST transformers
  are missing. Raise ImportError if the .pyc file is missing.

Third set of changes for dictionary versionning, updates after the first round
of the PEP 509 on python-ideas:

* Remove dict.__version__ read-only property: the version is now only
  accessible from the C API
* Change the type of the C field ``ma_verison`` from ``size_t`` to ``unsigned
  PY_INT64_T`` to also use 64-bit unsigned integer on 32-bit platforms. The
  risk of misisng a change in a guard with a 32-bit version is too high,
  whereas the risk with a 64-bit version is very very low.

Fourth set of changes for function specialization, updates after the first round
of the PEP 510 on python-ideas:

* Remove func.specialize() and func.get_specialized() at the Python level,
  replace them with C functions. Expose them again as fat.specialize(func, ...)
  and fat.get_specialized(func)
* fat.get_specialized() now returns a list of tuples, instead of a list of dict
* Make fat.Guard type private: rename it to fat._Guard
* Add fat.PyGuard: toy to implement a guard in pure Python
* Guard C API: rename first_check to init and support reporting errors


Change log
==========

Detailed changes of the FAT Python between November 24, 2015 and January 12,
2016.

End of november
---------------

Major change:

* Add a __version__ read-only property to dict, remove the verdict subtype of
  dict. As a consequence, dictionary guards now hold a strong reference to the
  dict value

Minor changes:

* Allocate dynamically memory for specialized code and guards, don't use fixed-size
  arrays anymore
* astoptimizer: enhance scope detection
* optimize astoptimizer: don't copy a whole AST tree anymore with
  copy.deepcopy(), only copy modified nodes.
* Add Config.max_constant_size
* Reenable checks on cell variables: allow cell variables if they are the same
* Reenable optimizations on methods calling super(), but never copy super()
  builtin to constants. If super() is replaced with a string, the required free
  variable (reference to the current class) is not created by the compiler
* Add PureBuiltin config
* NodeVisitor now calls generic_visit() before visit_XXX()
* Loop unrolling now also optimizes tuple iterators
* At the end of Python initialization, create a copy of the builtins dictionary
  to be able later to detect if a builtin name was replaced.
* Implement collections.UserDict.__version__

December (first half)
---------------------

Major changes:

* Implement 4 new optimizations:

  * constant propagation
  * constant folding
  * replace builtin __debug__ variable with its value
  * dead code elimination

* Add support of per module configuration using an __astoptimizer__ variable
* code.co_lnotab now supports negative line number delta.  Change the type of
  line number delta in co_lnotab from unsigned 8-bit integer to signed 8-bit
  integer. This change fixes almost all issues about line numbers.

Minor changes:

* Change .pyc magic number to 3600
* Remove unused fat.specialized_method() function
* Remove Lib/fat.py, rename Modules/_fat.c to Modules/fat.c: fat module is now
  only implemented in C
* Fix more tests of the Python test suite
* A builtin guard now adds a guard on globals. Ignore also the specialization
  if globals()[name] already exists.
* Ignore duplicated guards
* Implement namespace following the control flow for constant propagation
* Config.max_int_bits becomes a simple integer
* Fix bytecode compilation for tuple constants. Don't merge (0, 0) and (0.0,
  0.0) constants, they are different.
* Call more builtin functions
* Optimize the optimizer: write a metaclass to discover visitors when the class
  is created, not when the class is instanciated


December (second half)
----------------------

Major changes:

* Implement "simplify iterable" optimization. The loop unrolling optimization
  now relies on it to replace ``range(n)``.
* Split the function optimization in two stages: first apply optimizations
  which don't require specialization, then apply optimizations which
  require specialization.
* Replace the builtin __fat__ variable with a new sys.flags.fat flag

Minor changes:

* Extend optimizations to optimize more cases (more builtins, more loop
  unrolling, remove more dead code, etc.)
* Add Config.logger attribute. astoptimize logs into sys.stderr when Python is
  started in verbose mode (python3 -v)
* Move func.patch_constants() to code.replace_consts()
* Enhance marshal to fix tests: call frozenset() to get the empty frozenset
  singleton
* Don't remove code which must raise a SyntaxError. Don't remove code
  containing the continue instruction.
* Restrict GlobalNonlocalVisitor to the current namespace
* Emit logs when optimizations are skipped
* Use some maths to avoid optimization pow() if result is an integer and will
  be larger than the configuration. For example, don't optimize 2 ** (2**100).


January
-------

Major changes:

* astoptimizer now produces a single builtin guard with all names,
  instead of a guard per name.
* Major API refactoring detailed in a dedicated section above

Minor changes:

* Start to write PEPs
* Dictionary guards now expect a list of names, instead of a single name, to
  reduce the cost of guards.
* GuardFunc now uses a strong reference to the function, instead of a weak
  reference to simplify the code
* Initialize dictionary version to 0
