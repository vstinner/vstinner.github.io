+++++++++++++++++++++++++++++++++++++++++++++++++
PEP 741: C API to configure Python initialization
+++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2024-09-24 17:00
:tags: c-api, cpython
:category: cpython
:slug: pyconfig-pep-741
:authors: Victor Stinner

PEP 741 story
=============

.. image:: {static}/images/starry_night_van_gogh.jpg
   :alt: The Starry Night (1889) by Vincent Van Gogh
   :target: https://en.wikipedia.org/wiki/The_Starry_Night

Sometimes, writing a PEP can be a wild ride. It took two whole years
between the early discussions and getting `PEP 741 <https://peps.python.org/pep-0741/>`__ eventually accepted by
the Steering Council. The API is only made of 18 functions, but it took
more than 200 messages to design properly these functions!

PEP 741 is new C API to configure the Python initialization using
strings for option names. It also provides a new API to get the current
runtime Python configuration.

In 2019, I wrote `PEP 587 – Python Initialization Configuration
<https://peps.python.org/pep-0587/>`_. It was supposed to be the only
API replacing all scattered existing APIs. Well, it seems like it wasn't
complete enough and its design shown some issues since I decided to
write a new PEP 741!

Painting: *The Starry Night (1889) by Vincent Van Gogh*.


August 2022: CVE-2020-10735 fix
===============================

In August 2022, Gregory P. Smith opened
`FR: Allow private runtime config to enable extending without breaking the PyConfig ABI
<https://discuss.python.org/t/fr-allow-private-runtime-config-to-enable-extending-without-breaking-the-pyconfig-abi/18004>`_
discussion to propose supporting configuration as text. Example::

    check_hash_pycs_mode=always
    unknownok:avoid_medusas_gaze=yes

The need was to add a new option to fix CVE-2020-10735 vulnerability. It
will become ``PyConfig.int_max_str_digits`` in Python 3.12. The problem
is to add a new ``PyConfig`` member without breaking the ABI in stable
Python versions (such as Python 3.11). At the end, the problem was
worked around by adding a separated global variable
(``_Py_global_config_int_max_str_digits``).


August 2023: First implementation
=================================

In August 2023, I created `an issue
<https://github.com/python/cpython/issues/107954>`_ to implement
Gregory's idea. I wrote a proof-of-concept to accept configuration as
text in a format similar to TOML. Example::

    # int
    bytes_warning = 2

    # string
    filesystem_encoding = "utf8"   # comment

    # list
    argv = ['python', '-c', 'code']

    # you can put comments for the fun
    verbose = 1  # comment here as well
    # after, anywhere!

Quickly, I ran into parsing issues with quotes and escaping characters
such newlines and quotes.


October 2023
============

Rewrite
-------

I decided to write a new implementation using configuration option names
as strings and values as integer, string, or string list. Example::

    if (PyInitConfig_SetInt(config, "dev_mode", 1) < 0) {
        goto error;
    }

The Python initialization is a complex beast. How to allocate memory
when the memory allocator is not configured yet? Which encoding should
be used, knowing that the locale encoding is not configured yet?

I started with wide string (``wchar_t*``) and bytes string (``char*``).
The bytes strings should be decoded from the locale encoding which
requires to preinitialize Python to configure the locale encoding.

Getter functions
----------------

I was asked to add getter functions such as ``PyInitConfig_GetInt()``
and ``PyInitConfig_GetStr()``.

Current configuration
---------------------

I was also asked to add functions to get the current runtime
configuration. I proposed the following API::

    int PyConfig_GetInt(const char *key, int64_t *value);
    int PyConfig_GetStr(const char *key, PyObject **value);
    int PyConfig_GetStrList(const char *key, PyObject **value);

* Raise ``ValueError`` if the key doesn't exist.
* Raise ``TypeError`` if it's the wrong type.
* ``PyConfig_GetInt()`` raises OverflowError if the value doesn’t fit
  into ``int64_t``. It cannot happen with the current implementation.

I wrote `an implementation
<https://github.com/python/cpython/pull/112609>`_ to play with the API.


Custom options
--------------

With my proposed ``PyInitConfig`` API, we can accept custom options and
store them in a separated hash table, and later expose them as a dict.

Example::

    PyInitConfig_SetInt("accept_custom_options", 1);
    PyInitConfig_SetStr("my_custom_key", "value");

And later retrieve it in Python::

    my_custom_key = sys.get_config()['my_custom_key']  # str


January 2024: Create PEP 741
============================

