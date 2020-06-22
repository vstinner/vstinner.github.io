I used ``disassemble PyTuple_New`` command of gdb to get the assembly code.

Benchmark
=========

* bench_tuple: PyTuple_New(n)

  * tuple-0: 4.84 ns +- 0.00 ns -> 4.47 ns +- 0.01 ns: 1.08x faster (-8%)
  * tuple-1: 18.2 ns +- 0.2 ns -> 19.0 ns +- 0.2 ns: 1.04x slower (+4%)
  * tuple-5: 30.1 ns +- 0.1 ns -> 31.3 ns +- 0.2 ns: 1.04x slower (+4%)

* bench_dict: 10.9 ns +- 0.9 ns -> 12.8 ns +- 1.0 ns: 1.18x slower (+18%)
* bench_fromid: 2.38 ns +- 0.01 ns -> 4.08 ns +- 0.01 ns: 1.71x slower (+71%)

Changes
=======

* Reference (before first free list change):
  commit dc24b8a2ac32114313bae519db3ccc21fe45c982
* Make tuple free list per-interpreter:
  commit 69ac6e58fd98de339c013fe64cd1cf763e4f9bca
* Make dict free lists per-interpreter:
  https://github.com/python/cpython/pull/20645
* _PyUnicode_FromId():
  https://github.com/python/cpython/pull/20058

PyTuple_New (1)
===============

C code
------

::

    PyObject *
    PyTuple_New(Py_ssize_t size)
    {
        PyTupleObject *op;
        PyInterpreterState *interp = _PyInterpreterState_GET();
        struct _Py_tuple_state *state = &interp->tuple;
        if (size == 0 && state->free_list[0]) {
            op = state->free_list[0];
            Py_INCREF(op);
            return (PyObject *) op;
        }
        op = tuple_alloc(state, size);
        if (op == NULL) {
            return NULL;
        }
        for (Py_ssize_t i = 0; i < size; i++) {
            op->ob_item[i] = NULL;
        }
        if (size == 0) {
            state->free_list[0] = op;
            ++state->numfree[0];
            Py_INCREF(op);          /* extra INCREF so that this is never freed */
        }
        tuple_gc_track(op);
        return (PyObject *) op;
    }


master
------

gcc -O3::

    Dump of assembler code for function PyTuple_New:
       0x000000000047bd20 <+0>:	push   rbx
       0x000000000047bd21 <+1>:	mov    rax,QWORD PTR [rip+0x2e1710]        # 0x75d438 <_PyRuntime+568>
       0x000000000047bd28 <+8>:	mov    rbx,QWORD PTR [rax+0x10]
       0x000000000047bd2c <+12>:	mov    rax,QWORD PTR [rbx+0x1608]
       0x000000000047bd33 <+19>:	test   rax,rax
       0x000000000047bd36 <+22>:	je     0x47bd40 <PyTuple_New+32>
       0x000000000047bd38 <+24>:	add    QWORD PTR [rax],0x1
       0x000000000047bd3c <+28>:	pop    rbx
       0x000000000047bd3d <+29>:	ret
       0x000000000047bd3e <+30>:	xchg   ax,ax
       0x000000000047bd40 <+32>:	xor    esi,esi
       0x000000000047bd42 <+34>:	mov    edi,0x71f6c0
       0x000000000047bd47 <+39>:	call   0x538920 <_PyObject_GC_NewVar>
       0x000000000047bd4c <+44>:	test   rax,rax
       0x000000000047bd4f <+47>:	je     0x47bd3c <PyTuple_New+28>
       0x000000000047bd51 <+49>:	add    DWORD PTR [rbx+0x16a8],0x1
       0x000000000047bd58 <+56>:	lea    rsi,[rax-0x10]
       0x000000000047bd5c <+60>:	mov    QWORD PTR [rbx+0x1608],rax
       0x000000000047bd63 <+67>:	add    QWORD PTR [rax],0x1
       0x000000000047bd67 <+71>:	mov    rdx,QWORD PTR [rip+0x2e16ca]        # 0x75d438 <_PyRuntime+568>
       0x000000000047bd6e <+78>:	mov    rdx,QWORD PTR [rdx+0x10]
       0x000000000047bd72 <+82>:	mov    rcx,QWORD PTR [rdx+0x2c8]
       0x000000000047bd79 <+89>:	mov    rdx,QWORD PTR [rax-0x8]
       0x000000000047bd7d <+93>:	mov    rdi,QWORD PTR [rcx+0x8]
       0x000000000047bd81 <+97>:	and    edx,0x3
       0x000000000047bd84 <+100>:	or     rdx,rdi
       0x000000000047bd87 <+103>:	mov    QWORD PTR [rdi],rsi
       0x000000000047bd8a <+106>:	mov    QWORD PTR [rax-0x8],rdx
       0x000000000047bd8e <+110>:	mov    QWORD PTR [rax-0x10],rcx
       0x000000000047bd92 <+114>:	mov    QWORD PTR [rcx+0x8],rsi
       0x000000000047bd96 <+118>:	pop    rbx
       0x000000000047bd97 <+119>:	ret
    End of assembler dump.

