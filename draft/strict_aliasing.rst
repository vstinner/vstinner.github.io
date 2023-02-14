Strict aliasing and type punning

https://reviews.llvm.org/rG5960a57ef79ea29f638ef9d609541fc19764880c

dtoa.c:
https://github.com/python/cpython/commit/28205b203a4742c40080b4a2b4b2dcd800716edc

* `Understanding Strict Aliasing
  <http://cellperformance.beyond3d.com/articles/2006/06/understanding-strict-aliasing.html>`_ (Mike Acton, June 1, 2006)
* `Demystifying The Restrict Keyword
  <http://cellperformance.beyond3d.com/articles/2006/05/demystifying-the-restrict-keyword.html>`_ (Mike Acton, May 29, 2006)
* `Type punning isn't funny: Using pointers to recast in C is bad.
  <https://www.cocoawithlove.com/2008/04/using-pointers-to-recast-in-c-is-bad.html>`_
  (April, 2008) by Matt Gallagher

Magic ``UNION_CAST()`` macro::

   #define UNION_CAST(x, destType) \
      (((union {__typeof__(x) a; destType b;})x).b)
