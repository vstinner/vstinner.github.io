+++++++++++++++++++++++++++++++
New Python 3.8 exceptions hooks
+++++++++++++++++++++++++++++++

:date: 2019-06-05 23:00
:tags: python
:category: python
:slug: python38-except-hooks
:authors: Victor Stinner

I added two new hooks to Python 3.8 to handle "unraisable" and "uncaught"
exceptions:

* `sys.unraisablehook()
  <https://docs.python.org/dev/library/sys.html#sys.unraisablehook>`_
* `threading.excepthook()
  <https://docs.python.org/dev/library/threading.html#threading.excepthook>`_

None should be called directly:

* ``sys.unraisablehook()`` is called by the C function ``PyErr_WriteUnraisable:q

``sys.unraisablehook()``
