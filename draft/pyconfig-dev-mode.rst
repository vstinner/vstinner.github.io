++++++++++++++++++++++++++++++++++++++++++
PyConfig: Python Development Mode (-X dev)
++++++++++++++++++++++++++++++++++++++++++

:date: 2020-01-13 23:00
:tags: cpython
:category: python
:slug: pyconfig-dev-mode
:authors: Victor Stinner

This article describes the discussion on the design of the development mode
that I added to Python 3.7 and how it was implemented. It can be enabled by
``python3 -X dev`` command line or ``PYTHONDEVMODE=1`` environment variable.

python-ideas
============

In March 2016, I proposed on Python-ideas, `Add a developer mode to Python: -X
dev command line option
<https://mail.python.org/pipermail/python-ideas/2016-March/039314.html>`__:

    When I develop on CPython, I'm always building Python in debug mode
    using ``./configure --with-pydebug``. This mode enables a **lot** of extra
    checks which helps me to detect bugs earlier. The debug mode makes Python
    much slower and so is not the default.

    I propose to add a "development mode" to Python, to get a few checks
    to detect bugs earlier: a new ``-X dev`` command line option. Example::

       python3.6 -X dev script.py

    I propose to enable:

    * Show ``DeprecationWarning`` and ``ResourceWarning warnings``: ``python -Wd``
    * Show ``BytesWarning`` warning: ``python -b``
    * Enable Python assertions (``assert``) and set ``__debug__`` to True:
      remove (or just ignore) ``-O`` or ``-OO`` command line arguments
    * faulthandler to get a Python traceback on segfault and fatal errors:
      ``python -X faulthandler``
    * Debug hooks on Python memory allocators: ``PYTHONMALLOC=debug``

I even wrote an implementation using ``exec()``. Ronald Oussoren `commented my
patch <https://bugs.python.org/issue26670#msg262659>`_:

    Why does this patch execv() the interpreter to set options? I'd expect it
    to be possible to get the same result by updating the argument parsing code
    in Py_Main.

More on that later :-)

Marc-Andre Lemburg `didn't buy the idea
<https://mail.python.org/pipermail/python-ideas/2016-March/039325.html>`_:

    I'm not sure whether this would make things easier for the
    majority of developers, e.g. someone not writing C extensions
    would likely not be interested in debugging memory allocations
    or segfaults, someone spending more time on numerics wouldn't
    bother with bytes warnings, etc.

Opinion shared by Ethan Furman, so I gave up at this point. I closed my issue.


DeprecationWarning and async keyword
====================================

LWN: `Who should see Python deprecation warnings?
<https://lwn.net/Articles/740804/>`_ (December 2017) by Jonathan Corbet.

     In early November, one sub-thread of a big discussion on preparing for the
     Python 3.7 release focused on the await and async identifiers. They will
     become keywords in 3.7, meaning that any code using those names for any
     other purpose will break. Nick Coghlan observed that Python 3.6 does not
     warn about the use of those names, calling it "a fairly major
     oversight/bug". In truth, though, Python 3.6 does emit warnings in that
     case — but users rarely see them.

https://mail.python.org/pipermail/python-dev/2017-November/150132.html

https://mail.python.org/pipermail/python-dev/2017-November/150250.html

In Novembre 2017, Nick Coghlan proposed `PEP 565: Show DeprecationWarning in
__main__ <https://www.python.org/dev/peps/pep-0565/>`_.

I wasn't convinced that only displaying warnings in the __main__ module is
enough to help developers to fix issues in their code. I came back with my
idea, now on the python-dev list, `Add a developer mode to Python: -X dev
command line option
<https://mail.python.org/pipermail/python-dev/2017-November/150514.html>`__.

This mode shows ``DeprecationWarning`` and ``ResourceWarning`` is all modules,
not only in the ``__main__`` module. Having an opt-in mode for developers was
the best option in my opinion. Python should not spam users with warnings which
are designed for developers than users.

Implementation issues
=====================

When I proposed the idea, my plan was to call exec() to replace the current
process with a new process. But when I tried to implement it, it was more
tricky than expected. My first blocker issue was to remove ``-O`` option from
the command line. I hate having to parse the command line: it is very fragile,
it's easy to make mistake.

So I tried to write a clean implementation: configure Python properly in
"development mode". One blocker issue is to implement ``PYTHONMALLOC=debug``.
The C code to read and apply the Python configuration used Python objects
before the Python initialization even started. For example, ``-W`` and ``-X``
options were stored as Python lists. It means that the Python memory allocator
was used before Python would be able to parse ``PYTHONMALLOC`` environment
variable.

Moreover, the Python configuration is quite complex. Many options are
inter-dependent. For example, the ``-E`` command line option ignores
environment variables with a name staring with ``PYTHON``: like
``PYTHONMALLOC``! Python has to parse the command line before being able to
handle ``PYTHONMALLOC``. But, again, the code parsing the command line used
Python objects.

In short, it wasn't possible to write a clean implementation of the development
mode.