interp_current branch
---------------------

Assembly::

    Dump of assembler code for function PyTuple_New:
       0x000000000047cb60 <+0>:	push   rbx
       0x000000000047cb61 <+1>:	mov    rbx,QWORD PTR [rip+0x2f93f8]        # 0x775f60 <_PyRuntime+576>
       0x000000000047cb68 <+8>:	mov    rax,QWORD PTR [rbx+0x1610]
       0x000000000047cb6f <+15>:	test   rax,rax
       0x000000000047cb72 <+18>:	je     0x47cb80 <PyTuple_New+32>
       0x000000000047cb74 <+20>:	add    QWORD PTR [rax],0x1
       0x000000000047cb78 <+24>:	pop    rbx
       0x000000000047cb79 <+25>:	ret
       0x000000000047cb7a <+26>:	nop    WORD PTR [rax+rax*1+0x0]
       0x000000000047cb80 <+32>:	xor    esi,esi
       0x000000000047cb82 <+34>:	mov    edi,0x7336e0
       0x000000000047cb87 <+39>:	call   0x53b210 <_PyObject_GC_NewVar>
       0x000000000047cb8c <+44>:	test   rax,rax
       0x000000000047cb8f <+47>:	je     0x47cb78 <PyTuple_New+24>
       0x000000000047cb91 <+49>:	add    DWORD PTR [rbx+0x16b0],0x1
       0x000000000047cb98 <+56>:	lea    rsi,[rax-0x10]
       0x000000000047cb9c <+60>:	mov    QWORD PTR [rbx+0x1610],rax
       0x000000000047cba3 <+67>:	add    QWORD PTR [rax],0x1
       0x000000000047cba7 <+71>:	mov    rdx,QWORD PTR [rip+0x2f93aa]        # 0x775f58 <_PyRuntime+568>
       0x000000000047cbae <+78>:	mov    rdx,QWORD PTR [rdx+0x10]
       0x000000000047cbb2 <+82>:	mov    rcx,QWORD PTR [rdx+0x2c8]
       0x000000000047cbb9 <+89>:	mov    rdx,QWORD PTR [rax-0x8]
       0x000000000047cbbd <+93>:	mov    rdi,QWORD PTR [rcx+0x8]
       0x000000000047cbc1 <+97>:	and    edx,0x3
       0x000000000047cbc4 <+100>:	or     rdx,rdi
       0x000000000047cbc7 <+103>:	mov    QWORD PTR [rdi],rsi
       0x000000000047cbca <+106>:	mov    QWORD PTR [rax-0x8],rdx
       0x000000000047cbce <+110>:	mov    QWORD PTR [rax-0x10],rcx
       0x000000000047cbd2 <+114>:	mov    QWORD PTR [rcx+0x8],rsi
       0x000000000047cbd6 <+118>:	pop    rbx
       0x000000000047cbd7 <+119>:	ret
    End of assembler dump.


PyTuple_New (2)
===============

OLD
---

