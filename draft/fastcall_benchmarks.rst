bench_recursion, related to FASTCALL?
http://bugs.python.org/issue29227#msg285147

map(lambda x: x, range(1000)
============================

 1023  ../3.4/python -m perf timeit 'list(map(lambda x:x, range(1000)))' -v -o 3.4.json
 1024  ../3.5/python -m perf timeit 'list(map(lambda x:x, range(1000)))' -v -o 3.5.json
 1026  ./python -m perf timeit 'list(map(lambda x:x, range(1000)))' -v -o 3.7.json
 1029  ../2.7/python -m perf timeit 'map(lambda x:x, range(1000))' -v -o 2.7.json

haypo@smithers$ ./python -m perf compare_to 2.7.json 3.4.json 3.5.json 3.7.json
Median +- std dev: [2.7] 97.8 us +- 20.1 us -> [3.4] 103 us +- 1 us: 1.05x slower (+5%)
Not significant!
Median +- std dev: [2.7] 97.8 us +- 20.1 us -> [3.5] 113 us +- 0 us: 1.16x slower (+16%)
Median +- std dev: [2.7] 97.8 us +- 20.1 us -> [3.7] 88.1 us +- 0.3 us: 1.11x faster (-10%)

__getitem__()
=============

Use FASTCALL in call_method() to avoid temporary tuple
http://bugs.python.org/issue29507
Median +- std dev: [ref] 121 ns +- 5 ns -> [patch] 82.8 ns +- 1.0 ns: 1.46x faster (-31%)
