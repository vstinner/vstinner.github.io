++++++++++++++++++++++++++++++++++++++
Status of Python 3 in OpenStack Mitaka
++++++++++++++++++++++++++++++++++++++

:date: 2016-03-01 17:00
:tags: openstack, python3
:category: python
:slug: python3_openstack_mitaka
:authors: Victor Stinner
:summary: Status of Python 3 in OpenStack Mitaka

Previous status: `Python 3 Status in OpenStack Liberty
<http://techs.enovance.com/7807/python-3-status-openstack-liberty>`_ (September
2015).


Since most OpenStack services reached the feature freeze of the Mitaka cycle
(November 2015-April 2016), it's time to look behind to see the progress made
on the Python 3 support.


Services ported to Python 3
===========================

13 services were ported to Python 3 during the Mitaka cycle:

* Cinder
* Congress
* Designate
* Glance
* Heat
* Horizon
* Manila
* Mistral
* Octavia
* Searchlight
* Solum
* Watcher
* Zaqar

Red Hat contributed to the port of Cinder, Glance and Horizon services.

"Ported to Python 3" means that all unit tests pass on Python 3.4 and a voting
job runs these tests on the gate. It is not enough to run applications on
production with Python 3. Functional tests are not run on Python 3 yet, and
functional tests will probably identify a few remaining issues specific to
Python 3.

See the `Python 3 wiki page <https://wiki.openstack.org/wiki/Python3>`_ to see
the current status of the OpenStack port to Python 3, especially the list of
services ported to Python 3.


Services not ported yet
=======================

It became simpler to list services which are not compatible with Python 3, than
listing services already ported to Python!

8 services needs to be ported:

* Work-in-progress:

  * Magnum: 83% (959 unit tests/1,161)
  * Cue: 81% (208 unit tests/257)
  * Nova: 74% (10,859 unit tests/14,726)
  * Barbican: 34% (392 unit tests/1168)
  * Keystone: 27% (1200 unit tests/4455)
  * Swift: 0% (3 unit tests/4,435)

* Port not started yet:

  * Murano: non-voting python34 gate
  * Trove: no python34 gate

Red Hat contributed Python 3 patches to Cue, Designate, Swift and Trove
in the Mitaka cycle.


Pytohn 3 issues in Eventlet
===========================

Four Python 3 issues were fixed in Eventlet:

- `Issue #295: Python 3: wsgi doesn't handle correctly partial write of
  socket send() when using writelines()
  <https://github.com/eventlet/eventlet/issues/295>`_
- PR #275: `Issue #274: Fix GreenSocket.recv_into() <https://github.com/eventlet/eventlet/pull/275>`_.
  Issue: `On Python 3, sock.makefile('rb').readline() doesn't handle blocking
  errors correctly <https://github.com/eventlet/eventlet/issues/274>`_
- PR #257: `Fix GreenFileIO.readall() for regular file
  <https://github.com/eventlet/eventlet/pull/257>`_
- `Issue #248: eventlet.monkey_patch() on Python 3.4 makes stdout
  non-blocking <https://github.com/eventlet/eventlet/issues/248>`_: pull
  request `Fix GreenFileIO.write()
  <https://github.com/eventlet/eventlet/pull/250>`_


How to port remainaing code?
============================

The `Python 3 wiki page <https://wiki.openstack.org/wiki/Python3>`_ contains
a lot of information about adding Python 3 support to Python 2 code.

Come to the ``#openstack-python3`` IRC channel on the Freenode network to
discuss Python 3!


Next: Functional tests
======================

Same plan than the previous status on OpenStack Liberty: the next major
milestone will be to run functional tests on Python 3.

Minor progress was made in the Mitaka cycle: it is now possible to choose to
install some packages on Python 3 in DevStack. It was a first requirement for
functional tests since gates use DevStack.

Experiments on running functional tests have started on Heat and Neutron
projects.
