FogLAMP Plugins
===============

The following set of plugins are available for FogLAMP. These plugins
extend the functionality by adding new sources of data, new destinations,
processing filters that can enhance or modify the data, rules for
notification delivery and notification delivery mechanisms.

South Plugins
-------------

South plugins add new ways to get data into FogLAMP, a number of south
plugins are available ready built or users may add new south plugins of
their own by writing them in Python or C/C++.

.. list-table:: FogLAMP South Plugins
    :widths: 20 50
    :header-rows: 1

    * - Name
      - Description
    * - am2315
      - FogLAMP south plugin for an AM2315 temperature and humidity sensor
    * - b100-modbus-python
      - A south plugin to read data from a Dynamic Ratings B100 device over Modbus
    * - benchmark
      - A FogLAMP benchmark plugin to measure the ingestion rates on particular hardware
    * - cc2650
      - A FogLAMP south plugin for the Texas Instruments SensorTag CC2650
    * - coap
      - A south plugin for FogLAMP that pulls data from a COAP sensor
    * - coral-enviro
      - None
    * - csv
      - A FogLAMP south plugin in C++ for reading CSV files
    * - csv-async
      - A FogLAMP asynchronous plugin for reading CSV data
    * - dht
      - A FogLAMP south plugin in C++ that interfaces to a DHT-11 temperature and humidity sensor
    * - dht11
      - A FogLAMP south plugin that interfaces a DHT-11 temperature sensor
    * - dnp3
      - A south plugin for FogLAMP that implements the DNP3 protocol
    * - envirophat
      - A FogLAMP south service for the Raspberry Pi EnviroPhat sensors
    * - expression
      - A FogLAMP south plugin that uses a user define expression to generate data
    * - FlirAX8
      - A FogLAMP hybrid south plugin that uses foglamp-south-modbus-c to get temperature data from a Flir Thermal camera
    * - game
      - The south plugin used for the FogLAMP lab session game involving remote controlled cars
    * - http
      - A Python south plugin for FogLAMP used to connect one FogLAMP instance to another
    * - human-detector
      - FogLAMP south service plugin that detects person in the live video stream
    * - ina219
      - A FogLAMP south plugin for the INA219 voltage and current sensor
    * - J1708
      - A plugin that uses the SAE J1708 protocol to load data from the ECU of heavy duty vehicles.
    * - J1939
      - None
    * - modbus-c
      - A FogLAMP south plugin that implements modbus-tcp and modbus-rtu
    * - modbustcp
      - A FogLAMP south plugin that implements modbus-tcp in Python
    * - mqtt-sparkplug
      - A FogLAMP south plugin that implements the Sparkplug API over MQTT
    * - opcua
      - A FogLAMP south service that pulls data from an OPC-UA server
    * - openweathermap
      - A FogLAMP south plugin to pull weather data from OpenWeatherMap
    * - playback
      - A FogLAMP south plugin to replay data stored in a CSV file
    * - pt100
      - A FogLAMP south plugin for the PT100 temperature sensor
    * - random
      - A south plugin for FogLAMP that generates random numbers
    * - randomwalk
      - A FogLAMP south plugin that returns data that with randomly generated steps
    * - roxtec
      - A FogLAMP south plugin for the Roxtec cable gland project
    * - sensehat
      - A FogLAMP south plugin for the Raspberry Pi Sensehat sensors
    * - sensorphone
      - A FogLAMP south plugin the task to the iPhone SensorPhone app
    * - sinusoid
      - A FogLAMP south plugin that produces a simulated sine wave
    * - systeminfo
      - A FogLAMP south plugin that gathers information about the system it is running on.
    * - usb4704
      - A FogLAMP south plugin the Advantech USB-4704 data acquisition module
    * - wind-turbine
      - A FogLAMP south plugin for a number of sensor connected to a wind turbine demo
    * - beckhoff
      - A Beckhoff ADS data ingress plugin for FogLAMP, this monitors Beckhoff PLCs and returns the state of internal variables within the PLC
    * - csvplayback
      - csv playback using pandas
    * - digiducer
      - South plugin for the Digiducer 333D01 vibration sensor
    * - human-detector
      - A machine learning model to detect people within a live video stream
    * - phidget
      - FogLAMP south code for different phidgets
    * - s7
      - A south plugin that uses the S7 Communications protocol to read data from a Siemens S7 series PLC.
    * - sarcos
      - A south plugin to process the Sarcos XO data files


North Plugins
-------------

North plugins add new destinations to which data may be sent by FogLAMP. A
number of north plugins are available ready built or users may add new
north plugins of their own by writing them in Python or C/C++.

.. list-table:: FogLAMP North Plugins
    :widths: 20 50
    :header-rows: 1

    * - Name
      - Description
    * - gcp
      - A north plugin to send data to Google Cloud Platform IoT Core
    * - harperdb
      - None
    * - http
      - A Python implementation of a north plugin to send data between FogLAMP instances using HTTP
    * - http-c
      - A FogLAMP north plugin that sends data between FogLAMP instances using HTTP/HTTPS
    * - kafka
      - A FogLAMP plugin for sending data north to Apache Kafka
    * - kafka-python
      - None
    * - opcua
      - A north plugin for FogLAMP that makes it act as an OPC-UA server for the data it reads from sensors
    * - thingspeak
      - A FogLAMP north plugin to send data to Matlab's ThingSpeak cloud
    * - influxdb
      - A north plugin for sending data to InfluxDB
    * - influxdbcloud
      - A north plugin to send data from FogLAMP to the InfuxDBCloud
    * - splunk
      - A north plugin for sending data to Splunk


