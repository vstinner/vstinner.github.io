++++++++++++++++++++++
Python Debug Build ABI
++++++++++++++++++++++

:date: 2019-06-19 18:00
:tags: python, c-api
:category: python
:slug: python-debug-build-abi
:authors: Victor Stinner

First attempt
=============

Example with sleep.py::

    import time

    def func():
        time.sleep(60)

    func()

First attempt::

    vstinner@apu$ gdb -args python3 sleep.py
    GNU gdb (GDB) Fedora 8.3-3.fc30

    Reading symbols from python3...
    (No debugging symbols found in python3)
    Missing separate debuginfos, use: dnf debuginfo-install python3-3.7.3-3.fc30.x86_64

    (gdb) run
    Starting program: /usr/bin/python3 sleep.py
    [Thread debugging using libthread_db enabled]
    Using host libthread_db library "/lib64/libthread_db.so.1".

    ^C
    Program received signal SIGINT, Interrupt.
    0x00007ffff7ecaaeb in select () from /lib64/libc.so.6

    (gdb) py-bt
    Undefined command: "py-bt".  Try "help".

    (gdb) where
    #0  0x00007ffff7ecaaeb in select () from /lib64/libc.so.6
    #1  0x00007ffff7c591fd in ?? () from /lib64/libpython3.7m.so.1.0
    #2  0x00007ffff7b9a833 in _PyMethodDef_RawFastCallKeywords ()
       from /lib64/libpython3.7m.so.1.0
    #3  0x00007ffff7b9aa63 in _PyCFunction_FastCallKeywords ()
       from /lib64/libpython3.7m.so.1.0
    #4  0x00007ffff7bd3063 in ?? () from /lib64/libpython3.7m.so.1.0
    #5  0x00007ffff7c158b2 in _PyEval_EvalFrameDefault ()
       from /lib64/libpython3.7m.so.1.0
    ...

* Function arguments are missing
* My favorite command ``py-bt`` is not available

Second attempt
==============

Fedora gdb suggests: ``dnf debuginfo-install python3-3.7.3-3.fc30.x86_64``. Let
me try::

    sudo dnf debuginfo-install -y python3

::

    $ gdb -args python3 sleep.py
    GNU gdb (GDB) Fedora 8.3-3.fc30

    Reading symbols from python3...
    Reading symbols from /usr/lib/debug/usr/bin/python3.7m-3.7.3-3.fc30.x86_64.debug...

    (gdb) run
    Starting program: /usr/bin/python3 sleep.py
    Missing separate debuginfos, use: dnf debuginfo-install glibc-2.29-9.fc30.x86_64
    [Thread debugging using libthread_db enabled]
    Using host libthread_db library "/lib64/libthread_db.so.1".

    ^C
    Program received signal SIGINT, Interrupt.
    0x00007ffff7ecaaeb in select () from /lib64/libc.so.6

    (gdb) py-bt
    Traceback (most recent call first):
      <built-in method sleep of module object at remote 0x7fffea77d3b8>
      File "sleep.py", line 4, in func
        time.sleep(60)
      File "sleep.py", line 6, in <module>
        func()

    (gdb) where
    #0  0x00007ffff7ecaaeb in select () from /lib64/libc.so.6
    #1  0x00007ffff7c591fd in pysleep (secs=<optimized out>) at /usr/src/debug/python3-3.7.3-3.fc30.x86_64/Modules/timemodule.c:1829
    #2  time_sleep (self=<optimized out>, obj=<optimized out>) at /usr/src/debug/python3-3.7.3-3.fc30.x86_64/Modules/timemodule.c:371
    #3  0x00007ffff7b9a833 in _PyMethodDef_RawFastCallKeywords (method=0x7ffff7d84400 <time_methods+288>,
        self=<module at remote 0x7fffea77d3b8>, args=<optimized out>, nargs=<optimized out>, kwnames=0x0)
        at /usr/src/debug/python3-3.7.3-3.fc30.x86_64/Objects/call.c:644
    #4  0x00007ffff7b9aa63 in _PyCFunction_FastCallKeywords (func=<built-in method sleep of module object at remote 0x7fffea77d3b8>,
        args=<optimized out>, nargs=<optimized out>, kwnames=<optimized out>) at /usr/src/debug/python3-3.7.3-3.fc30.x86_64/Objects/call.c:730
    #5  0x00007ffff7bd3063 in call_function (pp_stack=0x7fffffffcec0, oparg=<optimized out>, kwnames=0x0)
        at /usr/src/debug/python3-3.7.3-3.fc30.x86_64/Python/ceval.c:4568
    #6  0x00007ffff7c158b2 in _PyEval_EvalFrameDefault (f=<optimized out>, throwflag=<optimized out>)
        at /usr/src/debug/python3-3.7.3-3.fc30.x86_64/Python/ceval.c:3093
    ...

It is better:

* ``py-bt`` works: display the Python traceback
* **Most** function arguments are now displayed, but some are missing:
  ``args=<optimized out>``


The "optimized out" problem
===========================

