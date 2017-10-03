#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Tests backup and restore core functionalities
"""

# import pytest
import sys
import os
import time
import subprocess

import foglamp.backup_restore.lib as lib
from foglamp.backup_restore.backup import (Backup)
# from foglamp.backup_restore.restore import (Restore)

from foglamp import logger

__author__ = "Stefano Simonelli"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_MODULE_NAME = "test_backup_restore"

_CMD_TIMEOUT = " timeout --signal=9  "


# Logger setup, for the library also
_logger = logger.setup(_MODULE_NAME)
lib._logger = _logger


def exec_external_command(_cmd, _output_capture=False, _timeout=0, wait=True):
    """
    # FIXME: temporary function

    Executes an external/shell commands


    Args:
        _cmd: command to execute
        _output_capture: if the output of the command should be captured or not
        _timeout: 0 no timeout or the timeout in seconds for the execution of the command

    Returns:
        _status: exit status of the command
        _output: output of the command
    Raises:
    Todo:
    """

    _output = ""

    if _timeout != 0:
        _cmd = _CMD_TIMEOUT + str(_timeout) + " " + _cmd
        _logger.debug("Executing command using the timeout |{timeout}| ".format(timeout=_timeout))

    _logger.debug("{func} - cmd |{cmd}| ".format(func=sys._getframe().f_code.co_name,
                                                 cmd=_cmd))

    if _output_capture:
        process = subprocess.Popen(_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    else:
        process = subprocess.Popen(_cmd, shell=True)

    if wait:
        _status = process.wait()
    else:
        _status = 0
        _output = ""

    if _output_capture:
        output_tmp = process.stdout.read()

        output_tmp2 = output_tmp.decode("utf-8")
        _output = output_tmp2.replace("\n", "\n\r")

    return _status, _output


class TestBackupRestore:
    """ Tests backup and restore code functionalities """

    @staticmethod
    def _retrieve_last_backup_info():
        cmd = """

            SELECT  id,file_name FROM foglamp.backups WHERE id = (
                SELECT max(id) FROM foglamp.backups
            )            
        """

        data = lib.storage_retrieve(cmd)

        if len(data) > 0:
            _id = data[0]['id']
            file_name = data[0]['file_name']
        else:
            _id = -1
            file_name = ""

        return _id, file_name

    @staticmethod
    def _load_data(n_times, wait=False):

        cmd = """
            bash -c ' 
            cd  ~/Development/FogLAMP/src/python;\
            source venv/foglamp/bin/activate;\
            cd  ~/Development/FogLAMP/benchmarks;\
            for i in {1..""" + str(n_times)+ """}; do \
            python -m fogbench -t  /home/foglamp/Development/FogLAMP/benchmarks/fogbench/templates/fogbench_sensor_coap.template.json -H localhost -P 5683  -O 100;\
            done
            '
        """

        cmd = cmd.replace("\n", " ")
        # FIXME:
        cmd_status, output = exec_external_command(cmd, _output_capture=False, wait=wait)

        print("\n{func} - status |{status}|  - n_times |{n_times}| - output |{output}|".format(
            func=sys._getframe().f_code.co_name,
            status=cmd_status,
            n_times=n_times,
            output=output))

    @staticmethod
    def _clean_up_postgresql():

        # FIXME: add check correct clean up execution

        # FIXME:
        cmd = """
            sudo  /etc/init.d/postgresql restart;\
            sleep 5;\
            sudo  /etc/init.d/postgresql restart;\
            cd ~/Development/FogLAMP/src/sql;
            PGPASSWORD=postgres psql -U postgres -h localhost -f foglamp_ddl.sql postgres;
            PGPASSWORD=foglamp psql -U foglamp -h localhost -f foglamp_init_data.sql foglamp        
        """

        # FIXME:
        cmd_status, output = exec_external_command(cmd,  _output_capture=True, wait=True)

        print("\n{func} - status |{status}| - output |{output}|".format(
            func=sys._getframe().f_code.co_name,
            status=cmd_status,
            output=output))

    def _exec_backup(self):
        """ Executes a backup and checks the successful execution on the storage layer and on the file system """

        max_row_id_before, file_name = self._retrieve_last_backup_info()

        backup = Backup()

        exit_value = 1
        if backup.start():
            exit_value = backup.execute()

            backup.stop()

        assert exit_value == 0

        max_row_id_after, file_name = self._retrieve_last_backup_info()

        print("\n{func} - row_id |{before}| - row_id |{after}| - file |{file}|".format(
            func=sys._getframe().f_code.co_name,
            before=max_row_id_before,
            after=max_row_id_after,
            file=file_name))

        # Checks if the backup procedure has created the backup information in the storage layer
        assert max_row_id_after > max_row_id_before

        # Checks if the backup procedure has created the backup file in the file system
        assert os.path.exists(file_name)

    def test_exec_backup_cold(self):
        """ Tests a cold backup """

        self._exec_backup()

    def test_exec_backup_warm(self):
        """ Tests a warm backup """

        # FIXME: clean up - Not stable
        self._clean_up_postgresql()
        # FIXME: add check correct clean up execution
        self._load_data(2, False)

        time.sleep(2)

        self._exec_backup()
