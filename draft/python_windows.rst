flake8.exe: https://bugs.python.org/issue44184
    bpo-44184: Fix subtype_dealloc() for freed type (GH-26274)
    https://github.com/python/cpython/commit/615069eb08494d089bf24e43547fbc482ed699b8

    Fix a crash at Python exit when a deallocator function removes the
    last strong reference to a heap type.

    Don't read type memory after calling basedealloc() since
    basedealloc() can deallocate the type and free its memory.

tox4 hangs: https://bugs.python.org/issue45274
    https://github.com/python/cpython/pull/28532
