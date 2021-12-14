+++++++++++++++++++++++++++
Python incompatible changes
+++++++++++++++++++++++++++

:date: 2021-12-08 16:00
:tags: c-api, cpython
:category: cpython
:slug: python-incompatible-changes
:authors: Victor Stinner

Incompatible Changes
====================

* PyTypeObject.tp_print
* PyCode_New()
* types.CodeType constructor
* ast.Constant
* Py_TYPE() and Py_SIZE() l-value
* asyncore, asynchat, smtpd modules removal
* collections aliases
* open() "U" mode
* async and await keyword
* inspect.getargspec() removal

Fedora: single package build failure caused many packages fail to build
=======================================================================

In Fedora, when a package fails to build, it can cause many other packages
to build if they depend on it. A package can be broken for different reasons:

* Python incompatible change
* Broken build dependency
* Broken runtime dependency
* Building C extensions fail
* Test failure: new warning treated as error, pytest change, etc.
* Something else.

Identifying the root issue causing 20+ package failures take time, it requires
to dig into build logs of each package.

A common task is to identify the most important dependencies and first fix
these ones.


ast.Constant change
===================

Remove specific constant AST types in favor of ast.Constant
https://bugs.python.org/issue32892

* astroid (used by pylint):

  * https://github.com/PyCQA/astroid/issues/617
  * https://github.com/PyCQA/astroid/issues/616

* pyflakes:

  * https://github.com/PyCQA/pyflakes/issues/367
  * https://github.com/PyCQA/pyflakes/pull/369

* Genshi:

  * https://github.com/python/performance/issues/46
  * https://genshi.edgewall.org/ticket/612

* Chameleon:

  * https://github.com/python/performance/issues/47
  * https://github.com/malthe/chameleon/issues/272

* Mako: https://github.com/sqlalchemy/mako/issues/287

Fedora bugs
===========

* Python 3.10: https://bugzilla.redhat.com/showdependencytree.cgi?id=PYTHON3.10&hide_resolved=0
* Python 3.9: https://bugzilla.redhat.com/showdependencytree.cgi?id=PYTHON39&hide_resolved=0
* Python 3.8: https://bugzilla.redhat.com/showdependencytree.cgi?id=PYTHON38&hide_resolved=0
* Python 3.7: https://bugzilla.redhat.com/showdependencytree.cgi?id=PYTHON37&hide_resolved=0


PyUnicode_InternImmortal()
==========================

https://bugs.python.org/issue41692

In December 2021, no project of the PyPI top 5000 projects call
PyUnicode_InternImmortal().

Open question: is it ok to remove the symbol from the stable ABI? A solution is
to remove the function from the API, keep it in the ABI, but modify it to only
raise an error.

Py_REFCNT()
===========

Changed in Python 3.10:

* https://bugs.python.org/issue39573

breezy uses "Py_REFCNT(self) -= 1;"

* Breezy ("bzr"): https://bugs.launchpad.net/brz/+bug/1904868
* PySide: https://bugreports.qt.io/browse/PYSIDE-1436

PEP 570 Positional only arguments (May 2019)
============================================

* https://www.python.org/dev/peps/pep-0570
* https://github.com/python/cpython/pull/12701
* Expected stability of PyCode_New() and types.CodeType() signatures
  https://mail.python.org/archives/list/python-dev@python.org/thread/VXDPH2TUAHNPT5K6HBUIV6VASBCKKY2K/

Python API change: types.CodeType constructor
---------------------------------------------

* Add CodeType.replace() to Python 3.8:

  * https://bugs.python.org/issue37032
  * https://docs.python.org/dev/library/types.html#types.CodeType.replace

Broken projects:

* Genshi:

  * https://github.com/edgewall/genshi/pull/19
  * Recently updated to use CodeType.replace() to support Python 3.10:
    https://github.com/edgewall/genshi/commit/a23f3054b96b487215b04812c680075c5117470a

* Hypothesis:

  * https://github.com/HypothesisWorks/hypothesis/issues/1943
  * https://github.com/HypothesisWorks/hypothesis/commit/8f47297fa2e19c426a42b06bb5f8bf1406b8f0f3

* ipython:
  https://github.com/ipython/ipython/commit/248128dfaabb33e922b1e36a298fd7ec0c730069

* Cloud Pickle:
  https://github.com/cloudpipe/cloudpickle/commit/b9dc17fc5f723ffbfc665295fafdd076907c0a93

C API change: PyCode_New()
--------------------------

* https://bugs.python.org/issue37221
* https://bugs.python.org/issue36886
  Failed to construct CodeType on Python-3.8.0a4
