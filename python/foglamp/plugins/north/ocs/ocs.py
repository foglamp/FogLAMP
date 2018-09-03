# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" The OCS North is a plugin output formatter for the FogLAMP appliance.
    It is loaded by the send process (see The FogLAMP Sending Process) and runs in the context of the send process,
    to send the reading data to OSIsoft OCS (OSIsoft Cloud Services) using the OSIsoft OMF format.
    PICROMF = PI Connector Relay OMF
"""

import ast
import json
import logging

from foglamp.common import logger
from foglamp.plugins.north.common.omf_translator import *


__author__ = "Stefano Simonelli, Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


_MODULE_NAME = "ocs_north"
_CONFIG_CATEGORY_DESCRIPTION = 'Configuration of OCS North plugin'
# The parameters used for the interaction with OCS are :
#    producerToken                      - It allows to ingest data into OCS using OMF.
#    tenant_id / client_id / client_id  - They are used for the authentication and interaction with the OCS API,
#                                         they are associated to the specific OCS account.
#    namespace                          - Specifies the OCS namespace where the information are stored,
#                                         it is used for the interaction with the OCS API.
#
_DEFAULT_CONFIG_OCS = {
    'plugin': {
        'description': 'OCS North Plugin',
        'type': 'string',
        'default': 'ocs',
        "readonly": "true"
    },
    "URL": {
        "description": "The URL of OCS (OSIsoft Cloud Services) ",
        "type": "string",
        "default": "https://dat-a.osisoft.com/api/omf",
        "order": "1"
    },
    "producerToken": {
        "description": "The producer token used to authenticate as a valid publisher and "
                       "required to ingest data into OCS using OMF.",
        "type": "string",
        "default": "ocs_producer_token",
        "order": "2"
    },
    "namespace": {
        "description": "Specifies the OCS namespace where the information are stored and "
                       "it is used for the interaction with the OCS API.",
        "type": "string",
        "default": "ocs_namespace_0001",
        "order": "6"
    },
    "tenant_id": {
        "description": "Tenant id associated to the specific OCS account.",
        "type": "string",
        "default": "ocs_tenant_id",
        "order": "7"
    },
    "client_id": {
        "description": "Client id associated to the specific OCS account, "
        "it is used to authenticate the source for using the OCS API.",
        "type": "string",
        "default": "ocs_client_id",
        "order": "8"
    },
    "client_secret": {
        "description": "Client secret associated to the specific OCS account, "
        "it is used to authenticate the source for using the OCS API.",
        "type": "string",
        "default": "ocs_client_secret",
        "order": "9"
    },
    "OMFMaxRetry": {
        "description": "Max number of retries for the communication with the OMF PI Connector Relay",
        "type": "integer",
        "default": "5",
        "order": "3"
    },
    "OMFRetrySleepTime": {
        "description": "Seconds between each retry for the communication with the OMF PI Connector Relay",
        "type": "integer",
        "default": "1",
        "order": "4"
    },
    "OMFHttpTimeout": {
        "description": "Timeout in seconds for the HTTP operations with the OMF PI Connector Relay",
        "type": "integer",
        "default": "30",
        "order": "5"
    },
    "StaticData": {
        "description": "Static data to include in each sensor reading sent to OMF.",
        "type": "JSON",
        "default": json.dumps(
            {
                "Location": "Palo Alto",
                "Company": "Dianomic"
            }
        )
    },
    "applyFilter": {
        "description": "Whether to apply filter before processing the data",
        "type": "boolean",
        "default": "False"
    },
    "filterRule": {
        "description": "JQ formatted filter to apply (applicable if applyFilter is True)",
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
        "default": "int32"
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
_CONFIG_CATEGORY_OMF_TYPES_NAME = 'OCS_TYPES'
_CONFIG_CATEGORY_OMF_TYPES_DESCRIPTION = 'OCS Types'
_DEFAULT_CONFIG_OMF_TYPES = {}


def plugin_info():
    """ Returns information about the plugin."""
    return {
        'name': "OCS North",
        'version': "1.0.0",
        'type': "north",
        'interface': "1.0",
        'config': _DEFAULT_CONFIG_OCS
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
        data: plugin_handle from sending_process
        raw_data  : Data to send as retrieved from the storage layer
        stream_id
    Returns:
        data_to_send : True, data successfully sent to the destination system
        new_position : Last row_id already sent
        num_sent     : Number of rows sent, used for the update of the statistics
    Raises:
    """
    _logger = handle['logger']
    ocs_north = OCSNorthPlugin(handle)

    try:
        is_data_sent = False
        ocs_north._type_id = await ocs_north._get_next_type_id()
        data_to_send, last_id = await ocs_north.prepare_to_send(raw_data)
        num_to_sent = len(data_to_send)
        await ocs_north.send_message("data", data_to_send) # Send Data
        is_data_sent = True
    except Exception as ex:
        _logger.exception("cannot complete the sending operation - error details |{0}|".format(ex))
        await ocs_north.delete_omf_types_already_created()
        raise ex

    return is_data_sent, last_id, num_to_sent


def plugin_reconfigure():
    pass


def plugin_shutdown(data):
    pass


class OCSNorthPlugin(OmfTranslator):
    """ North OCS North Plugin """

    def __init__(self, handle):
        super().__init__(handle)

    def filter_identifier(self, identifier):
        """
        Rules for OCS identifier:
        1. not case sensitive
        2. can contain spaces
        3. cannot start with two underscores (__)
        4. can contain max 250 characters
        5. cannot use /;:?/[]{}'#@!$%\*&+=
        6. cannot end or start with a period
        7. cannot contain consecutive period
        8. cannot consist of just one period

        :param identifier:
        :return: identifier
        """
        new_identifier = identifier[:249] if len(identifier) > 250 else identifier
        new_identifier = new_identifier[2:] if new_identifier.startswith('__') else new_identifier
        new_identifier = new_identifier[1:] if new_identifier.startswith('.') else new_identifier
        new_identifier = new_identifier[:-1] if new_identifier.endswith('.') else new_identifier
        new_identifier = new_identifier.replace('%', 'prcntg_') if new_identifier.startswith('%') else new_identifier
        new_identifier = new_identifier.replace('%', '_prcntg') if new_identifier.endswith('%') else new_identifier

        new_identifier = new_identifier. \
            replace('..', '.'). \
            replace(' ', ''). \
            replace('`', ''). \
            replace('~', ''). \
            replace('!', ''). \
            replace('@', ''). \
            replace('#', ''). \
            replace('$', ''). \
            replace('%', ''). \
            replace('^', ''). \
            replace('&', ''). \
            replace('*', ''). \
            replace('(', ''). \
            replace(')', ''). \
            replace('+', ''). \
            replace('=', ''). \
            replace('{', ''). \
            replace('}', ''). \
            replace('[', ''). \
            replace(']', ''). \
            replace('|', ''). \
            replace('\\', ''). \
            replace(':', ''). \
            replace(";", ''). \
            replace('"', ''). \
            replace("'", ''). \
            replace("/", '_'). \
            replace("?", ''). \
            replace("`", ""). \
            replace(",", "")
        return new_identifier
