Bug 1797052 - python27, 34, 35, 36 fails to build on aarch64 in rawhide: Segmentation fault in test_constructor
https://bugzilla.redhat.com/show_bug.cgi?id=1797052

ssh 147.75.73.38
ssh vstinner@192.168.122.21
mock -r fedora-rawhide-aarch64 --enable-network --shell
cd /builddir/build/BUILD/Python-2.7.17/build/optimized
./bug.sh

mmap
====

size=0x8000000000001000

mm = (char *) (MMAP (0, size, PROT_READ | PROT_WRITE, 0));                                                                                                                                                         │


gcc -O3 bug on Fedora 31
========================

cd /home/vstinner/Python-2.7.17/build2

vim Makefile # replace -O2 with -O3
for name in $(find ../Modules/_io/ -name "*.c"); do touch $name; done
make


Build vanilla Python
====================

set -e -x
curl -O https://www.python.org/ftp/python/2.7.17/Python-2.7.17.tar.xz
tar -xf Python-2.7.17.tar.xz
cd Python-2.7.17
mkdir build
cd build
../configure -C \
 --enable-ipv6 \
 --enable-shared \
 --enable-unicode=ucs4 \
 --with-system-expat \
 --with-system-ffi \
 CC=gcc \
 'LDFLAGS=-specs=/usr/lib/rpm/redhat/redhat-hardened-ld'
make clean
CFLAGS='-fno-strict-aliasing -O2 -g -pipe -Wp,-D_FORTIFY_SOURCE=2 -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1 -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv -DNDEBUG'
make EXTRA_CFLAGS="$CFLAGS" -j12
LD_LIBRARY_PATH=$PWD ./python -m test -v test_io


TODO
====

* Test redhat-rpm-config-146-1.fc32.noarch.rpm

Koshei
======

Last working AArch64 build:
    https://koji.fedoraproject.org/koji/taskinfo?taskID=40446811
RPM components of the buildroot:
    https://koji.fedoraproject.org/koji/rpmlist?buildrootID=18917528%20&start=50&order=nvr&type=component

Manual build
============

mkdir build
cd build
../configure '--build=aarch64-redhat-linux-gnu' '--host=aarch64-redhat-linux-gnu' '--program-prefix=' '--disable-dependency-tracking' '--prefix=/usr' '--exec-prefix=/usr' '--bindir=/usr/bin' '--sbindir=/usr/sbin' '--sysconfdir=/etc' '--datadir=/usr/share' '--includedir=/usr/include' '--libdir=/usr/lib64' '--libexecdir=/usr/libexec' '--localstatedir=/var' '--sharedstatedir=/var/lib' '--mandir=/usr/share/man' '--infodir=/usr/share/info' '--enable-ipv6' '--enable-shared' '--enable-unicode=ucs4' '--with-dbmliborder=gdbm:ndbm:bdb' '--with-system-expat' '--with-system-ffi' '--with-dtrace' '--with-tapset-install-dir=/usr/share/systemtap/tapset' 'build_alias=aarch64-redhat-linux-gnu' 'host_alias=aarch64-redhat-linux-gnu' 'CC=gcc' 'CFLAGS=-O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv ' 'LDFLAGS=-Wl,-z,relro -Wl,--as-needed  -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld ' 'CPPFLAGS=' 'PKG_CONFIG_PATH=:/usr/lib64/pkgconfig:/usr/share/pkgconfig'
make EXTRA_CFLAGS='-fno-strict-aliasing -O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv  -DNDEBUG -O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv'
LD_LIBRARY_PATH=$PWD ./python -m test -v test_io

