# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

"""Core server module"""

import signal
import asyncio
import time
import uuid
from aiohttp import web

__author__ = "Amarendra Kumar Sinha"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

__start_time = time.time()

__registry = list()

async def ping(request):
    since_started = time.time() - __start_time

    return web.json_response({'uptime': since_started})

async def register(request):
    """
    Register a service

    :Example: curl -d '{"type": "StorageService", "name": "Storage Services", "address": "127.0.0.1", "port": "8090"}'  -X POST  http://localhost:8082/foglamp/service
    """

    try:
        data = await request.json()

        service_name = data.get('name', None)
        service_type = data.get('type', None)
        service_address = data.get('address', None)
        service_port = data.get('port', None)

        if not (service_name or service_type or service_address or service_port):
            raise ValueError('One or more values for type/name/address/port missing')

        service_id = uuid.uuid4()

        _resp = {
            'id': str(service_id),
            'message': "Service registered successfully"
        }

        __registry.append({'service_id': str(service_id), 'status': 'Running', 'payload': data})

        return web.json_response(_resp)
    except ValueError as ex:
        raise web.HTTPNotFound(reason=str(ex))
    except Exception as ex:
        raise web.HTTPInternalServerError(reason='FogLAMP has encountered an internal error', text=str(ex))

async def unregister(request):
    """
    Unregister a service

    :Example: curl -X DELETE  http://localhost:8082/foglamp/service/dc9bfc01-066a-4cc0-b068-9c35486db87f
    """

    try:
        service_id = request.match_info.get('service_id', None)

        if not service_id:
            raise ValueError('No service_id')

        match = next((l for l in __registry if l['service_id'] == service_id), None)
        if not match:
            raise ValueError('This service_id {} does not exist'.format(service_id))

        __registry.remove(match)

        _resp = {'id': str(service_id), 'message': "Service unresistered"}

        return web.json_response(_resp)
    except ValueError as ex:
        raise web.HTTPNotFound(reason=str(ex))
    except Exception as ex:
        raise web.HTTPInternalServerError(reason='FogLAMP has encountered an internal error', text=str(ex))


async def get_service(request):
    """
    Returns a list of all services
    """
    try:
        return web.json_response(__registry)
    except Exception as ex:
        raise web.HTTPInternalServerError(reason='FogLAMP has encountered an internal error', text=str(ex))

async def shutdown(request):
    pass

async def register_interest(request):
    pass

async def unregister_interest(request):
    pass

async def notify_change(request):
    pass

