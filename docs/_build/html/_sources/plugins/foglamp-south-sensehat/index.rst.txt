.. Images
.. |sensehat_1| image:: images/sensehat_1.jpg

SenseHAT
========

.. image:: images/sensehat.jpg
   :align: right

The *foglamp-south-sensehat* is a plugin that uses the Raspberry Pi Sense HAT sensor board. The Sense HAT has an 8×8 RGB LED matrix, a five-button joystick and includes the following sensors:

  - Gyroscope

  - Accelerometer

  - Magnetometer

  - Temperature

  - Barometric pressure

  - Humidity

In addition it has an 8x8 matrix for RGB LED's, these are not included in the devices the plugin supports.

Individual sensors can be enabled or disabled separately in the configuration. Separate assets are created for each sensor within FogLAMP with individual controls over the naming of these assets.

.. note::

   The Sense HAT plugin is only available on the Raspberry Pi as it is specific the GPIO pins of that device.

To create a south service with the Sense HAT

  - Click on *South* in the left hand menu bar

  - Select *sensehat* from the plugin list

  - Name your service and click *Next*

  +--------------+
  | |sensehat_1| |
  +--------------+

  - Configure the plugin

    - **Asset Name Prefix**: An optional prefix to add to the asset names. 

    - **Pressure Sensor**: A toggle control to turn on or off collection of pressure information

    - **Pressure Sensor Name**: Set a name for the Pressure sensor asset

    - **Temperature Sensor**: A toggle control to turn on or off collection of temperature information

    - **Temperature Sensor Name**: Set a name for the temperature sensor asset

    - **Humidity Sensor**: A toggle control to turn on or off collection of humidity information

    - **Humidity Sensor Name**: Set a name for the humidity sensor asset

    - **Gyroscope Sensor**: A toggle control to turn on or off collection of gyroscope information

    - **Gyroscope Sensor Name**: Set a name for the gyroscope sensor asset

    - **Accelerometer Sensor**: A toggle to turn on or off collection of accelerometer data

    - **Accelerometer Sensor Name**: Set a name for the accelerometer sensor asset

    - **Magnetometer Sensor**: A toggle control to turn on or off collection of magnetometer data

    - **Magnetometer Sensor Name**: Set a name for the magnetometer sensor asset

    - **Joystick Sensor**: A toggle control to turn on or off collection of joystick data

    - **Joystick Sensor Name**: Set a name for the joystick sensor asset

  - Click *Next*

  - Enable the service and click on *Done*
