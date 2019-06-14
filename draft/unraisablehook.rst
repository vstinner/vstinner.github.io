+++++++++++++++++++++++++++++++
New Python 3.8 exceptions hooks
+++++++++++++++++++++++++++++++

:date: 2019-06-05 23:00
:tags: python
:category: python
:slug: python38-sys-unraisablehook
:authors: Victor Stinner

I added two new hooks to Python 3.8 to handle "unraisable" and "uncaught"
exceptions:

* `bpo-36829 <https://bugs.python.org/issue36829>`_:
  `sys.unraisablehook()
  <https://docs.python.org/dev/library/sys.html#sys.unraisablehook>`_

* `bpo-1230540 <https://bugs.python.org/issue1230540>`_:
  `threading.excepthook()
  <https://docs.python.org/dev/library/threading.html#threading.excepthook>`_

None should be called directly:

* ``sys.unraisablehook()`` is called by the C function
  ``PyErr_WriteUnraisable``.

* ``threading.excepthook()`` is called by ``threading.Thread`` if the thread
  doesn't catch an exception.

Adding source parameter to the warnings module
==============================================

When I proposed the ``unraisablehook()`` API, I wanted the API to be
extensible: be able to pass more information without having to update every
hook (avoid breaking the backward compatibility).

I had a bad experience with the ``warnings`` "hooks": ``showwarning()`` and
``formatwarning()`` functions can be overriden, but they use a fixed number of
positional parameters. If they are called with an additional parameter, they
fail with a ``TypeError``.

I wanted to pass a new ``source`` parameter to these functions to display where
an object has been allocated when a ``ResourceWarning`` is logged, using the
``tracemalloc`` module.

Example::

    def func():
        f = open(__file__)
        f = None

    func()

Feature::

    $ python3 -Wd -X tracemalloc=5 filebug.py
    filebug.py:3: ResourceWarning: unclosed file <_io.TextIOWrapper name='filebug.py' mode='r' encoding='UTF-8'>
      f = None
    Object allocated at (most recent call first):
      File "filebug.py", lineno 2
        f = open(__file__)
      File "filebug.py", lineno 5
        func()

To extend the warnings module, I chose to rely on the existing
``WarningMessage`` class which can be used to "pack" all parameters as a single
object. This class was used by ``catch_warnings`` context manager.

I had to add new ``_showwarnmsg()`` and ``_formatwarnmsg()`` function called
with a ``WarningMessage`` instance. But the implementation had to still detect
when ``showwarning()`` and/or ``formatwarning()`` is overriden. In this case,
the overriden function should be called with the legacy API.

After Python 3.6 release,


   https://bugs.python.org/issue26604


The implementation is tricky, and it caused a few minor regressions:

https://github.com/python/cpython/commit/be7c460fb50efe3b88a00281025d76acc62ad2fd


API discussed on python-dev
===========================

When Thomas Grainger opened `bpo-36829 <https://bugs.python.org/issue36829>`_,
he used the title: "CLI option to make PyErr_WriteUnraisable abort the current
process".

Zackery Spytz wrote the `PR 13175
<https://github.com/python/cpython/pull/13175>`_ to add a ``-X
abortunraisable`` command line option. When this option is used,
``PyErr_WriteUnraisable()`` called ``Py_FatalError("Unraisable exception")``
which calls ``abort()``: it raises the ``SIGABRT`` signal which kills the
process by default.

I proposed a different design: add a new hook to arbitrary Python code to
handle an "unraisable exception": add ``sys.unraisablehook()``.

Implementation issue: what happens if an "unraisable exception" is triggered
late during Python finalization? What if sys.unraisablehook has been set to
``None``?

I succeeded to write `too_late_unraisable.py
<https://bugs.python.org/file48321/too_late_unraisable.py>`_ which triggers an
unraisable exception very late during Python finalization. In this case,
the custom unraisablehook is already unregistered.

`I asked <https://bugs.python.org/issue36829#msg342001>`_:

    The question now becomes: do *all* calls to ``PyErr_WriteUnraisable()``
    must abort the process? What is the point? Only a very low level debugger
    like gdb can be used to see the exception.

Thomas `replied <https://bugs.python.org/issue36829#msg342003>`_:

    The point for me is that CI will fail if it happens, then I can use gdb to
    find out the cause.

I'm not comfortable with forcing users to use a low-level debugger to debug "unraisable exceptions".

I started a discussion on the python-dev mailing list: `bpo-36829: Add
sys.unraisablehook()
<https://mail.python.org/pipermail/python-dev/2019-May/157441.html>`_.


What if a custom hook raises a new exception?
=============================================

This issue was easy to fix: ``PyErr_WriteUnraisable()`` logs the new exception
using ``sys.excepthook``.


test.support.catch_unraisable_exception()
=========================================

I wrote a new context manager catching unraisable exceptions:
``test.support.catch_unraisable_exception()``. The exception is stored and so
can be tested or used in the context manager, but cleared at context manager
exit.

I modified tests to use this new context manager:

* test_coroutines
* test_cprofile
* test_exceptions
* test_generators
* test_io
* test_raise
* test_ssl
* test_thread
* test_yield_from

Example::

        class BrokenDel:
            def __del__(self):
                raise ValueError("del is broken")

        obj = BrokenDel()
        with support.catch_unraisable_exception() as cm:
            del obj
            self.assertEqual(cm.unraisable.object, BrokenDel.__del__)


Object resurrection
===================

`bpo-37261: test_io leaks references on AMD64 Fedora Rawhide Refleaks 3.8
<https://bugs.python.org/issue37261>`_

test_io leaks references `on AMD64 Fedora Rawhide Refleaks 3.8:
<https://buildbot.python.org/all/#/builders/229/builds/10>`_::

    test_io leaked [23208, 23204, 23208] references, sum=69620
    test_io leaked [7657, 7655, 7657] memory blocks, sum=22969

The issue has been introduced by my change::

    commit c15a682603a47f5aef5025f6a2e3babb699273d6
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Thu Jun 13 00:23:49 2019 +0200

        bpo-37223: test_io: silence destructor errors (GH-14031)

https://en.wikipedia.org/wiki/Object_resurrection#Problems


Hook features
=============

* Can log the exception into a file, send it to the network, open a popup, etc.
* Inspect the Python stack, ex: ``traceback.print_stack()``
* Inspect object content
* Get the traceback where the object has been allocated:
  ``tracemalloc.get_object_traceback()``
* Kill the process: ``signal.raise_signal(signal.SIGABRT)`` implements the
  initial ``-X abortunraisable`` idea
* Detect unraisable exception when running tests and make tests in this case:
  I implemented this idea in regrtest, bpo-xxx.