C code::

    PyObject *
    PyTuple_New(Py_ssize_t size)
    {
        PyTupleObject *op;
        if (size == 0 && free_list[0]) {
            op = free_list[0];
            Py_INCREF(op);
            return (PyObject *) op;
        }
        op = tuple_alloc(size);
        if (op == NULL) {
            return NULL;
        }
        for (Py_ssize_t i = 0; i < size; i++) {
            op->ob_item[i] = NULL;
        }
        if (size == 0) {
            free_list[0] = op;
            ++numfree[0];
            Py_INCREF(op);          /* extra INCREF so that this is never freed */
        }
        tuple_gc_track(op);
        return (PyObject *) op;
    }


Assembly::

    (gdb) disassemble PyTuple_New
    Dump of assembler code for function PyTuple_New:
       0x00000000004f3ea0 <+0>:	test   rdi,rdi
       0x00000000004f3ea3 <+3>:	jne    0x4f3ec0 <PyTuple_New+32>
       0x00000000004f3ea5 <+5>:	mov    rax,QWORD PTR [rip+0x2ca934]        # 0x7be7e0 <free_list.lto_priv.4>
       0x00000000004f3eac <+12>:	test   rax,rax
       0x00000000004f3eaf <+15>:	je     0x4f3ec0 <PyTuple_New+32>
       0x00000000004f3eb1 <+17>:	add    QWORD PTR [rax],0x1
       0x00000000004f3eb5 <+21>:	ret
       0x00000000004f3eb6 <+22>:	nop    WORD PTR cs:[rax+rax*1+0x0]
       0x00000000004f3ec0 <+32>:	jmp    0x4f3e10 <PyTuple_New>
    End of assembler dump.

    (gdb) disassemble 0x4f3e10
    Dump of assembler code for function PyTuple_New:
       0x00000000004f3e10 <+0>:	push   r12
       0x00000000004f3e12 <+2>:	push   rbx
       0x00000000004f3e13 <+3>:	mov    rbx,rdi
       0x00000000004f3e16 <+6>:	sub    rsp,0x8
       0x00000000004f3e1a <+10>:	call   0x4f3d10 <tuple_alloc>
       0x00000000004f3e1f <+15>:	mov    r12,rax
       0x00000000004f3e22 <+18>:	test   rax,rax
       0x00000000004f3e25 <+21>:	je     0x4f3e76 <PyTuple_New+102>
       0x00000000004f3e27 <+23>:	test   rbx,rbx
       0x00000000004f3e2a <+26>:	jle    0x4f3e88 <PyTuple_New+120>
       0x00000000004f3e2c <+28>:	lea    rdx,[rbx*8+0x0]
       0x00000000004f3e34 <+36>:	lea    rdi,[rax+0x18]
       0x00000000004f3e38 <+40>:	xor    esi,esi
       0x00000000004f3e3a <+42>:	call   0x41c180 <memset@plt>
       0x00000000004f3e3f <+47>:	mov    rax,QWORD PTR [rip+0x2aac32]        # 0x79ea78 <_PyRuntime+568>
       0x00000000004f3e46 <+54>:	lea    rcx,[r12-0x10]
       0x00000000004f3e4b <+59>:	mov    rax,QWORD PTR [rax+0x10]
       0x00000000004f3e4f <+63>:	mov    rdx,QWORD PTR [rax+0x2c8]
       0x00000000004f3e56 <+70>:	mov    rax,QWORD PTR [r12-0x8]
       0x00000000004f3e5b <+75>:	mov    rsi,QWORD PTR [rdx+0x8]
       0x00000000004f3e5f <+79>:	and    eax,0x3
       0x00000000004f3e62 <+82>:	or     rax,rsi
       0x00000000004f3e65 <+85>:	mov    QWORD PTR [rsi],rcx
       0x00000000004f3e68 <+88>:	mov    QWORD PTR [r12-0x8],rax
       0x00000000004f3e6d <+93>:	mov    QWORD PTR [r12-0x10],rdx
       0x00000000004f3e72 <+98>:	mov    QWORD PTR [rdx+0x8],rcx
       0x00000000004f3e76 <+102>:	add    rsp,0x8
       0x00000000004f3e7a <+106>:	mov    rax,r12
       0x00000000004f3e7d <+109>:	pop    rbx
       0x00000000004f3e7e <+110>:	pop    r12
       0x00000000004f3e80 <+112>:	ret
       0x00000000004f3e81 <+113>:	nop    DWORD PTR [rax+0x0]
       0x00000000004f3e88 <+120>:	jne    0x4f3e3f <PyTuple_New+47>
       0x00000000004f3e8a <+122>:	add    DWORD PTR [rip+0x2ca9ef],0x1        # 0x7be880 <numfree.lto_priv.4>
       0x00000000004f3e91 <+129>:	mov    QWORD PTR [rip+0x2ca948],rax        # 0x7be7e0 <free_list.lto_priv.4>
       0x00000000004f3e98 <+136>:	add    QWORD PTR [rax],0x1
       0x00000000004f3e9c <+140>:	jmp    0x4f3e3f <PyTuple_New+47>
    End of assembler dump.