In January 2024, I decide to write `PEP 741 – Python Configuration C API
<https://peps.python.org/pep-0741/>`__ since it became
difficult to follow the discussion which has a long history (since
August 2022). I `announced PEP 741
<https://discuss.python.org/t/pep-741-python-configuration-c-api/43637>`_
and the discussion continued there.

Specification
-------------

First proposed API.

C API:

* ``PyInitConfig`` structure
* ``PyInitConfig_Python_New()``
* ``PyInitConfig_Isolated_New()``
* ``PyInitConfig_Free(config)``
* ``PyInitConfig_SetInt(config, name, value)``
* ``PyInitConfig_SetStr(config, name, value)``
* ``PyInitConfig_SetWStr(config, name, value)``
* ``PyInitConfig_SetStrList(config, name, length, items)``
* ``PyInitConfig_SetWStrList(config, name, length, items)``
* ``Py_InitializeFromInitConfig(config)``
* ``PyInitConfig_Exception(config)``
* ``PyInitConfig_GetError(config, &err_msg)``
* ``PyInitConfig_GetExitCode(config, &exitcode)``
* ``Py_ExitWithInitConfig(config)``
* ``PyConfig_Get(name)``
* ``PyConfig_GetInt(name, &value)``

Python API:

* ``sys.get_config(name)``

Discussions
-----------

It was proposed to switch to UTF-8 for strings, instead of using the
locale encoding.

It was asked to not add PEP 741 API to the limited C API, whereas it has
been asked by multiple users.

It was asked to get rid of the preinitialization which causes tricky
implementation issues with the locale encoding and the memory allocator.


February 2024: Second version of PEP 741
========================================

Second version
--------------

In February 2024, I wrote a major second version:
`PEP 741: Python Configuration C API (second version)
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403>`_.

* Use UTF-8 for strings, instead of the locale encoding.
* Add locale encoding strings, such as ``PyInitConfig_SetStrLocale()``.
  So the API now has 3 kinds of strings.
* Remove support for custom configuration options.

API to set the current runtime configuration
--------------------------------------------

I decided to add ``PyConfig_Set()`` to **set** configuration options at
runtime:

* Return ``0`` on success.
* Set an error in config and return ``-1`` on error.

The problem was to decide which options should be read-only and which
options can be modified.

I decided to allow modifying options which can already be modified with
an existing API. For example, the ``argv`` option is read from
``sys.argv`` which can modified. So this option can be modified with
``PyConfig_Set()``.

I also decided to allow modifying some ``sys.flags`` flags, but not
all of them. For example, it becomes possible to modify
``bytes_warning`` which gets ``sys.flags.bytes_warning``.



April 2024: Steering Council feedback
=====================================

In April 2024, the Steering Council wrote that `they had is having a
tough time evaluating PEP 741
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403/38>`_.

Their main concerns were:

* The number of string types (3).
* The stable ABI.
* The locale encoding.


May 2024: Third PEP version
===========================

I `rewrote PEP 741 (3rd major version)
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403/62>`_
to make it the most likely to be accepted the Steering Council:

* Remove string types other than UTF-8 (1 string type instead of 3).
* Exclude the API from the limited C API.
* Remove the explicit preconfiguration.
* Remove the rationale about the limited C API / stable ABI.
* Remove the "Python Configuration", only keep the "Isolated
  Configuration".


August 2024: PEP approved
=========================

In August 2024, the Steering Council eventually `accepted PEP 741
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403/88>`_.

Once it was approved, I merged PEP 741 implementation. It's now
available for testing in the future Python 3.14 version!


Example
=======

It becomes possible to modify some ``sys.flags`` which were read-only
previously. Example on Python 3.14 using the ``_testcapi`` (which must
not be used in production, using for testing!)::

    $ ./python
    >>> import sys
    >>> import _testcapi

    # BytesWarning is disabled by default
    >>> b'bytes' == 'unicode'
    False
    >>> _testcapi.config_get('bytes_warning')
    0
    >>> sys.flags.bytes_warning
    0

    # Set bytes_warning option
    >>> _testcapi.config_set('bytes_warning', 1)
    >>> _testcapi.config_get('bytes_warning')
    1
    >>> sys.flags.bytes_warning
    1

    # Comparison now emits BytesWarning
    >>> b'bytes' == 'unicode'
    <python-input-8>:1: BytesWarning: Comparison between bytes and string
      b'bytes' == 'unicode'
    False


Statistics
==========

Statistics on Discourse threads:

* First thread: 62 messages
* Second thread: 55 messages
* Third thread: 89 messages

Total: **206** messages!
