# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

import platform
import os
from aiohttp import web
import logging
from foglamp.common import logger
from foglamp.common.plugin_discovery import PluginDiscovery
from foglamp.services.core.api.plugins import common

__author__ = "Rajesh Kumar"
__copyright__ = "Copyright (c) 2019, Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_logger = logger.setup(__name__, level=logging.INFO)

valid_plugin = ['north', 'south', 'filter', 'notificationDelivery', 'notificationRule']


async def plugin_delete(request):
    """
    Remove plugin from foglamp

    '''
    EndPoint: curl -X DELETE http://host-ip:port/foglamp/plugins/{type}/{name}
    '''
    Example:
        curl -X DELETE http://host-ip:port/foglamp/plugins/south/sinusoid
        curl -X DELETE http://host-ip:port/foglamp/plugins/north/http_north
        curl -X DELETE http://host-ip:port/foglamp/plugins/filter/expression
        curl -X DELETE http://host-ip:port/foglamp/plugins/notificationDelivery/alexa
        curl -X DELETE http://host-ip:port/foglamp/plugins/notificationRule/Average
    """
    plugin_type = request.match_info.get('type', None)
    name = request.match_info.get('name', None)
    try:
        plugin_type = str(plugin_type).lower() if not str(plugin_type).startswith('notification') else plugin_type
        if plugin_type not in valid_plugin:
            raise ValueError("Invalid plugin type.Please provide valid type:{}".format(valid_plugin))
        installed_plugin = PluginDiscovery.get_plugins_installed(plugin_type, False)
        if name not in [plugin['name'] for plugin in installed_plugin]:
            raise KeyError("Invalid {} plugin name or plugin is not installed.".format(name))
        if plugin_type in ['notificationDelivery', 'notificationRule']:
            plugin_type = 'notify' if plugin_type == 'notificationDelivery' else 'rule'
        res, log_path = purge_plugin(plugin_type, name)
        if res != 0:
            _logger.error("Something went wrong.Please check log:-{}".format(log_path))
            raise RuntimeError("Something went wrong.Please check log:-{}".format(log_path))
    except ValueError as ex:
        raise web.HTTPBadRequest(reason=str(ex))
    except KeyError as ex:
        raise web.HTTPBadRequest(reason=str(ex))
    except RuntimeError as ex:
        raise web.HTTPBadRequest(reason=str(ex))
    return web.json_response({'message': '{} plugin removed successfully'.format(name)})


def purge_plugin(plugin_type: str, name: str):
    """
        Remove plugin based on platform
    """
    _logger.info("Plugin removal started...")
    name = name.replace('_', '-').lower()
    plugin_name = 'foglamp-{}-{}'.format(plugin_type, name)
    stdout_file_path = common.create_log_file(action='delete', plugin_name=plugin_name)
    get_platform = platform.platform()
    package_manager = 'yum' if 'centos' in get_platform or 'redhat' in get_platform else 'apt'
    if package_manager == 'yum':
        cmd = "sudo {} -y remove {} > {} 2>&1".format(package_manager, plugin_name, stdout_file_path)
    else:
        cmd = "sudo {} -y purge {} > {} 2>&1".format(package_manager, plugin_name, stdout_file_path)
    code = os.system(cmd)
    return code, stdout_file_path