Filter Plugins
--------------

Filter plugins add new ways in which data may be modified, enhanced
or cleaned as part of the ingress via a south service or egress to a
destination system. A number of north plugins are available ready built
or users may add new north plugins of their own by writing them in Python
or C/C++.

It is also possible, using particular filters, to supply expressions
or script snippets that can operate on the data as well. This provides a
simple way to process the data in FogLAMP as it is read from devices or
written to destination systems.

.. list-table:: FogLAMP Filter Plugins
    :widths: 20 50
    :header-rows: 1

    * - Name
      - Description
    * - asset
      - A FogLAMP processing filter that is used to block or allow certain assets to pass onwards in the data stream
    * - change
      - A FogLAMP processing filter plugin that only forwards data that changes by more than a configurable amount
    * - delta
      - A FogLAMP processing filter plugin that removes duplicates from the stream of data and only forwards new values that differ from previous values by more than a given tolerance
    * - expression
      - A FogLAMP processing filter plugin that applies a user define formula to the data as it passes through the filter
    * - fft
      - A FogLAMP processing filter plugin that calculates a Fast Fourier Transform across sensor data
    * - Flir-Validity
      - A FogLAMP processing filter used for processing temperature data from a Flir thermal camera
    * - metadata
      - A FogLAMP processing filter plugin that adds metadata to the readings in the data stream
    * - python27
      - A FogLAMP processing filter that allows Python 2 code to be run on each sensor value.
    * - python35
      - A FogLAMP processing filter that allows Python 3 code to be run on each sensor value.
    * - rate
      - A FogLAMP processing filter plugin that sends reduced rate data until an expression triggers sending full rate data
    * - rms
      - A FogLAMP processing filter plugin that calculates RMS value for sensor data
    * - scale
      - A FogLAMP processing filter plugin that applies an offset and scale factor to the data
    * - scale-set
      - A FogLAMP processing filter plugin that applies a set of sale factors to the data
    * - threshold
      - A FogLAMP processing filter that only forwards data when a threshold is crossed
    * - blocktest
      - A filter designed to aid testing. It combines incoming readings into bigger blocks before sending onwards
    * - downsample
      - A data down sampling filter
    * - ema
      - Generate exponential moving average datapoint: include a rate of current value and a rate of history values
    * - eventrate
      - A filter designed for use in the north to trigger sending rates based on event notification assets
    * - fft2
      - Filter for FFT signal processing, finding peak frequencies, etc.
    * - rms-trigger
      - An RMS filter that uses a trigger asset rather than a fixed set of readings for each caclulation
    * - simple-python
      - The simple Python filter plugin is analogous to the expression filter but accept Python code rather than the expression syntax
    * - statistics
      - Generic statistics filter for FogLAMP data
    * - vibration_features
      - A filter plugin that takes a stream of vibration data and generates a set of features that characterise that data


Notification Rule Plugins
-------------------------

Notification rule plugins provide the logic that is used by the
notification service to determine if a condition has been met that should
trigger or clear that condition and hence send a notification. A number of
notification plugins are available as standard, however as with any plugin the
user is able to write new plugins in Python or C/C++ to extend the set of
notification rules.

.. list-table:: FogLAMP Notification Rule Plugins
    :widths: 20 50
    :header-rows: 1

    * - Name
      - Description
    * - average
      - A FogLAMP notification rule plugin that evaluates an expression based sensor data notification rule plugin that triggers when sensors values depart from the moving average by more than a configured limit.
    * - outofbound
      - A FogLAMP notification rule plugin that triggers when sensors values exceed limits set in the configuration of the plugin.
    * - simple-expression
      - A FogLAMP notification rule plugin that evaluates an expression based sensor data
    * - ML-bad-bearing
      - Notification rule plugin to detect bad bearing
    * - ML-engine-failure
      - Notification rule plugin for detecting imminent engine failure using ML model
    * - periodic
      - A rule that periodically fires based on a timer when data is observed.


Notification Delivery Plugins
-----------------------------

Notification delivery plugins provide the mechanisms to deliver the
notification messages to the systems that will receive them.  A number
of notification delivery plugins are available as standard, however as
with any plugin the user is able to write new plugins in Python or C/C++
to extend the set of notification rules.

.. list-table:: FogLAMP Notification Delivery Plugins
    :widths: 20 50
    :header-rows: 1

    * - Name
      - Description
    * - alexa-notifyme
      - A FogLAMP notification delivery plugin that sends notifications to the Amazon Alexa platform
    * - asset
      - A FogLAMP notification delivery plugin that creates an asset in FogLAMP when a notification occurs
    * - blynk
      - A FogLAMP notification delivery plugin that sends notifications to the Blynk service
    * - email
      - A FogLAMP notification delivery plugin that sends notifications via email
    * - google-hangouts
      - A FogLAMP notification delivery plugin that sends alerts on the Google hangout platform
    * - ifttt
      - A FogLAMP notification delivery plugin that triggers an action of IFTTT
    * - python35
      - A FogLAMP notification delivery plugin that runs an arbitrary Python 3 script
    * - slack
      - A FogLAMP notification delivery plugin that sends notifications via the slack instant messaging platform
    * - telegram
      - A FogLAMP notification delivery plugin that sends notifications via the telegram service
    * - north
      - Deliver notification data via a FogLAMP north task

