# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Test GCP Gateway plugin"""

import os
import subprocess
import http.client
import json
import time
import pytest
from pathlib import Path
import utils

__author__ = "Yash Tatkondawar"
__copyright__ = "Copyright (c) 2019 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

taskname = "gcp-gateway"
north_plugin = "GCP-Gateway"
# TODO : pass package_build_version to setup script from conftest.py
package_build_version = "nightly"
# This  gives the path of directory where FogLAMP is cloned. test_file < packages < python < system < tests < ROOT
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
SCRIPTS_DIR_ROOT = "{}/tests/system/python/packages/data/".format(PROJECT_ROOT)


@pytest.fixture
def reset_foglamp(wait_time):
    try:
        subprocess.run(["cd {}/tests/system/python/scripts/package && ./reset"
                       .format(PROJECT_ROOT)], shell=True, check=True)
    except subprocess.CalledProcessError:
        assert False, "reset package script failed!"

    # Wait for foglamp server to start
    time.sleep(wait_time)


@pytest.fixture
def remove_and_add_foglamp_pkgs():
    try:
        subprocess.run(["cd {}/tests/system/python/scripts/package && ./remove"
                       .format(PROJECT_ROOT)], shell=True, check=True)
    except subprocess.CalledProcessError:
        assert False, "remove package script failed!"

    try:
        subprocess.run(["cd {}/tests/system/python/scripts/package/ && ./setup {}"
                       .format(PROJECT_ROOT, package_build_version)], shell=True, check=True)
    except subprocess.CalledProcessError:
        assert False, "setup package script failed"

    try:
        subprocess.run(["sudo apt install -y foglamp-north-gcp-gateway foglamp-south-sinusoid"], shell=True, check=True)
    except subprocess.CalledProcessError:
        assert False, "installation of http-south package failed"


def get_ping_status(foglamp_url):
    _connection = http.client.HTTPConnection(foglamp_url)
    _connection.request("GET", '/foglamp/ping')
    r = _connection.getresponse()
    assert 200 == r.status
    r = r.read().decode()
    jdoc = json.loads(r)
    return jdoc


def get_statistics_map(foglamp_url):
    _connection = http.client.HTTPConnection(foglamp_url)
    _connection.request("GET", '/foglamp/statistics')
    r = _connection.getresponse()
    assert 200 == r.status
    r = r.read().decode()
    jdoc = json.loads(r)
    return utils.serialize_stats_map(jdoc)


class TestGCPGateway:
    def test_gcp_gateway(self, remove_and_add_foglamp_pkgs, reset_foglamp, foglamp_url, wait_time):
        payload = {"name": "Sine", "type": "south", "plugin": "sinusoid", "enabled": True, "config": {}}
        post_url = "/foglamp/service"
        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("POST", post_url, json.dumps(payload))
        res = conn.getresponse()
        print(res.reason)
        assert 200 == res.status, "ERROR! POST {} request failed".format(post_url)
        res = res.read().decode()
        r = json.loads(res)

        payload = {"name": taskname,
                   "plugin": "{}".format(north_plugin),
                   "type": "north",
                   "schedule_type": 3,
                   "schedule_repeat": 30,
                   "schedule_enabled": True,
                   "config": {"project_id": {"value": "foglamp"},
                              "registry_id": {"value": "flreg1"},
                              "device_id": {"value": "flgate1"},
                              "key": {"value": "rsa_private"}}
                   }
        post_url = "/foglamp/scheduled/task"
        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("POST", post_url, json.dumps(payload))
        res = conn.getresponse()
        print(res.reason)
        assert 200 == res.status, "ERROR! POST {} request failed".format(post_url)
        res = res.read().decode()
        r = json.loads(res)

        time.sleep(wait_time)

        ping_response = get_ping_status(foglamp_url)
        assert 0 < ping_response["dataRead"]
        assert 0 < ping_response["dataSent"]

        actual_stats_map = get_statistics_map(foglamp_url)
        assert 0 < actual_stats_map['SINUSOID']
        assert 0 < actual_stats_map['READINGS']
        assert 0 < actual_stats_map['Readings Sent']
        assert 0 < actual_stats_map[taskname]
