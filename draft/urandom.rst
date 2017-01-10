+++++++++++++++++++
Python os.urandom()
+++++++++++++++++++

My believes in PRNG:

* Reading /dev/urandom is slow and not secure
* OpenSSL RAND_pseudo_bytes() is ultra secure, audited by millions of people,
  and is very unlikely to have any kind of bug
* Reading /dev/random is much more secure than /dev/urandom because it quickly
  blocks

Bugs:

* http://bugs.python.org/issue18756
  os.urandom() fails under high load
  => Python uses a private persistent FD, as Java does.
* Issue #26735: On Solaris, getrandom() is limited to returning up to 1024
  bytes. Call it multiple times if more bytes are requested.
* http://bugs.python.org/issue21207
  urandom persistent fd - not re-openned after fd close
* PEP 524:
  https://lwn.net/Articles/693189/

OpenSSL RAND_pseudo_bytes() bugs:

* 2011: OpenSSL fork(), two processes with the same pid geneates the same
  "random" number sequences. Bug reported to OpenSSL, Ruby, Exim, Python, etc.
  "Is is a bug or a feature?". Feature? Really? The truth is that fixing the
  issue would impact performances and OpenSSL is not strong sources of entropy.
  http://www.openwall.com/lists/oss-security/2013/04/12/3
  https://bugs.python.org/issue18747
  https://bugs.ruby-lang.org/issues/4579
  https://lists.exim.org/lurker/message/20130402.171710.92f14a60.fi.html
  Status in 2017: not fixed yet?
* 2013, Android: "Improper initialization of the underlying PRNG":
  https://android-developers.googleblog.com/2013/08/some-securerandom-thoughts.html
* 2008, Debian: very weak seed, 2^16 possible seeds.
  https://www.debian.org/security/2008/dsa-1571

Intel RNG instruction.
