# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" The OMF North is a plugin output formatter for the FogLAMP appliance.
    It is loaded by the send process (see The FogLAMP Sending Process) and runs in the context of the send process,
    to send the reading data to a PI Server (or Connector) using the OSIsoft OMF format.
    PICROMF = PI Connector Relay OMF
"""

import ast
import json
import logging

from foglamp.common import logger
from foglamp.plugins.north.pi_server.omf_translator import *

__author__ = "Stefano Simonelli, Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


_MODULE_NAME = "pi_server_north"
_CONFIG_CATEGORY_DESCRIPTION = 'PI Server North Plugin'
_DEFAULT_CONFIG_OMF = {
    'plugin': {
        'description': 'PI Server North Plugin',
        'type': 'string',
        'default': 'pi_server',
        'readonly': 'true'
    },
    "URL": {
        "description": "URL of PI Connector to send data to",
        "type": "string",
        "default": "https://pi-server:5460/ingress/messages",
        "order": "1"
    },
    "producerToken": {
        "description": "Producer token for this FogLAMP stream",
        "type": "string",
        "default": "pi_server_producer_token",
        "order": "2"
    },
    "OMFMaxRetry": {
        "description": "Max number of retries for communication with the OMF PI Connector Relay",
        "type": "integer",
        "default": "3",
        "order": "3"
    },
    "OMFRetrySleepTime": {
        "description": "Seconds between each retry for communication with the OMF PI Connector Relay. "
                       "This time is doubled at each attempt.",
        "type": "integer",
        "default": "1",
        "order": "4"
    },
    "OMFHttpTimeout": {
        "description": "Timeout in seconds for HTTP operations with the OMF PI Connector Relay",
        "type": "integer",
        "default": "10",
        "order": "5"
    },
    "StaticData": {
        "description": "Static data to include in each sensor reading sent via OMF",
        "type": "JSON",
        "default": json.dumps(
            {
                "Location": "Palo Alto",
                "Company": "Dianomic"
            }
        )
    },
    "applyFilter": {
        "description": "Should filter be applied before processing the data?",
        "type": "boolean",
        "default": "False"
    },
    "filterRule": {
        "description": "JQ formatted filter to apply (only applicable if applyFilter is True)",
        "type": "string",
        "default": ".[]"
    },
    "formatNumber": {
        "description": "OMF format property to apply to the type Number",
        "type": "string",
        "default": "float64"
    },
    "formatInteger": {
        "description": "OMF format property to apply to the type Integer",
        "type": "string",
        "default": "int64"
    },
    "verifySSL": {
        "description": "Verify SSL certificate",
        "type": "boolean",
        "default": "false"
    },
    "compression": {
        "description": "Compression required",
        "type": "boolean",
        "default": "false"
    }
}

_OMF_PREFIX_MEASUREMENT = "measurement"
_OMF_PREFIX_SENSOR = "sensor"
_CONFIG_CATEGORY_OMF_TYPES_NAME = 'OMF_TYPES'
_CONFIG_CATEGORY_OMF_TYPES_DESCRIPTION = 'OMF Types'
_DEFAULT_CONFIG_OMF_TYPES = {}


def plugin_info():
    return {
        'name': "PI Server North",
        'version': "1.0.0",
        'type': "north",
        'interface': "1.0",
        'config': _DEFAULT_CONFIG_OMF
    }



def plugin_init(data):
    """ Initializes the OMF plugin for the sending of blocks of readings to the PI Connector."""

    # Check producerToken first. No need to proceed further if producerToken is missing or is invalid
    try:
        if data['producerToken'] == "": raise ValueError("the producerToken cannot be an empty string, use the FogLAMP API to set a proper value.")
    except KeyError:
        raise ValueError("the producerToken must be defined, use the FogLAMP API to set a proper value.")

    # Define logger
    _log_debug_level = data['debug_level']
    _stream_id = data['stream_id']
    logger_name = _MODULE_NAME + "_" + str(_stream_id)
    _logger = logger.setup(logger_name, level=logging.INFO if _log_debug_level in [0, 1, None] else logging.DEBUG)

    # Fetch and validate OMF_TYPES fetched from configuration
    _config_omf_types = data['sending_process_instance']._fetch_configuration(
        cat_name=_CONFIG_CATEGORY_OMF_TYPES_NAME,
        cat_desc=_CONFIG_CATEGORY_OMF_TYPES_DESCRIPTION,
        cat_config=_DEFAULT_CONFIG_OMF_TYPES,
        cat_keep_original=True)
    for item in _config_omf_types:
        if _config_omf_types[item]['type'] == 'JSON':
            new_value = json.loads(_config_omf_types[item]['value'])
            _config_omf_types[item]['value'] = new_value

    # Generate prefixes for static/dynamic data sepaprate for each source
    _prefix_sensor = "{}_{}".format(_OMF_PREFIX_SENSOR, data['source']['value'])
    _prefix_measurement = "{}_{}".format(_OMF_PREFIX_MEASUREMENT, data['source']['value'])

    _config = {}
    _config['_CONFIG_CATEGORY_NAME'] = data['_CONFIG_CATEGORY_NAME']
    _config['URL'] = data['URL']['value']
    _config['producerToken'] = data['producerToken']['value']
    _config['OMFMaxRetry'] = int(data['OMFMaxRetry']['value'])
    _config['OMFRetrySleepTime'] = int(data['OMFRetrySleepTime']['value'])
    _config['OMFHttpTimeout'] = int(data['OMFHttpTimeout']['value'])
    _config['StaticData'] = ast.literal_eval(data['StaticData']['value'])
    _config['formatNumber'] = data['formatNumber']['value']
    _config['formatInteger'] = data['formatInteger']['value']
    _config['verifySSL'] = data['verifySSL']['value']
    _config['compression'] = data['compression']['value']
    _config['sending_process_instance'] = data['sending_process_instance']
    _config['prefix_measurement'] = _prefix_measurement
    _config['prefix_sensor'] = _prefix_sensor
    _config['logger'] = _logger
    _config['config_omf_types'] = _config_omf_types

    return _config


async def plugin_send(handle, raw_data, stream_id):
    """ Translates and sends to the destination system the data provided by the Sending Process
    Args:
        handle: plugin_handle from sending_process
        raw_data  : Data to send as retrieved from the storage layer
        stream_id
    Returns:
        data_to_send : True, data successfully sent to the destination system
        new_position : Last row_id already sent
        num_sent     : Number of rows sent, used for the update of the statistics
    Raises:
    """
    _logger = handle['logger']
    pi_server_north = PIServerNorthPlugin(handle)

    try:
        is_data_sent = False
        pi_server_north._type_id = await pi_server_north._get_next_type_id()
        data_to_send, last_id = await pi_server_north.prepare_to_send(raw_data)
        num_to_sent = len(data_to_send)
        await pi_server_north.send_message("data", data_to_send) # Send Data
        is_data_sent = True
    except (plugin_exceptions.URLFetchError, plugin_exceptions.DataSendError, Exception) as ex:
        _logger.exception("cannot complete the sending operation - error details |{0}|".format(ex))
        await pi_server_north.delete_omf_types_already_created()
        raise plugin_exceptions.DataSendError(ex)

    return is_data_sent, last_id, num_to_sent


def plugin_reconfigure():
    pass


def plugin_shutdown(data):
    pass


class PIServerNorthPlugin(OmfTranslator):
    """ PI Server North Plugin """

    def __init__(self, handle):
        super().__init__(handle)

    def filter_identifier(self, identifier):
        new_identifier = identifier[:249] if len(identifier) > 250 else identifier
        new_identifier = new_identifier.replace('%', 'prcntg_') if new_identifier.startswith('%') else new_identifier
        new_identifier = new_identifier.replace('%', '_prcntg') if new_identifier.endswith('%') else new_identifier

        new_identifier = new_identifier. \
            replace(' ', ''). \
            replace('%', ''). \
            replace("/", '_')
        return new_identifier
