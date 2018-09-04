# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" The OMF North is a plugin output formatter for the FogLAMP appliance.
    It is loaded by the send process (see The FogLAMP Sending Process) and runs in the context of the send process,
    to send the reading data to a PI Server (or Connector) using the OSIsoft OMF format.
    PICROMF = PI Connector Relay OMF
"""

import aiohttp
import asyncio
import copy
import json

import foglamp.plugins.north.common.common as plugin_common
import foglamp.plugins.north.common.exceptions as plugin_exceptions
from foglamp.common.storage_client import payload_builder
from foglamp.common.storage_client.exceptions import StorageServerError

__author__ = "Stefano Simonelli, Amarendra K Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


class OmfType:
    type_payload = None

    def __init__(self):
        self.type_payload = dict()
        self.type_payload['properties'] = dict()

    def check_property(self, property):
        if not isinstance(property, dict):
            return False
        is_valid = True
        for i, v in property.items():
            if i not in ['type', 'format', 'isindex', 'isname', 'name', 'description', 'uom']:
                is_valid = False
                break
            if i == 'type' and v not in ['array', 'object', 'boolean', 'integer', 'string', 'number',
                                         'additionalProperties']:
                is_valid = False
                break
            if i == 'type' and v == 'array':
                if 'items' not in v:
                    is_valid = False
                    break
                if not isinstance(v['items'], dict):
                    is_valid = False
                    break
                is_valid = self.check_property(property['items'])
            if i == 'type' and v == 'object':
                if 'properties' not in v and 'additionalProperties' not in v:
                    is_valid = False
                    break
                if 'properties' in v and not isinstance(v['properties'], dict):
                    is_valid = False
                    break
                if 'additionalProperties' in v and not isinstance(v['additionalProperties'], dict):
                    is_valid = False
                    break
                is_valid = self.check_property(property['properties'])

        return is_valid

    def add_id(self, id):
        self.type_payload['id'] = id
        return self

    def add_version(self, version=None):
        if version is None:
            version = '1.0.0.0'
        self.type_payload['version'] = version
        return self

    def add_type(self, item_type):
        self.type_payload['type'] = 'object'
        return self

    def add_classfication(self, classification):
        if classification not in ['static', 'dynamic']:
            classification = 'static'
        self.type_payload['classification'] = classification
        return self

    def add_property(self, name, property):
        if self.check_property(property) is True:
            self.type_payload['properties'][name] = property
        return self

    def chain_payload(self):
        return self

    def payload(self):
        return self.type_payload


class OmfContainer:
    container_payload = None

    def __init__(self):
        self.container_payload = dict()

    def add_id(self, id):
        self.container_payload['id'] = id
        return self

    def add_typeid(self, type_id):
        self.container_payload['typeid'] = type_id
        return self

    def add_typeversion(self, type_version):
        self.container_payload['typeversion'] = type_version
        return self

    def add_name(self, name):
        self.container_payload['name'] = name
        return self

    def add_description(self, description):
        self.container_payload['description'] = description
        return self

    def add_tags(self, tags):
        if not isinstance(tags, list):
            tags = list(tags)
        self.container_payload['tags'] = tags
        return self

    def add_metadata(self, metadata):
        if isinstance(metadata, dict):
            self.container_payload['metadata'] = metadata
        return self

    def add_indexes(self, indexes):
        if not isinstance(indexes, list):
            indexes = list(indexes)
        self.container_payload['indexes'] = indexes
        return self

    def chain_payload(self):
        return self

    def payload(self):
        return self.container_payload


class OmfData:
    data_payload = None

    def __init__(self):
        self.data_payload = dict()
        self.data_payload['values'] = list()

    def add_containerid(self, container_id):
        self.data_payload['containerid'] = container_id
        return self

    def add_typeid(self, type_id):
        self.data_payload['typeid'] = type_id
        return self

    def add_typeversion(self, type_version):
        self.data_payload['typeversion'] = type_version
        return self

    def add_values(self, value):
        self.data_payload['values'].append(value)
        return self

    def chain_payload(self):
        return self

    def payload(self):
        return self.data_payload


class OmfTranslator(object):
    def __init__(self, handle):
        self._config = handle
        self._config_omf_types = handle['config_omf_types']
        self._logger = handle['logger']
        self._sending_process_instance = handle['sending_process_instance']
        self._verify_ssl = True if handle['verifySSL'] == 'true' else False
        self._compression = True if handle['compression'] == 'true' else False
        self._prefix_measurement = handle['prefix_measurement']
        self._prefix_sensor = handle['prefix_sensor']
        self._new_types = list()
        self._new_config_types = dict()
        self._type_id = None

    def filter_identifier(self, identifier):
        return identifier.replace(' ', '')

    # TODO: Remove this type_id and all related stuff if found useless
    async def _get_next_type_id(self):
        """ Retrieves the list of OMF types already defined/sent to the PICROMF"""
        try:
            payload = payload_builder.PayloadBuilder() \
                .SELECT('type_id') \
                .ORDER_BY(['type_id', 'desc']) \
                .LIMIT(1) \
                .payload()
            omf_created_objects = await self._sending_process_instance._storage_async.query_tbl_with_payload(
                'omf_created_objects', payload)
        except StorageServerError as ex:
            self._logger.error(ex)

        next_type_id = 1 if len(omf_created_objects['rows']) == 0 else int \
            (omf_created_objects['rows'][0]['type_id']) + 1
        return str(next_type_id)

    async def delete_omf_types_already_created(self):
        """ Deletes OMF types/objects tracked as already created, it is used to force the recreation of the types"""
        config_category_name = self._config['_CONFIG_CATEGORY_NAME']
        try:
            payload = payload_builder.PayloadBuilder() \
                .WHERE(['configuration_key', '=', config_category_name]) \
                .payload()
            await self._sending_process_instance._storage_async.delete_from_tbl("omf_created_objects", payload)
        except StorageServerError as ex:
            self._logger.error(ex)

    async def _retrieve_omf_types_already_created(self, configuration_key):
        """ Retrieves the list of OMF types already defined/sent to the PICROMF"""
        try:
            payload = payload_builder.PayloadBuilder() \
                .SELECT('asset_code') \
                .WHERE(['configuration_key', '=', configuration_key]) \
                .payload()
            omf_created_objects = await self._sending_process_instance._storage_async.query_tbl_with_payload(
                'omf_created_objects', payload)
        except StorageServerError as ex:
            self._logger.error(ex)

        # Extracts only the asset_code column
        rows = []
        for row in omf_created_objects['rows']:
            rows.append(row['asset_code'])
        return rows

    async def _flag_created_omf_type(self, configuration_key, asset_code):
        """ Stores into the Storage layer the successfully creation of the type into PICROMF."""
        try:
            payload = payload_builder.PayloadBuilder() \
                .INSERT(configuration_key=configuration_key,
                        asset_code=asset_code,
                        type_id=self._type_id) \
                .payload()
            await self._sending_process_instance._storage_async.insert_into_tbl("omf_created_objects", payload)
        except StorageServerError as ex:
            self._logger.error(ex)

    async def _create_omf_types_automatic(self, asset_info):
        asset_id = self.filter_identifier(asset_info["asset_code"])
        static_id = "{}_{}".format(self._prefix_sensor, asset_id)
        dynamic_id = "{}_{}".format(self._prefix_measurement, asset_id)

        asset_data = asset_info["asset_data"]

        static_omf_type = OmfType(). \
            add_id(static_id). \
            add_type("object"). \
            add_classfication('static'). \
            add_version('1.0.0.0'). \
            chain_payload()
        static_omf_type.add_property("Name", property={"type": "string", "isindex": True})
        for item in self._config['StaticData']:
            static_omf_type.add_property(item, property={"type": "string"})

        dynamic_omf_type = OmfType(). \
            add_id(dynamic_id). \
            add_type("object"). \
            add_classfication('dynamic'). \
            add_version('1.0.0.0'). \
            chain_payload()
        dynamic_omf_type.add_property("Time", property={"type": "string", "format": "date-time", "isindex": True})
        for item in asset_data:
            item_type = plugin_common.evaluate_type(asset_data[item])
            if item_type == "integer":
                property = {"type": item_type, "format": self._config['formatInteger']}
            elif item_type == "number":
                property = {"type": item_type, "format": self._config['formatNumber']}
            else:
                property = {"type": item_type}
            dynamic_omf_type.add_property(self.filter_identifier(item), property=property)

        omf_type = [static_omf_type.payload(), dynamic_omf_type.payload()]

        self._new_types.append({
            "asset_id": asset_id,
            "static_id": static_id,
            "dynamic_id": dynamic_id,
        })

        self._new_config_types[asset_info["asset_code"]] = {
            'static': static_omf_type.payload(),
            'dynamic': dynamic_omf_type.payload()
        }
        await self.send_message("type", omf_type)

    async def _create_omf_types_from_configuration(self, asset_code):
        asset_code_omf_type = copy.deepcopy(self._config_omf_types[asset_code]["value"])
        asset_id = self.filter_identifier(asset_code)

        for item in self._config_omf_types[asset_code]["value"]:
            self._new_types.append({
                "asset_id": asset_id,
                "static_id": item['static']['id'],
                "dynamic_id": item['dynamic']['id'],
            })
        await self.send_message("type", asset_code_omf_type)

    async def _find_new_omf_types(self, raw_data):
        """ Finds if any types are present"""
        if len(raw_data) == 0:
            return None, None

        config_category_name = self._config['_CONFIG_CATEGORY_NAME']

        asset_codes_to_evaluate = plugin_common.identify_unique_asset_codes(raw_data)
        asset_codes_already_created = await self._retrieve_omf_types_already_created(config_category_name)

        return asset_codes_to_evaluate, asset_codes_already_created

    async def _add_new_omf_types(self, asset_codes_to_evaluate, asset_codes_already_created):
        """ Handles the creation of the OMF types related to the asset codes using one of the 2 possible ways :
                Automatic OMF Type Mapping
                Configuration Based OMF Type Mapping
        """
        if asset_codes_to_evaluate is None and asset_codes_already_created is None:
            return

        config_category_name = self._config['_CONFIG_CATEGORY_NAME']

        for item in asset_codes_to_evaluate:
            asset_code = item["asset_code"]
            from_configuration = True
            if not any(tmp_item == asset_code for tmp_item in asset_codes_already_created):
                try:
                    if asset_code not in self._config_omf_types: raise KeyError
                    if not self._config_omf_types[asset_code]: raise ValueError
                except (KeyError, ValueError):
                    from_configuration = False
                try:
                    if from_configuration is False:
                        await self._create_omf_types_automatic(item)  # configuration_based = False
                    else:
                        await self._create_omf_types_from_configuration(asset_code)  # configuration_based = True
                except:
                    self._logger.warning("Error in creating type for {}:{}".format(config_category_name, asset_code))
                else:
                    await self._flag_created_omf_type(config_category_name, asset_code)

    async def _create_omf_containers(self):
        containers = list()
        for item in self._new_types:
            asset_id = item['asset_id']
            container_id = item['dynamic_id']  #"{}_{}".format(self._prefix_measurement, asset_id)

            container = OmfContainer()
            container. \
                add_id(container_id). \
                add_typeid(item['dynamic_id']). \
                add_typeversion('1.0.0.0')
            containers.append(container.payload())
        if len(containers) > 0:
            await self.send_message("container", containers)

    async def _create_omf_static(self):
        static_data = list()
        for item in self._new_types:
            data = OmfData()
            values = {"Name": item['asset_id']}
            values.update(copy.deepcopy(self._config['StaticData']))
            data. \
                add_typeid(item['static_id']). \
                add_values(values)
            static_data.append(data.payload())
        if len(static_data) > 0:
            await self.send_message("data", static_data)

    async def _create_omf_links(self):
        link_data = list()
        data = OmfData()
        data.add_typeid('__Link')
        for item in self._new_types:
            asset_id = item['asset_id']
            link_1 = {
                "source": {
                    "typeid": item["static_id"],
                    "index": "_ROOT"
                },
                "target": {
                    "typeid": item["static_id"],
                    "index": asset_id
                }
            }
            link_2 = {
                "source": {
                    "typeid": item["static_id"],
                    "index": asset_id
                },
                "target": {
                    "containerid": item["dynamic_id"],
                }
            }
            data.add_values(link_1).add_values(link_2)
        link_data.append(data.payload())
        if len(link_data[0]['values']) > 0:
            await self.send_message("data", link_data)

    def create_omf_data(self, raw_data):
        """ Transforms the in memory data into a new structure that could be converted into JSON for the PICROMF"""
        data_to_send = list()
        _last_id = 0
        for row in raw_data:
            asset_id = self.filter_identifier(row["asset_code"])
            container_id = "{}_{}".format(self._prefix_measurement, asset_id)
            try:
                # The code formats the date to the format OMF/the PI Server expects directly
                # without using python date library for performance reason and
                # because it is expected to receive the date in a precise/fixed format :
                #   2018-05-28 16:56:55.000000+00
                value = {"Time": "{}T{}Z".format(row['user_ts'][0:10], row['user_ts'][11:23])}
                for i, v in row['reading'].items():
                    value.update({self.filter_identifier(i): v})

                data = OmfData()
                data.add_containerid(container_id).add_values(value)
                data_to_send.append(data.payload())
                _last_id = row['id']  # Latest position reached
            except Exception as e:
                self._logger.warning(
                    "cannot prepare sensor information for the destination - error details |{0}|".format(e))
        return data_to_send, _last_id

    async def prepare_to_send(self, raw_data):
        # Maintain below order
        asset_codes_to_evaluate, asset_codes_already_created = await self._find_new_omf_types \
            (raw_data) # Find new Types
        await self._add_new_omf_types(asset_codes_to_evaluate, asset_codes_already_created) # Create new Types
        await self._create_omf_static() # Create Static
        await self._create_omf_containers() # Create Containers
        await self._create_omf_links() # Create Links

        data_to_send, last_id = self.create_omf_data(raw_data) # Create Data
        return data_to_send, last_id

    async def send_message(self, message_type, omf_data):
        """ Sends data to PI - it retries the operation using a sleep time increased *2 for every retry"""
        url = self._config['URL']
        header = {
            'producertoken': self._config['producerToken'],
            'messagetype': message_type,
            'action': 'create',
            'messageformat': 'JSON',
            'omfversion': '1.0'
        }
        data = json.dumps(omf_data)
        timeout = self._config['OMFHttpTimeout']

        sleep_time = self._config['OMFRetrySleepTime']
        num_retry = 1
        max_retry = self._config['OMFMaxRetry']
        _message = None
        _error_exception = None

        while num_retry <= max_retry:
            _error_exception = None
            try:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=self._verify_ssl)) as session:
                    async with session.post(url=url, headers=header, data=data, timeout=timeout) as resp:
                        status_code = resp.status
                        text = await resp.text()
                        self._logger.debug(">>>>>>>> IN %s, %s, %s", message_type, omf_data, str(status_code) + " " + text)
                        self._logger.debug(">>>>>>>> OUT %s, %s", status_code, text)
                        if not str(status_code).startswith('2'):  # Evaluate the HTTP status codes
                            raise RuntimeError(str(status_code) + " " + text)
            except (TimeoutError, asyncio.TimeoutError) as ex:
                _message = "an error occurred during the request to the destination - server address |{0}| - error details |{1}|".format(self._config['URL'], "connection Timeout")
                _error_exception = plugin_exceptions.URLConnectionError(_message)
            except RuntimeError as e:
                _message = "an error occurred during the request to the destination - server address |{0}| - error details |{1}|".format(self._config['URL'], str(e))
                _error_exception = plugin_exceptions.URLFetchError(_message)
            except Exception as e:
                _message = "an error occurred during the request to the destination - server address |{0}| - error details |{1}|".format(self._config['URL'], str(e))
                _error_exception = Exception(_message)

            # Retry if any _error_exception is found
            if _error_exception is not None:
                await asyncio.sleep(sleep_time)
                num_retry += 1
                sleep_time *= 2
            else: break

        # Finally, if _error_exception is not None, raise it
        if _error_exception is not None: raise _error_exception
