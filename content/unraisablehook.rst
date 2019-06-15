+++++++++++++++++++++++++++++
Python 3.8 sys.unraisablehook
+++++++++++++++++++++++++++++

:date: 2019-06-15 01:00
:tags: python
:category: python
:slug: python38-sys-unraisablehook
:authors: Victor Stinner

I added a new `sys.unraisablehook
<https://docs.python.org/dev/library/sys.html#sys.unraisablehook>`_ function to
allow to set a custom hook to control how "unraisable exceptions" are handled.
It already testable in `Python 3.8 beta1 is available
<https://pythoninsider.blogspot.com/2019/06/python-380b1-is-now-available-for.html>`_!

An "unraisable exception" is an error which happens when Python cannot report
it to the caller. For example, error in an object finalizer (``__del__()``), in
a weak reference callback or during a garbage collector collection. At the C
level, ``PyErr_WriteUnraisable()`` function is used to handle such exception.

Designing the new hook was tricky, as its implementation.

.. image:: {static}/images/hidden_kitten.jpg
   :alt: Hidden kitten
   :target: https://www.flickr.com/photos/dawnmanser/8046201692/


Kill Python at the first unraisable exception
=============================================

Last May, Thomas Grainger opened `bpo-36829
<https://bugs.python.org/issue36829>`_: "CLI option to make
PyErr_WriteUnraisable abort the current process". He wrote:

    Currently it's quite easy for these errors to go unnoticed. (...) The point
    for me is that CI will fail if it happens, then I can use gdb to find out
    the cause

Zackery Spytz wrote the `PR 13175
<https://github.com/python/cpython/pull/13175>`_ to add ``-X abortunraisable``
command line option. When this option is used, ``PyErr_WriteUnraisable()``
calls ``Py_FatalError("Unraisable exception")`` which calls ``abort()``: it
raises ``SIGABRT`` signal which kills the process by default.

Handle unraisable exception in Python: sys.unraisablehook
=========================================================

I concur with Thomas that it's easy to miss such exception, but I dislike
killing the process. It's not practical to have to use a low-level debugger
like gdb to handle such bug.

I proposed a different design: add a new hook to arbitrary Python code to
handle an "unraisable exception": add ``sys.unraisablehook()``.

I wrote a `hook example <https://bugs.python.org/issue36829#msg341868>`_ which
displays the Python stack where the exception occurred using the ``traceback``
module.

I chose to pass an single object as argument to sys.unraisablehook. The object
has 4 attributes:

* exc_type: Exception type.
* exc_value: Exception value, can be None.
* exc_traceback: Exception traceback, can be None.
* object: Object causing the exception, can be None.

I wanted an extensible API: keep the backward compatibility even if tomorrow we
add a new attribute to the object to pass more information.

To explain the rationale of this desing, let me tell you my bad experience with
the ``warnings`` module.


Adding source parameter to the warnings module
==============================================

In March 2016, I was tried how debugging ``ResourceWarning`` projects: it's
hard to guess where the bug comes from. The warning is logged where the
resource is released, but I was interested by where the resource was allocated.

My ``tracemalloc`` module provides a convenient ``get_object_traceback()``
function which provides the traceback where any Python has been allocated. The
main constraint is that it requires ``tracemalloc`` to trace all memory
allocations.

I opened `bpo-26604 <https://bugs.python.org/issue26604>`_: "ResourceWarning:
Use tracemalloc to display the traceback where an object was allocated when a
ResourceWarning is emitted".

The problem is that the ``showwarning()`` and ``formatwarning()`` functions of
``warnings`` can be overriden. They use a fixed number of positional
parameters. If they are called with an additional parameter, they fail with a
``TypeError``. I wanted to add a new ``source`` parameter to these functions.

To extend the warnings module, I chose to rely on the existing
``WarningMessage`` class which can be used to "pack" all parameters as a single
object. This class was used by ``catch_warnings`` context manager.

