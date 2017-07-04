++++++++++++++++
Python buildbots
++++++++++++++++

:date: 2017-07-04 18:00
:tags: cpython, builbot
:category: python
:slug: python-buildbots
:authors: Victor Stinner

I spent the last 6 months on working on buildbots: reduce the failure rate,
send email notitication on failure, fix random bugs, detect more bugs using
warnings, backport fixes to older branches, etc.

Python buildbots
================

CPython is running a `Buildbot <https://buildbot.net/>`_ server for continuous
integration, but tests are run as post-commit: see `Python buildbots
<https://www.python.org/dev/buildbot/>`_.

CPython is tested by a wide range of buildbot slaves:

* 6 operating systems:

  * Linux: Debian, Ubuntu, Gentoo, RHEL, SLES
  * Windows: 7, 8, 8.1, 10
  * macOS: Tiger, El Capitain, Sierra
  * FreeBSD: 9, 10, CURRENT
  * AIX
  * OpenIndiana (currently offline)

* 5 CPU architectures:

  * ARMv7
  * x86 (Intel 32 bit)
  * x86-64 aka "AMD64" (Intel 64-bit)
  * PPC64, PPC64LE
  * s390x

There are different kinds of tests:

* Python test suite
* Docs: check that the documentation can be build and doesn't contain warnings
* "Refleaks": check for reference leaks and memory leaks, run the Python test
  suite with the ``--huntrleaks`` option
* "DMG": Build the macOS installer with the
  ``Mac/BuildScript/build-installer.py`` script

Python is tested in different configurations:

* Debug: ``./configure --with-pydebug``, the most common configuration
* Non-debug: release mode, with compiler optimizations
* PGO: Profiled Guided Optimization, ``./configure --enable-optimizations``
* Installed: ``./configure --prefix=XXX && make install``
* Shared library (libpython): ``./configure --enable-shared``

Currently, 4 branches are tested:

* ``master``: called "3.x" on buildbots
* ``3.6``
* ``3.5``
* ``2.7``

There is also ``custom``, a special branch used by core developers for testing
patches.

The buildbot configuration can be found in the ``master/master.cfg`` file of
the `buildmaster-config project
<https://github.com/python/buildmaster-config/>`_.


Fix warnings
============

Add a new Orange color :-)

Mailing list
------------

Since May 2017, buildbots are now sending notifications to a new
`buildbot-status mailing list
<https://mail.python.org/mm3/mailman3/lists/buildbot-status.python.org/>`_ when
a buildbot starts failing: if the previous run was successful (green or orange)
but the new build failed (red).

* Create the mailing list
* Fix a bug in our buildbot to be able to send emails
* Whitelist buildbot@python.org email
* Enjoy!

https://bugs.python.org/issue30325

Fix environment changed warnings
--------------------------------

* Test leaking files
* Core dump: test_subprocess
* Threads, @reap_threads, test_asyncio
* New --fail-env-changed
* --fail-env-changed now used on the master branch on buildbots, Travis CI and
  AppVeyor

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


Funny Bugs
==========

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

