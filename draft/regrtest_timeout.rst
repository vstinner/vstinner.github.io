* 2011-03-31: https://bugs.python.org/issue11727
  https://hg.python.org/cpython/rev/bdc946dc512a
* 15 min by default: https://hg.python.org/cpython/rev/15f6fe139181
* 30 min by default: https://hg.python.org/cpython/rev/053bc5ca199b
* no default: https://hg.python.org/cpython/rev/394f0ea0d29e

* faulthandler uses pthread_sigmark to fix test_sendall_interrupted() of test_socket
  https://bugs.python.org/issue11753#msg132921

* signal_handler() is not reentrant: deadlock in Py_AddPendingCall()
  https://bugs.python.org/issue11768
