* GC bug 1: https://bugs.python.org/issue40149 _abc._abc_data type has no traverse func
* GC bug 2: https://github.com/python/cpython/commit/6104013838e181e3c698cb07316f449a0c31ea96 _thread.Lock has no traverse func
* GC bug:

  * https://github.com/python/cpython/commit/11ef53aefbecfac18b63cee518a7184f771...
  * https://bugs.python.org/issue42866

* GC bug 3: https://bugs.python.org/issue40217 all types need a traverse function and visit the type
* GC bug 4: https://bugs.python.org/issue42972 instances must be tracked

  * original email: https://mail.python.org/archives/list/python-dev@python.org/thread/C4ILXGPKBJQYUN5YDMTJOEOX7RHOD4S3/

* Python no longer leaks memory at exit: https://mail.python.org/archives/list/python-dev@python.org/thread/E4C6TDNVDPDNNP73HTGHN5W42LGAE22F/
