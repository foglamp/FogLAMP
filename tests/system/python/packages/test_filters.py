# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Test Filters Package System tests:
        foglamp-south-http-south south plugin
        foglamp-filter-expression, foglamp-filter-python35, foglamp-filter-simple-python, foglamp-filter-ema filter plugins
"""

# FIXME: This test requires aiocoap,cbor pip packages installed explicitly due to FOGL-3500

__author__ = "Yash Tatkondawar"
__copyright__ = "Copyright (c) 2019 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

import subprocess
import http.client
import json
import os
import time
import urllib.parse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
SCRIPTS_DIR_ROOT = "{}/tests/system/python/packages/data/".format(PROJECT_ROOT)

ASSET_NAME_PY35 = "end_to_end_py35"
ASSET_NAME_SP = "end_to_end_sp"
ASSET_NAME_EMA = "end_to_end_ema"
TEMPLATE_NAME = "template.json"
SENSOR_VALUE = 12.25
# TODO: pass package_build_version to setup script from conftest.py
package_build_version = "nightly"


def post_request(foglamp_url, post_url, payload):
    conn = http.client.HTTPConnection(foglamp_url)
    conn.request("POST", post_url, json.dumps(payload))
    res = conn.getresponse()
    assert 200 == res.status, "ERROR! POST {} request failed".format(post_url)
    res = res.read().decode()
    r = json.loads(res)
    return r


def get_request(foglamp_url, get_url):
    con = http.client.HTTPConnection(foglamp_url)
    con.request("GET", get_url)
    res = con.getresponse()
    assert 200 == res.status, "ERROR! GET {} request failed".format(get_url)
    r = json.loads(res.read().decode())
    return r


def put_request(foglamp_url, put_url, payload):
    conn = http.client.HTTPConnection(foglamp_url)
    conn.request("PUT", put_url, json.dumps(payload))
    res = conn.getresponse()
    assert 200 == res.status, "ERROR! PUT {} request failed".format(put_url)
    r = json.loads(res.read().decode())
    return r


def call_fogbench(wait_time):
    execute_fogbench = 'cd {}/extras/python ;python3 -m fogbench -t $FOGLAMP_ROOT/data/tests/{} ' \
                       '-p http -O 10'.format(PROJECT_ROOT, TEMPLATE_NAME)
    exit_code = os.system(execute_fogbench)
    assert 0 == exit_code
    time.sleep(wait_time)


def add_south_http(foglamp_url, name):
    data = {"name": name, "type": "south", "plugin": "http_south", "enabled": True}
    post_url = "/foglamp/service"
    post_request(foglamp_url, post_url, data)


def generate_json(asset_name):
    subprocess.run(["cd $FOGLAMP_ROOT/data && mkdir -p tests"], shell=True, check=True)

    fogbench_template_path = os.path.join(
        os.path.expandvars('${FOGLAMP_ROOT}'), 'data/tests/{}'.format(TEMPLATE_NAME))
    with open(fogbench_template_path, "w") as f:
        f.write(
            '[{"name": "%s", "sensor_values": '
            '[{"name": "sensor", "type": "number", "min": %f, "max": %f, "precision": 2}]}]' % (
                asset_name, SENSOR_VALUE, SENSOR_VALUE))


def verify_south_added(foglamp_url, name):
    get_url = "/foglamp/south"
    result = get_request(foglamp_url, get_url)
    assert len(result["services"])
    assert "name" in result["services"][0]
    assert name == result["services"][0]["name"]


def verify_ping(foglamp_url):
    get_url = "/foglamp/ping"
    ping_result = get_request(foglamp_url, get_url)
    assert "dataRead" in ping_result
    assert 0 < ping_result['dataRead'], "data NOT seen in ping header"
    return ping_result


def verify_asset(foglamp_url, ASSET_NAME):
    ASSET_NAME = "http-" + ASSET_NAME
    get_url = "/foglamp/asset"
    result = get_request(foglamp_url, get_url)
    assert len(result), "No asset found"
    assert "assetCode" in result[0]
    assert ASSET_NAME == result[0]["assetCode"]
    return result[0]


def verify_readings(foglamp_url, ASSET_NAME):
    ASSET_NAME = "http-" + ASSET_NAME
    get_url = "/foglamp/asset/{}".format(ASSET_NAME)
    result = get_request(foglamp_url, get_url)
    assert len(result), "No readings found"
    assert "reading" in result[0]
    return result[0]


class TestPython35:
    HTTP_SOUTH_SVC_NAME = "South_http #1"

    @classmethod
    def setup_class(cls):
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
            subprocess.run(["sudo apt install -y foglamp-south-http-south foglamp-filter-expression "
                            "foglamp-filter-python35"], shell=True, check=True)
        except subprocess.CalledProcessError:
            assert False, "installation of packages failed"

        try:
            subprocess.run(["cd {}/tests/system/python/scripts/package && ./reset"
                           .format(PROJECT_ROOT)], shell=True, check=True)
        except subprocess.CalledProcessError:
            assert False, "reset package script failed!"

    def test_filter_python35_with_uploaded_script(self, foglamp_url, wait_time):
        add_south_http(foglamp_url, self.HTTP_SOUTH_SVC_NAME)
        time.sleep(wait_time * 2)
        verify_south_added(foglamp_url, self.HTTP_SOUTH_SVC_NAME)

        generate_json(ASSET_NAME_PY35)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 10 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 10 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 12.25 == reading_resp["reading"]["sensor"]

        data = {"name": "py35", "plugin": "python35", "filter_config": {"enable": "true"}}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["py35"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        url = foglamp_url + urllib.parse.quote('/foglamp/category/{}_py35/script/upload'
                                               .format(self.HTTP_SOUTH_SVC_NAME))
        script_path = 'script=@{}/readings35.py'.format(SCRIPTS_DIR_ROOT)
        upload_script = "curl -sX POST '{}' -F '{}'".format(url, script_path)
        exit_code = os.system(upload_script)
        assert 0 == exit_code

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 20 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 20 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 2.45 == reading_resp["reading"]["sensor"]

    def test_filter_python35_with_updated_content(self, foglamp_url, retries, wait_time):
        copy_file = "cp {}/readings35.py {}/readings35.py.bak".format(SCRIPTS_DIR_ROOT, SCRIPTS_DIR_ROOT)
        exit_code = os.system(copy_file)
        assert 0 == exit_code

        sed_cmd = "sed -i \"s+newVal .*+newVal = reading[key] * 10+\" {}/readings35.py".format(SCRIPTS_DIR_ROOT)
        exit_code = os.system(sed_cmd)
        assert 0 == exit_code

        url = foglamp_url + urllib.parse.quote('/foglamp/category/{}_py35/script/upload'
                                               .format(self.HTTP_SOUTH_SVC_NAME))
        script_path = 'script=@{}/readings35.py'.format(SCRIPTS_DIR_ROOT)
        upload_script = "curl -sX POST '{}' -F '{}'".format(url, script_path)
        exit_code = os.system(upload_script)
        assert 0 == exit_code

        time.sleep(wait_time)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 30 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 30 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 122.5 == reading_resp["reading"]["sensor"]

        move_file = "mv {}/readings35.py.bak {}/readings35.py".format(SCRIPTS_DIR_ROOT, SCRIPTS_DIR_ROOT)
        exit_code = os.system(move_file)
        assert 0 == exit_code, "{} cmd failed!".format(move_file)

    def test_filter_python35_disable_enable(self, foglamp_url, retries, wait_time):
        data = {"enable": "false"}
        put_request(foglamp_url, urllib.parse.quote("/foglamp/category/{}_py35".format(self.HTTP_SOUTH_SVC_NAME),
                                                    safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 40 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 40 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 12.25 == reading_resp["reading"]["sensor"]

        data = {"enable": "true"}
        put_request(foglamp_url, urllib.parse.quote("/foglamp/category/{}_py35"
                                                    .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 50 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 50 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 122.5 == reading_resp["reading"]["sensor"]

    def test_filter_python35_expression(self, foglamp_url, wait_time):
        data = {"name": "expr", "plugin": "expression",
                "filter_config": {"name": "triple", "expression": "sensor*2", "enable": "true"}}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["expr"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/disable"
        put_request(foglamp_url, put_url, data)

        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/enable"
        put_request(foglamp_url, put_url, data)

        time.sleep(wait_time)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 60 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 60 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 122.5 == reading_resp["reading"]["sensor"]
        assert 245.0 == reading_resp["reading"]["triple"]

    def test_delete_filter_python35(self, foglamp_url, wait_time):
        data = {"pipeline": ["expr"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=false" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("DELETE", '/foglamp/filter/py35')
        res = conn.getresponse()
        assert 200 == res.status, "ERROR! Failed to delete filter"

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 70 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 70 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 24.5 == reading_resp["reading"]["triple"]

    def test_filter_python35_by_enabling_disabling_south(self, foglamp_url, wait_time):
        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/disable"
        put_request(foglamp_url, put_url, data)

        time.sleep(wait_time)

        get_url = "/foglamp/south"
        result = get_request(foglamp_url, get_url)
        assert self.HTTP_SOUTH_SVC_NAME == result["services"][0]["name"]
        assert "shutdown" == result["services"][0]["status"]

        data = {"name": "py35", "plugin": "python35", "filter_config": {"enable": "true"}}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["py35"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        url = foglamp_url + urllib.parse.quote('/foglamp/category/{}_py35/script/upload'
                                               .format(self.HTTP_SOUTH_SVC_NAME))
        script_path = 'script=@{}/readings35.py'.format(SCRIPTS_DIR_ROOT)
        upload_script = "curl -sX POST '{}' -F '{}'".format(url, script_path)
        exit_code = os.system(upload_script)
        assert 0 == exit_code

        data = {"schedule_name": self.HTTP_SOUTH_SVC_NAME}
        put_url = "/foglamp/schedule/enable"
        put_request(foglamp_url, put_url, data)

        time.sleep(wait_time)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 80 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_PY35)
        assert 80 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_PY35)
        assert 2.45 == reading_resp["reading"]["sensor"]
        assert 4.9 == reading_resp["reading"]["triple"]

    def test_delete_south_service(self, foglamp_url):
        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("DELETE", urllib.parse.quote('/foglamp/service/{}'
                                                  .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'))
        res = conn.getresponse()
        assert 200 == res.status, "ERROR! Failed to delete service"

        get_url = "/foglamp/south"
        result = get_request(foglamp_url, get_url)
        assert 0 == len(result["services"])

        filename = "{}_py35_script_readings35.py".format(self.HTTP_SOUTH_SVC_NAME).lower()
        filepath = "$FOGLAMP_ROOT/data/scripts/{}".format(filename)
        assert False is os.path.isfile('{}'.format(filepath))

    @classmethod
    def teardown_class(cls):
        try:
            subprocess.run(["cd {}/tests/system/python/scripts/package && ./reset"
                           .format(PROJECT_ROOT)], shell=True, check=True)
            subprocess.run(["cd $FOGLAMP_ROOT/data && rm -rf tests"], shell=True, check=True)
        except subprocess.CalledProcessError:
            assert False, "reset failed!"


class TestSimplePython:
    HTTP_SOUTH_SVC_NAME = "South_http #2"

    @classmethod
    def setup_class(cls):
        try:
            subprocess.run(["sudo apt install -y foglamp-filter-simple-python"], shell=True, check=True)
        except subprocess.CalledProcessError:
            assert False, "installation of packages failed"

    def test_filter_simple_python(self, foglamp_url, wait_time):
        add_south_http(foglamp_url, self.HTTP_SOUTH_SVC_NAME)
        time.sleep(wait_time * 2)
        verify_south_added(foglamp_url, self.HTTP_SOUTH_SVC_NAME)

        generate_json(ASSET_NAME_SP)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 10 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 10 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 12.25 == reading_resp["reading"]["sensor"]

        data = {"name": "SP",
                "plugin": "simple-python",
                "filter_config": {
                    "code": "reading[b'\''sensor'\''] = reading[b'\''sensor'\''] + 100",
                    "enable": "true"
                }}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["SP"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 20 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 20 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 112.25 == reading_resp["reading"]["sensor"]

    def test_filter_simple_python_with_updated_content(self, foglamp_url, wait_time):
        data = {"code": "reading[b'''sensor'''] = reading[b'''sensor'''] * 10"}
        put_url = "/foglamp/category/{}_SP".format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 30 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 30 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 122.5 == reading_resp["reading"]["sensor"]

    def test_filter_simple_python_disable_enable(self, foglamp_url, wait_time):
        data = {"enable": "false"}
        put_request(foglamp_url, urllib.parse.quote("/foglamp/category/{}_SP"
                                                    .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 40 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 40 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 12.25 == reading_resp["reading"]["sensor"]

        data = {"enable": "true"}
        put_request(foglamp_url, urllib.parse.quote("/foglamp/category/{}_SP"
                                                    .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 50 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 50 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 122.5 == reading_resp["reading"]["sensor"]

    def test_filter_simple_python_and_expression(self, foglamp_url, wait_time):
        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/disable"
        put_request(foglamp_url, put_url, data)

        data = {"name": "expr", "plugin": "expression",
                "filter_config": {"name": "triple", "expression": "sensor*2", "enable": "true"}}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["expr"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/enable"
        put_request(foglamp_url, put_url, data)

        # Sleeping until service is enabled
        time.sleep(wait_time)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 60 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 60 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 122.5 == reading_resp["reading"]["sensor"]
        assert 245 == reading_resp["reading"]["triple"]

    def test_delete_filter_simple_python(self, foglamp_url, wait_time):
        data = {"pipeline": ["expr"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=false" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("DELETE", '/foglamp/filter/SP')
        res = conn.getresponse()
        assert 200 == res.status, "ERROR! Failed to delete filter"

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 70 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 70 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 24.5 == reading_resp["reading"]["triple"]

    def test_filter_simple_python_by_enabling_disabling_south(self, foglamp_url, wait_time):
        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/disable"
        put_request(foglamp_url, put_url, data)

        time.sleep(wait_time)

        get_url = "/foglamp/south"
        result = get_request(foglamp_url, get_url)
        assert self.HTTP_SOUTH_SVC_NAME == result["services"][0]["name"]
        assert "shutdown" == result["services"][0]["status"]

        data = {"name": "SP #1",
                "plugin": "simple-python",
                "filter_config": {
                    "code": "reading[b'\''sensor'\''] = reading[b'\''sensor'\''] + 100",
                    "enable": "true"
                }}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["SP #1"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/enable"
        put_request(foglamp_url, put_url, data)

        # Sleeping until service is enabled
        time.sleep(wait_time)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 80 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_SP)
        assert 80 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_SP)
        assert 112.25 == reading_resp["reading"]["sensor"]
        assert 24.5 == reading_resp["reading"]["triple"]

    def test_delete_south_service(self, foglamp_url):
        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("DELETE", urllib.parse.quote('/foglamp/service/{}'
                                                  .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'))
        res = conn.getresponse()
        assert 200 == res.status, "ERROR! Failed to delete service"

        get_url = "/foglamp/south"
        result = get_request(foglamp_url, get_url)
        assert 0 == len(result["services"])

    @classmethod
    def teardown_class(cls):
        try:
            subprocess.run(["cd {}/tests/system/python/scripts/package && ./reset"
                           .format(PROJECT_ROOT)], shell=True, check=True)
            subprocess.run(["cd $FOGLAMP_ROOT/data && rm -rf tests"], shell=True, check=True)
        except subprocess.CalledProcessError:
            assert False, "reset failed!"


class TestEma:
    HTTP_SOUTH_SVC_NAME = "South_http #3"

    @classmethod
    def setup_class(cls):
        try:
            subprocess.run(["sudo apt install -y foglamp-filter-ema"], shell=True, check=True)
        except subprocess.CalledProcessError:
            assert False, "installation of package failed"

    def test_filter_ema(self, foglamp_url, retries, wait_time):
        add_south_http(foglamp_url, self.HTTP_SOUTH_SVC_NAME)
        time.sleep(wait_time * 2)
        verify_south_added(foglamp_url, self.HTTP_SOUTH_SVC_NAME)

        generate_json(ASSET_NAME_EMA)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 10 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 10 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]

        data = {"name": "ema", "plugin": "ema", "filter_config": {"enable": "true"}}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["ema"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 20 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 20 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 12.25 == reading_resp["reading"]["ema"]

    def test_filter_ema_with_updated_content(self, foglamp_url, wait_time):
        data = {"rate": "1"}
        put_url = "/foglamp/category/{}_ema".format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 30 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 30 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 12.25 == reading_resp["reading"]["ema"]

    def test_filter_ema_disable_enable(self, foglamp_url, wait_time):
        data = {"enable": "false"}
        put_request(foglamp_url, urllib.parse.quote("/foglamp/category/{}_ema"
                                                    .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 40 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 40 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]

        data = {"enable": "true"}
        put_request(foglamp_url, urllib.parse.quote("/foglamp/category/{}_ema"
                                                    .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'), data)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 50 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 50 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 12.25 == reading_resp["reading"]["ema"]

    def test_filter_ema_and_expression(self, foglamp_url, wait_time):
        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/disable"
        put_request(foglamp_url, put_url, data)

        time.sleep(wait_time)

        data = {"name": "expr", "plugin": "expression",
                "filter_config": {"name": "triple", "expression": "sensor*2", "enable": "true"}}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["expr"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/enable"
        put_request(foglamp_url, put_url, data)

        # Sleeping until service is enabled
        time.sleep(wait_time)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 60 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 60 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 12.25 == reading_resp["reading"]["ema"]
        assert 24.5 == reading_resp["reading"]["triple"]

    def test_delete_filter_ema(self, foglamp_url, wait_time):
        data = {"pipeline": ["expr"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=false" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("DELETE", '/foglamp/filter/ema')
        res = conn.getresponse()
        assert 200 == res.status, "ERROR! Failed to delete filter"

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 70 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 70 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 24.5 == reading_resp["reading"]["triple"]

    def test_filter_ema_by_enabling_disabling_south(self, foglamp_url, wait_time):
        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/disable"
        put_request(foglamp_url, put_url, data)

        time.sleep(wait_time)

        get_url = "/foglamp/south"
        result = get_request(foglamp_url, get_url)
        assert self.HTTP_SOUTH_SVC_NAME == result["services"][0]["name"]
        assert "shutdown" == result["services"][0]["status"]

        data = {"name": "ema1", "plugin": "ema", "filter_config": {"enable": "true"}}
        post_request(foglamp_url, "/foglamp/filter", data)

        data = {"pipeline": ["ema1"]}
        put_url = "/foglamp/filter/{}/pipeline?allow_duplicates=true&append_filter=true" \
            .format(self.HTTP_SOUTH_SVC_NAME)
        put_request(foglamp_url, urllib.parse.quote(put_url, safe='?,=,&,/'), data)

        data = {"schedule_name": "{}".format(self.HTTP_SOUTH_SVC_NAME)}
        put_url = "/foglamp/schedule/enable"
        put_request(foglamp_url, put_url, data)

        # Sleeping until service is enabled
        time.sleep(wait_time)

        call_fogbench(wait_time)

        ping_response = verify_ping(foglamp_url)
        assert 80 == ping_response["dataRead"]

        asset_response = verify_asset(foglamp_url, ASSET_NAME_EMA)
        assert 80 == asset_response["count"]

        reading_resp = verify_readings(foglamp_url, ASSET_NAME_EMA)
        assert 12.25 == reading_resp["reading"]["sensor"]
        assert 24.5 == reading_resp["reading"]["triple"]
        assert 17.1104009314 == reading_resp["reading"]["ema"]

    def test_delete_south_service(self, foglamp_url):
        conn = http.client.HTTPConnection(foglamp_url)
        conn.request("DELETE", urllib.parse.quote('/foglamp/service/{}'
                                                  .format(self.HTTP_SOUTH_SVC_NAME), safe='?,=,&,/'))
        res = conn.getresponse()
        assert 200 == res.status, "ERROR! Failed to delete service"

        get_url = "/foglamp/south"
        result = get_request(foglamp_url, get_url)
        assert 0 == len(result["services"])

    @classmethod
    def teardown_class(cls):
        try:
            subprocess.run(["cd {}/tests/system/python/scripts/package && ./reset"
                           .format(PROJECT_ROOT)], shell=True, check=True)
            subprocess.run(["cd $FOGLAMP_ROOT/data && rm -rf tests"], shell=True, check=True)
        except subprocess.CalledProcessError:
            assert False, "reset failed!"

# TODO: Add tests for filters with North also.
