++++++++++++++++++++++++++++++++++++++++++++++++++++++
Port your Python 2 applications to Python 3 with sixer
++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2015-06-16 15:00
:tags: python3, sixer
:category: python
:slug: python3-sixer
:authors: Victor Stinner
:summary: Port your Python 2 applications to Python 3 with sixer


From 2to3 to 2to6
=================

When Python 3.0 was released, the official statement was to port your
application using `2to3 <https://docs.python.org/3.5/library/2to3.html>`_ and
drop Python 2 support. It didn't work because you had to port all libraries
first. If a library drops Python 2 support, existing applications running on
Python 2 cannot use this library anymore.

This chicken-and-egg issue was solved by the creation of the `six module
<https://pythonhosted.org/six/>`_ by `Benjamin Peterson
<https://benjamin.pe/>`_. Thank you so much Benjamin! Using the six module, it
is possible to write a single code base working on Python 2 and Python 3.

2to3 was hacked to create the `modernize
<http://python-modernize.readthedocs.org/>`_ and `2to6
<https://github.com/limodou/2to6>`_ projects to *add Python 3 support* without
loosing Python 2 support. Problem solved!


Creation of the sixer tool
==========================

Problem solved? Well, not for my specific use case. I'm porting the huge
OpenStack project to Python 3. modernize and 2to6 modify a lot of things at
once, add unwanted changes (ex: add ``from __future__ import absolute_import``
at the top of each file), and don't respect the OpenStack coding style
(especially the `complex rules to sort and group Python imports
<http://docs.openstack.org/developer/hacking/#imports>`_).

I wrote the `sixer <https://pypi.python.org/pypi/sixer>`_ project to
*generate* patches for OpenStack. The problem is that OpenStack code changes
very quickly, so it's common to have to fix conflicts the day after submiting
a change. At the beginning, it took at least one week to get Python 3 changes
merged, whereas many changes are merged every day, so being able to regenerate
patches helped a lot.

I created the `sixer <https://pypi.python.org/pypi/sixer>`_ tool using a list
of regular expressions to replace a pattern with another. For example, it
replaces ``dict.itervalues()`` with ``six.itervalues(dict)``. The code was
very simple.  The most difficult part was to respect the OpenStack coding
style for Python imports.

sixer is a success since its creationg, it helped me to fix the all obvious
Python 3 issues: replace ``unicode(x)`` with ``six.text_type(x)``, replace
``dict.itervalues()`` with ``six.itervalues(dict)``, etc. These changes are
simple, but it's boring to have to modify manually many files. The OpenStack
Nova project has almost 1500 Python files for example.

The development version of sixer supports the following operations:

- all
- basestring
- dict0
- dict_add
- iteritems
- iterkeys
- itertools
- itervalues
- long
- next
- raise
- six_moves
- stringio
- unicode
- urllib
- xrange


Creation of the Sixer Test Suite
================================

Slowly, I added more and more patterns to sixer. The code became too complex
to be able to check regressions manually, so I also started to write unit
tests. Now each operation has at least one unit test. Some complex operations
have four tests or more.

At the beginning, tests called directly the Python function. It is fast and
convenient, but it failed to catch regressions on the command line program.
So I added tests running sixer has a blackbox: pass an input file and check
the output file. Then I added specific tests on the code parsing command line
options.


The new "all" operation
=======================

At the beginning, I used sixer to generate a patch for a single pattern. For
example, replace ``unicode()`` in a whole project.

Later, I started to use it differently: I fixed all Python 3 issues at once,
but only in some selected files. I did that when we reached a minimum set of
tests which pass on Python 3 to have a green py34 check on Jenkins. Then we
ported tests one by one. It's better to write short patches, they are easier
and faster to review. And the review process is the bottlebeck of the
OpenStack development process.

To fix all Python 3 at once, I added an ``all`` operation which simply applies
sequentially each operation. So ``sixer`` can now be used as ``modernize`` and
``2to6`` to fix all Python 3 issues at once in a whole project.

I also added the ability to pass filenames instead of having to pass a
directory to modify all files in all subdirectories.


New urllib, six_moves and stringio operations
=============================================


urllib
------

I tried to keep the sixer code simple. But some changes are boring to write,
like replacing ``urllib`` imports ``six.moves.urllib`` imports. Python 2 has 3
modules (``urllib``, ``urllib2``, ``urlparse``), whereas Pytohn 3 uses a
single ``urllib`` namespace with submodules (``urllib.request``,
``urllib.parse``, ``urllib.error``). Some Python 2 functions moved to one
submodule, whereas others moved to another submodules. It required to know
well the old and new layout.

After loosing many hours to write manually patches for ``urllib``, I decided
to add a ``urllib`` operation. In fact, it was so not long to implement it,
compared to the time taken to write patches manually.

stringio
--------

Handling StringIO is also a little bit tricky because String.StringIO and
String.cStringIO don't have the same performance on Python 2. Producing
patches without killing performances require to pick the right module or
symbol from six: ``six.StringIO()`` or ``six.moves.cStringIO.StringIO`` for
example.

six_moves
---------

The generic ``six_moves`` operation replaces various Python 2 imports with
imports from ``six.moves``:

- BaseHTTPServer
- ConfigParser
- Cookie
- HTMLParser
- Queue
- SimpleHTTPServer
- SimpleXMLRPCServer
- __builtin__
- cPickle
- cookielib
- htmlentitydefs
- httplib
- repr
- xmlrpclib


KISS: emit warnings instead of complex implementation
=====================================================

As I wrote, I tried to keep sixer simple (KISS principle: Keep It Simple,
Stupid). I'm also lazy, I didn't try to write a perfect tool. I don't want to
spend hours on the sixer project.

When it was too tricky to make a decision or to implement a pattern, sixer
emits "warnings" instead. For example, a warning is emitted on
``def next(self):`` to remind that a ``__next__ = next`` alias is probably
needed on this class for Python 3.


Conclusion
==========

The sixer tool is incomplete and generates invalid changes. For example, it
replaces patterns in comments, docstrings and strings, whereas usually these
changes don't make sense. But I'm happy because the tool helped me a lot
for to port OpenStack, it saved me hours.

I hope that the tool will now be useful to others! Don't hesitate to give me
feedback.

