# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

import asyncio
import time
import json
import logging
import socket
import subprocess
import os

from aiohttp import web

from foglamp.common import logger
from foglamp.services.core import server
from foglamp.services.core.api.statistics import get_statistics
from foglamp.services.core import connect
from foglamp.common.configuration_manager import ConfigurationManager
from foglamp.services.core.service_registry.service_registry import ServiceRegistry
from foglamp.common.service_record import ServiceRecord

__author__ = "Amarendra K. Sinha, Ashish Jabble"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

__start_time = time.time()

_logger = logger.setup(__name__, level=logging.INFO)

_help = """
    -------------------------------------------------------------------------------
    | GET             | /foglamp/ping                                             |
    | PUT             | /foglamp/shutdown                                         |
    | PUT             | /foglamp/restart                                          |
    -------------------------------------------------------------------------------
"""


def get_since_started():
    try:
        # Full command is:
        #      PID=$(ps -ef | grep foglamp.services.core | grep -v grep | awk '{print $2}'); ps -o etimes= -p $PID | awk '{print $1}'
        cmd = "ps -o etimes= -p $PID"

        # Get PID
        _FOGLAMP_DATA = os.getenv("FOGLAMP_DATA", default=None)
        _FOGLAMP_ROOT = os.getenv("FOGLAMP_ROOT", default='/usr/local/foglamp')
        path = _FOGLAMP_ROOT + "/data" if _FOGLAMP_DATA is None else _FOGLAMP_DATA
        pid_file_name = "{}/var/run/foglamp.core.pid".format(path)
        with open(pid_file_name, 'r') as content_file:
            content = content_file.read()
            foglamp_pid = json.loads(content).get("processID")

        # Get uptime
        a = subprocess.Popen(["ps", "-o", "etimes=", "-p", "{}".format(foglamp_pid)], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        outs, errs = a.communicate()
        if outs is None and errs is None:
            raise OSError('Error in executing command "{}"'.format(cmd))
        if a.returncode != 0:
            raise OSError('Error in executing command "{}". Error: {}, return code: {}'.format(cmd,
                                                                                     errs.decode('utf-8').replace('\n', ''),
                                                                                     a.returncode))
        d = [b for b in outs.decode('utf-8').split('\n') if b != '']
        return d[0].strip()
    except Exception as ex:
        _logger.exception("Error in getting uptime: {}".format(str(ex)))


async def ping(request):
    """
    Args:
       request:

    Returns:
           basic health information json payload

    :Example:
           curl -X GET http://localhost:8081/foglamp/ping
    """

    try:
        auth_token = request.token
    except AttributeError:
        if request.is_auth_optional is False:
            cfg_mgr = ConfigurationManager(connect.get_storage_async())
            category_item = await cfg_mgr.get_category_item('rest_api', 'allowPing')
            allow_ping = True if category_item['value'].lower() == 'true' else False
            if allow_ping is False:
                _logger.warning("Permission denied for Ping when Auth is mandatory.")
                raise web.HTTPForbidden

    stats_request = request.clone(rel_url='foglamp/statistics')
    data_read, data_sent, data_purged = await get_stats(stats_request)

    host_name = socket.gethostname()
    # all addresses for the host
    all_ip_addresses_cmd_res = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE)
    ip_addresses = all_ip_addresses_cmd_res.stdout.decode('utf-8').replace("\n", "").strip().split(" ")

    svc_name = server.Server._service_name

    def services_health_litmus_test():
        all_svc_status = [ServiceRecord.Status(int(service_record._status)).name.upper()
                          for service_record in ServiceRegistry.all()]
        if 'FAILED' in all_svc_status:
            return 'red'
        elif 'UNRESPONSIVE' in all_svc_status:
            return 'amber'
        return 'green'

    status_color = services_health_litmus_test()
    safe_mode = True if server.Server.running_in_safe_mode else False

    return web.json_response({'uptime': get_since_started(),
                              'dataRead': data_read,
                              'dataSent': data_sent,
                              'dataPurged': data_purged,
                              'authenticationOptional': request.is_auth_optional,
                              'serviceName': svc_name,
                              'hostName': host_name,
                              'ipAddresses': ip_addresses,
                              'health': status_color,
                              'safeMode': safe_mode
                              })


async def get_stats(req):
    """
    :param req: a clone of 'foglamp/statistics' endpoint request
    :return:  data_read, data_sent, data_purged
    """

    res = await get_statistics(req)
    stats = json.loads(res.body.decode())

    def filter_stat(k):

        """
        there is no statistics about 'Readings Sent' at the start of FogLAMP
        so the specific exception is caught and 0 is returned to avoid the error 'index out of range'
        calling the API ping.
        """
        try:
            v = [s['value'] for s in stats if s['key'] == k]
            value = int(v[0])
        except IndexError:
            value = 0

        return value

    data_read = filter_stat('READINGS')
    data_sent = filter_stat('Readings Sent')
    data_purged = filter_stat('PURGED')

    return data_read, data_sent, data_purged


async def shutdown(request):
    """
    Args:
        request:

    Returns:

    :Example:
            curl -X PUT http://localhost:8081/foglamp/shutdown
    """

    try:
        loop = request.loop
        loop.call_later(2, do_shutdown, request)
        return web.json_response({'message': 'FogLAMP shutdown has been scheduled. '
                                             'Wait for few seconds for process cleanup.'})
    except TimeoutError as err:
        raise web.HTTPInternalServerError(reason=str(err))
    except Exception as ex:
        raise web.HTTPException(reason=str(ex))


def do_shutdown(request):
    _logger.info("Executing controlled shutdown")
    try:
        loop = request.loop
        asyncio.ensure_future(server.Server.shutdown(request), loop=loop)
    except RuntimeError as e:
        _logger.exception("Error while stopping FogLAMP server: {}".format(str(e)))
        raise


async def restart(request):
    """
    :Example:
            curl -X PUT http://localhost:8081/foglamp/restart
    """

    try:
        _logger.info("Executing controlled shutdown and start")
        asyncio.ensure_future(server.Server.restart(request), loop=request.loop)
        return web.json_response({'message': 'FogLAMP restart has been scheduled.'})
    except TimeoutError as e:
        _logger.exception("Error while stopping FogLAMP server: %s", e)
        raise web.HTTPInternalServerError(reason=e)
    except Exception as ex:
        _logger.exception("Error while stopping FogLAMP server: %s", ex)
        raise web.HTTPException(reason=ex)
