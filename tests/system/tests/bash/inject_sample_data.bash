#!/bin/bash

# Injects data into FogLAMP
echo '[{"name":"'$1'","sensor_values":[{"name":"sensor","type":"number","min":10,"max":10,"precision":0}]}]' >   ${TMP_FILE_OVERWRITE} 2>&1
$TEST_BASEDIR/bash/inject_fogbench_data.bash -t ${TMP_FILE_OVERWRITE} 2>> ${RESULT_DIR}/$TEST_NAME.2.temp | grep '^Total Messages Transferred: '
