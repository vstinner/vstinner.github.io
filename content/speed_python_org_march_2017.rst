++++++++++++++++++++++++++++++++++++
speed.python.org results: March 2017
++++++++++++++++++++++++++++++++++++

:date: 2017-03-29 00:40
:tags: benchmark
:category: benchmark
:slug: speed-python-org-march-2017
:authors: Victor Stinner

In feburary 2017, CPython from Bitbucket with Mercurial moved to GitHub with
Git: read `[Python-Dev] CPython is now on GitHub
<https://mail.python.org/pipermail/python-dev/2017-February/147381.html>`_ by
Brett Cannon.

In 2016, I worked on speed.python.org to automate running benchmarks and make
benchmarks more stable. At the end, I had a single command to:

* tune the system for benchmarks
* compile CPython using LTO+PGO
* install CPython
* install performance
* run performance
* upload results

But my tools were written for Mercurial and speed.python.org uses Mercurial
revisions as keys for changes. Since the CPython repository was converted to
Git, I have to remove all old results and run again old benchmarks. But before
removing everyhing, I took screenshots of the most interesting pages. It would
prefer to keep a copy of all data, but it would require to write new tools
and I am not motivated to do that.

Python 3.7 compared to Python 2.7
=================================

Benchmarks where Python 3.7 is **faster** than Python 2.7:

.. image:: {filename}/images/speed2017/python37_faster_py27.png
   :alt: python37_faster_py27

Benchmarks where Python 3.7 is **slower** than Python 2.7:

.. image:: {filename}/images/speed2017/python37_slower_py27.png
   :alt: python37_slower_py27


Significant optimizations
=========================

CPython became regulary faster in 2016 on the following benchmarks.

call_method, the main optimized was `Speedup method calls 1.2x
<https://bugs.python.org/issue26110>`_:

.. image:: {filename}/images/speed2017/call_method.png
   :alt: call_method

float:

.. image:: {filename}/images/speed2017/float.png
   :alt: float

hexiom:

.. image:: {filename}/images/speed2017/hexiom.png
   :alt: hexiom

nqueens:

.. image:: {filename}/images/speed2017/nqueens.png
   :alt: nqueens

pickle_list, something happened near September 2016:

.. image:: {filename}/images/speed2017/pickle_list.png
   :alt: pickle_list

richards:

.. image:: {filename}/images/speed2017/richards.png
   :alt: richards

scimark_lu, I like the latest dot!

.. image:: {filename}/images/speed2017/scimark_lu.png
   :alt: scimark_lu

scimark_sor:

.. image:: {filename}/images/speed2017/scimark_sor.png
   :alt: scimark_sor

sympy_sum:

.. image:: {filename}/images/speed2017/sympy_sum.png
   :alt: sympy_sum

telco is one of the most impressive, it became regulary faster:

.. image:: {filename}/images/speed2017/telco.png
   :alt: telco

unpickle_list, something happened between March and May 2016:

.. image:: {filename}/images/speed2017/unpickle_list.png
   :alt: unpickle_list


The enum change
===============

One change related to the ``enum`` module had significant impact on the two
following benchmarks.

python_startup:

.. image:: {filename}/images/speed2017/python_startup.png
   :alt: python_startup

See "Python startup performance regression" section of `My contributions to
CPython during 2016 Q4 <{filename}/python_contrib_2016q4.rst>`_ for the
explanation on changes around September 2016.

regex_compile became 1.2x slower (312 ms => 376 ms: +20%) because constants
of the ``re`` module became ``enum`` objects: see `convert re flags to (much
friendlier) IntFlag constants (issue #28082)
<http://bugs.python.org/issue28082>`_.

.. image:: {filename}/images/speed2017/regex_compile.png
   :alt: regex_compile


Benchmarks became stable
========================

The following benchmarks are microbenchmarks which are impacted by many
external factors. It's hard to get stable results. I'm happy to see that
results are stable. I would say very stable compared to results when I started
to work on the project!

call_simple:

.. image:: {filename}/images/speed2017/call_simple.png
   :alt: call_simple

spectral_norm:

.. image:: {filename}/images/speed2017/spectral_norm.png
   :alt: spectral_norm


Straight line
=============

It seems like no optimization had a significant impact on the following
benchmarks. You can also see that benchmarks became stable, so it's easier to
detect performance regression or significant optimization.

dulwich_log:

.. image:: {filename}/images/speed2017/dulwich_log.png
   :alt: dulwich_log

pidigits:

.. image:: {filename}/images/speed2017/pidigits.png
   :alt: pidigits

sqlite_synth:

.. image:: {filename}/images/speed2017/sqlite_synth.png
   :alt: sqlite_synth

Apart something around April 2016, tornado_http result is stable:

.. image:: {filename}/images/speed2017/tornado_http.png
   :alt: tornado_http


Unstable benchmarks
===================

After months of efforts to make everything stable, some benchmarks are still
unstable, even if temporary spikes are lower than before. See `Analysis of a
Python performance issue <{filename}/analysis_python_performance_issue.rst>`_
to see the size of previous tempoary performance spikes.

regex_v8:

.. image:: {filename}/images/speed2017/regex_v8.png
   :alt: regex_v8

scimark_sparse_mat_mult:

.. image:: {filename}/images/speed2017/scimark_sparse_mat_mult.png
   :alt: scimark_sparse_mat_mult

unpickle_pure_python:

.. image:: {filename}/images/speed2017/unpickle_pure_python.png
   :alt: unpickle_pure_python


Boring results
==============

There is nothing interesting to say on the following benchmark results.

2to3:

.. image:: {filename}/images/speed2017/2to3.png
   :alt: 2to3

crypto_pyaes:

.. image:: {filename}/images/speed2017/crypto_pyaes.png
   :alt: crypto_pyaes

deltablue:

.. image:: {filename}/images/speed2017/deltablue.png
   :alt: deltablue

logging_silent:

.. image:: {filename}/images/speed2017/logging_silent.png
   :alt: logging_silent

mako:

.. image:: {filename}/images/speed2017/mako.png
   :alt: mako

xml_etree_process:

.. image:: {filename}/images/speed2017/xml_etree_process.png
   :alt: xml_etree_process

xml_etre_iterparse:

.. image:: {filename}/images/speed2017/xml_etre_iterparse.png
   :alt: xml_etre_iterparse

