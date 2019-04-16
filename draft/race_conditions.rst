Coredump:

* FreeBSD: ``sudo sysctl -w 'kern.corefile =%N.%P.core'`` to include pid in
  coredump filenames, since 2 process can crash at the same time.

Run directly a test without regrtest in a loop until it fails::

    while true; do ./python Lib/test/test_multiprocessing_spawn.py WithManagerTestMyManager.test_mymanager_context_prestarted  -v || break; done