gdb mostly works, but there are many ``<optimized out>``: it happens when the
compiler choose to store parameters or variables in registers. Example::

    (gdb) frame 0
    #0  select () from /lib64/libc.so.6

    (gdb) frame 1
    #1  pysleep (secs=<optimized out>) ...
    (gdb) p secs
    $1 = <optimized out>

    (gdb) frame 2
    #2  time_sleep (self=<optimized out>, obj=<optimized out>) ...
    (gdb) p obj
    $2 = <optimized out>

Going deeper doesn't help::

    (gdb) frame 3
    #3  _PyMethodDef_RawFastCallKeywords (method=0x7ffff7d84400 <time_methods+288>,
        self=<module at remote 0x7fffea77d3b8>, args=<optimized out>, nargs=<optimized out>, kwnames=0x0)
        ...
    (gdb) p args
    $3 = <optimized out>

    (gdb) frame 4
    #4  _PyCFunction_FastCallKeywords (func=<built-in method sleep of module object at remote 0x7fffea77d3b8>,
        args=<optimized out>, nargs=<optimized out>, kwnames=<optimized out>) ...
    (gdb) p args
    $4 = <optimized out>

    (gdb) frame 5
    #5  call_function (pp_stack=0x7fffffffcec0, oparg=<optimized out>, kwnames=0x0) ...
    (gdb) p oparg
    $5 = <optimized out>

On the basic example, it is really hard to retrieve the argument ``60`` of the
most recent Python frame: ``time.sleep(60)``.

I had to go up to ``_PyEval_EvalFrameDefault()`` and inspects the very
low-level ``stack_pointer`` variable to get it::

    (gdb) frame 6
    #6  _PyEval_EvalFrameDefault (f=<optimized out>, throwflag=<optimized out>) ...
    (gdb) p stack_pointer[-1]
    $9 = 60

Note: Maybe following gdb advice, run ``dnf debuginfo-install
glibc-2.29-9.fc30.x86_64``, would allow to get the parameter in the frame 0
(``select()``).


Debug build ABI
===============

Antoine Pitrou once asked who rely on the ``Py_TRACE_REFS`` feature. It's a
macro which adds 2 fields (``_ob_prev`` and ``_ob_next``) to the most important
structure of Python: ``PyObject``. It creates a double-linked list of all
Python objects, so it becomes possible to iterate on all objects. For example,
this feature add ``sys.getobjects()`` function. It is different than
``gc.get_objects()`` which only returns the objects tracked by the garbage
collector.

I created `bpo-36465: Make release and debug ABI compatible
<https://bugs.python.org/issue36465>`_ to propose to no longer define
``Py_TRACE_REFS`` macro when Python is built in debug mode.

I started a thread on python-dev mailing list: `No longer enable Py_TRACE_REFS
by default in debug build
<https://mail.python.org/pipermail/python-dev/2019-April/157015.html>`_. This
discussion gone in many directions but missed my initial point: enhance the
debugging experience.

So I created a second thread with a better title and better rationale: `Use C
extensions compiled in release mode on a Python compiled in debug mode
<https://mail.python.org/pipermail/python-dev/2019-April/157178.html>`_.

One month later, the change was approved by core developers, I pushed my
`commit f4e4703e
<https://github.com/python/cpython/commit/f4e4703e746067d6630410408d414b11003334d6>`__::

    commit f4e4703e746067d6630410408d414b11003334d6
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Thu Apr 25 00:56:28 2019 +0200

        bpo-36465: Make release and debug ABI compatible (GH-12615)

        Release build and debug build are now ABI compatible: the Py_DEBUG
        define no longer implies Py_TRACE_REFS define which introduces the
        only ABI incompatibility.

        A new "./configure --with-trace-refs" build option is now required to
        get Py_TRACE_REFS define which adds sys.getobjects() function and
        PYTHONDUMPREFS environment variable.

        Changes:

        * Add ./configure --with-trace-refs
        * Py_DEBUG no longer implies Py_TRACE_REFS

Release builds and debug builds are now ABI compatible: defining the
``Py_DEBUG`` macro no longer implies the ``Py_TRACE_REFS`` macro, which
introduces the only ABI incompatibility. The ``Py_TRACE_REFS`` macro, which
adds the :func:`sys.getobjects` function and the :envvar:`PYTHONDUMPREFS`
environment variable, can be set using the new ``./configure --with-trace-refs``
build option.


Don't link C extensions to libpython
====================================

The second problem is that C extensions are explicitly linked to ``libpython``.
Example::

    $ python3 -c 'import _asyncio; print(_asyncio.__file__)'
    /usr/lib64/python3.7/lib-dynload/_asyncio.cpython-37m-x86_64-linux-gnu.so
    $ ldd $(python3 -c 'import _asyncio; print(_asyncio.__file__)')
            libpython3.7m.so.1.0 => /lib64/libpython3.7m.so.1.0 (0x00007f65f32a3000)
            ...

