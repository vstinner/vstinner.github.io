+++++++++++++++++++++++++++++
Debug a Python reference leak
+++++++++++++++++++++++++++++

:date: 2022-11-04 13:00
:tags: refleak, cpython
:category: cpython
:slug: debug-python-refleak
:authors: Victor Stinner

.. image:: {static}/images/refleak.jpg
   :alt: Childhood memories in the countryside
   :target: https://twitter.com/djamilaknopf/status/1587441869403099136

This morning, I got `this email
<https://mail.python.org/archives/list/buildbot-status@python.org/message/MU2EJRTFF4ZCYTDXYER7KCL3IQUM5F3T/>`_
from the buildbot-status mailing list:

    The Buildbot has detected a new failure on builder PPC64LE Fedora Rawhide
    **Refleaks** 3.x while building Python.

I get many of buildbot failures per month (by email), but I like to debug
reference leaks: they are more challenging :-) I decided to write this article
to document and explain my work on maintaining Python (buildbots).

I truncated most the output of most commands in this article to make it easier
to read.

Drawing: `Childhood memories in the countryside
<https://twitter.com/djamilaknopf/status/1587441869403099136>`_ by `Djamila
Knopf <https://twitter.com/djamilaknopf/>`_.


Reproduce the bug
=================

I look into `buildbot logs
<https://buildbot.python.org/all/#builders/300/builds/548>`_::

    test_int leaked [1, 1, 1] references, sum=3

Aha, interesting: the ``test_int`` test leaks Python strong references, each
test iteration leaks exactly one reference. Well, in short, it leaks memory.

I build Python to check if the refleak is still there::

    git switch main
    make clean
    ./configure --with-pydebug
    make

The main branch is currently at this commit::

    $ git show main
    commit 2844aa6a8eb1d486b5c432f0ed33a2082998f41e
    (...)

I run the test with ``-R 3:3`` to check for reference leaks::

    $ ./python -m test -R 3:3 test_int
    (...)
    test_int leaked [1, 1, 1] references, sum=3
    (...)
    Total duration: 4.8 sec

Great! It's still there, it's real regression. I told you, I love this kind of
bugs :-)

Identify which test leaks (test.bisect_cmd)
===========================================

::

    $ ./python -m test test_int --list-cases|wc -l
    42
    $ wc -l Lib/test/test_int.py
    885 Lib/test/test_int.py

``test_int`` has only 42 methods and takes 4.8 seconds to run (with ``-R
3:3``).  That's small, but the file is made of 885 lines of Python code. I'm
lazy, I don't want to read so many lines. I will use ``python -m
test.bisect_cmd`` to identify which test method leaks so I have less test code
to read and reproducing the test will be even faster.

I run ``python -m test.bisect_cmd``::

    $ ./python -m test.bisect_cmd -R 3:3 test_int
    (...)
    [+] Iteration 17: run 1 tests/2
    (...)
    test_int leaked [1, 1, 1] references, sum=3
    (...)
    * test.test_int.PyLongModuleTests.test_pylong_misbehavior_error_path_from_str

I love watching this tool doing my job, I don't have anything to do! :-)

I confirm that the ``test_pylong_misbehavior_error_path_from_str()`` test
leaks::

    $ ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    test_int leaked [1, 1, 1] references, sum=3
    Total duration: 445 ms

The ``test_pylong_misbehavior_error_path_from_str()`` method is only 17 lines
of code, it's way better than 885 lines of code (52x less code to read). And
reproducing the bug now only takes 445 ms instead of 4.8 seconds (10x faster).

At this point, there is the brave method of looking into the C code: Python is
made of 500 000 lines of C code. Good luck! Or maybe there is another way?


Git bisection
=============

Again, I'm lazy. I always begin with the "divide to conquer" method. A Git
bisection is an efficient method for that.

I start ``git bisect``::

    git bisect reset
    git bisect start --term-bad=leak --term-good=noleak
    git bisect leak  # we just saw that current commit leaks

Defining "good" and "bad" terms helps me a lot to prevent mistakes: it's a nice
Git bisect feature! In the past, I always picked the wrong one at some point
which messed up the whole bisection.

Ok, now how can I know when the leak was introduced? Well, I like to move in
the past step by step: one day, two days, one week, one month, one year, etc.

