++++++++++++++++++++++++++++++++++++++++++++++++++
Status of the FAT Python project, January 12, 2016
++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-01-12 12:00
:tags: optimization
:category: python
:slug: fat-python-status-janv12-2016
:authors: Victor Stinner
:summary: Status of the FAT Python project, January 12, 2016

.. image:: images/fat_python.jpg
   :alt: FAT Python project
   :align: right
   :target: http://faster-cpython.readthedocs.org/fat_python.html

Previous status: `November 26, 2015 <fat-status-nov26-2015>`.

Summary
=======

* New optimizations implemented:

  * constant propagation
  * constant folding
  * dead code elimination
  * simplify iterable
  * replace builtin __debug__ variable with its value

The two previous known major bugs "Wrong Line Numbers (and Tracebacks)" and
"exec(code, dict)" are now fixed.


Change log
==========

End of november
---------------

Major change: Remove the verdict subtype of dict: add a __version__ read-only
property to dict. Dictionary guards now hold a strong reference to the dict
value

Minor changes:

* Use dynamically memory for specialized code and guards, don't use fixed-size
  arrays anymore
* astoptimizer: enhance scope detection
* optimize astoptimizer: avoid the copy module
* Implement Config.max_constant_size
* Reenable checks on cell variables: allow cell variables if they are the same
* Reenable optimizations on methods calling super(), but never copy super()
  builtin to constants. If super() is replaced with a string, the required free
  variable (reference to the current class) is not created by the compiler
* Add PureBuiltin config
* Bugfix in VariableVisitor: handle ast.For
* NodeVisitor now calls generic_visit() before visit_XXX()
* Loop unrollingoptimize also for tuples
* At the end of Python initialization, create of builtins to later detect
  if a builtin was replaced. Import _fat at startup.
* Implement collections.UserDict.__version__

December (first half)
---------------------

Major changes:

* code.co_lnotab now supports negative line number delta.  Change the type of
  line number delta in co_lnotab from unsigned 8-bit integer to signed 8-bit
  integer. This change fixes almost all issues about line number.
* Implement new optimizations:

  * constant propagation
  * constant folding
  * replace builtin __debug__ variable with its value
  * dead code elimination

* Add support of per module configuration using an __astoptimizer__ variable

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
* Add Config.logger attribute. site: log into sys.stderr in verbose mode
* Move func.patch_constants() to code.replace_consts()
* Enhance marshal to fix test_: call frozenset() to get the empty frozenset
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
* Large refactoring to redesign the function specialization API

Minor changes:

* Start to write PEPs
* Dictionary guards now expect a list of names, instead of a single name.
* GuardFunc now uses a strong reference to the function, instead of a weak
  reference to simplify the code
* Initialize dictionary version to 0


Rewrite the API
===============

To design the PEP 510 and the AST transformers PEP, the API has been deeply
refactored.

First round for function specialization:

* astoptimizer now adds ``import fat`` to optimized code when specialization is
  used
* Remove the function subtype: add directly the ``specialize()`` method to
  functions
* Add support of any callable object, to ``func.specialize()``, not only code
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


Second round for AST transformers:

* Add sys.implementation.ast_transformers and sys.implementation.optim_tag
* Rename sys.asthook to sys.ast_transformers
* Add -X fat command line option to enable the FAT mode: register the
  astoptimizer in AST transformers
* Replace -F command line option with -o OPTIM_TAG
* Remove sys.flags.fat (Python flag) and Py_FatPython (C variable)
* Rewrite how an AST transformer is registered
* importlib skips .py if optim_tag is not 'opt' and required AST transformers
  are missing. Raise ImportError if the .pyc file is missing.

Third round for function specialization:

* Remove func.specialize() and func.get_specialized() at the Python level,
  replace them with C functions. Expose them again as fat.specialize(func, ...)
  and fat.get_specialized(func)
* fat.get_specialized() now returns a list of tuples, instead of a list of dict
* Make fat.Guard type private: rename it to fat._Guard
* Add fat.PyGuard: toy to implement a guard in pure Python
* Guard C API: rename first_check to init and support reporting errors


Python Enhancement Proposals (PEP)
==================================

I proposed a whole API for pluggable static optimizers and function
specialization. I splitted changes in 3 different Python Enhancement Proposals
(PEP):

* PEP 509 - Add a private version to dict: "Add a new private version to builtin
  ``dict`` type, incremented at each change, to implement fast guards on
  namespaces."
* PEP 510 - Specialize functions: "Add functions to the Python C API to
  specialize pure Python functions: add specialized codes with guards. It
  allows to implement static optimizers respecting the Python semantics."
* PEP xxx - API for AST transformers: "Propose an API to support AST
  transformers."