I had to add new private ``_showwarnmsg()`` and ``_formatwarnmsg()`` function:
they are called with a ``WarningMessage`` instance. The implementation has to
detect when ``showwarning()`` and/or ``formatwarning()`` is overriden: the
overriden function must be called with the legacy API in this case. The
backward compatibility requirement makes the implementation complex.

After Python 3.6 was released with my new feature, `bpo-35178
<https://bugs.python.org/issue35178>`_ was reported: the ``warnings`` module
called a custom ``formatwarning()`` with the ``line`` argument passed as a
keyword argument, whereas other arguments are passed as positional arguments.
The `fix was trivial
<https://github.com/python/cpython/commit/be7c460fb50efe3b88a00281025d76acc62ad2fd>`_,
but it shows that backward compatibility is hard.


By the way, example of the feature using a ``filebug.py`` script::

    def func():
        f = open(__file__)
        f = None

    func()

The feature adds the "Object allocated at" traceback, whereas existing ``f =
None`` output is worthless. ::

    $ python3 -Wd -X tracemalloc=5 filebug.py
    filebug.py:3: ResourceWarning: unclosed file <_io.TextIOWrapper name='filebug.py' mode='r' encoding='UTF-8'>
      f = None
    Object allocated at (most recent call first):
      File "filebug.py", lineno 2
        f = open(__file__)
      File "filebug.py", lineno 5
        func()


Limitations of my unraisablehook idea
=====================================

To come back to `bpo-36829 <https://bugs.python.org/issue36829>`_, I identified
a limitation in my ``sys.unraisablehook`` idea: unraisable exceptions which
occurs very late during Python finalization cannot be handled by a custom hook.

Thomas said that he is fine with having to use ``gdb`` to debug an issue
during Python finalization.

In my experience, using ``gdb`` on Python installed on the system is unpleasant
since it's usually deeply optimized, and so gdb fails to read variables which
are only displayed as ``<optimized out>``. By the way, that's why I fixed the
`debug build of Python to be ABI compatible with a release build
<https://docs.python.org/dev/whatsnew/3.8.html#debug-build-uses-the-same-abi-as-release-build>`_,
but that's a different story.

Thomas's idea of killing the process allows to detect unraisable exceptions
whenever they occur.


API discussed on python-dev
===========================

I wanted to get more feedback on a new function added to the important ``sys``
module, so I started a discussion on the python-dev mailing list: `bpo-36829:
Add sys.unraisablehook()
<https://mail.python.org/pipermail/python-dev/2019-May/157436.html>`_.

New exception while handling an exception
-----------------------------------------

Nathaniel asked what happens if a custom hooks raises a new exception while
handling an unraisable exception. This problem is easy to fix:
``PyErr_WriteUnraisable()`` catchs the default hook to handle the new
exception.

Positional arguments
--------------------

Serhiy Storchaka `preferred
<https://mail.python.org/pipermail/python-dev/2019-May/157439.html>`_ passing 5
positional arguments (exc_type, exc_value, exc_tb, obj and msg):

    Currently we have no plans for adding more details, and I do not think that
    we will need to do this in future.

Later, he added:

    If you have plans for adding new details in future, I propose to add a 6th
    parameter "context" or "extra" (always None currently). It is as extensible
    as packing all arguments into a single structure, but you do not need to
    introduce the structure type and create its instance until you need to pass
    additional info.

Object resurrection
-------------------

Steve Dower was `concerned by object resurrection
<https://mail.python.org/pipermail/python-dev/2019-May/157452.html>`_ and
proposed to only pass repr(obj) to the hook.

`I explained
<https://mail.python.org/pipermail/python-dev/2019-May/157463.html>`_ that an
object can only be resurrected after its finalization, which is different than
deallocation. Accessing a finalized object should not crash Python. The
deallocation makes an object unsable, except that deallocation only happens
once the last references to an object is gone, and so the object is no longer
accessible.

`Nathaniel added
<https://mail.python.org/pipermail/python-dev/2019-May/157467.html>`_ that
``repr()`` would limit features of the hook:

    A clever hook might want the actual object, so it can pretty-print it, or
    open an interactive debugger and let it you examine it, or something.

