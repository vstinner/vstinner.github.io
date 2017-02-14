+++++++++++++++++++++++++++++++++++++++++
PEP 524: os.urandom() now blocks on Linux
+++++++++++++++++++++++++++++++++++++++++

:date: 2017-02-14 12:00
:tags: cpython
:category: python
:slug: pep-524-os-urandom-blocking
:authors: Victor Stinner

getrandom() avoids file descriptors
-----------------------------------

Last years, I'm making sometimes enhancements in the Python code used to
generate random numbers, the C implementation of ``os.urandom()``. My main two
changes were to use the new ``getentropy()`` and ``getrandom()`` functions when
available on Linux, Solaris, OpenBSD, etc.

In 2013, ``os.urandom()`` opened a file descriptor to read from
``/dev/urandom`` and then closed it. It was decided to use a single private
file descriptor and keep it open to prevent ``EMFILE`` or ``ENFILE`` errors
(too many open files) under high system loads with many threads: see the issue
#18756.

The private file descriptor introduced a backward incompatible change in badly
written programs. The code was modified to call ``fstat()`` to check if the
file descriptor was closed and replaced with a different file descriptor (check
if ``st_dev`` or ``st_ino`` changed).

The Linux kernel 3.17 added a new ``getrandom()`` syscall which gives access to
random bytes without having to handle a file descriptor. I modified
``os.urandom()`` to call ``getrandom()`` to avoid file descriptors, but a
different issue appeared.

On embedded devices and virtual machines, Python hangs at startup. On Debian, a
systemd script used Python to compute a MD5 checksum, but Python startup
blocked. Python was waiting until the system urandom pool is initialized with
enough entropy which took longer than 90 seconds, the systemd timeout. As a
consequence, system boot takes longer than 90 seconds or can even fail!

getrandom() hangs at system startup
-----------------------------------

The fix was obvious: call ``getrandom(GRND_NONBLOCK)`` which fails immediately
if the call would block, and fall back on reading /dev/urandom which doesn't
block even if the entropy pool is not initialized yet.

Quickly, our security experts complained that falling back on ``/dev/urandom``
makes Python less secure because it returns random number even if the system
didn't collect enough entropy. Using ``getrandom()`` in blocking mode for
``os.urandom()`` makes Python more secure.

Discussion storm
----------------

The proposed change started a huge rain of messages. More than 200 messages,
maybe even more than 500 messages on the bug tracker and python-dev mailing
list. Everyone became a security expert and wanted to give his/her very
important opinion, without listening to other arguments.

Christian Heimes and Donald Stufft, real security expert, left the discussion,
and even quitted temporarely the Python community.

I stopped to read new messages. I was simply enable to read all of them, and
the discussion made me angry.

New mailing list and two new PEPs
---------------------------------

A new ``security-sig`` mailing list, subtitled "os.urandom rehab clinic", was
created just to fix the issue!

Nick Coghlan wrote the `PEP 522: Allow BlockingIOError in security sensitive
APIs <https://www.python.org/dev/peps/pep-0522/>`_. Basically: he considers
that there is no good default behaviour when ``os.urandom()`` would block, so
raise an exception to let users decide.

I wrote  `PEP 524: Make os.urandom() blocking on Linux
<https://www.python.org/dev/peps/pep-0524/>`_. My PEP proposes to make
``os.urandom()`` blocking, *but* modify Python startup to fall back on
non-blocking RNG to initialize the secret hash seed and the ``random`` module
(which is *not* security sensitive).

Nick exposes a concrete use case: be able to check if ``os.urandom()`` would
block. Instead of adding a flag to ``os.urandom()`` or change ``os.urandom()``
behaviour, I chose to expose the low-level C ``getrandom()`` function as a
Python ``os.getrandom()`` function. Calling ``os.getrandom(os.GRND_NONBLOCK,
1)`` raises a ``BlockingIOError`` exception, as Nick proposed for
``os.urandom()``, so it's possible to decide what to do in this case.

While both PEPs are valid, my PEP was *less* backward incompatible, simpler and
maybe closer to what users *expect*. The special case "os.urandom() would
block" is special with my PEP, but my PEP allows to decide what to do in that
case.

Guido van Rossum approved my PEP and rejected Nick's PEP.

Final change
------------

First, I added a new ``os.getrandom()`` function: expose the Linux
``getrandom()`` syscall (issue #27778). I also added the two getrandom() flags:
os.GRND_RANDOM and os.GRND_NONBLOCK.

Second, I modified ``os.urandom()`` to block on Linux: call ``getrandom(0)``
instead of ``getrandom(GRND_NONBLOCK)`` (issue #27776). I also added a private
``_PyOS_URandomNonblock()`` function used to initialize the hash secret and
used by ``random.Random.seed()`` (and so to initialize the ``random`` module).

The ``os.urandom()`` function now blocks on Linux 3.17 and newer until the
system urandom entropy pool is initialized to increase the security.

Read also LWN articles
----------------------

* `A system call for random numbers: getrandom()
  <https://lwn.net/Articles/606141/>`_ (July 2014)
* `Python's os.urandom() in the absence of entropy
  <https://lwn.net/Articles/693189/>`_ (July 2016)
* `The long road to getrandom() in glibc
  <https://lwn.net/Articles/711013/>`_ (January 2017)