CONFIG_ARGS='--build=aarch64-redhat-linux-gnu' '--host=aarch64-redhat-linux-gnu' '--program-prefix=' '--disable-dependency-tracking' '--prefix=/usr' '--exec-prefix=/usr' '--bindir=/usr/bin' '--sbindir=/usr/sbin' '--sysconfdir=/etc' '--datadir=/usr/share' '--includedir=/usr/include' '--libdir=/usr/lib64' '--libexecdir=/usr/libexec' '--localstatedir=/var' '--sharedstatedir=/var/lib' '--mandir=/usr/share/man' '--infodir=/usr/share/info' '--enable-ipv6' '--enable-shared' '--enable-unicode=ucs4' '--with-dbmliborder=gdbm:ndbm:bdb' '--with-system-expat' '--with-system-ffi' '--with-dtrace' '--with-tapset-install-dir=/usr/share/systemtap/tapset' 'build_alias=aarch64-redhat-linux-gnu' 'host_alias=aarch64-redhat-linux-gnu' 'CC=gcc' 'CFLAGS=-O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv ' 'LDFLAGS=-Wl,-z,relro -Wl,--as-needed  -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld ' 'CPPFLAGS=' 'PKG_CONFIG_PATH=:/usr/lib64/pkgconfig:/usr/share/pkgconfig'
PY_CFLAGS='-fno-strict-aliasing -O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv  -DNDEBUG -O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv -I. -IInclude -I/builddir/build/BUILD/Python-2.7.17/Include -fPIC -DPy_BUILD_CORE'
LDFLAGS='-Wl,-z,relro -Wl,--as-needed  -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld'
CFLAGS='-fno-strict-aliasing -O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv  -DNDEBUG -O2 -g -pipe -Wall -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2 -Wp,-D_GLIBCXX_ASSERTIONS -fexceptions -fstack-protector-strong -grecord-gcc-switches -specs=/usr/lib/rpm/redhat/redhat-hardened-cc1  -fasynchronous-unwind-tables -fstack-clash-protection -D_GNU_SOURCE -fPIC -fwrapv'


Downgrade
=========

# rpm -q gcc glibc redhat-rpm-config
gcc-9.2.1-1.fc32.3.aarch64
glibc-2.30.9000-29.fc32.aarch64
redhat-rpm-config-147-1.fc32.noarch


Reproduce in mock
=================

cd /builddir/build/BUILD/Python-2.7.17/build/optimized/
LD_LIBRARY_PATH=$PWD ./python -m test -v test_io

Build the package in the container: rpmbuild
============================================

dnf install 'dnf-command(builddep)'

dnf install fedpkg
fedpkg clone python27 --anonymous
cd python27/
fedpkg srpm
rpmbuild --rebuild python*.src.rpm

Install dependencies:

dnf install \
 autoconf \
 bluez-libs-devel \
 bzip2-devel \
 expat-devel \
 gdbm-devel \
 gmp-devel \
 libX11-devel \
 libdb-devel \
 libffi-devel \
 libnsl2-devel \
 libtirpc-devel \
 mesa-libGL-devel \
 ncurses-devel \
 openssl-devel \
 readline-devel \
 sqlite-devel \
 systemtap-sdt-devel \
 tcl-devel \
 tix-devel \
 tk-devel \
 zlib-devel


Build the package outside the container: fedpkg mockbuild
=========================================================

dnf install fedpkg -y
fedpkg clone python27 --anonymous
cd python27
fedpkg mockbuild --mock-config fedora-rawhide-aarch64 --no-clean-all --enablerepo=local

Downgrade glibc
===============

<mock-chroot> sh-5.0# rpm -q glibc
glibc-2.30.9000-29.fc32.aarch64


https://koschei.fedoraproject.org/package/python27
=> https://koschei.fedoraproject.org/build/7736139

GCC: 9.2.1-1.fc32.3 => 10.0.1-0.3.fc32
glibc: 2.30.9000-29.fc32 => 2.30.9000-30.fc32

glibc-2.30.9000-29.fc32: https://koji.fedoraproject.org/koji/buildinfo?buildID=1426527
GCC: 9.2.1-1.fc32.3: https://koji.fedoraproject.org/koji/buildinfo?buildID=1398686

Downgrade glibc
==============

set -x
URL=https://kojipkgs.fedoraproject.org//packages/glibc/2.30/4.fc31/aarch64/
dnf install \
 $URL/glibc-minimal-langpack-2.30-4.fc31.aarch64.rpm \
 $URL/glibc-all-langpacks-2.30-4.fc31.aarch64.rpm \
 $URL/glibc-2.30-4.fc31.aarch64.rpm \
 $URL/glibc-common-2.30-4.fc31.aarch64.rpm \
 $URL/glibc-headers-2.30-4.fc31.aarch64.rpm \
 $URL/glibc-devel-2.30-4.fc31.aarch64.rpm
