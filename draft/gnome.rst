++++++++++++++++++++++++++++++
Debug Graphics issues in GNOME
++++++++++++++++++++++++++++++

:date: 2019-09-11 15:30
:tags: linux
:category: linux
:slug: debug-graphics-issues-gnome
:authors: Victor Stinner

Wayland
=======

This section is unrelated to Hybrid Graphics, but useful to debug graphics
issues.

Do I use Wayland?
-----------------

Is "type wayland" found in the loginctl session status? ::

    $ loginctl session-status|grep Service:
    Service: gdm-password; type wayland; class user

Is ``WAYLAND_DISPLAY`` environment variable set? ::

    $ env|grep -E '^(XDG_SESSION_TYPE|WAYLAND_DISPLAY|DISPLAY)'
    XDG_SESSION_TYPE=wayland
    WAYLAND_DISPLAY=wayland-0
    DISPLAY=:0

Is Xwayland running? ::

    $ ps ax|grep Xwayland
     1956 tty2     Sl+    6:38 /usr/bin/Xwayland :0 ...

In GNOME Shell, Mutter spawns Xwayland and sets the ``DISPLAY`` environment
variable which is inherited by child processes: all graphical applications
started in GNOME.


Is this application using Wayland or Xorg?
------------------------------------------

The ``xprop`` program can be in Wayland to check if an application is using
Xorg or Wayland: the mouse cursor becomes a cross only and only if the
application is used Xorg (X11 API).

Opt-in for Wayland
------------------

To opt-in for Wayland support in **Firefox** and Thunderbird, set ``MOZ_ENABLE_WAYLAND=1`` environment variable.

For example, I put the following line into ``/etc/environment`` to run Firefox
with Wayland::

    MOZ_ENABLE_WAYLAND=1

When a Wayland compositor is running, Gtk applications prefer Wayland by
default. In that case, you can opt-in for X11 by seting ``GDK_BACKEND=x11``
environment variable.


GNOME
=====

`GNOME <https://www.gnome.org/>`_ desktop made of multiple components:

* `Mutter <https://en.wikipedia.org/wiki/Mutter_(software)>`_: compositor
  supportting Xorg and Wayland, use **Clutter** library
* `libinput <https://wayland.freedesktop.org/libinput/doc/latest/>`_:
  library that provides a full input stack for display servers and other
  applications that need to handle input devices provided by the kernel.
  Try ``sudo libinput list-devices`` and ``sudo libinput debug-events``
  commands.
* `GJS <https://gitlab.gnome.org/GNOME/gjs/wikis/Home>`_: Javascript Bindings
  for Gnome, use Mozilla SpiderMonkey. Provide "gjs" program which can run
  Javascript in the command line.
* `Xwayland <https://wayland.freedesktop.org/xserver.html>`_: X server using
  Wayland compositor
* `GNOME Shell <https://en.wikipedia.org/wiki/GNOME_Shell>`_ is the GNOME
  desktop environment. It is written in C and JavaScript as a plugin for
  Mutter. It's the **gnome-shell** program. Main features:

  * Handle inputs using **libinput** library
  * Wayland compositor using **Mutter** (as a library)
  * Run shell extensions written in Javascript using **GJS** (as a library)

Mutter spawns Xwayland and sets the ``DISPLAY`` environment variable which
is inherited by child processes: all graphical applications started in GNOME.


