import subprocess
import os
import json
import importlib.util
from typing import Dict

from foglamp.common import logger
from foglamp.common.common import _FOGLAMP_ROOT, _FOGLAMP_PLUGIN_PATH

_logger = logger.setup(__name__)
_lib_path = _FOGLAMP_ROOT + "/" + "plugins"


def get_plugin_info(name, dir):
    try:
        arg1 = _find_c_util('get_plugin_info')
        arg2 = _find_c_lib(name, dir)
        cmd_with_args = [arg1, arg2, "plugin_info"]
        p = subprocess.Popen(cmd_with_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        res = out.decode("utf-8")
        jdoc = json.loads(res)
    except (OSError, subprocess.CalledProcessError, Exception) as ex:
        _logger.exception("%s C plugin get info failed due to %s", name, ex)
        return {}
    else:
        return jdoc


def _find_c_lib(name, dir):
    _path = [_lib_path + "/" + dir]
    _path = _find_plugins_from_env(_path)
    for fp in _path:
        for path, subdirs, files in os.walk(fp):
            for fname in files:
                # C-binary file
                if fname.endswith(name + '.so'):
                    return os.path.join(path, fname)
    return None


def _find_c_util(name):
    for path, subdirs, files in os.walk(_FOGLAMP_ROOT):
        for fname in files:
            # C-utility file
            if fname == name:
                return os.path.join(path, fname)
    return None


def find_c_plugin_libs(direction):
    libraries = []
    _path = [_lib_path]
    _path = _find_plugins_from_env(_path)
    for fp in _path:
        for root, dirs, files in os.walk(fp + "/" + direction):
            for name in dirs:
                p = os.path.join(root, name)
                for path, subdirs, f in os.walk(p):
                    for fname in f:
                        # C-binary file
                        if fname.endswith('.so'):
                            # Replace lib and .so from fname
                            libraries.append(fname.replace("lib", "").replace(".so", ""))
    return libraries


def _find_plugins_from_env(_plugin_path: list) -> list:
    if _FOGLAMP_PLUGIN_PATH:
        plugin_paths = _FOGLAMP_PLUGIN_PATH.split(";")
        for pp in plugin_paths:
            if not os.path.isdir(pp):
                _logger.warning("{} is not a directory!".format(pp))
            else:
                subdirs = [dirs for root, dirs, files in os.walk(pp)]
                if not len(subdirs):
                    _logger.warning("{} - no sub directories found".format(pp))
                else:
                    _plugin_path.append(pp)
    return _plugin_path


def load_python_plugin(plugin_module_path: str, plugin: str, _type: str) -> Dict:
    _plugin = None
    try:
        spec = importlib.util.spec_from_file_location("module.name", "{}/{}.py".format(plugin_module_path, plugin))
        _plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_plugin)
    except FileNotFoundError:
        if _FOGLAMP_PLUGIN_PATH:
            plugin_paths = _FOGLAMP_PLUGIN_PATH.split(";")
            for pp in plugin_paths:
                if os.path.isdir(pp):
                    plugin_module_path = "{}/{}/{}".format(pp, _type, plugin)
                    spec = importlib.util.spec_from_file_location("module.name", "{}/{}.py".format(
                        plugin_module_path, plugin))
                    _plugin = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(_plugin)

    return _plugin


def load_and_fetch_python_plugin_info(plugin_module_path: str, plugin: str, _type: str) -> Dict:
    _plugin = load_python_plugin(plugin_module_path, plugin, _type)
    # Fetch configuration from the configuration defined in the plugin
    plugin_info = _plugin.plugin_info()
    if plugin_info['type'] != _type:
        msg = "Plugin of {} type is not supported".format(plugin_info['type'])
        raise TypeError(msg)
    return plugin_info
