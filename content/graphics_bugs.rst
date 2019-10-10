++++++++++++++++++++++++++++++++++
Graphics bugs in Firefox and GNOME
++++++++++++++++++++++++++++++++++

:date: 2019-10-10 17:00
:tags: linux
:category: linux
:slug: graphics-bugs-firefox-gnome
:authors: Victor Stinner

After explaining how to `Debug Hybrid Graphics issues on Linux
<{filename}/hybrid_graphics.rst>`_, here is the story of four graphics bugs
that I had in GNOME and Firefox on my Fedora 30 between May 2018 and September
2019: bugs in gnome-shell, Gtk, Firefox and mutter.

.. image:: {static}/images/glitch.jpg
   :alt: Glitch
   :target: https://www.flickr.com/photos/34298393@N06/14488759356/


gnome-shell freezes
===================

In May 2018, six months after I got my Lenovo P50 laptop, gnome-shell was
"sometimes" freezing between 1 and 5 seconds. It was annoying because key
stokes created repeated keys writing "helloooooooooooooooooooooo" instead of
"hello" for example.

My colleagues led my to ``#fedora-desktop`` of the GIMP IRC server where I met
my colleague **Jonas Ådahl** (jadahl) who almost immediately identified my
issue! Extract of the IRC chat:

::

    15:03 <vstinner> hello. i upgraded from F27 to F28, and it seems like I
        switched from Xorg to Wayland. sometimes, the desktop hangs a few
        milliseconds (less than 2 secondes)
    15:03 <vstinner> bentiss told me that  "libinput error: client bug: timer
        event7 keyboard: offset negative (-39ms)" can occur when shell is too
        slow
    15:04 <vstinner> journalctl shows me frenquently the bug
        https://gitlab.gnome.org/GNOME/gnome-shell/issues/1 "Object
        Shell.GenericContainer (0x559e6bfddc60), has been already finalized.
        Impossible to get any property from it."
    15:04 <vstinner> i also get "Window manager warning: last_user_time
        (3093467) is greater than comparison timestamp (3093466).  This most
        likely represents a buggy client sending inaccurate timestamps in
        messages such as _NET_ACTIVE_WINDOW.  Trying to work around..." errors
        in logs (from shell)
    15:05 <vstinner> bentiss: ah, i also get "libinput error: client bug: timer
        event7 trackpoint: offset negative (-352ms)" errors
    15:06 <vstinner> it's a recent laptop, Lenovo P50: 32 GB of RAM, 4 physical
        CPUs (8 threads) Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz
    15:06 <vstinner> so. what can i do to debug such performance issue? may it
        come from shell? what does it mean if shell is slow? can it be a GPU
        issue?  a javascript issue?
    ...
    15:13 <jadahl> vstinner: whats your hardware? Do you have a hybrid gpu
        system?
    15:13 <jadahl> ah, yes P50
    15:14 <jadahl> vstinner: there is a branch on mutter upstream that fixes
        that issue. want to compile it to test?


Ten minutes after I asked my question, Jonas asked the right question: **Do you
have a hybrid gpu system?**

I was able to workaround the issue by connecting my laptop to my TV using the
HDMI port::

    15:22 < jadahl> for example, IIRC if you have a monitor connected to the
        HDMI, the issue will go away since the secondary GPU is always awake
        anyway
    ...
    15:31 < vstinner> jadahl: i plugged a HDMI cable to my TV and it seems like
        the issue is gone
    15:31 < vstinner> jadahl: impressive

When an external monitor is used (like a TV plugged on the HDMI port), my
NVIDIA GPU is always active which works around the bug I had in gnome-shell.

Jonas provided me a RPM package for Fedora including his work-in-progress fix:
`Upload HW cursor sprite on-demand
<https://gitlab.gnome.org/GNOME/mutter/merge_requests/106>`_. I confirmed that
this change fixed my bug. His mutter change has been merged upstream.

Firefox crash when selecting text
=================================

