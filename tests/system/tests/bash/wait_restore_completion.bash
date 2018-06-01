#!/bin/bash

if [[ "${EXECUTION_ENV}" != "ucore" ]]; then

    echo ERROR : Test implemented only for the Ubuntu Core environment.
    exit 1
fi


$TEST_BASEDIR/bash/wait_foglamp_status.bash "STOPPED"
$TEST_BASEDIR/bash/wait_foglamp_status.bash "RUNNING"

$TEST_BASEDIR/bash/wait_backup_status.bash $1 "RESTORED"