I pick a random commit merged yesterday::

    $ date
    Fri Nov  4 11:55:12 CET 2022

    $ git log
    (...)
    commit 016c7d37b6acfe2203542a2655080c6402b3be1f
    Date:   Thu Nov 3 23:21:01 2022 +0000
    (...)
    commit 4c4b5ce2e529a1279cd287e2d2d73ffcb6cf2ead
    Date:   Thu Nov 3 16:18:38 2022 -0700
    (...)

I'm not lucky at my first bet, the code already leaked yesterday::

    $ git checkout 4c4b5ce2e529a1279cd287e2d2d73ffcb6cf2ead^C
    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    test_int leaked [1, 1, 1] references, sum=3

I repeat the process, I pick a random commit the day before::

    $ git log
    (...)
    commit f3007ac3702ea22c7dd0abf8692b1504ea3c9f63
    Author: Victor Stinner <vstinner@python.org>
    Date:   Wed Nov 2 20:45:58 2022 +0100
    (...)

For my greatest pleasure, I pick a commit made by myself. Maybe I'm lucky and
I'm the one who introduced the leak :-D ::

    $ git checkout f3007ac3702ea22c7dd0abf8692b1504ea3c9f63
    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    (...)
    Tests result: NO TESTS RAN

"NO TESTS RAN" means that the test doesn't exist. Oh wait, the test didn't
exist 2 days ago? So the test itself is new? Well, no tests ran also means...
"no leak".

