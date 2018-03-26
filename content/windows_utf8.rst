++++++++++++++++++++++++++++++++++++
Python 3.6 now uses UTF-8 on Windows
++++++++++++++++++++++++++++++++++++

:date: 2018-03-22 17:00
:tags: cpython
:category: python
:slug: python36-utf8-windows
:authors: Victor Stinner

September 2016, a few days before the CPython core dev sprint, **Steve Dower**
proposed two major backward incompatible changes for Python 3.6 on Windows:
`PEP 528: Change Windows console encoding to UTF-8
<https://www.python.org/dev/peps/pep-0528/>`_ and `PEP 529: Change Windows
filesystem encoding to UTF-8 <https://www.python.org/dev/peps/pep-0529/>`_.
At the first read, I was sure that the PEP 529 will break all applications on
Windows. This article tells the story behind the PEPs approval.

**This article is the fourth in a series of articles telling the history and
rationale of the Python 3 Unicode model for the operating system:**

* 1. `Python 3.0 listdir() Bug on Undecodable Filenames <{filename}/python30_listdir.rst>`_
* 2. `Python 3.1 surrogateescape error handler (PEP 383) <{filename}/pep383.rst>`_
* 3. `Python 3.2 Painful History of the Filesystem Encoding <{filename}/fs_encoding.rst>`_
* 4. `Python 3.6 now uses UTF-8 on Windows <{filename}/windows_utf8.rst>`_
* 5. `Python 3.7 and the POSIX locale <{filename}/posix_locale.rst>`_
* 6. `Python 3.7 UTF-8 Mode <{filename}/utf8_mode.rst>`_

PEP 529
=======

September 2016, **Steve Dower**, who works for Microsoft, wrote the `PEP 529:
Change Windows filesystem encoding to UTF-8
<https://www.python.org/dev/peps/pep-0529/>`_ and `posted it to python-dev
<https://mail.python.org/pipermail/python-dev/2016-September/146051.html>`_ for
comments.

.. image:: {filename}/images/steve_dower.jpg
   :alt: Steve Dower
   :target: http://stevedower.id.au/blog/

Abstract:

    **Historically, Python uses the ANSI APIs** for interacting with the
    Windows operating system, often via C Runtime functions. However, these
    have been long discouraged in favor of the UTF-16 APIs. Within the
    operating system, all text is represented as UTF-16, and the ANSI APIs
    perform encoding and decoding using the active code page. See Naming Files,
    Paths, and Namespaces for more details.

    This PEP proposes **changing the default filesystem encoding on Windows to
    utf-8**, and changing all filesystem functions to use the Unicode APIs for
    filesystem paths. This will not affect code that uses strings to represent
    paths, however those that use bytes for paths will now be able to correctly
    round-trip all valid paths in Windows filesystems. **Currently, the
    conversions between Unicode (in the OS) and bytes (in Python) were lossy**
    and would fail to round-trip characters outside of the user's active code
    page.

    Notably, this does not impact the encoding of the contents of files. These
    will continue to default to ``locale.getpreferredencoding()`` (for text
    files) or plain bytes (for binary files). This only affects the encoding
    used when users pass a bytes object to Python where it is then passed to
    the operating system as a path name.

My analysis
===========

Here is my analysis on the rationale for the PEP 529 change.

**On Unix, the native type for filenames is bytes**. A filename is seen by the
Linux kernel as an opaque object. The ext4 filesystem stores filenames as
bytes. If a Python 2 application uses Unicode for filenames, filesystem
operations can fail with a Unicode error (encoding or decoding error) depending
on the locale encoding. If the locale encoding is ASCII, Unicode errors are
likely to occur at the first non-ASCII filename. For example, Mercurial handles
filenames as bytes.

On Python 3, handling filenames as Unicode works thanks to the
``surrogateescape`` error handler. **Most Python 2 applications ported to
Python 3 keep their Python 2 support, and so still handle filenames bytes.**

Problems arise when such software is used on Windows.

**On Windows, the native type for filenames is Unicode**. Many functions come
in two flavors: "ANSI" (bytes) and "Wide" (Unicode) versions. In my opinion,
the ANSI flavor mostly exists for backward compatibility. In Python 3.5,
passing a filename as bytes uses the ANSI flavor, whereas the Wide flavor is
used for Unicode filenames. The ANSI flavor uses the ANSI code page which is
very limited compared to Unicode, usually only 256 code points or less. Some
filenames not encodable to the ANSI code page simply cannot be opened, renamed,
etc. using the ANSI API.

