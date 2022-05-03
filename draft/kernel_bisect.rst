brk() regression on AArch64 on static-pie binary -- issue with ASLR and a guard page?

The bug
=======

Running "ldconfig -p" in a loop does crash. Example with the shell command:

$ while true; do LC_ALL=C LANG=C /sbin/ldconfig -p > /dev/null; rc=$?; echo "$(date): $rc"; if [ $rc -ne 0 ]; then break; fi; done

errno is a TLS variable, but glibc failed to allocate memory for the TLS
variable, so its attempts to write to NULL if I understand correctly.

The last brk() result 0xaaaac182d000 is smaller than the brk() argument
0xaaaac182db98, so the glibc __brk() considers that the memory allocation
failed.

Oh, the kernel was updated the same day. Maybe it's a kernel regression:

* old kernel (ok): 5.17.0-0.rc0.20220112gitdaadb3bd0e8d.63.fc36.aarc
* new kernel (bug): 5.17.0-0.rc8.123.fc37.aarch64

This bug reminds me an old kernel brk issue on AArch64: https://bugzilla.redhat.com/show_bug.cgi?id=1797052

With ASLR enabled (/proc/sys/kernel/randomize_va_space = 2), "ldconfig -p" crash after between 300 and 1300 runs.

With ASLR disabled (/proc/sys/kernel/randomize_va_space = 0), I fail to reproduce "ldconfig -p" crash: I stopped my test after 20,000 iterations.

empty.c::

    _Thread_local int var1 = 0;
    int main() {
            volatile int x = 1;
            var1 = x;
            return 0;
    }

Reproducer: get attached empty.c and run:

$ gcc -std=c11 -static-pie -g empty.c -o empty -O2
$ i=0; while true; do ./empty; rc=$?; i=$(($i + 1)); echo "$i: $(date): $rc"; if [ $rc -ne 0 ]; then break; fi; done
(...)

Sadly, the final Linux 5.17 release is also affected.


$ uname -r
5.17.0-128.fc37.aarch64

I tested different kernel versions to bisect the issue, it's between builds 63 (2022-01-12 git daadb3bd0e8d) and 83 (5.17rc2):

* ok: 5.17.0-0.rc0.20220112gitdaadb3bd0e8d.63.fc36.aarch64 (last built kernel without the bug)
* BUG: 5.17.0-0.rc2.83.fc36.aarch64 (first built kernel with the bug)
* BUG: 5.17.0-0.rc2.20220202git9f7fb8de5d9b.84.fc36.aarch64

Sadly, all builds between build 63 and build 83 failed.

Just to be sure, I also tested the kernel 5.16.0-60.fc36.aarch64: ok.


Regression
==========

* kernel: https://bugzilla.kernel.org/show_bug.cgi?id=215720
* Fedora downstream issue: https://bugzilla.redhat.com/show_bug.cgi?id=2066147
* Python issue: https://bugs.python.org/issue47078

Bisect with RPM packages
========================

Download::

    wget https://kojipkgs.fedoraproject.org//packages/kernel/5.16.0/60.fc36/aarch64/kernel-5.16.0-60.fc36.aarch64.rpm
    wget https://kojipkgs.fedoraproject.org//packages/kernel/5.16.0/60.fc36/aarch64/kernel-core-5.16.0-60.fc36.aarch64.rpm
    wget https://kojipkgs.fedoraproject.org//packages/kernel/5.16.0/60.fc36/aarch64/kernel-devel-5.16.0-60.fc36.aarch64.rpm
    wget https://kojipkgs.fedoraproject.org//packages/kernel/5.16.0/60.fc36/aarch64/kernel-modules-5.16.0-60.fc36.aarch64.rpm

[vstinner@python-builder-fedora-rawhide-aarch64 ~]$ ls rpm
kernel-5.17.0-128.fc37.aarch64.rpm       kernel-devel-5.17.0-128.fc37.aarch64.rpm
kernel-core-5.17.0-128.fc37.aarch64.rpm  kernel-modules-5.17.0-128.fc37.aarch64.rpm

[vstinner@python-builder-fedora-rawhide-aarch64 ~]$ ls rpm-5.16
kernel-5.16.0-60.fc36.aarch64.rpm       kernel-devel-5.16.0-60.fc36.aarch64.rpm
kernel-core-5.16.0-60.fc36.aarch64.rpm  kernel-modules-5.16.0-60.fc36.aarch64.rpm

[vstinner@python-builder-fedora-rawhide-aarch64 ~]$ ls rpm-83
kernel-5.17.0-0.rc2.83.fc36.aarch64.rpm       kernel-devel-5.17.0-0.rc2.83.fc36.aarch64.rpm
kernel-core-5.17.0-0.rc2.83.fc36.aarch64.rpm  kernel-modules-5.17.0-0.rc2.83.fc36.aarch64.rpm

[vstinner@python-builder-fedora-rawhide-aarch64 ~]$ ls rpm-84
kernel-5.17.0-0.rc2.20220202git9f7fb8de5d9b.84.fc36.aarch64.rpm
kernel-core-5.17.0-0.rc2.20220202git9f7fb8de5d9b.84.fc36.aarch64.rpm
kernel-devel-5.17.0-0.rc2.20220202git9f7fb8de5d9b.84.fc36.aarch64.rpm
kernel-modules-5.17.0-0.rc2.20220202git9f7fb8de5d9b.84.fc36.aarch64.rpm


Build the kernel
================

Download::

    git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

``build.sh`` shell script (in the parent directory) to build and the install the
Linux kernel (``linux/`` directory)::

    set -e -x

    export LANG=
    export MAKEFLAGS="-j$(nproc)"

    cd linux
    git checkout .

    sed -i -e 's/EXTRAVERSION *=.*/EXTRAVERSION = -debug2/g' Makefile
    git apply ../subcmd.patch

    cp /boot/config-5.17.0-128.fc37.aarch64 .config
    yes "" | time make oldconfig

    time make

    sudo make modules_install
    sudo make install

To boot on the new kernel: just reboot.

A regression prevented me to build the kernel. I found the fix and put it
in a patch: ``subcmd.patch``.

Remove an old kernel installed by the ``build.sh`` script since ``/boot`` is
small (1 GB) and each kernel takes a lot of space::

    set -e -x
    #name=5.17.0-bad2+
    name=5.16.0-bisect15+
    sudo rm -rf /boot/initramfs-$name.img /boot/System.map-$name /boot/vmlinuz-$name /lib/modules/$name/ $(sudo bash -c "ls /boot/loader/entries/*-$name.conf")


git bisect
==========

Use regular git commands::

    git bisect reset
    git bisect start
    git bisect bad e783362eb54cd99b2cac8b3a9aeac942e6f6ac07 # Jan 23: Linux 5.17-rc1
    git bisect good 51620150ca2df62f8ea472ab8962be590c957288 # Jan 19
    ...

