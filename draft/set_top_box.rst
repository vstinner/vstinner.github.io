July 2012-October 2013.

Working on embedded devices is not trivial. I would like to tell you the story
of my previous job. I was responsible of fixing all bugs from the hardware to
the top-level application. It was a set top box ("STB" or just "box") to watch
television, record programs, buy movie (video on demand), etc. The customer
required that our software survived a stresstest for 1 week. When I started to
work on that, it crashed after 1 hour.

The first weeks, it was easy to identify bugs and to report them to the
maintainer of each component. We were making progress everyday, it was fine.

Slowly, some of my colleagues were reaffected to other projets. At the same
time, it took more and more time to reproduce bugs: some bugs took an half day
to be reproduced, so we had to be careful to add enough debug information to
guess what the bug could be.

We started to develop more and more tools around the product. One practical
issue for me was to upload the new image of the system. It took me between 10
and 30 minutes because I had to access a very complex UI written in slow Java,
reboot the box, hold pressing 3 keys and hope that everything will be fine.  If
you made a mistake, you had to use the urgency system restore which added 10 to
20 additional minutes. And it was easy to make a mistake. Sometimes, I
copied-paste the wrong MAC address. Sometimes, I forgot to click a button. The
update required a lot of small steps, nothing was automated. I tried but failed
to automate the "firmware upgrade" because of the giant Java application which
had no accessible API from the outside.

If I recall correctly, the box was part of a testing network in Belgium and we
had a VPN connected through dedicated link.

One of my practical issue was to get more boxes. At some point, reproducing a
single bug took at least 1 day. Having multiple boxes increased the chance of
seeing a bug and allowed me to debug while other boxes were hunting new bugs
for me. I had to wait until a colleague moved to a new team or left the company
to get a second box. I also requested a second television: the application was
very visual and I had to carefully watch the application to check if there were
any glitch. It took me at 6 months to get 3 boxes with 3 televisions. 3
televisions + the monitor of my desktop computer took a lot of space on my
desk.  I had a physical wall between me and my colleagues. I had to stand up
to talk to them.

After 6 months of fixing random bugs, the product became more stable but still
didn't respect the constraint of surviving 7 days of stresstests. Boxes started
to crash after 3 to 5 days. The testing team installed a wall of 10 boxes
with 10 televisions to help me hunting bugs.

At some point, we started to notice a visual bug in the television: a large
part of the screen became black until reboot. The bug was not in the software.
My colleagues who know their stuff identified the bug in the firmware of the
HDMI chip. We called the vendor of this chip, but the team who was working on
this chip left the company. I'm not sure how our CEO negociated that, but
someone from this vendor came into our company and succeeded to fix the bug!
Impressive stuff.

I started to notice crashes in the Linux kernel. Thanks to the help of
colleagues, I succeeded to get Linux kernel logs in a serial line (technically,
it was a USB connector on the computer side) and set up a serial port terminal
to see these logs. After some time, we were able to reproduce the bug and see
logs: it was something related to the network card driver. The bug occurred
when the system memory was very low. I am not sure that I understood correctly,
but the driver didn't handle properly a memory allocation failure. Some bugs
were fixed, but also tuned the system to ensure that the kernel always has 1
MiB of memory.

