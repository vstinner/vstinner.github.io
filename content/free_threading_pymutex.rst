+++++++++++++++++++++++++++++++++
Free Threading internals: PyMutex
+++++++++++++++++++++++++++++++++

:date: 2026-06-18 12:00
:tags: free-threading, cpython
:category: cpython
:slug: free-threading-pymutex
:authors: Victor Stinner

.. image:: {static}/images/van_gogh_sunflowers.jpg
   :alt: Sunflowers - Vincent van Gogh (1888)
   :target: https://en.wikipedia.org/wiki/Sunflowers_(Van_Gogh_series)

I'm writing an article series on Free Threading internals to learn more about
Free Threading, explain how it works, and explain how it solved the "remove the
GIL" issue where previous attempts failed.

* 1. `Reference counting <{filename}/free_threading_refcount.rst>`_
* 2. `Deferred reference counting <{filename}/free_threading_deferred_refcount.rst>`_
* 3. `PyMutex <{filename}/free_threading_pymutex.rst>`_ (this article)

`PEP 703 <https://peps.python.org/pep-0703/>`_ replaces the unique Global
Interpreter Lock (GIL) with one lock per Python object. Since a lock is added
to every object, it's important that locks have small memory footprint and are
efficient. PEP 703 adds a new ``PyMutex`` for this purpose.

*Painting: Sunflowers - Vincent van Gogh (1888).*

Gilectomy locks
===============

The Gilectomy project only added ``py_recursivelock_t`` lock to
``PyDictObject``, ``PyListObject`` and ``PySetObject`` structures (``dict``,
``list`` and ``set`` types).

On x86-64 Linux, `py_recursivelock_t
<https://github.com/larryhastings/gilectomy/blob/de3aebf50a636e43fe65d4caed8ce5fc7eebe042/Include/lock.h#L172-L188>`_
size is **72 bytes**. On Python 3.13, an empty list size is 56 bytes, and an
empty dictionary size is 64 bytes. So adding 72 bytes for the lock is quite
significant! On Linux, `PY_NATIVELOCK_T
<https://github.com/larryhastings/gilectomy/blob/de3aebf50a636e43fe65d4caed8ce5fc7eebe042/Include/lock_linux.h#L34>`_
(4 bytes) is based on futex.

PyMutex
=======

In August 2023, Sam Gross opened the issue
`Add lightweight locking C API <https://github.com/python/cpython/issues/108724>`_.

PyMutex is a one byte lock with fast, inlineable lock and unlock functions for
the common uncontended case.  The design is based on WebKit's ``WTF::Lock``
(WTF stands for Web Template Framework):

* `Locking in WebKit <https://webkit.org/blog/6161/locking-in-webkit/>`_
  (May 2016) by Filip Pizlo
* `WebKit WTF/wtf/Lock.h source code
  <https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/Lock.h>`_

PyMutex is built using the ``_PyParkingLot`` APIs, which provides a
cross-platform futex-like API (based on WebKit's ``WTF::ParkingLot``).  This
internal API will be used for building other synchronization primitives used to
implement PEP 703, such as one-time initialization and events.

Pull request overview:

* ``PyMutex``: A 1-byte lock that doesn't require memory allocation to
  initialize and is generally faster than the existing ``PyThread_type_lock``.
  The API is internal only for now.

* ``_PyParking_Lot``: A futex-like API based on the API of the same name in
  WebKit.  Used to implement ``PyMutex``.

* ``_PyRawMutex``: A word sized lock used to implement ``_PyParking_Lot``.

* ``PyEvent``: A one time event. This was used a bunch in the "nogil" fork and
  is useful for testing the ``PyMutex`` implementation, so I've included it as
  part of the PR.

* ``pycore_llist.h``: Defines common operations on doubly-linked list.  Not
  strictly necessary (could do the list operations manually), but they come up
  frequently in the "nogil" fork. (Similar to
  `FreeBSD sys/queue.h <https://man.freebsd.org/cgi/man.cgi?queue>`_).

See the final commit: `Add PyMutex and _PyParkingLot APIs
<https://github.com/python/cpython/commit/0c89056fe59ac42f09978582479d40e58a236856>`_.

PyMutex implementation
======================

As written above, the ``PyMutex`` structure is made of a single byte:

.. code-block:: c

   typedef struct PyMutex {
       uint8_t _bits;  // (private)
   } PyMutex;

In fact, only 2 bits are used! The private ``_bits`` member can have 4 states:

* ``0b00``: Unlocked.
* ``0b01``: Locked.
* ``0b10``: Unlocked and has parked threads.
* ``0b11``: Locked and has parked threads.

``PyMutex_Lock()`` can lock with a single atomic compare-exchange operation in
the uncontended case using a static inline function:

.. code-block:: c

   PyAPI_FUNC(void) PyMutex_Lock(PyMutex *m);

   static inline void
   _PyMutex_Lock(PyMutex *m)
   {
       uint8_t expected = _Py_UNLOCKED;
       if (!_Py_atomic_compare_exchange_uint8(&m->_bits, &expected, _Py_LOCKED)) {
           PyMutex_Lock(m);
       }
   }
   #define PyMutex_Lock _PyMutex_Lock

Otherwise, it calls ``PyMutex_Lock()`` function to acquire the lock.


Flags
=====

The internal ``PyMutex_LockFlags()`` function accepts flags:

* ``_Py_LOCK_DONT_DETACH``: Do not detach/release the GIL when waiting on the
  lock.
* ``_PY_LOCK_DETACH``: Detach/release the GIL while waiting on the lock.
* ``_PY_LOCK_HANDLE_SIGNALS``: Handle signals if interrupted while waiting on
  the lock.
* ``_PY_FAIL_IF_INTERRUPTED``: Fail if interrupted by a signal while waiting on
  the lock.
* ``_PY_LOCK_PYTHONLOCK``: Locking & unlocking this lock requires attached
  thread state. If locking returns ``PY_LOCK_FAILURE``, a Python exception
  *may* be raised. (Intended for use with ``_PY_LOCK_HANDLE_SIGNALS`` and
  ``_PY_LOCK_DETACH``.)

The ``PyMutex_Lock()`` function uses ``_PY_LOCK_DETACH`` flag by default.


Performance
===========

The ``Tools/lockbench/lockbench.py`` benchmark compares ``PyMutex`` with the
existing ``PyThread_type_lock``.

Uncontended acquisition + release:

* Linux (x86-64): ``PyMutex`` 11 ns (4x faster), ``PyThread_type_lock`` 44 ns
* macOS (arm64): ``PyMutex`` 13 ns (1.4x faster), ``PyThread_type_lock`` 18 ns
* Windows (x86-64): ``PyMutex`` 13 ns (2.9x faster), ``PyThread_type_lock`` 38 ns

Critical section
================

In practice, the ``PyMutex`` should not be used directly, it's better to use
the critical section API instead: see `Py_BEGIN_CRITICAL_SECTION(obj)
documentation
<https://docs.python.org/dev/c-api/synchronization.html#c.Py_BEGIN_CRITICAL_SECTION>`_.

Critical sections avoid deadlocks by implicitly suspending active critical
sections, hence, they do not provide exclusive access such as provided by
traditional locks like ``PyMutex``. When a critical section is started, the
per-object lock for the object is acquired. If the code executed inside the
critical section calls C-API functions then it can suspend the critical section
thereby releasing the per-object lock, so other threads can acquire the
per-object lock for the same object.