main.c refactoring
==================

For all these reasons, I decided to look at ``Modules/main.c`` to see if I
could enhance the code to avoid some of these "bootstrap issues". At this time,
I didn't know that I will work on this file for one year and a half!

In `bpo-32030 <https://bugs.python.org/issue32030>`__, I prepared the Python
code base to be able to implement ``-X dev`` more easily later::

    commit f7e5b56c37eb859e225e886c79c5d742c567ee95
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Nov 15 15:48:08 2017 -0800

        bpo-32030: Split Py_Main() into subfunctions (#4399)

    ommit a7368ac6360246b1ef7f8f152963c2362d272183
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Wed Nov 15 18:11:45 2017 -0800

        bpo-32030: Enhance Py_Main() (#4412)

Add -X dev option
=================

In `bpo-32043 <https://bugs.python.org/issue32043>`__, I pushed `commit ccb0442a
<https://github.com/python/cpython/commit/ccb0442a338066bf40fe417455e5a374e5238afb>`__::

    commit ccb0442a338066bf40fe417455e5a374e5238afb
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Thu Nov 16 03:20:31 2017 -0800

        bpo-32043: New "developer mode": "-X dev" option (#4413)

        Add a new "developer mode": new "-X dev" command line option to
        enable debug checks at runtime.

Effects of the development mode:

* Add ``default`` warnings option. For example, display ``DeprecationWarning``
  and ``ResourceWarning`` warnings.
* Install debug hooks on memory allocators as if ``PYTHONMALLOC`` is set to
  ``debug``.
* Enable the `faulthandler`` module to dump the Python traceback on a crash.

Add PYTHONDEVMODE environment variable
======================================

Antoine Pitrou `proposed
<https://github.com/python/cpython/pull/4478#pullrequestreview-77874230>`_ to
add an environment variable to enable the new Python "developer mode" to
inherit the developer mode in child Python processes.

I created `bpo-32101 <https://bugs.python.org/issue32101>`__ and then I pushed
`commit 5e3806f8
<https://github.com/python/cpython/commit/5e3806f8cfd84722fc55d4299dc018ad9b0f8401>`__::

    commit 5e3806f8cfd84722fc55d4299dc018ad9b0f8401
    Author: Victor Stinner <victor.stinner@gmail.com>
    Date:   Thu Nov 30 11:40:24 2017 +0100

        bpo-32101: Add PYTHONDEVMODE environment variable (#4624)

        * bpo-32101: Add sys.flags.dev_mode flag
          Rename also the "Developer mode" to the "Development mode".
        * bpo-32101: Add PYTHONDEVMODE environment variable
          Mention it in the development chapiter.

Enable asyncio debug mode
=========================

I created `bpo-32047: asyncio: enable debug mode when -X dev is used
<https://bugs.python.org/issue32047>`_. `I asked in the -X dev thread on
python-dev
<https://mail.python.org/pipermail/python-dev/2017-November/150572.html>`_:

    What do you think? Is it ok to include asyncio in the global "developer mode"?

Antoine Pitrou didn't like the idea because asyncio debug mode was "quite
expensive", but Yury Selivanov (one of the asyncio maintainers) and Barry
Warsaw liked the idea, so I merged my PR: `commit 44862df2
<https://github.com/python/cpython/commit/44862df2eeec62adea20672b0fe2a5d3e160569e>`__.

Antoine Pitrou created `bpo-31970: asyncio debug mode is very slow
<https://bugs.python.org/issue31970>`_. Hopefully, he found a way to make
asyncio debug mode more efficient by truncating tracebacks to 10 frames:

`commit 921e9432 <https://github.com/python/cpython/commit/921e9432a1461bbf312c9c6dcc2b916be6c05fa0>`__::

    commit 921e9432a1461bbf312c9c6dcc2b916be6c05fa0
    Author: Antoine Pitrou <pitrou@free.fr>
    Date:   Tue Nov 7 17:23:29 2017 +0100

        bpo-31970: Reduce performance overhead of asyncio debug mode. (#4314)

Warnings
========

I completed the documentation and fixed warnings filters (`bpo-32089
<https://bugs.python.org/issue32089>`__).

Example
=======

Even with PEP 565, ``ResourceWarning`` is still not displayed by default::

    $ python3 -c 'print(len(open("README.rst").readlines()))'
    39

But it is displayed in development mode::

    $ python3 -X dev -c 'print(len(open("README.rst").readlines()))'
    -c:1: ResourceWarning: unclosed file <_io.TextIOWrapper name='README.rst' mode='r' encoding='UTF-8'>
    ResourceWarning: Enable tracemalloc to get the object allocation traceback
    39

If one of the development mode side effect causes an issue, it is still
possible to override most options. For example, ``PYTHONMALLOC=default`` does
not install debug hooks on memory allocators.


PEP 565
=======

By the way, Python 3.7 also got the implementation of Nick's `PEP 565: Show
DeprecationWarning in __main__ <https://www.python.org/dev/peps/pep-0565/>`__.

Example: XXX