About memory, the hardware had a special kind of memory. There was 128 MiB of
regular memory, and 128 MiB of "video" memory. Technically, it was possible to
access this memory for applications running in the user-space, with some tricks
on the memory allocators. We patched Python to get access to this memory and
we allocated a fixed chunk of memory (maybe 10 MiB, I don't recall). For such
hardware, you have to keep track of megabyte of memory: memory is expensive.

Python used something like 21 MiB of "resident" memory ("RSS" is ps), but the
whole system crashed if it used more than 22 MiB of memory. Sadly, there was
a memory leak. I recall that I used Valgrind to try to debug some memory
corrupted in applications written in C or C++. The architecture was MIPS,
Valgrind didn't support officially MIPS. The vendor provides a "BSP": Linux
kernel, compiler (gcc), libc (uclic), and a few tools like patched Valgrind.
When I tried it, Valgrind quickly crashed.

I tried a few other "memory debuggers", but I failed to use them or they didn't
find anything useful.

To debug Python memory leaks, I tried Heapy, Pympler and Melia. Heapy and
Pympler required to patch Python. Melia rendered a funky picture which wasn't
really useful. At the end, most of these tools said that most of memory was
used by "dict", "tuple" and "str" types... But most Python objects use these
types internally, it's not helpful at all. I started to write a tool which
logged all memory allocation and all memory deallocations. When I ran the
application for 10 minutes, it tooks something like 10 minutes to transfer the
large log file. Hopefully, the box had a large disk to store video. Then it
took a while to parse these logs to try to identifiy leaks. The whole process
was way too slow and inefficient.

The transfer was the bottleneck, so I redesigned my tool to compute a state
of memory allocations. Rather than logging malloc/free, the tool kept an up to
date state of all currently allocated memory blocks. It was a hash table
mapping a memory addresss (pointer) to a "trace" (light Python traceback).

Then I wrote a tool to dump this state on disk. The state was less than 1 MiB,
it was quick to transfer it to a faster computer. Thanks to that, it became
possible to compare two states to compute the differences. Using that, it is
way simpler to identify memory leaks: the tool listed line numbers in Python
files which reduces a lot of time needed to audit the code.

Thanks to this tool, we identified a reference leak in the "IML": interactive
pages similar to HTML but way simpler, something similar to a lightway
webbrowser. Fixing these memory leaks allowed was enough to be able to go to
the next steps.

Tests had to run for 3 to 5 days... but it was common to get a network outage
for the whole building, or even power outage. First time that I was that,
but it was quite common in the whole city sadly. At each failure, the tests
had to be restarted from scratch. After a power outage, all developers gone
to the coffee machine to make a break, since it took 1 to 2 hours for sysadmins
to restart servers.

I don't recall how, but we also identified a bug in atomic operations. It was a
bug in the libc or the compiler, I don't recall. I was amazing that such bug
can exist and that my colleagues were able to understand that we had such bug.

Working for this company was challenging, I learnt plently of stuff. But there
were things that I didn't like. It took me a while to publish the tool to track
Python memory leaks. Later, I understood that it was the first time ever that
the company published code under an open source license! By the way, I had
to basically rewrite the whole implementation (first to get ride of the glib
dependency) and to change the design (remote filters) when I wrote a PEP.
I also wrote a PEP to allow to plug your own memory allocators in Python.

There was a QA team of 5 or maybe 10 people, I don't recall. The team was
mostly testing manually the product. They used physical remote controller and
had testing plans to test different features of the product step by step. A
full test campain took a big week. The customer started to request releases
more frequently, but the management had a great idea: pay the QA test to work
late and during weekends! Well... It worked...

While I was fixing very low-level bugs, my colleagues working on the UI also
had to fix bugs, but we introduced regressions. It was strange, like fix
a bug in feature A broke the feature B which has no relationship. I started
to complain that we should have more automated tests. The QA team had the
hardware (something to send IR signals using a computer), the software (analyze
the television to identify text or numbers) and the knowledge to automate tests.
But the managment never accepted that it was worth it. I understood their
position as it would be cheaper to continue to test manually. The problem was
that the development took 1 year instead of 6 months. And we started to have
to pay because the delivery was too late.

Moreover, another team had the hardware (to turn off and turn on again a box)
and software to test the product. A colleague estimated that it would take
3 days to write a proof-of-concept of automated test. My experience with Python
buildbots told me that it would take more something like 3 weeks to get an
usable CI. Anyway, the management did nothing and we had zero automated tests.

Near the end of the project, I had a daily meeting with my manager, it was
basically him and him. He kept asking me for progress. I always replied "it
takes 1 week to reproduce a bug, the test started 1 day ago, I have no clue at
this point". After 1 month of such meetings, I asked him to stop these meetings
and I will keep him up to date. I don't know how it happened exactly, likely a
conflict between my manager and my N+2 (manager of my manager), but suddently,
I got 2 daily meetings instead of 1. No kidding.

One day, my back was blocked. I had to stop working for a few days. I
understood that my body was telling me to slow down: too much pressure.

On one side, the job was really exciting: a new challenge every single day!
On the other side, the lack of automated test, closed source software with DRM
and the management decided me to quit he company.

The worst part is that they didn't try to keep me. When I asked to get a
promotion, they told me that I was complaining too much and I was spreading my
bad mood on my colleagues.

I applied for a new job. A asked a salary increase which looked crazy to me,
and told me that if the employer accepts it, I had to take the job. They
offered me a job with the salary that I requested 1 day after my interview.
I accepted. Then I started a new great journey at Enovance! And I restarted
to work remotely.
