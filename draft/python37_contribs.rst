time.time_ns(): PEP 564
=======================

Article: `Python 3.7 nanoseconds (PEP 564) <{filename}/nanoseconds.rst>`_.

Script::

    import math
    import time

    LOOPS = 10 ** 6

    min_dt = [abs(time.time_ns() - time.time_ns())
              for _ in range(LOOPS)]
    min_dt = min(filter(bool, min_dt))
    print("min time_ns() delta: %s ns" % min_dt)

    min_dt = [abs(time.time() - time.time())
              for _ in range(LOOPS)]
    min_dt = min(filter(bool, min_dt))
    print("min time() delta: %s ns" % math.ceil(min_dt * 1e9))

Output::

    $ python3.7 x.py
    min time_ns() delta: 72 ns
    min time() delta: 239 ns

The ``time.time_ns()`` effective resolution measured in Python is **3.3x
better** than ``time.time()`` resolution.

New UTF-8 Mode
==============

With POSIX and C locales, something as basic as displaying non-ASCII characters
with ``print()`` fails on Python 2.7 and 3.6, but now works "as expected" on
Python 3.7 thanks to the UTF-8 Mode::

    $ LC_ALL=C python2.7 -c 'print(u"Unicode! \xe9\u20ac")'
    UnicodeEncodeError: 'ascii' codec can't encode ...

    $ LC_ALL=C python3.6 -c 'print(u"Unicode! \xe9\u20ac")'
    UnicodeEncodeError: 'ascii' codec can't encode ...

    $ LC_ALL=C python3.7 -c 'print(u"Unicode! \xe9\u20ac")'
    Unicode! é€

Using the UTF-8 Mode, UTF-8 is now used everywhere::

    $ python3.7 -X utf8
    >>> import locale; locale.getpreferredencoding()
    'UTF-8'
    >>> with open("/etc/passwd") as fp: print(fp.encoding)
    UTF-8
    >>> sys.stdin.encoding, sys.stdin.errors
    ('utf-8', 'surrogateescape')
    >>> sys.stdout.encoding, sys.stdout.errors
    ('utf-8', 'surrogateescape')

The UTF-8 Mode use the ``surrogateescape`` error handler for stdin and stdout
to `passthough undecodable bytes
<https://www.python.org/dev/peps/pep-0540/#passthough-for-undecodable-bytes-surrogateescape>`_.

To explain the benefit, let's create a ``testdir/`` directory which contains a
filename which cannot be decoded from UTF-8::

    $ mkdir testdir
    $ python3 -c 'open(b"testdir/nonascii\xff", "w").close()'

Python 2.7 is able to list the content of the directory, whereas Python 3.6 and
3.7 fail::

    $ python2.7 -c 'import os; print(os.listdir(u"testdir")[0])'
    nonascii�

    $ python3.6 -c 'import os; print(os.listdir("testdir")[0])'
    UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' ...

    $ python3.7 -c 'import os; print(os.listdir("testdir")[0])'
    UnicodeEncodeError: 'utf-8' codec can't encode character '\udcff' ...

In the UTF-8 Mode, Python 3.7 "just works" as Python 2.7::

    $ python3.7 -X utf8 -c 'import os; print(os.listdir("testdir")[0])'
    nonascii�

It doesn't fail with an hard Unicode error, but it produces mojibake. If you
are used to Unix command line tools, like ``cat`` or ``grep``, and most Python
2 applications, this behaviour should not surprise you.

Moreover, in these examples, Python 2.7 is cheating: it returns the filename as
a byte string, whereas we asked for Unicode. It can cause issues if the caller
really expects Unicode. Python 3.7 in UTF-8 Mode is more reliable since
listdir() always returns filenames as Unicode::

    # Python 2: ask Unicode, get bytes - WRONG
    $ python2.7 -c 'import os; print(type(os.listdir("testdir")[0]))'
    <type 'str'>

    # Python 2: ask Unicode, get Unicode - OK
    $ python3.7 -X utf8 -c 'import os; print(type(os.listdir("testdir")[0]))'
    <class 'str'>


Development mode, -X dev
========================

https://docs.python.org/dev/using/cmdline.html#id5
``-X dev`` documentation::

   Enable CPython's "development mode", introducing additional
   runtime checks which are too expensive to be enabled by default. It should
   not be more verbose than the default if the code is correct: new warnings
   are only emitted when an issue is detected. Effect of the developer mode:

     * Add ``default`` warning filter, as :option:`-W` ``default``.
     * Install debug hooks on memory allocators: see the
       :c:func:`PyMem_SetupDebugHooks` C function.
     * Enable the :mod:`faulthandler` module to dump the Python traceback
       on a crash.
     * Enable :ref:`asyncio debug mode <asyncio-debug-mode>`.
     * Set the :attr:`~sys.flags.dev_mode` attribute of :attr:`sys.flags` to
       ``True``

Example with Python 3.7::

    $ python3.7 -m venv ENV
    $ ENV/bin/python -m pip install tox
    Collecting tox
      Using cached tox-2.9.1-py2.py3-none-any.whl
    Collecting six (from tox)
      Using cached six-1.11.0-py2.py3-none-any.whl
    Collecting pluggy<1.0,>=0.3.0 (from tox)
      Using cached pluggy-0.6.0.tar.gz
    Collecting py>=1.4.17 (from tox)
      Downloading py-1.5.3-py2.py3-none-any.whl (84kB)
        100% |████████████████████████████████| 92kB 740kB/s
    Collecting virtualenv>=1.11.2; python_version != "3.2" (from tox)
      Downloading virtualenv-15.2.0-py2.py3-none-any.whl (2.6MB)
        100% |████████████████████████████████| 2.6MB 282kB/s
    Installing collected packages: six, pluggy, py, virtualenv, tox
      Running setup.py install for pluggy ... done
    Successfully installed pluggy-0.6.0 py-1.5.3 six-1.11.0 tox-2.9.1 virtualenv-15.2.0

No warning, everything is fine, right? New try using the new development mode::

    $ python3.7 -X dev -m venv ENV
    $ ENV/bin/python -X dev -m pip install tox
    ENV/lib/python3.8/site-packages/pip/_vendor/urllib3/util/selectors.py:14: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated, and in 3.8 it will stop working
      from collections import namedtuple, Mapping
    (...)
    Installing collected packages: virtualenv, six, pluggy, py, tox
    ENV/lib/python3.8/site-packages/pip/wheel.py:229: DeprecationWarning: This method will be removed in future versions.  Use 'parser.read_file()' instead.
      cp.readfp(data)
      Running setup.py install for pluggy ... done
    ENV/lib/python3.8/site-packages/pip/req/req_install.py:878: ResourceWarning: unclosed file <_io.BufferedReader name=4>
      spinner=spinner,
    (...)
    Successfully installed pluggy-0.6.0 py-1.5.3 six-1.11.0 tox-2.9.1 virtualenv-15.2.0

Uh oh: there are two different deprecation warnings and it's written that the
code will break in Python 3.8. Maybe it's time to upgrade the code the newer
API.

Moreover, there is a ``ResourceWarning`` about an unclosed file which can cause
issues on Windows or PyPy. Closing explicitly the file would prevent potential
bugs.

