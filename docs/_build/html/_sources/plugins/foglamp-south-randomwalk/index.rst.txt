.. Images
.. |random_1| image:: images/random_1.jpg
.. |random_2| image:: images/random_2.jpg

Random Walk
===========

The *foglamp-south-randomwalk* plugin is a plugin that will create random data between a pair of values. Each new value is based on a random increment or decrement of the previous. This results in an output that appears as follows

+------------+
| |random_2| |
+------------+

To create a south service with the Random Walk plugin

  - Click on *South* in the left hand menu bar

  - Select *randomwalk* from the plugin list

  - Name your service and click *Next*

  +------------+
  | |random_1| |
  +------------+

  - Configure the plugin

    - **Asset name**: The name of the asset that will be created

    - **Minimum Value**: The minimum value to include in the output

    - **Maximum Value**: The maximum value to include in the output

  - Click *Next*

  - Enable the service and click on *Done*

