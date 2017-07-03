Python buildbots
================

https://www.python.org/dev/buildbot/

CPython is tested by a wide range of buildbot slaves:

* Operating systems:

  * Linux: Debian, Ubuntu, Gentoo, RHEL, SLES
  * Windows: 7, 8, 8.1, 10
  * macOS: Tiger, El Capitain, Sierra
  * FreeBSD: 9, 10, CURRENT
  * AIX
  * OpenIndiana (currently offline)

* CPU

  * ARMv7
  * x86 (32 bit)
  * x86-64 aka "AMD64" (64-bit)
  * PPC64, PPC64LE
  * s390x

There are different kinds of tests:

* Python test suite
* Docs: check that the documentation can be build and doesn't contain warnings
* "Refleaks": check for reference leaks and memory leaks using the Python test
  suite, the ``--huntrleaks`` option of regrtest used with ``-R 3:3``.
* "DMG": Build the macOS installer using the
  ``Mac/BuildScript/build-installer.py`` script

Python can be tested with different configuration:

* Non-debug: default
* Debug: ``./configure --with-pydebug``
* Installed: ``./configure --prefix=XXX && make install``
* Shared library (libpython): ``./configure --enable-shared``

Tested branches:

* ``master``: called "3.x" on buildbots
* ``3.6``
* ``3.5``
* ``2.7``
* ``custom``: special branch used by core developers for testing patches

The buildbot configuration can be found in ``master/master.cfg`` file of the
`buildmaster-config project <https://github.com/python/buildmaster-config/>`_.


Fix warnings
============

Add a new Orange color :-)

Fix environment changed warnings
--------------------------------

* Test leaking files
* Core dump: test_subprocess
* Threads, @reap_threads, test_asyncio

Fix unstable tests, fail once, pass when run again
--------------------------------------------------

* Work-in-progress, big task


test.bisect
===========

http://bugs.python.org/issue29512

Python-Dev: `New work-in-progress bisection tool for the Python test suite (in
regrtest)
<https://mail.python.org/pipermail/python-dev/2017-June/148363.html>`_.

* Written for reference leaks
* Extented to environment changed: new --fail-env-changed option
* New available on 2.7, 3.5, 3.6 and master branches
* Tested on Linux and macOS
* Very useful!


Reference leaks
===============

XXX


Buildbot reports
================

I wrote 3 reports to the Python-Dev mailing list:

* May 3: `Status of Python buildbots
  <https://mail.python.org/pipermail/python-dev/2017-May/147838.html>`_
* June 8: `Buildbot report, june 2017
  <https://mail.python.org/pipermail/python-dev/2017-June/148271.html>`_
* June 29: `Buildbot report (almost July)
  <https://mail.python.org/pipermail/python-dev/2017-June/148511.html>`_


Bugs
====

http://bugs.python.org/issue30371

Jeremy Kloth:

    "Watch this space, but I'm pretty sure that it is (was) bad memory."

    "That's the real problem, I'm not *sure* it's the memory, but it does have
    the symptoms. And that is why my buildbot was down earlier, I was
    attempting to determine the bad stick and replace it."

https://mail.python.org/pipermail/python-buildbots/2017-June/000122.html


Kubilay Kocak:

    "Vacuum cleaner tripped RCD pulling too much current from the same
    circuit as heater was running on. Buildbot worker host on same circuit."

    "koobs-freebsd10 worker VM auto restart didn't get through filesystem
    recovery, which explains its non-return. Should be back in < 10 mins."

