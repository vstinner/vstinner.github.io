++++++++++++++++++++++++++++++++++++++++
Python 3.7 New Development Mode (-X dev)
++++++++++++++++++++++++++++++++++++++++

:date: 2018-03-06 15:30
:tags: cpython
:category: python
:slug: python37-new-dev-mode
:authors: Victor Stinner


Development mode, -X dev
========================

bpo-32043: New "developer mode": "-X dev" option (#4413)

Add a new "developer mode": new "-X dev" command line option to
enable debug checks at runtime.

Changes:

* Add unit tests for -X dev
* test_cmd_line: replace test.support with support.
* Fix _PyRuntimeState_Fini(): Use the same memory allocator
   than _PyRuntimeState_Init().
* Fix _PyMem_GetDefaultRawAllocator()

bpo-32047: -X dev enables asyncio debug mode (#4418)

The new -X dev command line option now also enables asyncio debug
mode.

commit 895862aa01793a26e74512befb0c66a1da2587d6
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 09:47:03 2017 -0800

    bpo-32088: Display Deprecation in debug mode (#4474)

    When Python is build is debug mode (Py_DEBUG), DeprecationWarning,
    PendingDeprecationWarning and ImportWarning warnings are now
    displayed by default.

    test_venv: run "-m pip" and "-m ensurepip._uninstall" with -W
    ignore::DeprecationWarning since pip code is not part of Python.

commit f39b674876d2bd47ec7fc106d673b60ff24092ca
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 15:24:56 2017 -0800

    bpo-32094: Update subprocess for -X dev (#4480)

    Modify subprocess._args_from_interpreter_flags() to handle -X dev
    option.

    Add also unit tests for test.support.args_from_interpreter_flags()
    and test.support.optim_args_from_interpreter_flags().


I worked with Nick Coghlan to polish how warnings filters are created during
Python startup to get a straighforward behaviour and implement properly
Nick's PEP xxx (show deprecation warnings by default in the __main__ module).

commit 09f3a8a1249308a104a89041d82fe99e6c087043
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 17:32:40 2017 -0800

    bpo-32089: Fix warnings filters in dev mode (#4482)

    The developer mode (-X dev) now creates all default warnings filters
    to order filters in the correct order to always show ResourceWarning
    and make BytesWarning depend on the -b option.

    Write a functional test to make sure that ResourceWarning is logged
    twice at the same location in the developer mode.

    Add a new 'dev_mode' field to _PyCoreConfig.

commit bc9b6e29cb52f8da15613f9174af2f603131b56d
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 20 18:59:50 2017 -0800

    bpo-32043: Rephrase -X dev documentation (#4478)

    * should not be more verbose if the code is correct
    * enabled checks can be "expensive"

commit 21c7730761e2a768e33b89b063a095d007dcfd2c
Author: Victor Stinner <victor.stinner@gmail.com>
Date:   Mon Nov 27 12:11:55 2017 +0100

    bpo-32089: Use default action for ResourceWarning (#4584)

    In development and debug mode, use the "default" action, rather than
    the "always" action, for ResourceWarning in the default warnings
    filters.

::

    bpo-32101: Add PYTHONDEVMODE environment variable (#4624)

    * bpo-32101: Add sys.flags.dev_mode flag
      Rename also the "Developer mode" to the "Development mode".
    * bpo-32101: Add PYTHONDEVMODE environment variable
      Mention it in the development chapiter.

::

    bpo-32230: Set sys.warnoptions with -X dev (#4820)

    Rather than supporting dev mode directly in the warnings module, this
    instead adjusts the initialisation code to add an extra 'default'
    entry to sys.warnoptions when dev mode is enabled.

    This ensures that dev mode behaves *exactly* as if `-Wdefault` had
    been passed on the command line, including in the way it interacts
    with `sys.warnoptions`, and with other command line flags like `-bb`.

    Fix also bpo-20361: have -b & -bb options take precedence over any
    other warnings options.

    Patch written by Nick Coghlan, with minor modifications of Victor Stinner.

::

    bpo-32101: Fix tests for PYTHONDEVMODE=1 (#4821)

    test_asycio: remove also aio_path which was used when asyncio was
    developed outside the stdlib.



