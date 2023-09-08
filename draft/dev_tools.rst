++++++++++++++++++++
My development tools
++++++++++++++++++++

Keyboard shortcut
=================

I defined ALT+e to spawn a Terminal.

GitHub
======

* Add ``.patch`` at the end of commit URL and PR URL to get it as a patch
  file.
* Type ``g n`` to to Go to Notifications

scm.py
======

https://github.com/vstinner/misc/blob/main/bin/scm.py

mymake.py
=========

https://github.com/vstinner/misc/blob/main/bin/mymake.py

Git aliases
===========

git b
git s

apply_patch.py
==============

https://github.com/vstinner/misc/blob/main/bin/apply_patch.py

gh_pr.sh
========

https://github.com/vstinner/misc/blob/main/bin/gh_pr.sh

sed
===

I use sed quite often for refactoring::

    sed -i -e 's/regex/replacement/g' files

When a config has so many comments that it's barely readable::

    sed -e '/^#/D;/^$/D' config_file

Remove lines with comments and empty lines.