Reuse sys.excepthook
--------------------

Steve Dower also `proposed to reuse sys.excepthook
<https://mail.python.org/pipermail/python-dev/2019-May/157453.html>`_, rather
than adding a new hook, and `create a new exception to pass extra info
<https://mail.python.org/pipermail/python-dev/2019-May/157465.html>`_.
Nathaniel `explained
<https://mail.python.org/pipermail/python-dev/2019-May/157460.html>`_ that
``sys.excepthook`` and ``sys.unraisablehook`` have different behavior and so
require to be different.

Naming
------

Gregory P. Smith proposed the term "uncatchable" rather than "unraisable".

Keyword-only arguments
----------------------

`Barry Warsaw suggested
<https://mail.python.org/pipermail/python-dev/2019-May/157457.html>`_ to
consider keyword-only arguments to help future proof the call signature.

Avoid redundant exc_type and exc_traceback parameters
-----------------------------------------------------

`Petr Viktorin asked
<https://mail.python.org/pipermail/python-dev/2019-May/157459.html>`_ why
``(exc_type, exc_value, exc_traceback)`` triple is needed, wheras *exc_type*
could be get from ``type(exc_type)`` and *exc_traceback* from
``exc.__traceback__``.

`I made some tests
<https://mail.python.org/pipermail/python-dev/2019-May/157462.html>`_.
*exc_value* can be ``NULL`` sometimes. In some cases, *exc_traceback* can be
set, whereas ``exc_value.__traceback__`` is not set (``None``).

Note: Later, I enhanced the existing hook to attempt to always get a traceback
and set ``exc_value.__traceback__`` to the traceback.


Merge my change: add sys.unraisablehook
=======================================

After one week of discussion, I was not convinced by any other alternative
proposition, so I decided to go with my solution since multiple core devs wrote
they liked it. I pushed my `commit ef9d9b63
<https://github.com/python/cpython/commit/ef9d9b63129a2f243591db70e9a2dd53fab95d86>`__::

    commit ef9d9b63129a2f243591db70e9a2dd53fab95d86
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Wed May 22 11:28:22 2019 +0200

        bpo-36829: Add sys.unraisablehook() (GH-13187)

        Add new sys.unraisablehook() function which can be overridden to
        control how "unraisable exceptions" are handled. It is called when an
        exception has occurred but there is no way for Python to handle it.
        For example, when a destructor raises an exception or during garbage
        collection (gc.collect()).

The python-dev discussion was very productive and very useful. I paid more
attention at object resurrection. Another example, I enhanced the hook to
create a traceback if it was not set.


test.support.catch_unraisable_exception()
=========================================

I wrote a new context manager catching unraisable exceptions:
``test.support.catch_unraisable_exception()``. The exception is stored and so
can be used for tests in the context manager, but cleared at context manager
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


test_io issues
==============

I modified test_io to ignore expected unraisable exceptions::

    commit c15a682603a47f5aef5025f6a2e3babb699273d6
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Thu Jun 13 00:23:49 2019 +0200

        bpo-37223: test_io: silence destructor errors (GH-14031)

Memory leak
-----------

This change introduced a memory leak, `bpo-37261
<https://bugs.python.org/issue37261>`_::

    test_io leaked [23208, 23204, 23208] references, sum=69620
    test_io leaked [7657, 7655, 7657] memory blocks, sum=22969

The problem was this ``catch_unraisable_exception`` method::

    def __exit__(self, *exc_info):
        del self.unraisable
        sys.unraisablehook = self._old_hook

Sometimes, ``del self.unraisable`` triggered a new unraisable exception.
At this point, ``catch_unraisable_exception`` hook was still registered,
and this hook does::

    def _hook(self, unraisable):
        self.unraisable = unraisable

At the end, ``del self.unraisable`` instruction *indirectly* sets again the
``self.unraisable`` attribute.

First fix
---------

First, I suspected that the  ``io.BufferedRWPair`` object which triggered the
first unraisable exception was resurrected, and that ``del self.unraisable``
called again its finalizer or deallocator, which triggered the *same*
unraisable exception again.

