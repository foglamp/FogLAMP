# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Module for Simple Data Simulator plugin """

import asyncio
import copy
import datetime
import json
import uuid

from foglamp.common import logger
from foglamp.plugins.common import utils
from foglamp.services.south import exceptions
from foglamp.services.south.ingest import Ingest

__author__ = "Ashwin Gopalakrishnan"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'Simple Simulator async plugin',
        'type': 'string',
        'default': 'simplesima'
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
        'name': 'Simple Data Simulator Async plugin',
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
    return data


def plugin_start(data):
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
        try:
            while True:
                # for i in range(0,500000):
                    time_stamp = str(datetime.datetime.now(tz=datetime.timezone.utc))
                    data = {
                        'asset': 'a',
                        'timestamp': time_stamp,
                        'key': str(uuid.uuid4()),
                        'readings': {
                            "a": 1,
                        }
                    }
                    await Ingest.add_readings(asset='{}'.format(data['asset']),
                                                       timestamp=data['timestamp'], key=data['key'],
                                                       readings=data['readings'])
        except (Exception, RuntimeError, pexpect.exceptions.TIMEOUT) as ex:
            _LOGGER.exception("simplesima async exception: {}".format(str(ex)))
            raise exceptions.DataRetrievalError(ex)
        _LOGGER.debug("simplesima async reading: {}".format(json.dumps(data)))
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
    _LOGGER.info("Old config for simplesima plugin {} \n new config {}".format(handle, new_config))

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
    _LOGGER.info('simplesima (async) Disconnected.')


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    _plugin_stop(handle)
    _LOGGER.info('simplesima async plugin shut down.')