ldconfig  # <===== FIX

URL=https://kojipkgs.fedoraproject.org//packages/glibc/2.30.9000/29.fc32/aarch64
dnf install \
 $URL/glibc-minimal-langpack-2.30.9000-29.fc32.aarch64.rpm \
 $URL/glibc-all-langpacks-2.30.9000-29.fc32.aarch64.rpm \
 $URL/glibc-2.30.9000-29.fc32.aarch64.rpm \
 $URL/glibc-common-2.30.9000-29.fc32.aarch64.rpm \
 $URL/glibc-headers-2.30.9000-29.fc32.aarch64.rpm \
 $URL/glibc-devel-2.30.9000-29.fc32.aarch64.rpm
ldconfig  # <===== FIX

Downgrade GCC
=============

URL=https://kojipkgs.fedoraproject.org//packages/gcc/9.2.1/1.fc32.3/aarch64
dnf install \
 $URL/cpp-9.2.1-1.fc32.3.aarch64.rpm \
 $URL/libgomp-9.2.1-1.fc32.3.aarch64.rpm \
 $URL/libasan-9.2.1-1.fc32.3.aarch64.rpm \
 $URL/gcc-9.2.1-1.fc32.3.aarch64.rpm \
 $URL/gcc-c++-9.2.1-1.fc32.3.aarch64.rpm \
 $URL/libstdc++-9.2.1-1.fc32.3.aarch64.rpm \
 $URL/libstdc++-devel-9.2.1-1.fc32.3.aarch64.rpm \
 https://kojipkgs.fedoraproject.org//packages/redhat-rpm-config/147/1.fc32/noarch/redhat-rpm-config-147-1.fc32.noarch.rpm


XXX  URL=https://kojipkgs.fedoraproject.org//packages/gcc/9.2.1/1.fc32.3/aarch64
XXX  dnf install \
XXX   $URL/libasan-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libubsan-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/gcc-c++-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/cpp-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libatomic-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libgcc-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/gcc-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libstdc++-devel-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libstdc++-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libgomp-9.2.1-1.fc32.3.aarch64.rpm
XXX
XXX  set -e -x
XXX  URL=https://kojipkgs.fedoraproject.org//packages/gcc/9.2.1/1.fc32.3/aarch64
XXX  dnf install \
XXX   $URL/cpp-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libgomp-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/libasan-9.2.1-1.fc32.3.aarch64.rpm \
XXX   $URL/gcc-9.2.1-1.fc32.3.aarch64.rpm
XXX   https://kojipkgs.fedoraproject.org//packages/redhat-rpm-config/147/1.fc32/noarch/redhat-rpm-config-147-1.fc32.noarch.rpm


Setup debug
===========

In the mock container.

# cat ~/.gdbinit
set auto-load safe-path /

dnf install -y gdb vim tmux
dnf install 'dnf-command(debuginfo-install)'
dnf debuginfo-install glibc


Crashes
=======

python27 test_io
----------------

0:01:40 load avg: 0.92 [188/403] test_io


* python27: test_io.test_constructor(): crash on malloc() on 'string' * 1000 which allocates 256 KB

python27: test_io.CBufferedWriterTest.test_constructor()

    def check_writes(self, intermediate_func):
        # Lots of writes, test the flushed output is as expected.
        contents = bytes(range(256)) * 1000

    at /builddir/build/BUILD/Python-2.7.17/Python/ceval.c:1485
1485                x = PyNumber_Multiply(v, w);

(gdb) p v
$20 = '\x00\x01\x02\x03(...)\xfd\xfe\xff'
(gdb) p *(PyStringObject*)v
$22 = {ob_refcnt = 1, ob_type = 0xfffff7f7bdc8 <PyString_Type>, ob_size = 256, ob_shash = -1, ob_sstate = 0, ob_sval = ""}
(gdb) p w
$23 = 1000

(gdb) up
#2  0x0000fffff7e48ca0 in string_repeat (a=0xffffe9fff290, n=<optimized out>) at /builddir/build/BUILD/Python-2.7.17/Objects/stringobject.c:1115
1115        op = (PyStringObject *)PyObject_MALLOC(PyStringObject_SIZE + nbytes);

    nbytes = 256 * 1000
    => call malloc(37 + 256 000)  : malloc(256037)

