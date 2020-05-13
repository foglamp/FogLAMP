.. Images
.. |scale| image:: images/scale.jpg

Scale Filter
============

The *foglamp-filter-scale* plugin is a simple filter that allows a scale factor and an offset to be applied to numerical data. It's primary uses are for adjusting values to match different measurement scales, for example converting temperatures from Centigrade to Fahrenheit or when a sensor reports a value in non-base units, e.g. 1/10th of a degree.

When adding a scale filter to either the south service or north task, via the *Add Application* option of the user interface, a configuration page for the filter will be shown as below;

+---------+
| |scale| |
+---------+

The configuration options supported by the scale filter are detailed in the table below

+-----------------+------------------------------------------------------------------+
| Setting         | Description                                                      |
+=================+==================================================================+
| Scale Factor    | The scale factor to multiply the numeric values by               |
+-----------------+------------------------------------------------------------------+
| Constant Offset | A constant to add to all numeric values after applying the scale |
+-----------------+------------------------------------------------------------------+
| Asset filter    | This is useful when applying the filter in the north, it allows  |
|                 | the filter to be applied only to those assets that match the     |
|                 | regular expression given. If left blank then the filter is       |
|                 | applied to all assets/                                           |
+-----------------+------------------------------------------------------------------+
