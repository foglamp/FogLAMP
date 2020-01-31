# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Test sending data to PI using Web API

"""

__author__ = "Praveen Garg"
__copyright__ = "Copyright (c) 2019 Dianomic Systems Inc"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

import subprocess
import http.client
import json
import pytest
import os
import time
import utils


TEMPLATE_NAME = "template.json"
ASSET = "bFOGL-2964-e2e-CoAP"
DATAPOINT = "sensor"
DATAPOINT_VALUE = 20


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


def _verify_egress(read_data_from_pi, pi_host, pi_admin, pi_passwd, pi_db, wait_time, retries, asset_name):
    retry_count = 0
    data_from_pi = None

    # See C/plugins/common/omf.cpp
    af_hierarchy_level = "data_piwebapi"
    type_id = 1
    recorded_datapoint = "{}_{}measurement_{}.{}".format(af_hierarchy_level, type_id, asset_name, DATAPOINT)

    while (data_from_pi is None or data_from_pi == []) and retry_count < retries:
        data_from_pi = read_data_from_pi(pi_host, pi_admin, pi_passwd, pi_db, asset_name, {recorded_datapoint})
        retry_count += 1
        time.sleep(wait_time*2)

    if data_from_pi is None or retry_count == retries:
        assert False, "Failed to read data from PI"

    assert data_from_pi[recorded_datapoint][-1] == DATAPOINT_VALUE


@pytest.fixture
def start_south_north(reset_and_start_foglamp, add_south, south_branch, start_north_pi_server_c_web_api,
                      remove_data_file, remove_directories,
                      foglamp_url, pi_host, pi_port, pi_admin, pi_passwd, pi_db, asset_name=ASSET):
    """ This fixture
        reset_and_start_foglamp: Fixture that resets and starts foglamp, no explicit invocation, called at start
        add_south: Fixture that adds a south service with given configuration
        start_north_pi_server_c_web_api: Fixture that starts PI north task
        remove_data_file: Fixture that remove data file created during the tests
        remove_directories: Fixture that remove directories created during the tests"""

    fogbench_template_path = os.path.join(
        os.path.expandvars('${FOGLAMP_ROOT}'), 'data/{}'.format(TEMPLATE_NAME))
    with open(fogbench_template_path, "w") as f:
        f.write(
            '[{"name": "%s", "sensor_values": '
            '[{"name": "%s", "type": "number", "min": %d, "max": %d, "precision": 0}]}]' % (
                asset_name, DATAPOINT, DATAPOINT_VALUE, DATAPOINT_VALUE))

    south_plugin = "coap"
    add_south(south_plugin, south_branch, foglamp_url, service_name="bCoAP FOGL-2964")
    start_north_pi_server_c_web_api(foglamp_url, pi_host, pi_port, pi_db=pi_db, pi_user=pi_admin, pi_pwd=pi_passwd)

    yield start_south_north

    # Cleanup code that runs after the caller test is over
    remove_data_file(fogbench_template_path)
    remove_directories("/tmp/foglamp-south-{}".format(south_plugin))


@pytest.mark.skip(reason="Web API based tests needs new setup!")
class TestE2E_CoAP_PI_WebAPI:
    def test_end_to_end(self, start_south_north, read_data_from_pi, foglamp_url, pi_host, pi_admin, pi_passwd, pi_db,
                        wait_time, retries, skip_verify_north_interface, asset_name=ASSET):
        """ Test that data is inserted in FogLAMP and sent to PI
            start_south_north: Fixture that add south and north instance
            read_data_from_pi: Fixture to read data from PI
            skip_verify_north_interface: Flag for assertion of data using PI web API
            Assertions:
                on endpoint GET /foglamp/ping
                on endpoint GET /foglamp/statistics
                on endpoint GET /foglamp/asset
                on endpoint GET /foglamp/asset/<asset_name>
                data received from PI is same as data sent"""

        conn = http.client.HTTPConnection(foglamp_url)
        subprocess.run(["cd $FOGLAMP_ROOT/extras/python; python3 -m fogbench -t ../../data/{}; cd -".format(TEMPLATE_NAME)],
                       shell=True, check=True)

        time.sleep(wait_time)

        ping_response = get_ping_status(foglamp_url)
        assert 1 == ping_response["dataRead"]

        retry_count = 1
        sent = 0
        if not skip_verify_north_interface:
            while retries > retry_count:
                sent = ping_response["dataSent"]
                if sent == 1:
                    break
                else:
                    time.sleep(wait_time)

                retry_count += 1
                ping_response = get_ping_status(foglamp_url)

            assert 1 == sent, "Failed to send data via PI Web API using Basic auth"

        actual_stats_map = get_statistics_map(foglamp_url)
        assert 1 == actual_stats_map[asset_name.upper()]
        assert 1 == actual_stats_map['READINGS']
        if not skip_verify_north_interface:
            assert 1 == actual_stats_map['Readings Sent']
            assert 1 == actual_stats_map['NorthReadingsToPI_WebAPI']

        conn.request("GET", '/foglamp/asset')
        r = conn.getresponse()
        assert 200 == r.status
        r = r.read().decode()
        retval = json.loads(r)
        assert len(retval) == 1
        assert asset_name == retval[0]["assetCode"]
        assert 1 == retval[0]["count"]

        conn.request("GET", '/foglamp/asset/{}'.format(asset_name))
        r = conn.getresponse()
        assert 200 == r.status
        r = r.read().decode()
        retval = json.loads(r)
        assert {DATAPOINT: DATAPOINT_VALUE} == retval[0]["reading"]

        if not skip_verify_north_interface:
            egress_tracking_details = utils.get_asset_tracking_details(foglamp_url, "Egress")
            assert len(egress_tracking_details["track"]), "Failed to track Egress event"
            tracked_item = egress_tracking_details["track"][0]
            assert "NorthReadingsToPI_WebAPI" == tracked_item["service"]
            assert asset_name == tracked_item["asset"]
            assert "PI_Server_V2" == tracked_item["plugin"]

            _verify_egress(read_data_from_pi, pi_host, pi_admin, pi_passwd, pi_db, wait_time, retries, asset_name)
