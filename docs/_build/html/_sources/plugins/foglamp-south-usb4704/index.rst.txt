.. Images
.. |usb_2| image:: images/usb_2.jpg

Advantech USB-4704
==================

.. image:: images/usb_1.jpg
     :align: left

The *foglamp-south-usb4704* plugin is a south plugin that is designed to gather data from an Advantech USB-4704 data acquisition module. The module supports 8 digital inputs and 8 analogue inputs. It is possible to configure the plugin to combine multiple digital input to create a single numeric data point or have each input as a boolean data point. Each analogue input, which is a 14 bit analogue to digital converter, becomes a single numeric data point in the range 0 to 16383, although a scale and offset may be applied to these values.

To create a south service with the USB-4704

  - Click on *South* in the left hand menu bar

  - Select *usb4704* from the plugin list

  - Name your service and click *Next*

  +---------+
  | |usb_2| |
  +---------+

  - Configure the plugin

    - **Asset Name**: The name of the asset that will be created with the values read from the USB-4704

    - **Connections**: A JSON document that describes the connections to the USB-4704 and the data points within the asset that they map to. The JSON document is a set of objects, one per data point. The objects contain a number of key/value pairs as follow

      +-------+----------------------------------------------------------------------+
      | Key   | Description                                                          |
      +=======+======================================================================+
      | type  | The type of connection, this may be either digital or analogue.      |
      +-------+----------------------------------------------------------------------+
      | pin   | The analogue pin used for the connection.                            |
      +-------+----------------------------------------------------------------------+
      | pins  | An array of pins for a digital connection, the first element in the  |
      |       | array becomes the most significant bit of the numeric value created. |
      +-------+----------------------------------------------------------------------+
      | name  | The data point name within the asset.                                |
      +-------+----------------------------------------------------------------------+
      | scale | An optional scale value that may be applied to the value.            |
      +-------+----------------------------------------------------------------------+

  - Click on *Next*
  
  - Enable your service and click on *Done* 
