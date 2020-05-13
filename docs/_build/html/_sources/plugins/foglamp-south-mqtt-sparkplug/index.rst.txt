.. Images
.. |sparkplug_1| image:: images/sparkplug_1.jpg

MQTT Sparkplug B
================

The *foglamp-south-mqtt-sparkplug* plugin implements the Sparkplug B payload format with an MQTT (Message Queue Telemetry Transport) transport. The plugin will subscribe to a configured topic and will process the Sparkplug B payloads, creating FogLAMP assets form those payloads. Sparkplug is an open source software specification of a payload format and set of conventions for transporting sensor data using MQTT as the transport mechanism.

.. note::

   Sparkplug is bi-directional, however this plugin will only read data from the Sparkplug device.

To create a south service with the MQTT Sparkplug B plugin

  - Click on *South* in the left hand menu bar

  - Select *mqtt_sparkplug* from the plugin list

  - Name your service and click *Next*

  +---------------+
  | |sparkplug_1| |
  +---------------+

  - Configure the plugin

    - **Asset Name**: The asset name which will be used for all data read.

    - **MQTT Host**: The MQTT host to connect to, this is the host that is running the MQTT broker.

    - **MQTT Port**: The MQTT port, this is the port the MQTT broker uses for unencrypted traffic, usually 1883 unless modified.

    - **Username**: The user name to be used when authenticating with the MQTT subsystem.

    - **Password**: The password to use when authenticating with the MQTT subsystem.

    - **Topic**: The MQTT topic to which the plugin will subscribe.

  - Click *Next*

  - Enable the service and click on *Done*

