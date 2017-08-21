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

Bug in socketserver.

Bug only occurs on FreeBSD 10 because the buildbot is slow. threading_cleanup()
has a timeout of 1 second.

Current workaround: skip test_logging tests using socketserver.

