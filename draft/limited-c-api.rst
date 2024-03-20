Stable ABI in Python 3.2
========================

In 2009, Martin von Löwis wrote `PEP 384 <https://peps.python.org/pep-0384/>`_
"Defining a Stable ABI" and implemented in Python 3.2. It is made in two parts:

* A **limited** C API: subset of the regular C API.
* The **stable** ABI: binary interface guaranteed to be supported by future
  Python versions.

The pitch is to build a C extension once, distribute this binary on PyPI,
and then forget since it will work on Python 3.2 and newer versions.


Test Limited C API in Python 3.10
=================================

`PEP 652 <https://peps.python.org/pep-0652/>`_ "Maintaining the Stable ABI"
by Petr Viktorin in Python 3.10.

Add:

* ``Misc/stable_abi.toml``: declaration of the stable ABI.
* ``test_stable_abi_ctypes`` test.
* ``make check-limited-abi`` test.

Limited C API Enhancements in Python 3.12
=========================================

`PEP 697 <https://peps.python.org/pep-0697/>`_ "Limited C API for Extending
Opaque Types" by Petr Viktorin in Python 3.12. It adds functions such as
`PyObject_GetTypeData <https://docs.python.org/3.12/c-api/object.html#c.PyObject_GetTypeData>`_
and
`PyObject_GetItemData <https://docs.python.org/3.12/c-api/object.html#c.PyObject_GetItemData>`_.



