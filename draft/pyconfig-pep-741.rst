++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
PEP 741: PyConfig C API to configure Python initialization
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2024-09-24 17:00
:tags: c-api, cpython
:category: cpython
:slug: pyconfig-pep-741
:authors: Victor Stinner

.. image:: {static}/images/starry_night_van_gogh.jpg
   :alt: The Starry Night (1889) by Vincent Van Gogh
   :target: https://en.wikipedia.org/wiki/The_Starry_Night

Painting: *The Starry Night (1889) by Vincent Van Gogh*.

August 2022: CVE-2020-10735 fix
===============================

In August 2022, Gregory P. Smith opened
`FR: Allow private runtime config to enable extending without breaking the PyConfig ABI
<https://discuss.python.org/t/fr-allow-private-runtime-config-to-enable-extending-without-breaking-the-pyconfig-abi/18004>`_
discussion to propose supporting configuration as text. Example::

    check_hash_pycs_mode=always
    unknownok:avoid_medusas_gaze=yes

The need was to add a new option to fix CVE-2020-10735. It will become
``PyConfig.int_max_str_digits`` in Python 3.12. The problem is to add
a new ``PyConfig`` member without breaking the ABI. At the end, the
problem was worked around by adding a separated global variable
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


October 2023
============

Rewrite
-------

Quickly, I ran into parsing issues with quotes and escaping characters
such a newline and quotes.

I decided to write a new implementation using a configuration option
name as a string and values as string or integer. Example::

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

These functions can fail, so an API was proposed to ignore errors::

    // Get a configuration option as an integer.
    // If configuration option `name` exists and converts successfully to a C int,
    // return the int value.
    // Otherwise, return `default_value`.
    // This never raises an exception.
    PyAPI_FUNC(int) PyConfig_GetIntOrDefault(
        const char *name,
        int default_value);


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
<https://peps.python.org/pep-0741/#implementation>`_ since it became
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

In February 2024, I wrote a major second version:
`PEP 741: Python Configuration C API (second version)
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403>`_.

* Use UTF-8 for strings, instead of the locale encoding.
* Add locale encoding strings, such as ``PyInitConfig_SetStrLocale()``.
  So the API now has 3 kinds of strings.
* Remove support for custom configuration options.


April 2024: Steering Council feedback
=====================================

In April 2024, the Steering Council wrote that `they had is having a
tough time evaluating PEP 741 (Python Configuration C API)
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403/38>`_.

Their main concerns were about:

* The number of string types (3).
* The stable ABI.
* The locale encoding.


May 2024: Third PEP version
===========================

I `rewrote PEP 741 (3rd major version)
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403/62>`_
to make it the most likely to be accepted the Steering Council:

* Remove string types other than UTF-8.
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


Discussions statistics
======================

* First Discourse thread: 62 messages
* Second Discourse thread: 55 messages
* Third Discourse thread: 89 messages

Total: **206** messages!