(gdb) up
#1  0x0000fffff7cbb29c in __GI___libc_malloc (bytes=256037) at malloc.c:3058
3058          victim = _int_malloc (&main_arena, bytes);

(gdb) up
#0  0x0000fffff7cba478 in _int_malloc (av=av@entry=0xfffff7dae9f8 <main_arena>, bytes=bytes@entry=256037) at malloc.c:4116
4116              set_head (remainder, remainder_size | PREV_INUSE);



4087        use_top:
4088          /*
4089             If large enough, split off the chunk bordering the end of memory
(gdb)
4090             (held in av->top). Note that this is in accord with the best-fit
4091             search rule.  In effect, av->top is treated as larger (and thus
4092             less well fitting) than any other available chunk since it can
4093             be extended to be as large as necessary (up to system
4094             limitations).
4095
4096             We require that av->top always exists (i.e., has size >=
4097             MINSIZE) after initialization, so if it would otherwise be
4098             exhausted by current request, it is replenished. (The main
4099             reason for ensuring it exists is that we may need MINSIZE space
4100             to put in fenceposts in sysmalloc.)
4101           */
4102
4103          victim = av->top;
4104          size = chunksize (victim);
4105
4106          if (__glibc_unlikely (size > av->system_mem))
4107            malloc_printerr ("malloc(): corrupted top size");
4108
4109          if ((unsigned long) (size) >= (unsigned long) (nb + MINSIZE))
4110            {
4111              remainder_size = size - nb;
4112              remainder = chunk_at_offset (victim, nb);
4113              av->top = remainder;
4114              set_head (victim, nb | PREV_INUSE |
4115                        (av != &main_arena ? NON_MAIN_ARENA : 0));
4116              set_head (remainder, remainder_size | PREV_INUSE); <============ HERE
4117
4118              check_malloced_chunk (av, victim, nb);
4119              void *p = chunk2mem (victim);
4120              alloc_perturb (p, bytes);

(gdb) p bytes  # requested size
$46 = 256037
(gdb) p nb     # rounded size
$32 = 256048
(gdb) p nb - bytes
$48 = 11

(gdb) p remainder_size
$29 = <optimized out>
(gdb) p victim
$30 = (mchunkptr) 0xaaaaaade13a0
(gdb) p remainder
$31 = (mchunkptr) 0xaaaaaae1fbd0

(gdb) p av->system_mem
$54 = 3641344
(gdb) p av->top
$55 = (mchunkptr) 0xaaaaaae1fbd0
(gdb) p av->top == remainder
$56 = 1


computed manually: size = 256048 = victim->mchunk_size & ~(1|2|4) == nb

(gdb) disassemble $pc,$pc+10
Dump of assembler code from 0xfffff7cba478 to 0xfffff7cba482:
=> 0x0000fffff7cba478 <_int_malloc+3240>:       str     x0, [x3, #8]
   0x0000fffff7cba47c <_int_malloc+3244>:       mov     x0, x21
   0x0000fffff7cba480 <_int_malloc+3248>:       b       0xfffff7cba118 <_int_malloc+2376>
End of assembler dump.
(gdb) p /x $x3
$34 = 0xaaaaaae1fbd0
(gdb) p /x $x0
$35 = 0x24431

Process maps:

aaaaaaaaa000-aaaaaaaab000 r-xp 00000000 fd:00 17573378                   /builddir/build/BUILD/Python-2.7.17/build/optimized/python
aaaaaaac9000-aaaaaaaca000 r--p 0000f000 fd:00 17573378                   /builddir/build/BUILD/Python-2.7.17/build/optimized/python
aaaaaaaca000-aaaaaaacb000 rw-p 00010000 fd:00 17573378                   /builddir/build/BUILD/Python-2.7.17/build/optimized/python
aaaaaaacb000-aaaaaae02000 rw-p 00000000 00:00 0                          [heap]
    --- <remainder> = $x3 = 0xaaaaaae1fbd0 is here ---
ffffe9efc000-ffffe9f3c000 rw-p 00000000 00:00 0





python36 test_random
--------------------

python36: 2020-02-14 around 09:00 @ 147.75.73.38: crash in
test_random.test_choices_algorithms().

Crash while running fedpkg mockbuild. Failed to reproduce manually :-(

STARTING: CHECKING OF PYTHON FOR CONFIGURATION: optimized
+ WITHIN_PYTHON_RPM_BUILD=
+ LD_LIBRARY_PATH=/builddir/build/BUILD/Python-3.6.10/build/optimized
+ /builddir/build/BUILD/Python-3.6.10/build/optimized/python -m test.regrtest -wW --slowest --findleaks -x test_distutils -x test_bdist_rpm -x test_gdb -x test_faulthandler
== CPython 3.6.10 (default, Jan 30 2020, 00:00:00) [GCC 10.0.1 20200130 (Red Hat 10.0.1-0.7)]
== Linux-5.4.17-200.fc31.aarch64-aarch64-with-fedora-32-Rawhide little-endian
== cwd: /builddir/build/BUILD/Python-3.6.10/build/optimized/build/test_python_26844
== CPU count: 8
== encodings: locale=UTF-8, FS=utf-8
Run tests sequentially
(...)
0:14:44 load avg: 0.62 [267/405] test_random
Fatal Python error: Segmentation fault

Current thread 0x0000ffff97239cc0 (most recent call first):
  File "/builddir/build/BUILD/Python-3.6.10/Lib/random.py", line 356 in choices
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/test_random.py", line 696 in test_choices_algorithms



Memory error
============

glibc: MALLOC_CHECK_=3
Valgrind: valgrind --suppressions=Misc/valgrind.suppr ./python ...
Python builtin: PYTHONMALLOC=debug or python -X dev

python36
========

+ ConfDir=/builddir/build/BUILD/Python-3.6.10/build/optimized
+ echo STARTING: CHECKING OF PYTHON FOR CONFIGURATION: optimized
STARTING: CHECKING OF PYTHON FOR CONFIGURATION: optimized
+ WITHIN_PYTHON_RPM_BUILD=
+ LD_LIBRARY_PATH=/builddir/build/BUILD/Python-3.6.10/build/optimized
+ /builddir/build/BUILD/Python-3.6.10/build/optimized/python -m test.regrtest -wW --slowest --findleaks -x test_distutils -x test_bdist_rpm -x test_gdb -x test_faulthandler
== CPython 3.6.10 (default, Jan 30 2020, 00:00:00) [GCC 10.0.1 20200130 (Red Hat 10.0.1-0.7)]
== Linux-5.4.17-200.fc31.aarch64-aarch64-with-fedora-32-Rawhide little-endian
== cwd: /builddir/build/BUILD/Python-3.6.10/build/optimized/build/test_python_26846
== CPU count: 8
== encodings: locale=UTF-8, FS=utf-8
Run tests sequentially
0:00:00 load avg: 2.05 [  1/405] test_grammar

...

++ pwd
+ topdir=/builddir/build/BUILD/Python-3.6.10
+ CheckPython optimized
+ ConfName=optimized
++ pwd
+ ConfDir=/builddir/build/BUILD/Python-3.6.10/build/optimized
+ echo STARTING: CHECKING OF PYTHON FOR CONFIGURATION: optimized
STARTING: CHECKING OF PYTHON FOR CONFIGURATION: optimized
+ WITHIN_PYTHON_RPM_BUILD=
+ LD_LIBRARY_PATH=/builddir/build/BUILD/Python-3.6.10/build/optimized
+ /builddir/build/BUILD/Python-3.6.10/build/optimized/python -m test.regrtest -wW --slowest --findleaks -x test_distutils -x test_bdist_rpm -x test_gdb -x test_faulthandler
== CPython 3.6.10 (default, Jan 30 2020, 00:00:00) [GCC 10.0.1 20200130 (Red Hat 10.0.1-0.7)]
== Linux-5.4.17-200.fc31.aarch64-aarch64-with-fedora-32-Rawhide little-endian
== cwd: /builddir/build/BUILD/Python-3.6.10/build/optimized/build/test_python_26844
== CPU count: 8
== encodings: locale=UTF-8, FS=utf-8
Run tests sequentially
0:00:00 load avg: 1.55 [  1/405] test_grammar
0:00:00 load avg: 1.55 [  2/405] test_opcodes
0:00:00 load avg: 1.55 [  3/405] test_dict



misc
====

PYTHONHOME=$PWD PYTHONPATH=$PWD/Lib:$PWD/build/optimized/build/lib.linux-aarch64-2.7/:$PWD/build/optimized/Modules/ LD_LIBRARY_PATH=$PWD/build/optimized/ PYTHONHOME=$PWD build/optimized/python -m test -u all -v test_warnings

make test

gcc -pthread -shared -Wl,-z,relro -Wl,--as-needed -Wl,-z,now -specs=/usr/lib/rpm/redhat/redhat-hardened-ld build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/_ctypes.o build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/callbacks.o build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/callproc.o build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/stgdict.o build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/cfield.o -L/usr/local/lib64 -L. -lffi -ldl -lpython2.7 -o build/lib.linux-aarch64-2.7/_ctypes.so

gcc -pthread -shared -Wl,-z,relro -Wl,--as-needed -Wl,-z,now
-specs=/usr/lib/rpm/redhat/redhat-hardened-ld
build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/_ctypes.o
build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/callbacks.o
build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/callproc.o
build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/stgdict.o
build/temp.linux-aarch64-2.7/builddir/build/BUILD/Python-2.7.17/Modules/_ctypes/cfield.o
-L/usr/local/lib64 -L. -lffi -ldl -lpython2.7 -o
build/lib.linux-aarch64-2.7/_ctypes.so


python36 test_random
====================

It took around 20 min to get a crash.

+ case $Module in
+ for Module in /builddir/build/BUILDROOT/python36-3.6.10-2.fc32.aarch64//usr/lib64/python3.6/lib-dynload/*.so
+ case $Module in
+ for Module in /builddir/build/BUILDROOT/python36-3.6.10-2.fc32.aarch64//usr/lib64/python3.6/lib-dynload/*.so
+ case $Module in
+ for Module in /builddir/build/BUILDROOT/python36-3.6.10-2.fc32.aarch64//usr/lib64/python3.6/lib-dynload/*.so
+ case $Module in
+ for Module in /builddir/build/BUILDROOT/python36-3.6.10-2.fc32.aarch64//usr/lib64/python3.6/lib-dynload/*.so
+ case $Module in
+ for Module in /builddir/build/BUILDROOT/python36-3.6.10-2.fc32.aarch64//usr/lib64/python3.6/lib-dynload/*.so
+ case $Module in
+ for Module in /builddir/build/BUILDROOT/python36-3.6.10-2.fc32.aarch64//usr/lib64/python3.6/lib-dynload/*.so
+ case $Module in
++ pwd
+ topdir=/builddir/build/BUILD/Python-3.6.10
+ CheckPython optimized
+ ConfName=optimized
++ pwd
+ ConfDir=/builddir/build/BUILD/Python-3.6.10/build/optimized
+ echo STARTING: CHECKING OF PYTHON FOR CONFIGURATION: optimized
STARTING: CHECKING OF PYTHON FOR CONFIGURATION: optimized
+ WITHIN_PYTHON_RPM_BUILD=
+ LD_LIBRARY_PATH=/builddir/build/BUILD/Python-3.6.10/build/optimized
+ /builddir/build/BUILD/Python-3.6.10/build/optimized/python -m test.regrtest -wW --slowest --findleaks -x test_distutils -x test_bdist_rpm -x test_gdb -x test_faulthandler
== CPython 3.6.10 (default, Jan 30 2020, 00:00:00) [GCC 10.0.1 20200130 (Red Hat 10.0.1-0.7)]
== Linux-5.4.17-200.fc31.aarch64-aarch64-with-fedora-32-Rawhide little-endian
== cwd: /builddir/build/BUILD/Python-3.6.10/build/optimized/build/test_python_26844
== CPU count: 8
== encodings: locale=UTF-8, FS=utf-8
Run tests sequentially
0:00:00 load avg: 1.58 [  1/405] test_grammar
0:00:00 load avg: 1.58 [  2/405] test_opcodes
0:00:00 load avg: 1.58 [  3/405] test_dict
(...)
0:14:39 load avg: 0.67 [264/405] test_queue
0:14:43 load avg: 0.62 [265/405] test_quopri
0:14:43 load avg: 0.62 [266/405] test_raise
0:14:44 load avg: 0.62 [267/405] test_random
Fatal Python error: Segmentation fault

Current thread 0x0000ffff97239cc0 (most recent call first):
  File "/builddir/build/BUILD/Python-3.6.10/Lib/random.py", line 356 in choices
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/test_random.py", line 696 in test_choices_algorithms
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/case.py", line 622 in run
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/case.py", line 670 in __call__
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/suite.py", line 122 in run
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/suite.py", line 84 in __call__
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/suite.py", line 122 in run
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/suite.py", line 84 in __call__
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/suite.py", line 122 in run
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/suite.py", line 84 in __call__
  File "/builddir/build/BUILD/Python-3.6.10/Lib/unittest/runner.py", line 176 in run
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/support/__init__.py", line 1921 in _run_suite
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/support/__init__.py", line 2017 in run_unittest
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/runtest.py", line 178 in test_runner
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/runtest.py", line 182 in runtest_inner
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/runtest.py", line 127 in runtest
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/main.py", line 407 in run_tests_sequential
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/main.py", line 514 in run_tests
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/main.py", line 617 in _main
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/main.py", line 582 in main
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/libregrtest/main.py", line 638 in main
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/regrtest.py", line 46 in _main
  File "/builddir/build/BUILD/Python-3.6.10/Lib/test/regrtest.py", line 50 in <module>
  File "/builddir/build/BUILD/Python-3.6.10/Lib/runpy.py", line 85 in _run_code
  File "/builddir/build/BUILD/Python-3.6.10/Lib/runpy.py", line 193 in _run_module_as_main
/var/tmp/rpm-tmp.7dmbdu: line 67: 26844 Segmentation fault      (core dumped) WITHIN_PYTHON_RPM_BUILD= LD_LIBRARY_PATH=$ConfDir $ConfDir/python -m test.regrtest -wW --slowest --findleaks -x test_distutils -x test_bdist_rpm -x test_gdb -x test_faulthandler
error: Bad exit status from /var/tmp/rpm-tmp.7dmbdu (%check)


RPM build errors:
    extra tokens at the end of %endif directive in line 592:  %endif # with debug_build

    extra tokens at the end of %else directive in line 594:  %else  # with flatpackage

    extra tokens at the end of %endif directive in line 619:  %endif # with flatpackage

    extra tokens at the end of %endif directive in line 760:  %endif # with debug_build

    extra tokens at the end of %endif directive in line 797:  %endif # with gdb_hooks

    extra tokens at the end of %endif directive in line 836:  %endif # with gdb_hooks

    extra tokens at the end of %endif directive in line 871:  %endif # with debug_build

    extra tokens at the end of %endif directive in line 1075:  %endif # with debug_build

    extra tokens at the end of %endif directive in line 1078:  %endif # with tests

    extra tokens at the end of %endif directive in line 1515:  %endif # with debug_build

    Bad exit status from /var/tmp/rpm-tmp.7dmbdu (%check)
Finish: rpmbuild python36-3.6.10-2.fc33.src.rpm
Finish: build phase for python36-3.6.10-2.fc33.src.rpm
ERROR: Exception(/home/vstinner/python36/python36-3.6.10-2.fc33.src.rpm) Config(fedora-rawhide-aarch64) 20 minutes 37 seconds
INFO: Results and/or logs in: /home/vstinner/python36/results_python36/3.6.10/2.fc33
ERROR: Command failed:
 # /usr/bin/systemd-nspawn -q -M ecb5774f04ae44a09f94ada1a759b03e -D /var/lib/mock/fedora-rawhide-aarch64/root -a --capability=cap_ipc_lock --bind=/tmp/mock-resolv.6ode8jeh:/etc/resolv.conf --setenv=TERM=vt100 --setenv=SHELL=/bin/bash --setenv=HOME=/builddir --setenv=HOSTNAME=mock --setenv=PATH=/usr/bin:/bin:/usr/sbin:/sbin --setenv=PROMPT_COMMAND=printf "\033]0;<mock-chroot>\007" --setenv=PS1=<mock-chroot> \s-\v\$  --setenv=LANG=en_US.UTF-8 -u mockbuild bash --login -c /usr/bin/rpmbuild -bb --target aarch64 --nodeps /builddir/build/SPECS/python36.spec

Could not execute mockbuild: Failed to execute command.

