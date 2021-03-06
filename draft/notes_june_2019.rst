Pycon US 2019
=============

* Talk: Diversity
  Slides:
  Video:
* Language Summit Talk: Mentoring
  Slides: https://github.com/vstinner/conf/blob/master/2019-Pycon/mentoring.pdf
  Article: http://pyfound.blogspot.com/2019/05/python-core-developer-mentorship.html
  https://twitter.com/VictorStinner/status/1123682765457719297
* Language Summit Lightning Talk: C API
  Slides: https://github.com/vstinner/conf/blob/master/2019-Pycon/status_stable_api_abi.pdf
  https://twitter.com/VictorStinner/status/1123701511035531265

https://twitter.com/ErSanyamKhurana/status/1126207835979812864
    And finally met Victor Stinner and others in person

People
    https://twitter.com/VictorStinner/status/1124791391526227968
    https://twitter.com/Captain_Joannah/status/1124879215999037440
    https://twitter.com/mariatta/status/1125528852640542720
    https://twitter.com/mariatta/status/1125456432005095426

Talks
    Pablo Galindo Salgado @pyblogsal : "Time to take out the rubbish: garbage
    collector" #PyCon2019
    https://twitter.com/VictorStinner/status/1124737024727101441

    Mariatta @mariatta 's talk: "Don't be a robot. Build the bot." I really
    love all these bots 🤩 , they are super useful for my daily job!
    https://twitter.com/VictorStinner/status/1124530356894478337

    Pablo Galindo Salgado @pyblogsal talks about the Python buildbots: "The
    Night's Watch is fixing the CIs in the darkness for you". I love the logo
    😍 . Language Summit #PyCon2019
    https://twitter.com/VictorStinner/status/1123620332017995776

    My talk
    https://twitter.com/loooorenanicole/status/1124423830284460032
    https://twitter.com/amcasari/status/1124421956214849536
    https://twitter.com/loooorenanicole/status/1124427136083869696
    https://twitter.com/loooorenanicole/status/1124423346349912064

SC
    https://twitter.com/VictorStinner/status/1125032883188654080

My colleague Petr Viktorin:
https://pyfound.blogspot.com/2019/05/petr-viktorin-extension-modules-and.html

Python 3.8 beta1: Victor
========================

* sys.unraisablehook()
  https://mail.python.org/pipermail/python-dev/2019-May/157436.html
  https://bugs.python.org/issue36829
* threading.excepthook()
  https://bugs.python.org/issue1230540
  Jonathan Ellis: "Thanks to @VictorStinner for fixing a Python bug I filed 14
  years ago! (link: https://bugs.python.org/issue1230540)
  bugs.python.org/issue1230540"
    https://twitter.com/spyced/status/1133171600969412611
* Stressful beta1: fix regressions
  https://mail.python.org/pipermail/python-dev/2019-June/157828.html
* This is me everyday at work: https://www.youtube.com/watch?v=AbSehcT19u0
  - Lois: Hal, can you replace the lightbulb in the kitchen?
  - Hal: CAN'T YOU SEE THAT'S WHAT I'M DOING?

Python 3.8 beta1: Others
========================

* PEP 570 approved
* Accessing global variables will be as fast as locals in Python 3.8. I
  researched and prototyped the approach before 3.7 but didn't have time to
  finish the work. Huge thanks to @methane for pushing this through.  🚀 🚀 🚀
  https://github.com/python/cpython/pull/12884
* async REPL: https://github.com/python/cpython/pull/13472

Example::

    $ python -m asyncio
    >>> await asyncio.sleep(1)

* Antoine Pitrou merged his PEP 574 implementation
  pickle version 5
  https://github.com/python/cpython/pull/7076
* threading.get_native_id():
  https://github.com/python/cpython/commit/b121f63155d8e3c7c42ab6122e36eaf7f5e9f7f5
* AsyncMock: https://github.com/python/cpython/pull/9296

subinterpreters, runtime
========================

https://twitter.com/VictorStinner/status/1126966411425927168
    My "small" contribution to prepare Python code for one GIL per interpreter
    (PEP 554, subinterpreters):
    https://github.com/python/cpython/commit/09532feeece39d5ba68a0d47115ce1967bfbd58e
    That's early work to identify how shared states are used and what should be
    fixed. cc @ericsnowcrntly

    https://github.com/python/cpython/commit/09532feeece39d5ba68a0d47115ce1967bfbd58e

https://pythoncapi.readthedocs.io/runtime.html
    Photos https://twitter.com/VictorStinner/status/1125887394220269568



