https://twitter.com/VictorStinner/status/1481783100191428611

Last month, a Kodi user reported a crash on Python 3.9 with a reproducer:
https://bugs.python.org/issue46070 The reproducer was not reliable. It took me
a while to trigger the crash in Visual Studio to get a debugger 🧐 It's a C
debugger. I need tricks to inspect Python objects & frames.

It is a crash 💣 on deallocating the _sre.compile() method in a
sub-interpreter: https://bugs.python.org/msg408662 The PyGC_Head._gc_prev
pointer is a dangling pointer 👻, structure used by the garbage collector 🗑️.
The crash can only be reproduced with Python 3.9 on Windows!

When I modified the reproducer, I found a bug 🦋 in _asyncio extension, which
has been fixed, but was unrelated 😒 git bisect took me a while, since the bug
was hidden by another change: change 1 adds bug, change 2 hides it, change 3
shows again the bug: https://bugs.python.org/msg410010

The regression was introduced by a change that I made 2 years ago 😱, make the
GC state per-interpreter:
https://github.com/python/cpython/commit/7247407c35330f3f6292f1d40606b7ba6afd5700
I failed to reproduce the issue on Linux, I tried 4 different memory
allocators! Out of time, I prepared a PR to revert my change 😥

But I still NEED to understand what's going on 😡... During a garbage
collection, PyGC_Head._gc_prev is used a for a different purpose (refs+flags).
Maybe interpreter 2 uses an object while interpreter 1 is running a GC
collection 🗑️? There are 2 references to the compile method.

[PHOTO 1]

I modified faulthandler to dump all tracebacks and log if an interpreter is
running a GC: it is not the case 😭. By the way, an object CANNOT be tracked by
two different GC at the same time: _PyObject_GC_TRACK() has an assertion
preventing that 🧐.

Oh, a method creates a reference cycle 😮! Is the GC required to break it? 🧐
Also, it seems like the internal dict copy is NOT tracked by the GC 😮! How
does _PyObject_GC_UNTRACK() really remove the object from a GC list? It
modifies the previous object which is FREED memory!

[PHOTO 2]

I modified PyObject to store in which interpreter an object has been created, and I logged when the method is deallocated 🧐:
"meth_dealloc(compile): m->ob_interp=000001EC1846F2A0, interp=000001EC184AB790"
The method is deallocated in a different interpreter! 😮

Moreover, the interpreter in which the method was created was already destroyed
and so its GC state became freed memory 👻! Details:
https://bugs.python.org/msg410493

How is the compile method stored in the GC list 🗑️? Oh, and by the way, how are
this GC list and objects really stored in memory? What happens when the memory
is freed 👻?

[PHOTO 3]

At the end, I wrote a simple fix 🥳: just untrack all objects when a GC is
destroyed:
https://github.com/python/cpython/commit/1a4d1c1c9b08e75e88aeac90901920938f649832
When _PyObject_GC_UNTRACK() is called later in a different interpreter, prev
and next objects are NULL rather than being dangling pointers 👻, and Python no
longer crash!

I hope you enjoyed this journey in debugging a random crash in sub-interpreters
on Windows with Python 3.9 😊 I'm happy that I avoided a revert and managed to
find a real FIX for that bug 🥳! The fix has a minor impact on performance at
exit, but it only impacts sub-interpreters.

Many assumptions that I made during my analysis were wrong 😮. It is easy to
follow the wrong path for too long, and fall into dead end ⛔️. Go backward and
try a different path. Making a break (or a nap 😴) helps 😉!
