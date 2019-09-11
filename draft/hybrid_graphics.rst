++++++++++++++++++++++++++++++++++
Bugs with Hybrid Graphics on Linux
++++++++++++++++++++++++++++++++++

:date: 2019-09-11 01:00
:tags: linux
:category: linux
:slug: bugs-hybrid-graphics-linux
:authors: Victor Stinner

`Hybrid Graphics <https://wiki.archlinux.org/index.php/Hybrid_graphics>`_ is a
complex hardware and software solution to increase the laptop battery autonomy:
a fast GPU is turned on an off automatically on demand, whereas a slow GPU is
used by default.

If it is designed and implemented carefully, users should not notice that a
laptop has two graphical devices.

Sadly, the Linux implementation is not perfect yet. Recent bugs motivated me to
write down an article about it.

Hybrid graphics
===============

Hybrid graphics have different names:

* "Dual GPUs"
* `vgaswitcheroo
  <https://www.kernel.org/doc/html/latest/gpu/vga-switcheroo.html>`_ in the
  Linux kernel
* `PRIME <https://wiki.archlinux.org/index.php/PRIME>`_ in Linux open source
  GPU drivers; the "muxless" flavor of hybrid graphics
* `Bumblebee <https://wiki.archlinux.org/index.php/bumblebee>`_:
  `NVIDIA Optimus <https://wiki.archlinux.org/index.php/NVIDIA_Optimus>`_
  for Linux
* "AMD Dynamic Switchable Graphics" for Radeon
* etc.

Laptop hybrid graphics come in two flavors:

* "muxed": Dual GPUs with a multiplexer chip to switch outputs between GPUs.
* "muxless": Dual GPUs but only one of them is connected to outputs. The other
  one is merely used to offload rendering, its results are copied over PCIe
  into the framebuffer. On Linux this is supported with **DRI PRIME**.

The development to support hybrid graphics in Linux started in 2010.

This article is about the Linux kernel vgaswitcheroo with the muxless PRIME
solution.

Why two GPUs?
=============

Power consumption: better laptop autonomy.

NVIDIA GPUs are powerful and consumes more power than Intel integrated devices
("IGP") which are less powerful.

Do I have two GPUs?
===================

On Linux, check if ``/sys/kernel/debug/vgaswitcheroo/`` directory exists.

Single GPU::

    $ sudo cat /sys/kernel/debug/vgaswitcheroo/switch
    cat: /sys/kernel/debug/vgaswitcheroo/switch: No such file or directory

Example with 2 GPUs::

    $ sudo cat /sys/kernel/debug/vgaswitcheroo/switch
    0:IGD:+:Pwr:0000:00:02.0
    1:DIS: :DynOff:0000:01:00.0


Hardware
========

My work gave me a Lenovo P50 laptop to work. It is my single computer at home,
so I needed a powerful laptop, even if it's heavy. The CPU, RAM and battery
are great, but the "dual GPU" design is causing some issues on Linux.

My Lenovo P50 has two GPUs::

    $ lspci|grep -i VGA
    00:02.0 VGA compatible controller: Intel Corporation HD Graphics 530 (rev 06)
    01:00.0 VGA compatible controller: NVIDIA Corporation GM107GLM [Quadro M1000M] (rev a2)

* Intel HD Graphics 530: **integrated GPU** ("IGP"). Low power consumption.
* NVIDIA Corporation GM107GLM [Quadro M1000M]: **discrete** GPU, powerful
  but uses more power than the IGP.

I didn't know that that the laptop had 2 GPUs when I chose the laptop model. I
only had the 3 choices between 3 models, I didn't look at specs in depth. I
started to real about "dual GPUs" when I started to get issues.

It is not easy to guess which graphic device is connected to which output.
When I disabled the nouveau driver (see below), I was no longer able to use
external monitors. I understood that:

* The Intel IGP is connected to the internal laptop screen
* The NVIDIA GPU is connected to the external monitors


BIOS
====

Hybrid graphics can be configured and/or disabled in the BIOS:

* Discrete Graphics mode will archieve higher graphics performances.
* Hybrid Graphics mode runs as Integrated Graphics mode to archieve longer
  battery life, and Discrete Graphics is enabled on demand.

On my Lenovo P50, **Discrete Graphics** removes "00:02.0 VGA compatible
controller: Intel Corporation HD Graphics 530" from ``lspci`` command output:
the Intel IGP is fully disabled.


Default GPU?
============

The GPU that is enabled by the BIOS during boot may be dependent on whether the
laptop is plugged into AC power or not.


Linux kernel
============

On Linux, dual GPU setup is handled by **vgaswitcheroo**::

    $ journalctl -b 0 -k|grep 'VGA switcheroo'
    Sep 11 02:29:54 apu kernel: VGA switcheroo: detected Optimus DSM method \_SB_.PCI0.PEG0.PEGP handle

    $ sudo cat /sys/kernel/debug/vgaswitcheroo/switch
    0:IGD:+:Pwr:0000:00:02.0
    1:DIS: :DynPwr:0000:01:00.0

DSM stands for (ACPI) "Device-Specific Method".

* ``IGD`` stands for **Integrated** Graphics Device
* ``DIS`` stands for **DIScrete** Graphics Device
* ``+`` marks the **active** card

