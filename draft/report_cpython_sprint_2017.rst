++++++++++++++++++++++++++++++++++++++++++
CPython sprint at Facebook, September 2017
++++++++++++++++++++++++++++++++++++++++++

My "new C API" PEP
==================

* [Python-Dev] New C API not leaking implementation details:
  an usable stable ABI
  https://mail.python.org/pipermail/python-dev/2017-September/149264.html
* PEP explainted to the CPython core developers
* New blog post to explain the PEP rationale in depth: https://github.com/vstinner/misc/blob/master/python/pep_c_api.rst
* PEP draft written last june: https://haypo.github.io/new-python-c-api.html

I used the whitebord to explain the changes I want to do, but also see how to
reorganize C header files of the ``Include/`` directory. The question is if
we need multiple versions of each header depending on the expected API,
how to avoid duplication, and how to choose an API.

Very good feedback, the PEP is likely to be accepted, once I have enough time
to rewrite it to include all comments.

CPython tutorial for newcomers
==============================

* https://cpython-core-tutorial.readthedocs.io/
* https://github.com/vstinner/cpython_core_tutorial/
* Tutorial introduced to Mariatta Wijaya and Ezio Metlotti who worked a lot
  on the existing CPython developer guide:
  https://devguide.python.org/
* Mariatta likes the idea and finds it useful. Ezio is reorganizing the
  developer guide sections. First, Ezio considered that the tutorial would
  duplicate the content, which is true, and that the devguide can be "bended"
  to look like my tutorial idea. But we have a different point of view on how
  content should be organized. I am trying to write many small pages whereas
  Ezio prefers long pages on the same topic. At the end, we agreed to keep
  a separated tutorial.

Multiple interpreters
=====================

Eric Snow is working on the CPython code base to support running multiple
interpreters in the same process: PEP 554, https://www.python.org/dev/peps/pep-0554/

I worked with Eric on static variables in the C code. Something like::

    static PyObject *var = NULL;
    if (var == NULL) {
        var = ...;
    }

Last march, I opened an issue to enhance such code to be able to clear these
variables at exit:

* https://bugs.python.org/issue29881
* https://github.com/python/cpython/pull/780

We discussed how to take in account multiple interpreters in such API. It was
said that we need to store the actual value in interpreter specific variables.
Each interpreter would have for example an hash table, and the variable would
have a key (ex: its address) to get the value from this table. So it becomes
possible to have a different value per interpreter.