My first attempt to fix the issue was to first clear the ``sys.unraisablehook``
by setting it to ``None``, and only later delete the attribute::

    def __exit__(self, *exc_info):
        self.unraisablehook = None
        sys.unraisablehook = self._old_hook
        del self.unraisable

This method ignores any unraisable hook which is triggered during ``__exit__``.

Second correct fix
------------------

But when I chatted with Pablo Galindo, he told me that an object cannot be
finalized twice thanks to Antoine Pitrou's `PEP 442: Safe object finalization
<https://www.python.org/dev/peps/pep-0442/>`_.

I looked again into gdb. Oh. In fact, it's more subtle. When ``__exit__()`` is
called, ``BufferedRWPair`` **deallocator** is called which calls the finalizer
of the ``BufferedWriter`` object which was stored in the ``BufferedRWPair``.

``BufferedRWPair`` does not trigger two unraisable exception. It's a different
object. My final fix is to restore the old hook before deleting the
``unraisable`` attribute::

    def __exit__(self, *exc_info):
        sys.unraisablehook = self._old_hook
        del self.unraisable

And I fixed test_io using two nested context managers::

    # Ignore BufferedWriter (of the BufferedRWPair) unraisable exception
    with support.catch_unraisable_exception():
        # Ignore BufferedRWPair unraisable exception
        with support.catch_unraisable_exception():
            pair = None
            support.gc_collect()
        support.gc_collect()

I also documented corner cases in ``sys.unraisablehook`` documentation:

   ``sys.unraisablehook`` can be overridden to control how unraisable
   exceptions are handled.

   Storing *exc_value* using a custom hook can create a **reference cycle**. It
   should be cleared explicitly to break the reference cycle when the exception
   is no longer needed.

   Storing *object* using a custom hook **can resurrect** it if it is set to an
   object which is being finalized. Avoid storing *object* after the custom
   hook completes to avoid resurrecting objects.


regrtest now detects unraisable exceptions
==========================================

Once I fixed all tests to silence all expected unraisable exceptions, I created
`bpo-37069 <https://bugs.python.org/issue37069>`_ to modify regrtest to install
a custom hook: a test is marked as "environment altered" (ENV_CHANGED) if the
test triggers an unraisable exception.

Using ``python3 -m test --fail-env-changed``, which is the case on all Python
CIs, a test is marked as failed in this case.

See `commit 95f61c8b
<https://github.com/python/cpython/commit/95f61c8b1619e736bd5e29a0da0183234634b6e8>`__::

    commit 95f61c8b1619e736bd5e29a0da0183234634b6e8
    Author: Victor Stinner <vstinner@redhat.com>
    Date:   Thu Jun 13 01:09:04 2019 +0200

        bpo-37069: regrtest uses sys.unraisablehook (GH-13759)

        regrtest now uses sys.unraisablehook() to mark a test as "environment
        altered" (ENV_CHANGED) if it emits an "unraisable exception".
        Moreover, regrtest logs a warning in this case.

        Use "python3 -m test --fail-env-changed" to catch unraisable
        exceptions in tests.


Hook features
=============

sys.unraisablehook allows to set a custom hook to handle unraisable exceptions.
It opens many interesting features:

* Log the exception into system logs, over the network, or open a popup.
* Inspect the Python stack: ``traceback.print_stack()``
* Inspect *object* content (object which caused the exception)
* Get the traceback where *object* has been allocated:
  ``tracemalloc.get_object_traceback()``

By the way, reimplement Thomas Grainger's initial idea became trivial::

    import signal, sys

    def abort_hook(unraisable):
        signal.raise_signal(signal.SIGABRT)

    sys.unraisablehook = abort_hook


threading.excepthook
====================

Since I was happy of ``sys.unraisablehook``, I decided to work on the 14-years
old issue `bpo-1230540 <https://bugs.python.org/issue1230540>`_: I proposed to
add `threading.excepthook()
<https://docs.python.org/dev/library/threading.html#threading.excepthook>`_,
but that's a different story!
