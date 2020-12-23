+++++++++++++++++++++++++++++++++++++++++++++++
Hide implementation details in the Python C API
+++++++++++++++++++++++++++++++++++++++++++++++

:date: 2020-12-23 16:00
:tags: optimization, cpython, c-api
:category: cpython
:slug: hide-implementation-details-python-c-api
:authors: Victor Stinner

This article is about discussions around the C API between 2016 and 2020, and
the creation of C API projects: pythoncapi, HPy and pythoncapi_compat. More and
more people are aware of issues caused by the C API and are working on
solutions.

Year 2016
=========

Between 2016 and 2017, Larry Hastings worked on removing the GIL in a CPython
fork called "The Gilectomy". He pushed the first commit in April 2016: `Removed
the GIL. Don't merge this!
<https://github.com/larryhastings/gilectomy/commit/4a1a4ff49e34b9705608cad968f467af161dcf02>`_
("Few programs work now").

At EuroPython 2016, he gave the talk `Larry Hastings - The Gilectomy
<https://www.youtube.com/watch?v=fgWUwQVoLHo>`_ where he explained that the
current parallelism bottleneck is the CPython reference counting which doesn't
scale with the number of threads.


Year 2017
=========

May
---

In 2017, I discussed with Eric Snow who was working on subinterpreters. He had
to modify public structures, especially the ``PyInterpreterState`` structure.
He created ``Include/internal/`` subdirectory to create a new "internal C API"
which should not be exported.

I started the discuss C API changes during the Python Language Summit
(PyCon US 2017): `"Python performance" slides (PDF)
<https://github.com/vstinner/conf/raw/master/2017-PyconUS/summit.pdf>`_.  See
also the LWN article: `Keeping Python competitive
<https://lwn.net/Articles/723752/#723949>`_ by Jake Edge.

July: first PEP draft
---------------------

I proposed the first PEP draft to python-ideas:
`PEP: Hide implementation details in the C API
<https://mail.python.org/archives/list/python-ideas@python.org/thread/6XATDGWK4VBUQPRHCRLKQECTJIPBVNJQ/>`__.

Abstract:

    Modify the C API to remove implementation details. Add an opt-in option
    to compile C extensions to get the old full API with implementation
    details.

    (...)

    Reference counting may be emulated in a future implementation for
    backward compatibility.

The plan is made of multiple small steps:

* Step 1: Split ``Include/`` into subdirectories
* Step 2: Add an opt-in API option to tools building packages
* Step 3: First pass of implementation detail removal
* Step 4: Switch the default API to the new restricted python API.
* Step 5: Continue Step 3: remove even more implementation details.

September
---------

I discussed my idea at the CPython core dev sprint (at Instagram, California).
The idea was liked by most (if not all) core developers who are fine with a
minor performance slowdown (caused by replacing macros with function calls).

I wrote `A New C API for CPython
<https://vstinner.github.io/new-python-c-api.html>`_ blog post about these
discussions.

November
--------

I proposed `Make the stable API-ABI usable
<https://mail.python.org/pipermail/python-dev/2017-November/150607.html>`_ on
the python-dev list.

Year 2018
=========

In July, I created the `pythoncapi project
<https://github.com/vstinner/pythoncapi>`_ to collect issues of the current C
API, list things to avoid in new functions like borrowed references, and start
to design a new better C API.

Year 2019
=========

In February, I sent `Update on CPython header files reorganization
<https://mail.python.org/archives/list/capi-sig@python.org/thread/WS6ATJWRUQZESGGYP3CCSVPF7OMPMNM6/>`_
to the capi-sig list.

In March, I modified the Python debug build to make its ABI compatible with the
release build ABI:
`What’s New In Python 3.8: Debug build uses the same ABI as release build
<https://docs.python.org/dev/whatsnew/3.8.html#debug-build-uses-the-same-abi-as-release-build>`_.

In May, I gave a lightning talk `Status of the stable API and ABI in Python 3.8
<https://github.com/vstinner/conf/blob/master/2019-Pycon/status_stable_api_abi.pdf>`_,
at the Language Summit (during Pycon US 2019).

In July, the `HPy project <https://hpy.readthedocs.io/>`_ was created during
EuroPython at Basel.


Years 2020
==========

April
-----

I proposed `PEP: Modify the C API to hide implementation details
<https://mail.python.org/archives/list/python-dev@python.org/thread/HKM774XKU7DPJNLUTYHUB5U6VR6EQMJF/#TKHNENOXP6H34E73XGFOL2KKXSM4Z6T2>`__
on the python-dev list. The main idea is to provide a new optimized Python
runtime which is backward incompatible on purpose, and continue to ship the
regular runtime which is fully backward compatible.

Abstract:

* Hide implementation details from the C API to be able to optimize CPython and
  make PyPy more efficient.
* The expectation is that most C extensions don't rely directly on CPython
  internals and so will remain compatible.
* Continue to support old unmodified C extensions by continuing to provide the
  fully compatible "regular" CPython runtime.
* Provide a new optimized CPython runtime using the same CPython code base:
  faster but can only import C extensions which don't use implementation
  details.  Since both CPython runtimes share the same code base, features
  implemented in CPython will be available in both runtimes.
* Stable ABI: Only build a C extension once and use it on multiple Python
  runtimes and different versions of the same runtime.
* Better advertise alternative Python runtimes and better communicate on the
  differences between the Python language and the Python implementation
  (especially CPython).

Note: Cython and cffi should be preferred to write new C extensions. This PEP
is about existing C extensions which cannot be rewritten with Cython.

June
----

I wrote `PEP 620 -- Hide implementation details from the C API
<https://www.python.org/dev/peps/pep-0620/>`_ and `proposed the PEP to
python-dev
<https://mail.python.org/archives/list/python-dev@python.org/thread/HKM774XKU7DPJNLUTYHUB5U6VR6EQMJF/>`_.
This PEP was rewritten from scratch. Python now distributes a new
``pythoncapi_compat.h`` header and a process is defined to reduce the number of
broken C extensions when introducing C API incompatible changes listed in this
PEP.

I created the `pythoncapi_compat project
<https://github.com/pythoncapi/pythoncapi_compat>`_: header file providing new
C API functions to old Python versions using static inline functions.

December
--------

I wrote a new ``upgrade_pythoncapi.py`` script to add Python 3.10
support to an extension module without losing support with Python 2.7.  I sent
`New script: add Python 3.10 support to your C extensions without losing Python
3.6 support
<https://mail.python.org/archives/list/capi-sig@python.org/thread/LFLXFMKMZ77UCDUFD5EQCONSAFFWJWOZ/>`_
to the capi-sig list.

The pythoncapi_compat project got its first two users (bitarray and immutables
projects).

I collaborated with the HPy project to create a manifesto explaining how the C
API prevents to optimize CPython and makes the CPython C API inefficient on
PyPy.
