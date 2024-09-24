++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
PEP 741: PyConfig C API to configure Python initialization
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:date: 2024-09-24 17:00
:tags: c-api, cpython
:category: cpython
:slug: pyconfig-pep-741
:authors: Victor Stinner

.. image:: {static}/images/regular_show.png
   :alt: Mordecai & Rigby: Regularstar Show by @ultrashroomz
   :target: https://www.youtube.com/watch?v=Zl0vC2pTIbo

Drawing: *Mordecai & Rigby: Regularstar Show by @ultrashroomz*.

August 2022
===========

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


August 2023
===========

In August 2023, I created `an issue
<https://github.com/python/cpython/issues/107954>`_ to implement
Gregory's idea. I wrote a proof-of-concept to accept configuration as
text.

Quickly, I ran into parsing issues with quotes and escaping characters
such a newline and quotes.

I decided to write a new implementation using a configuration option
name as a string and values as string or integer. Example (without error
handling)::

    if (PyInitConfig_SetInt(config, "dev_mode", 1) < 0) {
        goto error;
    }

The Python initialization is a complex beast. How to allocate memory
when the memory allocator is not configured yet? Which encoding should
be used, knowing that the locale encoding is not configured yet?

I started with wide string (``wchar_t*``) and "locale" string
(``char*``). The "locale" strings should be decoded from the locale
encoding which requires to preinitialize Python to configure the locale
encoding.


January 2024
============

In January 2024, I decide to write `PEP 741 – Python Configuration C API
<https://peps.python.org/pep-0741/#implementation>`_ since it became
difficult to follow the discussion which has a long history (since
August 2022). I `announced PEP 741
<https://discuss.python.org/t/pep-741-python-configuration-c-api/43637>`_
and the discussion continued there.

February 2024
=============

In February 2024, I wrote a major second version:
`PEP 741: Python Configuration C API (second version)
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403>`_.

* Use UTF-8 for strings.
* Add locale strings.

April 2024
==========

In April 2024, the Steering Council wrote that `they had is having a
tough time evaluating PEP 741 (Python Configuration C API)
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403/38>`_.

Their main concerns were about:

* The number of string types
* The stable ABI
* The locale encoding

I rewrote PEP 741 to make it the most likely to be accepted the Steering
Council:

* Remove the API from the stable ABI.
* Replace all string types with a single UTF-8 string format.
* Remove the preconfiguration.
* Remove the "Python Configuration", only keep the "Isolated
  Configuration".

September 2024
==============

In September 2024, the Steering Council eventually `accepted PEP 741
<https://discuss.python.org/t/pep-741-python-configuration-c-api-second-version/45403/88>`_.

Once it was approved, I merged PEP 741 implementation. It's now
available for testing in the future Python 3.14 version!

Discussions statistics
======================

* First Discourse thread: 62 messages
* Second Discourse thread: 55 messages
* Third Discourse thread: 89 messages

Total: **206** messages!
