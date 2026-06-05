+++++++++++++++++++++++++++++++
Free Threading internals: locks
+++++++++++++++++++++++++++++++

:date: 2026-06-05 19:00
:tags: free-threading, cpython
:category: cpython
:slug: free-threading-locks
:authors: Victor Stinner

Lock size
=========

The Gilectomy project adds ``py_recursivelock_t`` lock to ``PyDictObject``,
``PyListObject`` and ``PySetObject`` structures.

On x86-64 Linux, `py_recursivelock_t
<https://github.com/larryhastings/gilectomy/blob/de3aebf50a636e43fe65d4caed8ce5fc7eebe042/Include/lock.h#L172-L188>`_
size is 72 bytes. It inherits from `py_lock_t
<https://github.com/larryhastings/gilectomy/blob/de3aebf50a636e43fe65d4caed8ce5fc7eebe042/Include/lock.h#L172-L188>`_
which takes 32 bytes. And py_lock_t contains a `PY_NATIVELOCK_T
<https://github.com/larryhastings/gilectomy/blob/de3aebf50a636e43fe65d4caed8ce5fc7eebe042/Include/lock_linux.h#L34>`_
lock which is just 4 bytes (on Linux).

On Python 3.13, an empty list size is 56 bytes, and an empty dictionary size is
64 bytes. So adding 72 bytes for the lock is quite significant.

PEP 703 proposes a different design. Instead of adding a lock only to
collections, it adds a per-object lock (to all objects): add ``PyMutex
ob_mutex`` member to ``PyObject``. So ``PyMutex`` must be as small as possible.

PyMutex
=======

In August 2023, Sam Gross opened the issue
`Add lightweight locking C API <https://github.com/python/cpython/issues/108724>`_.

PyMutex is a one byte lock with fast, inlineable lock and unlock functions for
the common uncontended case.  The design is based on WebKit's WTF::Lock.

