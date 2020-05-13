.. Images
.. |digiducer_1| image:: images/digiducer_1.jpg
.. |digiducer_2| image:: images/digiducer_2.jpg
.. |digiducer_3| image:: images/digiducer_3.jpg

.. Links
.. |digiducer| raw:: html

   <a href="https://digiducer.com" target="_blank">Digiducer</a>

Digiducer Vibration Sensor
==========================

.. image:: images/digiducer.jpg
   :align: right

The *foglamp-south-digiducer* plugin allows a |digiducer|  333D01 USB Digital Accelerometer to be attached to FogLAMP for the collection of vibration data. The Digiducer is a piezoelectric accelerometer housed in a rugged enclosure complete with a data conditioning and acquisition interface that only requires a USB port on the FogLAMP device for connectivity.

The plugin allows for two modes of operation; continuous reading of the vibration data or sampled reading of the vibration data. In sampled mode the user configures a sample period and interval. The plugin will then read data for the sample period and forward it to the FogLAMP storage service. It will then pause collection for the sample interval before again collecting data. This repeats indefinitely.

To create a south service with the Digiducer

  - Click on *South* in the left hand menu bar

  - Select *digiducer* from the plugin list

  - Name your service and click *Next*

  +---------------+
  | |digiducer_1| |
  +---------------+

  - Configure the plugin

    - **Asset Name**: The name of the asset that will be created in FogLAMP.

    - **Sample Rate**: The rate at which data will be sampled. A number of frequencies are supported in the range 8KHz to 48KHz.

      +---------------+
      | |digiducer_2| |
      +---------------+

    - **Block size**: To aid efficiency the plugin collects data in blocks, this allows the block size to be tuned. The value should be a power of 2.

    - **Continuous Sampling**: This toggle supports the selection of continuous verses sampled collection.

    - **Sample Period**: The duration of each sample period in seconds.

    - **Sample Interval**: The time in seconds between each sample being taken.

    - **Channel**: Select collection of the 10G Peak channel, the 20G Peak channel or both channels

      +---------------+
      | |digiducer_3| |
      +---------------+

  - Click on *Next*

  - Enable your south service and click on *Done*
