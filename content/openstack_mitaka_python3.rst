++++++++++++++++++++++++++++++++++++++
Status of Python 3 in OpenStack Mitaka
++++++++++++++++++++++++++++++++++++++

:date: 2016-03-02 14:00
:tags: openstack, python3
:category: python
:slug: openstack_mitaka_python3
:authors: Victor Stinner
:summary: Status of Python 3 in OpenStack Mitaka

Now that most OpenStack services have reached feature freeze for the Mitaka
cycle (November 2015-April 2016), it's time to look back on the progress made
for Python 3 support.

Previous status update: `Python 3 Status in OpenStack Liberty
<http://techs.enovance.com/7807/python-3-status-openstack-liberty>`_
(September 2015).


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

Red Hat contributed to the Cinder, Designate, Glance and Horizon service
porting efforts.

"Ported to Python 3" means that all unit tests pass on Python 3.4 which is
verified by a voting gate job. It is not enough to run applications in
production with Python 3. Integration and functional tests are not run on
Python 3 yet. See the section dedicated to these tests below.

See the `Python 3 wiki page <https://wiki.openstack.org/wiki/Python3>`_ for the
current status of the OpenStack port to Python 3; especially the list of
services ported to Python 3.


Services not ported yet
=======================

It's become easier to list services which are not compatible with Python 3 than
listing services already ported to Python 3!

9 services still need to be ported:

* Work-in-progress:

  * Magnum: 83% (959 unit tests/1,161)
  * Cue: 81% (208 unit tests/257)
  * Nova: 74% (10,859 unit tests/14,726)
  * Barbican: 34% (392 unit tests/1168)
  * Keystone: 27% (1200 unit tests/4455)
  * Swift: 0% (3 unit tests/4,435)
  * Neutron-LBaaS: 0% (1 unit test/806)

* Port not started yet:

  * Murano: non-voting python34 gate
  * Trove: no python34 gate

Red Hat contributed Python 3 patches to Cue, Neutron-LBaaS, Swift and Trove
during the Mitaka cycle.

Trove developers are ready to start the port at the beginning of the next cycle
(Newton). The py34 test environment was blocked by the MySQL-Python dependency (it
was not possible to build the test environment), but this dependency is now
skipped on Python 3. Later, it will be `replaced with PyMySQL
<https://review.openstack.org/#/c/225915/>`_ on Python 2 and Python 3.

The status of Murano is unclear yet.


Python 3 issues in Eventlet
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


Next Milestone: Functional and integration tests
================================================

The next major milestone will be to run functional and integration tests on
Python 3.

* functional tests are restricted to one component (ex: only Glance)
* integration tests, like Tempest, test the integration of multiple components

It is now possible to install some packages on Python 3 in DevStack using
``USE_PYTHON3`` and ``PYTHON3_VERSION`` variables: `Enable optional Python 3
support <https://review.openstack.org/#/c/181165/>`_. It means that it is
possible to run tests with some services running on Python 3, and the remaining
services on Python 2.

The port to Python 3 of Glance, Heat and Neutron functional and integration
tests have already started.

For Glance, 159 functional tests already pass on Python 3.4.

Heat:

* project-config: `Add python34 integration test job for Heat
  <https://review.openstack.org/#/c/228194/>`_ (WIP)
* heat: `py34: integration tests <https://review.openstack.org/#/c/188033/>`_
  (WIP)

Neutron: the `Add the functional-py34 and dsvm-functional-py34 targets to
tox.ini <https://review.openstack.org/#/c/231897/>`_ change was merged, but a
gate job hasn't been added for it yet.

Another pending project is to fix issues specific to Python 3.5, but the gate
doesn’t use Python 3.5 yet. There are some minor issues, probably easy to fix.


How to port remaining code?
===========================

The `Python 3 wiki page <https://wiki.openstack.org/wiki/Python3>`_ contains
a lot of information about adding Python 3 support to Python 2 code.

Join us in the ``#openstack-python3`` IRC channel on Freenode to discuss
Python 3!