* https://bugs.python.org/issue36896
  clarify in types.rst that FunctionTypes & co  constructors don't have stable signature

  * https://github.com/python/cpython/pull/13271/files

* Cython

Add PyCode_NewWithPosOnlyArgs()
-------------------------------

* June 2019: bpo-37221: Add PyCode_NewWithPosOnlyArgs to be used internally and set PyCode_New as a compatibility wrapper
  https://github.com/python/cpython/pull/13959

Cython?
-------

* April 2019, master: https://github.com/cython/cython/commit/d22678c700446636360d3fe97aef60f0cedef741
* May 2019, branch 0.29.x: https://github.com/cython/cython/commit/61ed2e81b9580ba66cd7d42f67d336ab1c5d65ab
* June 2019: https://github.com/cython/cython/commit/9b6a02f7f28934fa0d02ab4d173c1b89bf3bd8f8


Removal of PyTypeObject.tp_print
================================

* CPython change, PEP 590

  * https://github.com/python/cpython/pull/13185
  * Replace PyTypeObject.tp_print with PyTypeObject.tp_vectorcall:
    https://github.com/python/cpython/commit/aacc77fbd77640a8f03638216fa09372cc21673d

* https://bugs.python.org/issue37250
* https://mail.python.org/pipermail/python-dev/2018-June/153927.html
* Cython

  * https://github.com/cython/cython/issues/2976
  * https://github.com/cython/cython/commit/f10a0a391edef10bd37095af87f521808cb362f7
  * Cython 0.29.10 (June 2, 2019)


Py_TYPE() and Py_SIZE()
=======================

Changed in Python 3.11:

* https://bugs.python.org/issue39573#msg379675
* https://bugs.python.org/issue45476#msg407410
* https://github.com/python/steering-council/issues/79

Article about these changes: https://vstinner.github.io/c-api-abstract-pyobject.html

Fixed:

* Cython: https://github.com/cython/cython/commit/d8e93b332fe7d15459433ea74cd29178c03186bd
* immutables: https://github.com/MagicStack/immutables/pull/52
* numpy:

  * https://github.com/numpy/numpy/commit/a96b18e3d4d11be31a321999cda4b795ea9eccaa
  * https://github.com/numpy/numpy/commit/f1671076c80bd972421751f2d48186ee9ac808aa

* pycurl: https://github.com/pycurl/pycurl/commit/e633f9a1ac4df5e249e78c218d5fbbd848219042
* bitarray: https://github.com/ilanschnell/bitarray/pull/109
* mercurial: https://bz.mercurial-scm.org/show_bug.cgi?id=6451
* boost: https://github.com/boostorg/python/commit/500194edb7833d0627ce7a2595fec49d0aae2484
* pyside2: https://bugreports.qt.io/browse/PYSIDE-1436
* breezy: https://bugs.launchpad.net/brz/+bug/1904868
* duplicity: https://git.launchpad.net/duplicity/commit/duplicity/_librsyncmodule.c?id=bbaae91b5ac6ef7e295968e508522884609fbf84
* gobject-introspection: https://gitlab.gnome.org/GNOME/gobject-introspection/-/merge_requests/243

Fix proposed:

* pybluez: https://github.com/pybluez/pybluez/pull/410

Broken:

* PyPAM
* pygobject3
* pylibacl
* rdiff-backup

Py_SIZE:

* Naked-0.1.31
* Shapely-1.8.0
* dedupe-hcluster-0.3.8
* fastdtw-0.3.4
* fuzzyset-0.0.19
* gluonnlp-0.10.0
* hdbscan-0.8.27
* jenkspy-0.2.0
* lightfm-1.16
* neobolt-1.7.17
* orderedset-2.0.3
* ptvsd-4.3.2
* py_spy-0.3.11
* pyemd-0.5.1
* pyhacrf-datamade-0.2.5
* pyjq-2.5.2
* pypcap-1.2.3
* python-crfsuite-0.9.7
* reedsolo-1.5.4
* tables-3.6.1
* thriftpy-0.3.9
* thriftrw-1.8.1
* tinycss-0.4
* triangle-20200424

Py_TYPE:

* datatable-1.0.0.tar.gz
* mypy-0.910
* pysha3-1.0.2
* recordclass-0.16.3


PEP 670
=======

Removing the return value of macros is an incompatible API change made on
purpose: see the Remove the return value section.

Some function arguments are still cast to PyObject* to prevent emitting new
compiler warnings.

Macros which can be used as l-value in an assignment are not modified by this
PEP to avoid incompatible changes.

PEP 674
=======