The ``_asyncio`` extension is explicitly linked to ``libpython3.7m.so.1.0``
which is built in release mode. In debug mode, the ``libpython`` filename is
different::

    $ python3.7dm -c 'import _asyncio; print(_asyncio.__file__)'
    /usr/lib64/python3.7/lib-dynload/_asyncio.cpython-37dm-x86_64-linux-gnu.so
    $ ldd $(python3.7dm -c 'import _asyncio; print(_asyncio.__file__)')
            libpython3.7dm.so.1.0 => /lib64/libpython3.7dm.so.1.0 (0x00007f015b5a7000)
            ...

``libpython3.7dm.so.1.0`` instead of ``libpython3.7m.so.1.0``: additional ``d``
in ABI flags which stands for "debug build". The ABI is different in Python 3.7
because of ``Py_TRACE_REFS``.

By the way, I'm using this check to know if I'm using a release or debug build of Python::

    $ python3.7
    >>> import sys; sys.gettotalrefcount()
    AttributeError: module 'sys' has no attribute 'gettotalrefcount'

    $ python3.7dm
    >>> import sys; sys.gettotalrefcount()
    65616

``sys.gettotalrefcount()`` is only available in debug build.

Always or never link C extensions to libpython?
-----------------------------------------------

In September 2018, I already worked on a similar issue: `bpo-34814: makesetup:
must link C extensions to libpython when compiled in shared mode
<https://bugs.python.org/issue34814>`__. This use case comes from `a bug
reported in RHEL bug tracker
<https://bugzilla.redhat.com/show_bug.cgi?id=1585201>`_ in June 2018.
When ``libpython`` is loading using::

    dlopen("libpython2.7.so.1.0", RTLD_LOCAL | RTLD_NOW)

It is not possible to import the ``struct`` module because it fails to
import its C extension ``_struct``::

    ImportError: /usr/lib64/python2.7/lib-dynload/_struct.so: undefined symbol: PyFloat_Type

In January 2019, `A similar issue was reported in Fedora bug tracker
<https://bugzilla.redhat.com/show_bug.cgi?id=1667914>`_.

In April 2019, the RHEL bug was also closed as "not a bug", so I also closed
the `bpo-34814 <https://bugs.python.org/issue34814>`__ as "not a bug":

    Since this issue has been created, no consensus could be found. So I close
    the issue to keep the status quo.

    In short, loading ``libpython`` with ``RTLD_LOCAL`` is not supported.

Static and dynamically linked Python
------------------------------------

In May 2014, **Antoine Pitrou** reported `bpo-21536: extension built with a
shared python cannot be loaded with a static python
<https://bugs.python.org/issue21536>`_:

    When a C extension is built (using distutils) with a shared library Python,
    it cannot be loaded with an otherwise identical statically linked Python.
    The other way round works fine.

Trivial example using the _ssl module::

    >>> import sys
    >>> sys.path.insert(0, '/home/antoine/cpython/shared/build/lib.linux-x86_64-3.5/')
    >>> import _ssl
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    ImportError: libpython3.5m.so.1.0: cannot open shared object file: No such file or directory

C extension linked to libpython since 2006
------------------------------------------

I identified an old change made in 2006 to link C extensions to libpython,
`bpo-832799 <https://bugs.python.org/issue832799>`__::

    commit 10acfd00b28a2aad7b73d35afdbc64b0baebea20
    Author: Martin v. Löwis <martin@v.loewis.de>
    Date:   Mon Apr 10 12:39:36 2006 +0000

        Patch #1429775: Link Python modules to libpython on linux if
        --enable-shared. Fixes #832799.

The rationale behind this change is not well documented.

No longer link C extensions to libpython
----------------------------------------

On Unix, C extensions are no longer linked to libpython except on Android
and Cygwin.
It is now possible
for a statically linked Python to load a C extension built using a shared
library Python.

On Unix, when Python is built in debug mode, import now also looks for C
extensions compiled in release mode and for C extensions compiled with the
stable ABI.
(Contributed by Victor Stinner in :issue:`36722`.)

But link C extensions to libpython on Android and AIX
------------------------------------------------------

XXXX


Embed Python in an application
==============================

Many application embed Python as a scripting language: Blender, LibreOffice,
Samba, gdb, vim, FontForge, etc.

XXX bug in Fedora: Samba/waf XXX

`bpo-36721 <https://bugs.python.org/issue36721>`__

To embed Python into an application, a new ``--embed`` option must be passed to
``python3-config --libs --embed`` to get ``-lpython3.8`` (link the application
to libpython). To support both 3.8 and older, try ``python3-config --libs
--embed`` first and fallback to ``python3-config --libs`` (without ``--embed``)
if the previous command fails.

Add a pkg-config ``python-3.8-embed`` module to embed Python into an
application: ``pkg-config python-3.8-embed --libs`` includes ``-lpython3.8``.
To support both 3.8 and older, try ``pkg-config python-X.Y-embed --libs`` first
and fallback to ``pkg-config python-X.Y --libs`` (without ``--embed``) if the
previous command fails (replace ``X.Y`` with the Python version).

On the other hand, ``pkg-config python3.8 --libs`` no longer contains
``-lpython3.8``. C extensions must not be linked to libpython (except on
Android and Cygwin, whose cases are handled by the script);
this change is backward incompatible on purpose.
