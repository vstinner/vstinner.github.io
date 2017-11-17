+++++++++++++++
Python Security
+++++++++++++++

:date: 2017-09-15 22:00
:tags: security, python
:category: python
:slug: python-security
:authors: Victor Stinner

I am working on the Python security for years, but I never wrote anything about
that. Let's fix this!

PSRT
====

I am part of the Python Security Response Team (PSRT): I get emails sent to
security@python.org. I try to analyze each report to validate that the bug
is reproductible, find impacted Python versions and start to discuss how to fix
the vulnerability. In some cases, the reported issue is not a security
vulnerability, is not related to CPython, or sometimes is already fixed.  We
also get reports about CPython, but also the web sites and other projects
related to Python.

Warning: I don't represent the PSRT, I speak for my own!


Vulnerabilities sent to PSRT
============================

In this article, I will focus on vulnerabilities impacting CPython: the C and
Python code of CPython core and the standard library.

When vulnerabilities are obvious bugs, they are quickly fixed. Done.

But it's not uncommon that fixing a vulnerability impacts the backward
compatibility which is a major concern of CPython core developers. There is
also a risk of rejecting legit input data because the added checks are too
strict. We have to be very careful and so fixing vulnerabilities can take
weeks, if not months in the worst case.

While CPython has few active core developers, the PSRT has even lesser active
members to handle incoming reports. We are volunteers, so please be kind and
patient...


Example of a complex fix
========================

The `urllib FTP protocol stream injection
<https://python-security.readthedocs.io/vuln/urllib_ftp_protocol_stream_injection.html>`_
vulnerability was reported to the PSRT at 2016-01-15. The fix was only merged
at 2017-07-26.

First, it was not obvious how the vulnerability can be exploited, nor if it
should be fixed.

Then it was not obvious if the vulnerability should be fixed in the urllib
module or in the ftplib module.

Even if the bug was public, it didn't get much attention. Since I don't know
well how the urllib module, I wrote an email to the python-dev mailing
list: `Need help to fix urllib(.parse) vulnerabilities
<https://mail.python.org/pipermail/python-dev/2017-July/148699.html>`_.

I proposed a fix for the urllib module: `Reject newline character (U+000A) in
URLs in urllib.parse <https://bugs.python.org/issue30713>`_. But it was
rejected, since it was the wrong approach and my checks were too strict in many
cases (rejected legit requests).

The final fix rejects ``\b`` and ``\r`` newline characters in the putline()
method of the ftplib module.


Track known and fixed CPython vulnerabilities
=============================================

Currently, not least that six branches still get security fixes!

* Python 2.7
* Python 3.3
* Python 3.4
* Python 3.5
* Python 3.6
* master: the development branch

Last year, I added a table to the Python developer guide to help me to track
the status of each branch: see the `Status of Python branches
<https://devguide.python.org/#status-of-python-branches>`_.

This year, I created a tool to help me to track known CPython vulnerabilities:
`python-security project <https://github.com/vstinner/python-security>`_ (hosted
at GitHub). The `vulnerabilities.yaml file
<https://github.com/vstinner/python-security/blob/master/vulnerabilities.yaml>`_
is a YAML file with one section per vulnerability. Each vulnerability has
a title, link to the Python bug, disclosure date, reported date, commits, etc.

The tool gets the date of commits and the Git tags which contains the commit
to infer the first Python versions of each branch which contain the fix. It
also build a timeline to help to understand how the vulnerability was handled.

I also wanted to be more transparent on how we handle vulnerabilities and our
velocity to fix them.

Honestly, I was disappointed that it took so long to fix some vulnerabilities
in the past. Hopefully, it seems like we are more reactive nowadays!


Example of a fixed vulnerability
================================

Example: `CVE-2016-5699: HTTP header injection
<https://python-security.readthedocs.io/vuln/cve-2016-5699_http_header_injection.html>`_.

Right now, Python 3.3 is still vulnerable (my fix was commited, I am now
waiting Python 3.3.7 which is coming at the end of september).

Since the vulnerability was reported, it took 108 days to merge the fix, 72
more days (total 180 days) for the first release including the fix (Python
2.7.10).

Sadly, the PSRT doesn't compute a severity of vulnerabilities yet.

Hopefully, for this vulnerability, web frameworks were able to workaround the
vulnerability by input sanitization.


Backport all fixes
==================

Last months, I backported fixes to the six branches which still accept security
fixes, to respect the contract with our users: we are doing our best to protect
you!

The good news is that with Python 2.7.14 and Python 3.3.7 releases scheduled
this month, all major security vulnerabilities will be fixed in all maintained
Python branches!

Some fixes were not backported on purpose. For example, the `CVE-2013-7040:
Hash not properly randomized
<https://python-security.readthedocs.io/vuln/cve-2013-7040_hash_not_properly_randomized.html#cve-2013-7040-hash-not-properly-randomized>`_
vulnerability requires to change the hash algorithm and we decided to not touch
Python 2.7 and 3.3 for backward compatibility reasons (don't break code relying
on the exact hash function). The issue was fixed in Python 3.4 by using the
SipHash hash algorithm which uses a hash secret (generated randomly by Python
at startup).


Python security documentation
=============================

Last months, I also started to collect random notes about the Python security.

Explore my `python-security.readthedocs.io
<https://python-security.readthedocs.io/>`_ documentation and send me feedback!