On the PyPI top 5000 projects, only 14 projects (0.3%) are affected by 4 macro
changes. Moreover, 24 projects just have to regenerate their Cython code to use
Py_SET_TYPE().

In practice, the majority of affected projects only have to make two changes:

* Replace Py_TYPE(obj) = new_type; with Py_SET_TYPE(obj, new_type);.
* Replace Py_SIZE(obj) = new_size; with Py_SET_SIZE(obj, new_size);.

PyDescr_NAME() and PyDescr_TYPE()

asyncore, asynchat, smtpd
=========================

Links:

* https://bugs.python.org/issue28533
* https://mail.python.org/archives/list/python-dev@python.org/thread/LZOOLX5EKOITW55TW7JQYKLXJUPCAJB4/
* https://github.com/python/steering-council/issues/86

Changes:

* Deprecate in 3.6 doc: https://github.com/python/cpython/commit/9bf2cbc4c498812e14f20d86acb61c53928a5a57
* ... reverted: https://hg.python.org/cpython/rev/6eb3312a9a16
* Remove asyncore from test_pyclbr: https://github.com/python/cpython/commit/138e7bbb0a5ed44bdd54605e8c58c8f3d3865321
* Remove 3 modules: https://github.com/python/cpython/commit/9bf2cbc4c498812e14f20d86acb61c53928a5a57
* Revert 3 modules: https://github.com/python/cpython/commit/cf7eaa4617295747ee5646c4e2b7e7a16d7c64ab

According to a code search in the PyPI top 5000 projects: the source code of 21
projects contains "import asyncore", "import asynchat" or "import smtpd":

* ansible-5.0.0
* cassandra-driver-3.25.0
* django-extensions-3.1.5
* eth_abi-2.1.1
* eth-account-0.5.6
* eth-hash-0.3.2
* eth-utils-2.0.0
* gevent-21.8.0
* h5py-3.6.0
* hexbytes-0.2.2
* jedi-0.18.1
* M2Crypto-0.38.0
* mercurial-6.0
* mypy-0.910
* plac-1.3.3
* pyftpdlib-1.5.6
* pyinotify-0.9.6
* pysnmp-4.4.12
* pytest-localserver-0.5.1
* pytype-2021.11.29
* tlslite-0.4.9

I ignored false positives like "from eventlet(...) import asyncore".

collections aliases, open() U flag
==================================

* https://mail.python.org/archives/list/python-dev@python.org/thread/EYLXCGGJOUMZSE5X35ILW3UNTJM3MCRE/#OUHSUXWDWQ2TL7ZESB5WODLNHKMBZHYH
* https://lwn.net/Articles/811369/
* https://docs.python.org/dev/whatsnew/3.9.html#you-should-check-for-deprecationwarning-in-your-code

open() "U" flag
---------------

* https://bugs.python.org/issue37330
* https://github.com/python/cpython/commit/e471e72977c83664f13d041c78549140c86c92de

Broken:

* docutils:

  * https://sourceforge.net/p/docutils/bugs/363/
  * https://sourceforge.net/p/docutils/bugs/364/
  * At 2019-07-22,  Günter Milde wrote: "Docutils 0.15 is released" (with the
    fix). The latest docutils version is 0.17.1.

* Samba build (waf):

  * https://bugzilla.samba.org/show_bug.cgi?id=14266
  * https://github.com/samba-team/samba/blob/1209c89dcf6371bbfa4f3929a47a573ef2916c1a/buildtools/wafsamba/samba_utils.py#L692

* 2020-03-04: bpo-39674: Revert "bpo-37330: open() no longer accept 'U' in file mode (GH-16959)" (GH-18767)
  https://github.com/python/cpython/commit/942f7a2dea2e95a0fa848329565c0d0288d92e47

* 2021-09-02: bpo-37330: open() no longer accept 'U' in file mode (GH-28118)
  https://github.com/python/cpython/commit/19ba2122ac7313ac29207360cfa864a275b9489e

Another candidate is to revert the ignored "U" mode in open(): commit e471e72977c83664f13d041c78549140c86c92de of bpo-37330.

Removing "U" mode of open() broke 11 packages in Fedora:

* aubio
* openvswitch
* python-SALib
* python-altgraph
* python-apsw
* python-magic-wormhole-mailbox-server
* python-munch
* python-parameterized
* python-pylibmc
* python-sphinx-testing
* veusz

Keeping "U" mode in Python 3.9 is also a formal request from Andrew Bartlett of the Samba project: https://bugs.python.org/issue37330#msg362362

collections
-----------

* Emit warning

  * https://bugs.python.org/issue25988
  * https://github.com/python/cpython/commit/c66f9f8d3909f588c251957d499599a1680e2320