I will make the assumption that "NO TESTS RAN" means "no leak" and see what's
going on::

    $ git bisect noleak
    Bisecting: 13 revisions left to test after this (roughly 4 steps)

    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    Tests result: NO TESTS RAN
    $ git bisect noleak
    Bisecting: 6 revisions left to test after this (roughly 3 steps)

    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    Tests result: NO TESTS RAN
    $ git bisect noleak
    Bisecting: 3 revisions left to test after this (roughly 2 steps)

    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    Tests result: NO TESTS RAN
    $ git bisect noleak
    Bisecting: 1 revision left to test after this (roughly 1 step)

    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    test_int leaked [1, 1, 1] references, sum=3
    $ git bisect leak
    Bisecting: 0 revisions left to test after this (roughly 0 steps)

    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    test_int leaked [1, 1, 1] references, sum=3

    vstinner@mona$ git bisect leak
    4c4b5ce2e529a1279cd287e2d2d73ffcb6cf2ead is the first leak commit

    commit 4c4b5ce2e529a1279cd287e2d2d73ffcb6cf2ead
    Author: Gregory P. Smith <greg@krypto.org>
    Date:   Thu Nov 3 16:18:38 2022 -0700

        gh-90716: bugfixes and more tests for _pylong. (#99073)

        * Properly decref on _pylong import error.
        * Improve the error message on _pylong TypeError.
        * Fix the assertion error in pydebug builds to be a TypeError.
        * Tie the return value comments together.

        These are minor followups to issues not caught among the reviewers on
        https://github.com/python/cpython/pull/96673.

     Lib/test/test_int.py | 39 +++++++++++++++++++++++++++++++++++++++
     Objects/longobject.c | 15 +++++++++++----
     2 files changed, 50 insertions(+), 4 deletions(-)

In total, it took 7 ``git bisect`` steps to identify a single commit. That's
quick! I also love this tool, I feel that it does my job!

Sometimes, I mess up with Git bisection. Here, `the guilty commit
<https://github.com/python/cpython/commit/4c4b5ce2e529a1279cd287e2d2d73ffcb6cf2ead>`_
seems like a good candidate since it changes ``Objects/longobject.c`` which is
C code, so it can likely introduce a leak. Moreover, this C file is the
implementation of the Python ``int`` type, so it is directly related to
``test_int`` (the test suite of the ``int`` type).

Just in case, I test manually the the leak before/after::

    # after
    $ git checkout 4c4b5ce2e529a1279cd287e2d2d73ffcb6cf2ead
    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    test_int leaked [1, 1, 1] references, sum=3

    # before
    $ git checkout 4c4b5ce2e529a1279cd287e2d2d73ffcb6cf2ead^
    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    Tests result: NO TESTS RAN

Ok, there is no doubt anymore: the commit introduced the leak. But since the
commit also adds the leaking test, maybe the leak already existed, and it's
just that nobody noticed the leak before.

Debug the leak
==============

Since I identified the commit introducing the leak, I only have to review code
changes by this single commit. But to debug the code, I prefer to come back to
the main branch. To prepare a fix, I will have to start from the main branch
anyway.

Go back to the main branch::

    $ git bisect reset
    $ git switch main

The second command is useless, I was already at the main branch. I did some
many mistakes with Git in the past, that I took the habit of doing things very
carefully. I don't care of doing things twice, just in case. It's cheaper than
messing with the Git god! Trust me.

Just in case, I double check that the leak is still there in the main branch::

    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    test_int leaked [1, 1, 1] references, sum=3

Ok, we are good to start debugging. Let me open Lib/test/test_int.py and look
for the test_pylong_misbehavior_error_path_from_str() method::

    @support.cpython_only  # tests implementation details of CPython.
    @unittest.skipUnless(_pylong, "_pylong module required")
    @mock.patch.object(_pylong, "int_from_string")
    def test_pylong_misbehavior_error_path_from_str(
            self, mock_int_from_str):
        big_value = '7'*19_999
        with support.adjust_int_max_str_digits(20_000):
            mock_int_from_str.return_value = b'not an int'
            with self.assertRaises(TypeError) as ctx:
                int(big_value)
            self.assertIn('_pylong.int_from_string did not',
                          str(ctx.exception))

            mock_int_from_str.side_effect = RuntimeError("test123")
            with self.assertRaises(RuntimeError):
                int(big_value)

Always divide to conquer: let me try to make the code as short as possible (7
lines), I also make the "big_value" smaller::

    @mock.patch.object(_pylong, "int_from_string")
    def test_pylong_misbehavior_error_path_from_str(self, mock_int_from_str):
        big_value = '7' * 9999
        with support.adjust_int_max_str_digits(10_000):
            mock_int_from_str.return_value = b'not an int'
            with self.assertRaises(TypeError) as ctx:
                int(big_value)

Ok, so the test is about converting a long string (9999 decimal digits) to an
integer using the new ``_pylong`` module which is implemented
in pure Python (``Lib/_pylong.py``) and called from C code
(``Objects/longobject.c``). Well, I followed recent developments, so I don't
have to dig into the C code to know that. It helps!

If I search for ``_pylong`` in ``Objects/longobject.c``, I find this
interesting function::

    /* asymptotically faster str-to-long conversion for base 10, using _pylong.py */
    static int
    pylong_int_from_string(const char *start, const char *end, PyLongObject **res)
    {
        PyObject *mod = PyImport_ImportModule("_pylong");
        ...
    }

With a quick look, I don't see any obvious reference leak in this code. I add
``printf()`` to make sure that I'm looking at the right function::

    static int
    pylong_int_from_string(const char *start, const char *end, PyLongObject **res)
    {
        ...
        PyObject *s = PyUnicode_FromStringAndSize(start, end-start);
        if (s == NULL) {
            Py_DECREF(mod);
            goto error;
        }
    printf("pylong_int_from_string()\n");
        PyObject *result = PyObject_CallMethod(mod, "int_from_string", "O", s);
        ...
    }

I added the print before the int_from_string() call, since this function is
overriden by the test.

I build Python and run the test::

    $ make
    $ ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    (...)
    beginning 6 repetitions
    123456
    pylong_int_from_string()
    .pylong_int_from_string()
    .pylong_int_from_string()
    .pylong_int_from_string()
    .pylong_int_from_string()
    .pylong_int_from_string()
    (...)

Ok, I'm looking at the right place. The print happens when the test runs. So
which code path is taken?  Let me add print calls *after* the function call::

    static int
    pylong_int_from_string(const char *start, const char *end, PyLongObject **res)
    {
        ...
        PyObject *result = PyObject_CallMethod(mod, "int_from_string", "O", s);
        Py_DECREF(s);
        Py_DECREF(mod);
        if (result == NULL) {
    printf("pylong_int_from_string() error\n");   // <====== ADD
            goto error;
        }
        if (!PyLong_Check(result)) {
    printf("pylong_int_from_string() wrong type\n");   // <====== ADD
            PyErr_SetString(PyExc_TypeError,
                            "_pylong.int_from_string did not return an int");
            goto error;
        }
    printf("pylong_int_from_string() ok\n");   // <====== ADD
        ...
    }

Test output::

    ...
    pylong_int_from_string() wrong type
    .pylong_int_from_string() wrong type
    .pylong_int_from_string() wrong type
    ...

Aha, the bug should be around the ``if (!PyLong_Check(result))`` code path. Oh
wait... ``result`` is a Python object, and in this code path, the function exits
without returning ``result`` to the caller, nor removing the reference to
``result``. That's our leak!


Write a fix
===========

To write a fix, I start by reverting all local changes (remove debug traces,
restore the original test code)::

    $ git checkout .

I write a fix::

    $ git diff
    diff --git a/Objects/longobject.c b/Objects/longobject.c
    index a872938990..652fdb7974 100644
    --- a/Objects/longobject.c
    +++ b/Objects/longobject.c
    @@ -2376,6 +2376,7 @@ pylong_int_from_string(const char *start, const char *end, PyLongObject **res)
             goto error;
         }
         if (!PyLong_Check(result)) {
    +        Py_DECREF(result);
             PyErr_SetString(PyExc_TypeError,
                             "_pylong.int_from_string did not return an int");
             goto error;

I build and test my fix::

    $ make && ./python -m test -R 3:3 test_int -m test_pylong_misbehavior_error_path_from_str
    (...)
    Tests result: SUCCESS

Ok, the leak is fixed! So it was a just a missing ``Py_DECREF()`` in code
recently added to Python. It's a common mistake. By the way, when I looked at
the code the first code, I also missed this "obvious" leak.

I prepare a PR::

    $ git switch -c int_str
    $ git commit -a
    # Commit message:
    # gh-90716: Fix pylong_int_from_string() refleak

Let me validate my work from the new clean commit::

    $ make && ./python -m test -R 3:3 test_int
    (...)
    Tests result: SUCCESS

I complete the commit message using ``git commit --amend``::

    gh-90716: Fix pylong_int_from_string() refleak

    Fix validated by:

        $ ./python -m test -R 3:3 test_int
        Tests result: SUCCESS

I run ``gh_pr.sh`` (my short shell script) to create a PR from the command
line.

I add the ``skip news`` label on the PR, since this refleak is not part of any
Python release, no user is impacted. It's not worth documenting it. I don't
think that the change is part of Python 3.12 alpha 1. Moreover, only very few
users test alpha 1 releases.

Here it is, my shiny PR fixing the leak! https://github.com/python/cpython/pull/99094

Since Gregory worked on longobject.c recently, I add him in copy of my PR. I
just add the comment ``cc @gpshead`` to my PR.

I don't plan to wait for this review. The change is just one line, I'm
confident that it does fix the issue, I don't need a review.

To finish, I `reply by email to the buildbot-status failure email
<https://mail.python.org/archives/list/buildbot-status@python.org/message/J3MC7FIPFN6GNQAWQQRHE4EDLE7J2MIQ/>`_.


Conclusion
==========

In total, it took me between one and two hours to reproduce, debug and fix this
reference leak.

In the meanwhile, I also looked into other Python stuffs (and I discussed with
friends!), while the bisection was running, or during the Python build. It's
hard to estimate exactly how much time it takes me to fix a refleak.

I consider that I'm efficient on fixing such leak since I'm following the
Python development: I was already aware of the on-going ``_pylong`` work. I
also fixed many refleaks in the past.

By the way, I wrote the ``python -m test.bisect_cmd`` tool exactly to
accelerate my work on debugging reference leaks. I'm now also used to Git
bisection.

For me, **the key of my whole methodology is to "divide to conquer"**:

* Reproduce the issue
* Get a reproducer
* Make the reproducer as fast as possible and as short as possible
* Use Git bisection to identify the change introducing the change
* Add print calls to identify which parts of the code and the test are
  taken by the issue

Oh by the way, while I finished my article, my PR got reviewed and I merged it:
`my commit fixing the leak
<https://github.com/python/cpython/commit/387f72588d538bc56669f0f28cc41df854fc5b43>`_!