master
------

Code::

    PyObject *
    PyTuple_New(Py_ssize_t size)
    {
        PyTupleObject *op;
        PyInterpreterState *interp = _PyInterpreterState_GET();
        struct _Py_tuple_state *state = &interp->tuple;
        if (size == 0 && state->free_list[0]) {
            op = state->free_list[0];
            Py_INCREF(op);
            return (PyObject *) op;
        }
        op = tuple_alloc(state, size);
        if (op == NULL) {
            return NULL;
        }
        for (Py_ssize_t i = 0; i < size; i++) {
            op->ob_item[i] = NULL;
        }
        if (size == 0) {
            state->free_list[0] = op;
            ++state->numfree[0];
            Py_INCREF(op);          /* extra INCREF so that this is never freed */
        }
        tuple_gc_track(op);
        return (PyObject *) op;
    }

Assembly::

    Dump of assembler code for function PyTuple_New:
       0x000000000048bce0 <+0>:	push   r12
       0x000000000048bce2 <+2>:	push   rbp
       0x000000000048bce3 <+3>:	push   rbx
       0x000000000048bce4 <+4>:	mov    rax,QWORD PTR [rip+0x311d8d]        # 0x79da78 <_PyRuntime+568>
       0x000000000048bceb <+11>:	mov    rbx,rdi
       0x000000000048bcee <+14>:	mov    rbp,QWORD PTR [rax+0x10]
       0x000000000048bcf2 <+18>:	lea    rdi,[rbp+0x1610]
       0x000000000048bcf9 <+25>:	test   rbx,rbx
       0x000000000048bcfc <+28>:	jne    0x48bd40 <PyTuple_New+96>
       0x000000000048bcfe <+30>:	mov    r12,QWORD PTR [rbp+0x1610]
       0x000000000048bd05 <+37>:	test   r12,r12
       0x000000000048bd08 <+40>:	je     0x48bd20 <PyTuple_New+64>
       0x000000000048bd0a <+42>:	add    QWORD PTR [r12],0x1
       0x000000000048bd0f <+47>:	mov    rax,r12
       0x000000000048bd12 <+50>:	pop    rbx
       0x000000000048bd13 <+51>:	pop    rbp
       0x000000000048bd14 <+52>:	pop    r12
       0x000000000048bd16 <+54>:	ret
       0x000000000048bd17 <+55>:	nop    WORD PTR [rax+rax*1+0x0]
       0x000000000048bd20 <+64>:	xor    esi,esi
       0x000000000048bd22 <+66>:	call   0x48bbe0 <tuple_alloc>
       0x000000000048bd27 <+71>:	mov    r12,rax
       0x000000000048bd2a <+74>:	test   rax,rax
       0x000000000048bd2d <+77>:	jne    0x48bdb0 <PyTuple_New+208>
       0x000000000048bd33 <+83>:	xor    r12d,r12d
       0x000000000048bd36 <+86>:	pop    rbx
       0x000000000048bd37 <+87>:	pop    rbp
       0x000000000048bd38 <+88>:	mov    rax,r12
       0x000000000048bd3b <+91>:	pop    r12
       0x000000000048bd3d <+93>:	ret
       0x000000000048bd3e <+94>:	xchg   ax,ax
       0x000000000048bd40 <+96>:	mov    rsi,rbx
       0x000000000048bd43 <+99>:	call   0x48bbe0 <tuple_alloc>
       0x000000000048bd48 <+104>:	mov    r12,rax
       0x000000000048bd4b <+107>:	test   rax,rax
       0x000000000048bd4e <+110>:	je     0x48bd33 <PyTuple_New+83>
       0x000000000048bd50 <+112>:	test   rbx,rbx
       0x000000000048bd53 <+115>:	jle    0x48bd68 <PyTuple_New+136>
       0x000000000048bd55 <+117>:	lea    rdx,[rbx*8+0x0]
       0x000000000048bd5d <+125>:	lea    rdi,[rax+0x18]
       0x000000000048bd61 <+129>:	xor    esi,esi
       0x000000000048bd63 <+131>:	call   0x41c180 <memset@plt>
       0x000000000048bd68 <+136>:	mov    rax,QWORD PTR [rip+0x311d09]        # 0x79da78 <_PyRuntime+568>
       0x000000000048bd6f <+143>:	lea    rcx,[r12-0x10]
       0x000000000048bd74 <+148>:	mov    rax,QWORD PTR [rax+0x10]
       0x000000000048bd78 <+152>:	mov    rdx,QWORD PTR [rax+0x2c8]
       0x000000000048bd7f <+159>:	mov    rax,QWORD PTR [r12-0x8]
       0x000000000048bd84 <+164>:	mov    rsi,QWORD PTR [rdx+0x8]
       0x000000000048bd88 <+168>:	and    eax,0x3
       0x000000000048bd8b <+171>:	or     rax,rsi
       0x000000000048bd8e <+174>:	mov    QWORD PTR [rsi],rcx
       0x000000000048bd91 <+177>:	mov    QWORD PTR [r12-0x8],rax
       0x000000000048bd96 <+182>:	mov    rax,r12
       0x000000000048bd99 <+185>:	mov    QWORD PTR [r12-0x10],rdx
       0x000000000048bd9e <+190>:	mov    QWORD PTR [rdx+0x8],rcx
       0x000000000048bda2 <+194>:	pop    rbx
       0x000000000048bda3 <+195>:	pop    rbp
       0x000000000048bda4 <+196>:	pop    r12
       0x000000000048bda6 <+198>:	ret
       0x000000000048bda7 <+199>:	nop    WORD PTR [rax+rax*1+0x0]
       0x000000000048bdb0 <+208>:	add    DWORD PTR [rbp+0x16b0],0x1
       0x000000000048bdb7 <+215>:	mov    QWORD PTR [rbp+0x1610],rax
       0x000000000048bdbe <+222>:	add    QWORD PTR [rax],0x1
       0x000000000048bdc2 <+226>:	jmp    0x48bd68 <PyTuple_New+136>
    End of assembler dump.