The other issue is that **some developers only develop on Unix** (ex: Linux or
macOS) **and never test their application on Windows**.

For a better rationale, read the `Background section
<https://www.python.org/dev/peps/pep-0529/#background>`_ of Steve Dower's PEP
:-)

Discussion at the CPython sprint and Guido's approval
=====================================================

Honestly, **at the first read, I was sure that the PEP 529 will break all
applications on Windows**.

Hopefully, thanks to the PSF and Instagram, I was able to attend my first
CPython sprint at Instagram headquarters: `CPython sprint, september 2016
<{filename}/cpython_sprint_2016.rst>`_. I discussed there with **Steve who
reassured me and explained me his PEP**. Later, we talked with **Guido van
Rossum**.

Even if I liked the idea of using UTF-8, I was still not fully confident that the
change will not break the world. **We agreed to try the change during Python
3.6 beta phase**, but revert it if something bad happens.

.. image:: {filename}/images/cpython_sprint_2016_photo.jpg
   :alt: CPython developers at the Facebook sprint
   :target: http://blog.python.org/2016/09/python-core-development-sprint-2016-36.html

Following this talk, `Guido accepted the PEP under conditions
<https://mail.python.org/pipermail/python-dev/2016-September/146277.html>`_

    I'm hijacking this thread to **provisionally accept PEP 529**. (I'll also
    do this for PEP 528, in its own thread.)

    **I've talked things over with Steve and Victor and we're going to do an
    experiment** (as `now written up in the PEP
    <https://www.python.org/dev/peps/pep-0529/#beta-experiment>`_) to tease out
    any issues with this change during the beta. **If serious problems crop up
    we may have to roll back the changes and reject the PEP** -- we won't get
    another chance at getting this right. (That would also mean that using the
    binary filesystem APIs will remain deprecated and will eventually be
    disallowed; as long as the PEP remains accepted they are undeprecated.)

    Congrats Steve! Thanks for the massive amount of work on the
    implementation and the thinking that went into the design. Thanks
    everyone else for their feedback.

    --Guido

**I was honoured that Guido listened to my Unicode experience** to take a
decision on the PEP ;-)

Steve chose the right timing to get his PEP accepted. Thanks to the sprint
which helped to quickly discussed such backward incompatible change, **the PEP
has been approved in just 12 days**! For comparison, some of my PEPs like my
`PEP 446: Make newly created file descriptors non-inheritable
<https://www.python.org/dev/peps/pep-0446/>`_ (another backward incompatible
change) took 8 months to get accepted.

PEP 528: Windows console
========================

Just before the PEP 529, Steve Dower also wrote `PEP 528: Change Windows
console encoding to UTF-8 <https://www.python.org/dev/peps/pep-0528/>`_.  This
change only impacts the Windows console, so there is a lower risk of breaking
the world.

This PEP was also `quickly approved by Guido
<https://mail.python.org/pipermail/python-dev/2016-September/146278.html>`_
during the CPython sprint.  Steve implemented it in Python 3.6.

Even if it's smaller change, it is **yet another change towards using UTF-8
everywhere**.

Great success!
==============

Hopefully, I was wrong about the risk of breaking the world. **No user
complained about these two backward incompatible changes: Python 3.6 on Windows
is a success!**

Python 3.6 now has a **better Unicode support** on Windows thanks to the PEP
528 and PEP 529!


Conclusion
==========

September 2016: Steve Dower proposed two major backward incompatible changes
for Python 3.6 on Windows: `PEP 528: Change Windows console encoding to UTF-8
<https://www.python.org/dev/peps/pep-0528/>`_ and `PEP 529: Change Windows
filesystem encoding to UTF-8 <https://www.python.org/dev/peps/pep-0529/>`_.

At the first read, I was sure that the PEP 529 (filesystem encoding) will break
all applications on Windows.

Thanks to the CPython core dev sprint, I was able to discuss with Steve who
reassured me and explained me his PEP 529. We agreed with Guido van Rossum to
try the change during Python 3.6 beta phase, but revert it if something bad
happens. I was honoured that Guido listened to my Unicode experience to take a
decision on the PEP.

The `PEP 528: Change Windows console encoding to UTF-8
<https://www.python.org/dev/peps/pep-0528/>`_ was also quickly approved,
another change towards using UTF-8 everywhere.

No user complained about these two backward incompatible changes: Python 3.6 on
Windows is a success!

Python 3.6 now has a better Unicode support thanks on Windows to the PEP 528
and PEP 529!
