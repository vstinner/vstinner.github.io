++++++++++++++++++++++++++++++++++++++
Process for incompatible C API changes
++++++++++++++++++++++++++++++++++++++

:date: 2021-03-26 12:00
:tags: c-api, cpython
:category: cpython
:slug: c-api-process-incompatible-changes
:authors: Victor Stinner

Process to deprecate
====================

* Add Py_DEPRECATED()
* Implement Py_DEPRECATED() for MSC
* The PEP 387 was updated to require deprecation during two Python releases,
  since the PEP 602 made the Python release shorter (12 months rather than
  18 months).
* The PEP 620 defines a `Process to reduce the number of broken C extensions
  <https://www.python.org/dev/peps/pep-0620/#process-to-reduce-the-number-of-broken-c-extensions>`_
  when introducing incompatible C API changes on purpose.
* Check PyPI top 4000 packages:

  * INADA Naoki wrote a recipe to download the source code of the top 4000 PyPI projects
    and then search for a regular expression in all sources:
    https://github.com/methane/notes/tree/master/2020/wchar-cache
  * `JSON file to the top 4000 PyPI Packages
    <https://hugovk.github.io/top-pypi-packages/>`_

* Fedora "continuous integration": Python packages of Fedora rebuilt with
  Python 3.10. Broken packages are reported to upstream projects, sometimes
  with fixes.

What's Next?
============

* Convert again Py_TYPE() and Py_SIZE() macros to static inline functions.
* Make upgrade_pythoncapi.py more popular! Try it on numpy. Maybe move the
  GitHub project under the PSF organization.
* Add "%T" formatter for Py_TYPE(obj)->tp_name:
  see `rejected bpo-34595 <https://bugs.python.org/issue34595>`_
* Avoid ``PyObject**`` type, direct access into an array of ``PyObject*``:

  * Deprecate PySequence_Fast_ITEMS()
  * Disallow ``&PyTuple_GET_ITEM(0)``: convert ``PyTuple_GET_ITEM()`` macro
    to static inline function:
    `bpo-41078 <https://bugs.python.org/issue41078>`_.
  * https://www.python.org/dev/peps/pep-0620/#avoid-functions-returning-pyobject
  * https://mail.python.org/archives/list/python-dev@python.org/thread/632CV42376SWVYAZTHG4ROOV2HRHOVZ7/

* Avoid funtions giving a direct access into object data with no API to signal
  when the resource can be released.

  * Issue for moving GC
  * Pin memory or copy memory, unpin or freed the copy when the resource is
    released
  * PyBytes_GetString()
  * Py_buffer with PyBuffer_Release() API notifies Python when the resource is
    no longer needed.

* Modify Cython to use getter functions. Attempt to make some structures
  opaque, like PyThreadState.

* `PEP 620 -- Hide implementation details from the C API
  <https://www.python.org/dev/peps/pep-0620/>`_ by Victor Stinner

See also the draft `PEP 652 -- Maintaining the Stable ABI
<https://www.python.org/dev/peps/pep-0652/>`_ by Petr Viktorin.
