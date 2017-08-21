Buildbot report, August 2017

Hi,

Here is a quick report of what changed recently on buildbots.

I added a new "python3 -m test.pythoninfo" command which is now run on Travis
CI, AppVeyor and buildbots. This command dumps various informations to help
debugging test failures on our CIs. For example, you get the Tcl version,
information about the threading implementation, etc. Currently, it's only run
on the master branch, but I plan to run it on Python 3.6 and 2.7 as well, but
later. See:

    https://bugs.python.org/issue30871

The pythoninfo idea comes from https://bugs.python.org/issue29854 when we
didn't know the readline version of a buildbot, and I didn't want to put such
information in regrtest output, since importing readline has side effects.

A few buildbots were removed:

* Python 3.5 was removed, since the 3.5 branch entered the security only stage:
  https://mail.python.org/pipermail/python-dev/2017-August/148794.html
* FreeBSD 9-STABLE (koobs-freebsd9): FreeBSD 9 is no more supported upstream,
  use FreeBSD 10 and FreeBSD CURRENT buildbots
* OpenIndiana: was offline since the beginning of June. Previous discussions on
  this list:

  * September 2016: OpenIndiana and Solaris support
    https://mail.python.org/pipermail/python-dev/2016-September/146538.html
  * April 2015: MemoryError and other bugs on AMD64 OpenIndiana 3.x
    https://mail.python.org/pipermail/python-dev/2015-April/138967.html
  * September 2014: Sad status of Python 3.x buildbots
    https://mail.python.org/pipermail/python-dev/2014-September/136175.html

* intel-ubuntu-skylake: Florin Papa wrote me that the machine became
  unavailable in December 2016.
* Yosemite ICC buildbot (intel-yosemite-icc): it was maintained by Zachary Ware
  and R. David Murray. Sadly, David lost the VM image to a disk crash :-( New
  ICC buildbots may come back later, wait & see ;-)
* macOS Snow Leopard (murray-snowleopard): this old machine was stuck at boot
  for an unknown reason. "It's an old machine, and it is probably time to get
  rid of it." wrote R. David Murray :-)
* Docs: replaced with Travis CI pre-commit checks which raise less (no?) false
  alarms

As usual, multiple race conditions were fixed in tests and in the code, to
reduce the buildbot failure rate.

Victor
