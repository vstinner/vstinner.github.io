++++++++++++++++++++++++
Traps in the C languages
++++++++++++++++++++++++

I really like the C language: it's close to hardware, it's very efficient, it's
very portable, etc. BUT there are traps which take time to learn, sometimes the
hard way.

UB: Undefined Behaviour
=======================

* `What Every C Programmer Should Know About Undefined Behavior #1/3
  <http://blog.llvm.org/2011/05/what-every-c-programmer-should-know.html>`_
* `What Every C Programmer Should Know About Undefined Behavior #2/3
  <http://blog.llvm.org/2011/05/what-every-c-programmer-should-know_14.html>`_
* `What Every C Programmer Should Know About Undefined Behavior #3/3
  <http://blog.llvm.org/2011/05/what-every-c-programmer-should-know_21.html>`_

UB: Compiler optimization, NULL
-------------------------------


* `Fun with NULL pointers, part 1 <https://lwn.net/Articles/342330/>`_
* `Fun with NULL pointers, part 2 <https://lwn.net/Articles/342420/>`_

UB: Compiler optimization, memset
---------------------------------

For security, memset() can be used to clear memory storing sensitive
information like a password or a secret key. The compiler can decide to remove
memset() if the call is done on the stack memory and the compiler understands
that the memory is no more accessible at the function exit.

Aliasing
========

* strict aliasing

https://hg.python.org/cpython/rev/2f0289c5ee73 fixed a crash on non-Intel
architectures.

