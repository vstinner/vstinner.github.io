Unstable benchmarks...

1. Disable ASLR
2. System noise / jitter: isolcpus, nohz_full
3. Adding deadcode makes Python faster or slower
4. PYTHONHASH
5. Command line
6. Environment variables
7. Exact memory addresses
8. Turbo Boost, benchmark becomes "suddenly" 20% slower on my laptop
9. Running powertop impacts performances
10. CPU frequency not reliable anymore: turbostat
11. Running turbostat works around the NOHZ_FULL bug
12. NOHZ_FULL bug: wrong P-state, half performance then suddenly nominal
    performance
13. NOHZ_FULL bug: wrong C-state, half performance then suddenly nominal
    performance
14. Theorical issue: CPU overheating can also slowdown benchmark
    between 2x and 5x
