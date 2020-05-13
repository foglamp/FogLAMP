.. Images
.. |envirophat_1| image:: images/envirophat_1.jpg
.. |envirophat_2| image:: images/envirophat_2.jpg

Enviro pHAT Plugin
==================

.. image:: images/envirophat_1.jpg
   :align: right

The *foglamp-south-envirophat* is a plugin that uses the Pimoroni Enviro pHAT sensor board. The Enviro pHAT board is an environmental sensing board populated with multiple sensors, the plugin pulls data from the;

  - RGB light sensor

  - Magnetometer

  - Accelerometer
  
  - Temperature/pressure Sensor

Individual sensors can be enabled or disabled separately in the configuration. Separate assets are created for each sensor within FogLAMP with individual controls over the naming of these assets.

.. note::

   The Enviro pHAT plugin is only available on the Raspberry Pi as it is specific the GPIO pins of that device.

To create a south service with the Enviro pHAT

  - Click on *South* in the left hand menu bar

  - Select *envirophat* from the plugin list

  - Name your service and click *Next*

  +----------------+
  | |envirophat_2| |
  +----------------+

  - Configure the plugin

    - **Asset Name Prefix**: An optional prefix to add to the asset names. The asset names created by the plugin are; rgb, magnetometer, accelerometer and weather. Using the prefix you can add an identifier to the front of each such that it becomes easier to differentiate between multiple instances of the sensor.

    - **RGB Sensor**: A toggle control to turn on or off collection of RGB light level information

    - **RGB Sensor Name**: Set a name for the RGB sensor asset

    - **Magnetometer Sensor**: A toggle control to turn on or off collection of magnetometer data

    - **Magnetometer Sensor Name**: Set a name for the magnetometer sensor asset

    - **Accelerometer Sensor**: A toggle to turn on or off collection of accelorometer data

    - **Accelerometer Sensor Name**: Set a name for the accelerometer sensor asset

    - **Weather Sensor**: A toggle to turn on or off collection of weather data

    - **Weather Sensor Name**: Set a name for the weather sensor asset

  - Click *Next*

  - Enable the service and click on *Done*
