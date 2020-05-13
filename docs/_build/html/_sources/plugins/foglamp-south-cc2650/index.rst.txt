.. Images
.. |cc2650_1| image:: images/cc2650_1.jpg

.. Links
.. |SensorTag| raw:: html

   <a href="https://www.ti.com/tool/TIDC-CC2650STK-SENSORTAG" target="_blank">CC2650 SensorTag</a>

CC2650 SensorTag
================

.. image:: images/cc2650.jpg
   :align: right

The *foglamp-south-cc2650* is a plugin that connects using Bluetooth to a Texas Instruments |SensorTag|. The SensorTag offers 10 sensors within a small, low powered package which may be read by this plugin and ingested into FogLAMP. These sensors include;

  - ambient light

  - magnetometer
   
  - humidity

  - pressure

  - accelerometer

  - gyroscope

  - object temperature

  - digital microphone

.. note::

   The sensor requires that you have a Bluetooth low energy adapter available that supports at least BLE 4.0.

To create a south service with the |SensorTag|

  - Click on *South* in the left hand menu bar

  - Select *cc2650* from the plugin list

  - Name your service and click *Next*

  +------------+
  | |cc2650_1| |
  +------------+

  - Configure the plugin

    - **Bluetooth Address**: The Bluetooth MAC address of the device

    - **Asset Name Prefix**: A prefix to add to the asset name

    - **Shutdown Threshold**: The time in seconds allowed for a shutdown operation to complete

    - **Connection Timeout**: The Bluetooth connection timeout to use when attempting to connect to the device

    - **Temperature Sensor**: A toggle to include the temperature data in the data ingested

    - **Temperature Sensor Name**: The data point name to assign the temperature data

    - **Luminance Sensor**: Toggle to control the inclusion of the ambient light data

    - **Luminance Sensor Name**: The data point name to use for the luminance data

    - **Humidity Sensor**: A toggle to include the humidity data

    - **Humidity Sensor Name**: The data point name to use for the humidity data

    - **Pressure Sensor**: A toggle to control the inclusion of pressure data

    - **Pressure Sensor Name**: The name to be used for the data point that will contain the atmospheric pressure data

    - **Movement Sensor**: A toggle that controls the inclusion of movement data gathered from the gyroscope, accelerometer and magnetometer

    - **Gyroscope Sensor Name**: The data point name to use for the gyroscope data

    - **Accelerometer Sensor Name**: The name of the data point that will record the accelerometer data

    - **Magnetometer Sensor Name**: The name to use for the magnetometer data

    - **Battery Data**: A toggle to control inclusion of the state of charge of the battery

    - **Battery Sensor Name**: The data point name for the battery charge percentage


  - Click *Next*

  - Enable the service and click on *Done*