In March 2019, Firefox with Wayland crashed on ``wl_abort()`` when selecting
more than 4000 characters in a ``<textarea>``. I found the bug in Gmail when
selecting the whole email text to remove it. Pressing **CTRL + A** or
Right-click + Select All **crashed the whole Firefox process!**

I reported the bug to Firefox: `Firefox with Wayland crash on wl_abort() when
selecting more than 4000 characters in a <textarea>
<https://bugzilla.mozilla.org/show_bug.cgi?id=1539773>`_.

Running gdb in Firefox caused me some troubles since it's a very large binary with
many libraries. I also read `Wayland protocol specifications
<https://cgit.freedesktop.org/wayland/wayland-protocols/tree/unstable/text-input/text-input-unstable-v3.xml#n138>`_.
I managed to analyze the bug and so I reported the bug to Gtk as well, `On
Wayland, notify_surrounding_text() crash on wl_abort() if text is longer than
4000 bytes <https://gitlab.gnome.org/GNOME/gtk/issues/1783>`_:

    According to gdb, ``wl_proxy_marshal_array_constructor_versioned()`` calls
    ``wl_abort()`` because the buffer is too short. It seems like
    ``wl_buffer_put()`` fails with ``E2BIG``.

Quickly, I identified that **my Gtk bug has already been fixed 3 months before
by Carlos Garnacho** (`imwayland: Respect maximum length of 4000 Bytes on
strings being sent <https://gitlab.gnome.org/GNOME/gtk/merge_requests/438>`_)
and **the fix is part of gtk-3.24.3** ("wayland: Respect length limits in text
protocol" says "Overview of Changes in GTK+ 3.24.3").

I requested to upgrade Gtk in Fedora. But it was not possible since the newer
version changed the theme. I was asked to cherry-pick the fix and that's what I
did: `imwayland: Respect maximum length of 4000 Bytes on strings
<https://src.fedoraproject.org/rpms/gtk3/pull-request/5>`_.

My PR was merged and a new package was built. I tested it and confirmed that it
fixed the crash: `FEDORA-2019-d67ec97b0b
<ttps://bodhi.fedoraproject.org/updates/FEDORA-2019-d67ec97b0b>`_. Soon, the
package was pushed to the public Fedora package repository.

**That's the cool part about open source: if you have the skills to hack the
code, you can fix an annoying which is affecting you!**


Firefox: [Wayland] Window partially or not updated when switching between two tabs
==================================================================================

Analyze the bug
---------------

In September 2019, after a large system upgrade (install 6 packages, upgrade
234 packages, remove 5 packages), Firefox started to not update the window
content sometimes when I switched from one tab to another. Example:

.. image:: {static}/images/firefox_bug_1.jpg
   :alt: Firefox bug of window partially updated

It took me a few hours to analyze the bug to be able to produce an useful bug
report.

I followed Fedora's guide `How to debug Firefox problems
<https://fedoraproject.org/wiki/How_to_debug_Firefox_problems>`_ advices.

First, I tried to **understand which GPU driver is used**. I finished by
blacklisting the nouveau driver in the Linux kernel, to ensure that Firefox was
using my Intel IGP. I still reproduced the bug.

I **disabled all Firefox extensions**: bug reproduced.

Then I created a new Firefox profile and started Firefox in **safe mode**: bug
reproduced.

I tested the latest Firefox binary from mozilla.org (Firefox 69.0): bug
reproduced.

Finally, **I tested Firefox Nightly** from mozilla.org (Firefox 71.0a1): bug
reproduced.

Ok, it was enough data to produce an interesting bug report. I reported
`[Wayland] Window partially or not updated when switching between two tabs
<https://bugzilla.mozilla.org/show_bug.cgi?id=1580152>`_ to Firefox.

Identify the regression using Fedora packages
---------------------------------------------

Then I looked at ``/var/log/dnf.log`` and I tried to identify which package
update could explain the regression.

I downgraded **gtk3**-3.24.11-1.fc30.x86_64 to gtk3.x86_64 3.24.10-1.fc30: bug
reproduced.

I rebooted on oldest available **Linux kernel**, version 5.2.8-200.fc30.x86_64:
bug reproduced. I checked journalctl logs to check which Linux version I was
running whhen the bug was first seen: Linux 5.2.9-200.fc30.x86_64.

I don't know why, but **downgrading Firefox was only my 3rd test**.

I downgraded firefox-69.0-2.fc30.x86_64 to firefox-68.0.2-1.fc30.x86_64: the
bug is gone! Ok, so **the regression comes from the Firefox package**, and it
was introduced between package versions 68.0.2-1.fc30 and 69.0-2.fc30.

On IRC, I met my colleague **Martin Stránský** who package Firefox for Fedora.
He told me that he is aware of my bug and may have a fix for my bug. Great!

Only 9 days later, **Martin Stránský** fix has been merged in Firefox upstream,
released in Firefox Nightly, and a new package has been shipped in Fedora 30!
Thanks Martin for your efficiency!

The final Firefox change is quite large and intrusive: `[Wayland] Fix rendering
glitches on wayland
<https://hg.mozilla.org/releases/mozilla-beta/rev/3281a617f22b>`_


Xwayland crash in xwl_glamor_gbm_create_pixmap()
================================================

In September 2019, while I was debugging the previous Firefox bug, I started my
IRC client hexchat.  Suddently, **Xwayland crashed which closed my whole Gnome
session**!  I was testing various GPU configurations to analyze the Firefox
bug.

ABRT managed to rebuild an useless traceback and identified an existing bug
report. It added my coment to `[abrt] xorg-x11-server-Xwayland:
OsLookupColor(): Segmentation fault at address 0x28
<https://bugzilla.redhat.com/show_bug.cgi?id=1729200#c20>`_ report.

At July 26, 2019 (1 month before I got the bug), **Olivier Fourdan** added `an
interesting comment <https://bugzilla.redhat.com/show_bug.cgi?id=1729200#c9>`_:

  ``glamor_get_modifiers+0x767`` is ``xwl_glamor_gbm_create_pixmap()`` so this
  is the same as `bug 1729925
  <https://bugzilla.redhat.com/show_bug.cgi?id=1729925>`_ fixed upstream with
  `xwayland: Do not free a NULL GBM bo
  <https://gitlab.freedesktop.org/xorg/xserver/merge_requests/242>`_.

So in fact, my bug was already fixed by **Olivier Fourdan** in Xwayland
upstream, but the fix didn't land into Fedora yet.


Thanks!
=======

I would like to thank the following developers who fixed my Fedora 30. What a
coincidence, all four are my collagues! It seems like Red Hat is investing in
the Linux desktop :-)

`Carlos Garnacho <https://blogs.gnome.org/carlosg/>`_ (Red Hat).

.. image:: {static}/images/carlos_garnacho.jpg
   :alt: Carlos Garnacho
   :target: https://www.flickr.com/photos/183829480@N06/48623543091/in/pool-14662216@N23/

`Jonas Ådahl <https://gitlab.gnome.org/jadahl>`_ (Red Hat).

.. image:: {static}/images/jonas_adahl.jpg
   :alt: Jonas Ådahl
   :target: https://www.flickr.com/photos/183829480@N06/48623189663/in/pool-14662216@N23/

`Martin Stránský <http://people.redhat.com/stransky/>`_ (Red Hat).

.. image:: {static}/images/mstransky.jpg
   :alt: Martin Stránský
   :target: http://people.redhat.com/stransky/

`Olivier Fourdan <https://en.wikipedia.org/wiki/Olivier_Fourdan>`_ (Red Hat).

.. image:: {static}/images/olivier_fourdan.jpg
   :alt: Olivier Fourdan
   :target: https://en.wikipedia.org/wiki/Olivier_Fourdan