* bpo-25988: Do not expose abstract collection classes in the collections module. (GH-10596)
  https://github.com/python/cpython/commit/ef092fe9905f61ca27889092ca1248a11aa74498
* bpo-39674: Revert "bpo-25988: Do not expose abstract collection classes in the collections module. (GH-10596)" (GH-18545)
  https://github.com/python/cpython/commit/af5ee3ff610377ef446c2d88bbfcbb3dffaaf0c9
* bpo-37324: Remove ABC aliases from collections (GH-23754)
  https://github.com/python/cpython/commit/c47c78b878ff617164b2b94ff711a6103e781753
* collections: remove deprecated aliases to ABC classes:
  https://bugs.python.org/issue37324
* Keep deprecated features in Python 3.9 to ease migration from Python 2.7, but remove in Python 3.10
  https://bugs.python.org/issue39674
* pip vendors html5lib which didn't get a release for 1 year 1/2

  * https://github.com/html5lib/html5lib-python/issues/419
  * https://github.com/html5lib/html5lib-python/commit/4f9235752cea29c5a31721440578b430823a1e69
  * https://github.com/pypa/pip/commit/ef7ca1472c1fdd085cffb8183b7ce8abbe9e2800

asyncio loop parameter removal
==============================

* https://docs.python.org/dev/whatsnew/3.10.html#changes-in-the-python-api
* https://bugs.python.org/issue42392

Python 3.7: async and await keywords
====================================

* async and await names are now reserved keywords.
* https://bugs.python.org/issue30406

Impacted projects: Twisted?

inspect signature
=================

* inspect.signature() added to Python 3.3
* inspect.getfullargspec() is still there
* Remove inspect.getargspec()

Part 1:

* https://bugs.python.org/issue20438
* Deprecate: https://hg.python.org/cpython/rev/3a5fec5e025d
* Remove deprecation: https://github.com/python/cpython/commit/0899b9809547ec2894dcf88cf4bba732c5d47d0d

Part 2:

* https://bugs.python.org/issue25486
* Remove: https://hg.python.org/cpython/rev/a565aad5d6e1
* Add again: https://hg.python.org/cpython/rev/32c8bdcd66cc

Part 3:

* https://bugs.python.org/issue45320
* Remove: https://github.com/python/cpython/commit/d89fb9a5a610a257014d112bdceef73d7df14082

Porting to Python 3.x documentations
====================================

* https://docs.python.org/dev/whatsnew/3.11.html#porting-to-python-3-11 and https://docs.python.org/dev/whatsnew/3.11.html#id2
* https://docs.python.org/dev/whatsnew/3.10.html#porting-to-python-3-10 and https://docs.python.org/dev/whatsnew/3.10.html#id2
* https://docs.python.org/dev/whatsnew/3.9.html#porting-to-python-3-9
* https://docs.python.org/dev/whatsnew/3.8.html#porting-to-python-3-8
* https://docs.python.org/dev/whatsnew/3.7.html#porting-to-python-3-7
* https://docs.python.org/dev/whatsnew/3.6.html#porting-to-python-3-6
* https://docs.python.org/dev/whatsnew/3.5.html#porting-to-python-3-5
* https://docs.python.org/dev/whatsnew/3.4.html#porting-to-python-3-4
* https://docs.python.org/dev/whatsnew/3.3.html#porting-to-python-3-3
* https://docs.python.org/dev/whatsnew/3.2.html#porting-to-python-3-2
* https://docs.python.org/dev/whatsnew/3.1.html#porting-to-python-3-1
* https://docs.python.org/dev/whatsnew/3.0.html#porting-to-python-3-0

See also "Deprecated" and "Removed" sections of these documents.

classmethod
===========

Irit: There was a change to classmethod in 3.9 which caused quite a lot of
headache for my team at work. It seems like it was not considered to be an API
change when it was made, the notes were "make it work" but the impact was
actually "change how it works", and we had a very widely used utility that
broke when it changed.

See: https://bugs.python.org/issue42832

(we noticed it too late to ask for it to be reverted)


Large code base
===============

A problem is that some companies have a large code bases and don't have the
resources to upgrade to every Python version, so they don't get
DeprecationWarning, but skip Python versions and get immediately errors about
*removed* features a pratical problem is to get a supported Python package on
the Linux distribution. well, Fedora provides many Python versions, but it's
not the case of other Linux distributions.

PEP 606 "Python Compatibility Version"
======================================

https://www.python.org/dev/peps/pep-0606/

PEP 608 "Coordinated Python release"
====================================

https://www.python.org/dev/peps/pep-0608/
