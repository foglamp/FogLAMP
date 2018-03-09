# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Module for MAX31865 'async' type plugin """

import asyncio
import copy
import datetime
import json
import uuid
import RPi.GPIO as GPIO

from foglamp.common import logger
from foglamp.plugins.common import utils
from foglamp.plugins.south.common.max31865 import *
from foglamp.services.south import exceptions
from foglamp.services.south.ingest import Ingest

__author__ = "Ashwin Gopalakrishnan"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'MAX31865 async plugin',
        'type': 'string',
        'default': 'max31865async'
    },
    'pins': {
        'description': 'Chip select pins to check',
        'type': 'string',
        'default': '5,6,7,8'
    },
    'shutdownThreshold': {
        'description': 'Time in seconds allowed for shutdown to complete the pending tasks',
        'type': 'integer',
        'default': '10'
    }
}

_LOGGER = logger.setup(__name__, level=20)


def plugin_info():
    """ Returns information about the plugin.
    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'MAX31865 Async plugin',
        'version': '1.0',
        'mode': 'async',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.
    Args:
        config: JSON configuration document for the South device configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """
    data = copy.deepcopy(config)
    pins = config['pins']['value']
    pins = pins.split(',')

    probes = []
    for pin in pins:
        probes.append(max31865(csPin=int(pin)))
    _LOGGER.info('MAX31865 with chip selects on pins {} initialized'.format(config['pins']['value']))
    return probes


def plugin_start(probes):
    """ Extracts data from the sensor and returns it in a JSON document as a Python dict.
    Available for async mode only.
    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        returns a sensor reading in a JSON document, as a Python dict, if it is available
        None - If no reading is available
    Raises:
        TimeoutError
    """
    async def save_data():
        if len(probes) is 0:
            return
        try:
            while True:
                for probe in probes:
                    temperature = await probe.readTemp()
                    time_stamp = str(datetime.datetime.now(tz=datetime.timezone.utc))
                    data = {
                        'asset': 'temperature{}'.format(probe.csPin),
                        'timestamp': time_stamp,
                        'key': str(uuid.uuid4()),
                        'readings': {
                            "temperature": temperature,
                        }
                    }
                    await Ingest.add_readings(asset='MAX31865/{}'.format(data['asset']),
                                                       timestamp=data['timestamp'], key=data['key'],
                                                       readings=data['readings'])
                await asyncio.sleep(1)
        except (Exception, RuntimeError, pexpect.exceptions.TIMEOUT) as ex:
            _LOGGER.exception("MAX31865 async exception: {}".format(str(ex)))
            raise exceptions.DataRetrievalError(ex)
        _LOGGER.debug("MAX31865 async reading: {}".format(json.dumps(data)))
        return
    asyncio.ensure_future(save_data())


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    it should be called when the configuration of the plugin is changed during the operation of the South device service;
    The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """
    _LOGGER.info("Old config for MAX31865 plugin {} \n new config {}".format(handle, new_config))

    # Find diff between old config and new config
    diff = utils.get_diff(handle, new_config)

    # TODO
    new_handle = copy.deepcopy(new_config)
    new_handle['restart'] = 'no'
    return new_handle


def _plugin_stop(handle):
    """ Stops the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    GPIO.cleanup()
    _LOGGER.info('MAX31865 (async) {} Disconnected.'.format(bluetooth_adr))


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    _plugin_stop(handle)
    _LOGGER.info('MAX31865 async plugin shut down.')
