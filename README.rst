pyzinc: Python support for Zinc (with Pandas)
=============================================

Overview
--------

`Zinc <https://project-haystack.org/doc/Zinc>`_ is a CSV-like format for
Project Haystack. This project exists solely to make it simple—and *fast!*—to
load Zinc-format strings into a ``ZincDataFrame`` or ``ZincSeries`` (which
themselves are just extended Pandas types).

This implementation does not claim to adhere to the Zinc spec yet, as it is
still in development.

Other Python libraries for Zinc exist, notably `hszinc
<https://github.com/widesky/hszinc>`_. So why this library? Basically only one reason: :ref:`performance`.

Example usage
-------------

Say you have the following in ``example.zinc``::

  ver:"3.0" view:"chart" hisStart:2020-05-18T00:00:00-07:00 Los_Angeles hisEnd:2020-05-18T01:15:00-07:00 Los_Angeles hisLimit:10000 dis:"Mon 18-May-2020"
  ts disKey:"ui::timestamp" tz:"Los_Angeles" chartFormat:"ka",v0 id:@p:q01b001:r:0197767d-c51944e4 "Building One VAV1-01 Eff Heat SP" navName:"Eff Heat SP" point his siteRef:@p:q01b001:r:8fc116f8-72c5320c "Building One" equipRef:@p:q01b001:r:b78a8dcc-828caa1b "Building One VAV1-01" curVal:65.972°F curStatus:"ok" kind:"Number" unit:"°F" tz:"Los_Angeles" sp temp cur haystackPoint air effective heating
  2020-05-17T23:47:08-07:00 Los_Angeles,
  2020-05-17T23:55:00-07:00 Los_Angeles,68.553°F
  2020-05-18T00:00:00-07:00 Los_Angeles,68.554°F
  2020-05-18T00:05:00-07:00 Los_Angeles,69.723°F
  2020-05-18T01:13:09-07:00 Los_Angeles,

you can load it with

.. code:: python

  import pyzinc

  with open("example.zinc", encoding="utf-8") as f:
      heating_sp = pyzinc.to_zinc_series(f.read())

Since ``pyzinc.ZincDataFrame`` inherits from ``pandas.DataFrame``, and
``pyzinc.Series`` inherits from ``pandas.Series``, you can perform all the
usual tasks you might wish to on a familiar Pandas object. The only added
attribute is a ``column_info`` containing an ``OrderedDict`` of metadata about
the table or series.

.. _performance:

Performance
-----------

Comparing pyzinc with hszinc, on an 11MB Grid with 2002 columns and 849 rows,
``hszinc.parse`` took ????? seconds and ``pyzinc.to_zinc_frame`` took 37.6 seconds.
