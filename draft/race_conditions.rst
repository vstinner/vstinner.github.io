ttk
===

ttk: fix LabeledScale and OptionMenu destroy() method (#3025)

bpo-31135: Call the parent destroy() method even if the used
attribute doesn't exist.

The LabeledScale.destroy() method now also explicitly clears label
and scale attributes to help the garbage collector to destroy all
widgets.

tkinter hangs randomly
======================

* Only reproduced on Windows
* Running the test opens blinking windows in a loop, so the keyboard and mouse
  becomes unusable
* When the test hangs, using the keyboard or mouse risk to "unblock" and so
  "hides" the bug
* test_ttk_guionly


test_logging threads
====================

* Sometimes, test_logging logs the warning: XXX
* I ran test_logging using --forever on Linux: unable to reproduce the bug
* I ran test_logging using --forever on FreeBSD 10 buildbot, where the bug
  occurs: unable to reproduce the bug
* I ran test_logging using --forever on FreeBSD 10 buildbot while running my
  "system_load.py 3" script: unable to reproduce the bug
* After 2 months, I found a way to reproduce the way, *sometimes*: run
  test_logging, while running "./python -m test -j4"
* Not possible to run automated bisection, since the test still fails randomly:
  pure race condition
* Manual bisection: continue to bisect until the bug occurs
* Cancel bisection (go backward) if the warning is no more emitted

https://bugs.python.org/issue30830
https://bugs.python.org/issue31233

Bug in socketserver.

Bug only occurs on FreeBSD 10 because the buildbot is slow. threading_cleanup()
has a timeout of 1 second.

Current workaround: skip test_logging tests using socketserver.


test_code memory leak
=====================

Story:

* Gentoo Refleak fails randomly on test_code
* In fact, it fails on many tests
* test.bisect identified a few test methods
* Unable to reproduce the bug, only triggered on the buildbot
* Test code simplified, always check that the bug can still be reproduced
* Need to run the test between 1 and 30 times to reproduce the bug
* PYTHONHASHSEED helps a lot to reproduce the bug
* PYTHONHASHSEED value changes each time a minor change is made in the code
* test_code: complex test using ctypes, ctypes creates many temporary objects
* test_sys: test creating a thread, using threading events
* rewrite Lib/threading.py: cause a bug in the test.support
* copy threading.Thread class: Thread2, simplify the class
* 10 minutes later, the Thread2 only adds itself to dangling: a WeakRefSet
* The threading module is not needed at all
  def __init__(self): dangling.add(self)
* WeakRefSet code duplicated and simplified: 15 minutes later, the code is
  reduced to a single set: set().add() is enough to trigger the bug
* Randomness:

  * The test fails randomly, something like 1 failure on 10 runs
  * PYTHONHASHSEED set manually
  * A failure can be reproduced using PYTHONHASHSEED
  * modified os.urandom() to only return b'\x04' * size
  * modified random to always return 4
  * bug no more reproduced

* Many rollbacks
* Use git to keep track of what I am doing

* gdb: breakpoint on _PyObject_Alloc and _PyObject_Free.
  setobject.c seems fine. test_current_frames() is fine!?
* later, gdb: ah! _Py_AllocatedBlocks increases, a bug in dict shared keys?
  No, bug stil reproduced with __slots__.
* maybe it's print('.', end='')?

XXX failed attempt to use tracemalloc

Key of the problem::

    >>> id(82914 - 82913) == id(1) # 64bit Python
    True
    >>> id(82914 - 82913) == id(1) # 32bit Python
    False

On 32-bit mode, Python integers are stored in base 2^15::

    >>> sys.int_info
    sys.int_info(bits_per_digit=15, sizeof_digit=2)

``82,914`` and ``82,913`` larger than ``2^15 - 1`` (``32,767``) and so stored
as two digits. But the x_sub() function of Objects/longobject.c has two
implementations. If both numbers are stored as a single digit, Python tries to
reuse small integer singletons (-5..257). Example::

    >>> x=1000; id((x+1) - x) == id(1)
    True
    >>> x=2**100; id((x+1) - x) == id(1)
    False

1,000 and 1,001 are stored as a single digit and so Python returns the
singleton. 2^100 and 2^100+1 are stored as multiple digits, and so Python
creates a new integer ``1`` which is different than the Python singleton ``1``.

https://bugs.python.org/issue31217#msg301076

* ``after - before`` creates an integer
* this integer is kept alive in the loop
* the integer is seen as a memory leak

Fixed by XXX