The last field is related to the PCI identifier::

    $ lspci|grep -i VGA
    00:02.0 VGA compatible controller: Intel Corporation HD Graphics 530 (rev 06)
    01:00.0 VGA compatible controller: NVIDIA Corporation GM107GLM [Quadro M1000M] (rev a2)

See `Linux kernel documentation: VGA Switcheroo
<https://www.kernel.org/doc/html/latest/gpu/vga-switcheroo.html>`_.

Xorg
====

Get OpenGL info::

    $ glxinfo|grep -E 'Device|direct rendering'
    direct rendering: Yes
        Device: Mesa DRI Intel(R) HD Graphics 530 (Skylake GT2)  (0x191b)

My Intel IGP is currently used.

DRI_PRIME environment variable
==============================

Setting DRI_PRIME=1 environment variable when running an application forces the usage
of the **discrete** (powerful) GPU. Example on my laptop::

    $ DRI_PRIME=1 glxinfo|grep -E 'Device|rendering'
    direct rendering: Yes
        Device: NV117 (0x13b1)

Wayland
=======

Wait, am I running Wayland? ::

    # Is "type wayland" found in the loginctl session status?
    $ loginctl session-status|grep Service:
    Service: gdm-password; type wayland; class user

    # Is WAYLAND_DISPLAY present?
    # DISPLAY is set by Xwayland for X11 applications
    $ env|grep -E '^(XDG_SESSION_TYPE|WAYLAND_DISPLAY|DISPLAY)'
    XDG_SESSION_TYPE=wayland
    WAYLAND_DISPLAY=wayland-0
    DISPLAY=:0

    # Is Xwayland running?
    $ ps ax|grep Xwayland
     1956 tty2     Sl+    6:38 /usr/bin/Xwayland :0 ...

First of all, the ``xprop`` program can be in Wayland to check if an
application is using Xorg or Wayland: the mouse cursor becomes a cross only and
only if the application is used Xorg (X11 API).

Environment to opt-in for Wayland support::

    export GDK_BACKEND=wayland

Firefox and Thunderbird can opt-in for Wayland by setting
``MOZ_ENABLE_WAYLAND=1`` environment variable. For example, I put the
following line into ``/etc/environment`` to enable it system-wide permanently::

    MOZ_ENABLE_WAYLAND=1


switcheroo-control
==================

`switcheroo-control <https://github.com/hadess/switcheroo-control>`_ is a
deamon controlling ``/sys/kernel/debug/vgaswitcheroo/switch`` (Linux kernel).
It can be accessed by DBus.

With this package installed on systems with dual-GPU, you can right-click on
apps (while it's not running) in GNOME Shell's Activities Overview and choose
"Launch using Dedicated Graphics Card" option.

Fedora 25 and later installs switcheroo-control by default.

When the daemon starts, it looks for ``xdg.force_integrated=VALUE`` parameter
in the Linux command line. If *VALUE* is ``1``, ``true`` or ``on``, or if
``xdg.force_integrated=VALUE`` is not found in the command line, the daemon
writes ``DIGD`` into ``/sys/kernel/debug/vgaswitcheroo/switch``: prefer the
IGP.

If ``xdg.force_integrated=0`` is found in the command line, the daemon does not
write anything into ``/sys/kernel/debug/vgaswitcheroo/switch``.

systemd:

* Check if the service is running: ``sudo systemctl status switcheroo-control.service``
* Disable the service: ``sudo systemctl disable switcheroo-control.service``
  and ``sudo systemctl stop switcheroo-control.service``

XXX is it deprecated in 2019?


Disable discrete GPU by blacklisting its driver (nouveau)
=========================================================

To debug graphical bugs, I wanted to ensure that the NVIDIA GPU is never
used. I found the solution of fully disabling the nouveau driver in the Linux
kernel: add ``modprobe.blacklist=nouveau`` to the Linux kernel command line
using::

    sudo grubby --update-kernel=ALL --args="modprobe.blacklist=nouveau"

To reenble nouveau, remove the parameter::

    sudo grubby --update-kernel=ALL --remove-args="modprobe.blacklist=nouveau"


Demo!
=====

When my laptop is idle, no 3D application running, the NVIDIA GPU is suspended::

    $ cat /sys/bus/pci/drivers/nouveau/0000\:01\:00.0/enable
    0
    $ cat /sys/bus/pci/drivers/nouveau/0000\:01\:00.0/power/runtime_status
    suspended

I run a 3D application on it::

    DRI_PRIME=1 glxgears

The NVIDIA GPU is awaken::

    $ cat /sys/bus/pci/drivers/nouveau/0000\:01\:00.0/enable
    2
    $ cat /sys/bus/pci/drivers/nouveau/0000\:01\:00.0/power/runtime_status
    active

Stop the 3D application. A few seconds later, the NVIDIA GPU is suspended
again::

    $ cat /sys/bus/pci/drivers/nouveau/0000\:01\:00.0/enable
    0
    $ cat /sys/bus/pci/drivers/nouveau/0000\:01\:00.0/power/runtime_status
    suspended


Links
=====

* https://www.kernel.org/doc/html/latest/gpu/vga-switcheroo.html
* https://wiki.archlinux.org/index.php/Hybrid_graphics
* https://wiki.archlinux.org/index.php/PRIME
* https://help.ubuntu.com/community/HybridGraphics
