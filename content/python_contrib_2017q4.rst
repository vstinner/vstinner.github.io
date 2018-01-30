++++++++++++++++++++++++++++++++++++++++++
My contributions to CPython during 2017 Q4
++++++++++++++++++++++++++++++++++++++++++

:date: 2018-01-29 17:00
:tags: cpython
:category: python
:slug: contrib-cpython-2017q4
:authors: Victor Stinner

My contributions to `CPython <https://www.python.org/>`_ during 2017 Q4
(octobre, november, december).

Previous report: `My contributions to CPython during 2017 Q3 (part3)
<{filename}/python_contrib_2017q3_part3.rst>`_.

Summary:

* Statistics
* Security fixes
* Enhancement: socket.close() now ignores ECONNRESET
* Removal of the macOS job of Travis CI
* New test.pythoninfo utility
* Revert commits if buildbots are broken
* Fix the Python test suite


Statistics
==========

::

    # All branches
    $ git log --after=2017-09-31 --before=2018-01-01 --reverse --branches='*' --author=Stinner|grep '^commit ' -c
    157

    # Master branch only
    $ git log --after=2017-09-31 --before=2018-01-01 --reverse --author=Stinner ref/upstream/master|grep '^commit ' -c
    124

Statistics: I pushed **124** commits in the master branch on a **total of 157
commits**, remaining: 33 commits in the other branches (backports, fixes
specific to Python 2.7 or 3.6, security fixes)