PyMutex is built using the _PyParkingLot APIs, which provides a cross-platform
futex-like API (based on WebKit's WTF::ParkingLot).  This internal API will be
used for building other synchronization primitives used to implement PEP 703,
such as one-time initialization and events.

WebKit WTF Lock

* https://webkit.org/blog/6161/locking-in-webkit/
* https://github.com/WebKit/WebKit/blob/main/Source/WTF/wtf/Lock.h

PR Overview:

The primary purpose of this PR is to implement PyMutex, but there are a number of support pieces (described below).

* PyMutex:  A 1-byte lock that doesn't require memory allocation to initialize
  and is generally faster than the existing PyThread_type_lock.  The API is
  internal only for now.

* _PyParking_Lot:  A futex-like API based on the API of the same name in
  WebKit.  Used to implement PyMutex.

* _PyRawMutex:  A word sized lock used to implement _PyParking_Lot.
* PyEvent:  A one time event.  This was used a bunch in the "nogil" fork and is
  useful for testing the PyMutex implementation, so I've included it as part of
  the PR.
* pycore_llist.h:  Defines common operations on doubly-linked list.  Not
  strictly necessary (could do the list operations manually), but they come up
  frequently in the "nogil" fork. ( Similar to
  https://man.freebsd.org/cgi/man.cgi?queue)

Commit: Add PyMutex and _PyParkingLot APIs
https://github.com/python/cpython/commit/0c89056fe59ac42f09978582479d40e58a236856

* PyMutex: use a single byte
* ``Include/cpython/pylock.h`` defines ``PyMutex``
* Parking lot

PyMutex
=======

.. code-block:: c

   // 0b00: unlocked
   // 0b01: locked
   // 0b10: unlocked and has parked threads
   // 0b11: locked and has parked threads
   typedef struct PyMutex {
       uint8_t _bits;  // (private)
   } PyMutex;

Flags:

* ``_Py_LOCK_DONT_DETACH``: Do not detach/release the GIL when waiting on the lock.
* _PY_LOCK_DETACH: Detach/release the GIL while waiting on the lock.
* ``_PY_LOCK_HANDLE_SIGNALS``: Handle signals if interrupted while waiting on the
  lock.
* ``_PY_FAIL_IF_INTERRUPTED``: Fail if interrupted by a signal while waiting on the
  lock.
* ``_PY_LOCK_PYTHONLOCK``: Locking & unlocking this lock requires attached thread
  state. If locking returns PY_LOCK_FAILURE, a Python exception *may* be
  raised. (Intended for use with _PY_LOCK_HANDLE_SIGNALS and _PY_LOCK_DETACH.)


PyMutex_Lock
============

.. code-block:: c

   void
   PyMutex_Lock(PyMutex *m)
   {
       _PyMutex_LockTimed(m, -1, _PY_LOCK_DETACH);
   }

   static inline void
   _PyMutex_Lock(PyMutex *m)
   {
       uint8_t expected = _Py_UNLOCKED;
       if (!_Py_atomic_compare_exchange_uint8(&m->_bits, &expected, _Py_LOCKED)) {
           PyMutex_Lock(m);
       }
   }
   #define PyMutex_Lock _PyMutex_Lock

``_PyMutex_LockTimed()``:

* Try again to lock using ``_Py_atomic_compare_exchange_uint8()``.
* Try 40 times to call ``_Py_atomic_compare_exchange_uint8()``
  or call ``sched_yield()``.
* Call ``_PyParkingLot_Park()``.

PyMutex_Unlock
==============

.. code-block:: c

   void
   PyMutex_Unlock(PyMutex *m)
   {
       if (_PyMutex_TryUnlock(m) < 0) {
           Py_FatalError("unlocking mutex that is not locked");
       }
   }

   static inline void
   _PyMutex_Unlock(PyMutex *m)
   {
       uint8_t expected = _Py_LOCKED;
       if (!_Py_atomic_compare_exchange_uint8(&m->_bits, &expected, _Py_UNLOCKED)) {
           PyMutex_Unlock(m);
       }
   }
   #define PyMutex_Unlock _PyMutex_Unlock

Slow-path:

.. code-block:: c

   int
   _PyMutex_TryUnlock(PyMutex *m)
   {
       uint8_t v = _Py_atomic_load_uint8(&m->_bits);
       for (;;) {
           if ((v & _Py_LOCKED) == 0) {
               // error: the mutex is not locked
               return -1;
           }
           else if ((v & _Py_HAS_PARKED)) {
               // wake up a single thread
               _PyParkingLot_Unpark(&m->_bits, mutex_unpark, m);
               return 0;
           }
           else if (_Py_atomic_compare_exchange_uint8(&m->_bits, &v, _Py_UNLOCKED)) {
               // fast-path: no waiters
               return 0;
           }
       }
   }

``_PyParkingLot_Unpark()`` finds the first waiter that is waiting on ``addr``
and wakes up the waiter outside of the bucket lock: call ``_PySemaphore_Wakeup()``.

Performance
===========

This also includes tests and a mini benchmark in Tools/lockbench/lockbench.py
to compare with the existing PyThread_type_lock.

Uncontended acquisition + release:

* Linux (x86-64): PyMutex: 11 ns, PyThread_type_lock: 44 ns
* macOS (arm64): PyMutex: 13 ns, PyThread_type_lock: 18 ns
* Windows (x86-64): PyMutex: 13 ns, PyThread_type_lock: 38 ns

Critical section
================

* Py_BEGIN_CRITICAL_SECTION()/Py_END_CRITICAL_SECTION()
* Py_BEGIN_CRITICAL_SECTION2()/Py_END_CRITICAL_SECTION2()
* Use ``PyThreadState.critical_section`` tagged pointer
* ``_Py_CRITICAL_SECTION_INACTIVE``
* ``_Py_CRITICAL_SECTION_TWO_MUTEXES``
* ``_Py_CRITICAL_SECTION_MASK``
* Use ``PyObject.ob_mutex`` (PyMutex)
