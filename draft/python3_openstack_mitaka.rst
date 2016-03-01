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

Since most OpenStack services reached the feature freeze of the Mitaka cycle,
it's time to look behind to see the progress made on the Python 3 support.

Three major services were ported by Red Hat to Python 3 during the Mitaka
cycle: Cinder, Glance and Horizon. Other services ported to Python 3: Congress,
Designate, Manila, Mistral, Octavia, Searchlight, Solum, Watcher, Zaqar. Total:
12 new services are compatible with Python 3.


Services not ported yet
=======================

It became simpler to list services which are not compatible with Python 3 yet:

* Approved by the Technical Committee:

  * Nova: 74% (10,859 unit tests/14,726)
  * Keystone: 27% (1200 unit tests/4455)
  * Swift: 0% (3 unit tests/4,435)
  * Trove: port not started yet (no python34 job)

* Other services, work-in-progress:

  * Barbican: 34% (392 unit tests/1168)
  * CUE (WIP): xxx/257

* Other services, unknown status / port not started:

  * Magneto
  * Magnum
  * Murano

Total: 10 services needs to be ported.


Eventlet issues with Python 3
=============================

As usually, many Python 3 issues were fixed in eventlet:

- Bug report: `Python 3: wsgi doesn't handle correctly partial write of
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


Next: Functional tests
======================