master COLD
===========

Using ``cold`` attribute.

Assembly::

    Dump of assembler code for function PyTuple_New:
    Address range 0x47d4c0 to 0x47d4e9:
       0x000000000047d4c0 <+0>:	mov    rax,QWORD PTR [rip+0x2f8a71]        # 0x775f38 <_PyRuntime+568>
       0x000000000047d4c7 <+7>:	mov    rdx,QWORD PTR [rax+0x10]
       0x000000000047d4cb <+11>:	test   rdi,rdi
       0x000000000047d4ce <+14>:	jne    0x41d76c <PyTuple_New.cold>
       0x000000000047d4d4 <+20>:	mov    rax,QWORD PTR [rdx+0x1610]
       0x000000000047d4db <+27>:	test   rax,rax
       0x000000000047d4de <+30>:	je     0x41d76c <PyTuple_New.cold>
       0x000000000047d4e4 <+36>:	add    QWORD PTR [rax],0x1
       0x000000000047d4e8 <+40>:	ret
    Address range 0x41d76c to 0x41d77e:
       0x000000000041d76c <-392532>:	add    rdx,0x1610
       0x000000000041d773 <-392525>:	mov    rsi,rdi
       0x000000000041d776 <-392522>:	mov    rdi,rdx
       0x000000000041d779 <-392519>:	jmp    0x41d5f3 <tuple_new_slowpath>
    End of assembler dump.
