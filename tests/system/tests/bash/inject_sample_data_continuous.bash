#!/bin/bash

#
# Expected input parameters :
#
#   $1 = asset name
#

TMP_FILE_OVERWRITE="$RESULT_DIR/$TEST_NAME.400.temp"
echo '[{"name":"'$1'","sensor_values":[{"name":"sensor","type":"number","min":10,"max":10,"precision":0}]}]' >   ${TMP_FILE_OVERWRITE} 2>&1

# Injects data into FogLAMP
function inject_data {

    $TEST_BASEDIR/bash/inject_fogbench_data.bash -t ${TMP_FILE_OVERWRITE} -O 100 -I 2 2>> ${RESULT_DIR}/$TEST_NAME.2.temp | grep '^Total Messages Transferred: '
}

# Injects sample data into FogLAMP until either it is killed or it reaches the timeout.
count=1
while [ true ]
do
    inject_data
    value=$?

    if [[ $count -lt ${RETRY_COUNT} ]]
    then
        echo -n "Injecting data - Execution N. :${count}: - "                                                           >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
        echo inject_data exit code :${value}:                                                                           >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
        sleep 1
        count=$((count+1))
    else
        echo -n "Data injection ended "                                                                                 >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
        echo "- timeout reached - N. of executions :${count}:"                                                          >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
        echo "inject_data exit code :${value}:"                                                                         >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
        exit 1
    fi
done
