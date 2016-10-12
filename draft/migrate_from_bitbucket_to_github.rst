+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Migrate an old Python project from Bitbucket (hg) to GitHub (git)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2016-10-12 22:00
:tags: python
:category: python
:slug: migrate-from-bitbucket-hg-to-github-git
:authors: Victor Stinner

Last 10 years, I wrote plently of small open source projects. Usually, I only
work on one project and then I give up and move to something else. My plan was
to let old projects die and maybe one day remove them completely. But some
projects fail to die, users report bugs or even send patches. I decided
recently to migrate some projects from Bitbucket to GitHub, and convert their
Mercurial repository to Git. I know that Bitbucket supports Git, but GitHub is
like super popular and I expect more contributions if most users already
know well the GitHub platform.

Convert Mercurial repository to Git
===================================

Use https://github.com/frej/fast-export : it's super easy. 4 commands and you
are done.

Create a new Git repository on GitHub, copy/paste commands to add a remote
to your local repository, push, you are done.


Migrate issues
==============

Use https://github.com/jeffwidman/bitbucket-issue-migration

Do it soon after creating the GitHub project, before someone creates an issue
on GitHub. Otherwise, thes script fails because identifiers are not the same.

I had to remove an assertion because someone created an issue 1 hour after the
creation of the GitHub project :-)


pep8
====

* Run autopep8
* Add pep8 rule to tox.ini
* Run "tox -e pep8"
* Fix a few issues
* Run again "tox -e pep8"
* Repeat until all issues are fixed
* Push everything
* Add pep8 to envlist in tox.ini
* Enable pep8 checks on Travis CI


Travis CI
=========

* Add .travis.yml
* Enable the project at https://travis-ci.org/
* Push something


