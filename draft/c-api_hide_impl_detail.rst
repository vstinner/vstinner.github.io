+++++++++++++++++++++++++++++++++++++++++++++++
Hide implementation details in the Python C API
+++++++++++++++++++++++++++++++++++++++++++++++

:date: 2020-12-23 16:00
:tags: optimization, cpython, c-api
:category: cpython
:slug: hide-implementation-details-python-c-api
:authors: Victor Stinner

Year 2016
=========

Gilectomy: 2016-2017.

First gilectomy commit: `Removed the GIL. Don't merge this!
<https://github.com/larryhastings/gilectomy/commit/4a1a4ff49e34b9705608cad968f467af161dcf02>`_
(April 2016), "Few programs work now."

Larry Hastings - The Gilectomy

EuroPython 2016: Larry Hastings - The Gilectomy
https://www.youtube.com/watch?v=fgWUwQVoLHo

Performance bottleneck: reference couting, ``PyObject.ob_refcnt``.

Year 2017
=========

Eric Snow work on subinterpreters.

* 2017-05: Idea proposed at the Python Language Summit, during PyCon US 2017.
  My `"Python performance" slides (PDF)
  <https://github.com/vstinner/conf/raw/master/2017-PyconUS/summit.pdf>`_.
  LWN article: `Keeping Python competitive
  <https://lwn.net/Articles/723752/#723949>`_.
* 2017-07: Idea proposed on python-ideas. `[Python-ideas] PEP: Hide
  implementation details in the C API
  <https://mail.python.org/pipermail/python-ideas/2017-July/046399.html>`_
* 2017-07-11:
  `[Python-ideas] PEP: Hide implementation details in the C API
  <https://mail.python.org/pipermail/python-ideas/2017-July/046399.html>`_
* 2017-09: Idea discussed at the CPython sprint at Instagram (California).
  Liked by all core developers. The expected performance slowdown is likely to
  be accepted.
* 2017-09: Blog post: `A New C API for CPython
  <https://vstinner.github.io/new-python-c-api.html>`_
* 2017-11: Idea proposed on python-dev, `[Python-Dev] Make the stable API-ABI
  usable
  <https://mail.python.org/pipermail/python-dev/2017-November/150607.html>`_
* 2017-12-21: It's an idea. There is an old PEP draft, but no implementation,
  the PEP has no number and was not accepted yet (nor really proposed).

Year 2018
=========

* 2018-06: capi-sig mailing list migrated to Mailman 3
* 2018-07-29: `pythoncapi project <https://github.com/vstinner/pythoncapi>`_
  created on GitHub

Year 2019
=========

* 2019-05-01: `Status of the stable API and ABI in Python 3.8
  <https://github.com/vstinner/conf/blob/master/2019-Pycon/status_stable_api_abi.pdf>`_,
  slides of Victor Stinner's lightning talk at the Language Summit (during
  Pycon US 2019)
* 2019-02-22: `[capi-sig] Update on CPython header files reorganization
  <https://mail.python.org/archives/list/capi-sig@python.org/thread/WS6ATJWRUQZESGGYP3CCSVPF7OMPMNM6/>`_

`HPy Initial commit
<https://github.com/hpyproject/hpy/commit/f0e9b058b81e69edb6e52b48910e50bdf7ac9092>`_:
July 2019 (EuroPython Basel).

HPy: a better API for Python
https://hpy.readthedocs.io/


Years 2020
==========

PEP 620 -- Hide implementation details from the C API
https://www.python.org/dev/peps/pep-0620/

Fix the Python C API to optimize Python
https://pythoncapi.readthedocs.io/optimize_python.html

PEP 620 Version History:

* Version 3, June 2020: PEP rewritten from scratch. Python now
  distributes a new ``pythoncapi_compat.h`` header and a process is
  defined to reduce the number of broken C extensions when introducing C
  API incompatible changes listed in this PEP.
* Version 2, April 2020:
  `PEP: Modify the C API to hide implementation details
  <https://mail.python.org/archives/list/python-dev@python.org/thread/HKM774XKU7DPJNLUTYHUB5U6VR6EQMJF/#TKHNENOXP6H34E73XGFOL2KKXSM4Z6T2>`_.
* Version 1, July 2017:
  `PEP: Hide implementation details in the C API
  <https://mail.python.org/archives/list/python-ideas@python.org/thread/6XATDGWK4VBUQPRHCRLKQECTJIPBVNJQ/#HFBGCWVLSM47JEP6SO67MRFT7Y3EOC44>`_
  sent to python-ideas
