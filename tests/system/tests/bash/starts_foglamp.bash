#!/bin/bash

# Starts FogLAMP, retries the operation if fails
count=0
while [ true ]
do
    # Starts FogLAMP
    $TEST_BASEDIR/bash/exec_any_foglamp_command.bash start                                                              >>  ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    foglamp_status=`tail -n1 ${RESULT_DIR}/$TEST_NAME.2.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp`

    if [[ "${foglamp_status}" == "FogLAMP started." ]]; then

        echo FogLAMP started - N. of retries :${count}:  >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1
        break
    else
        if [[ $count -le ${RETRY_COUNT} ]]
        then
            echo WARNING: FogLAMP not started, retrying ...                                                             >>  ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
            echo N. of retries :${count}:                                                                               >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1

            # Ensures the initial status, FogLAMP stopped
            $TEST_BASEDIR/bash/exec_any_foglamp_command.bash stop                                                       >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
            $TEST_BASEDIR/bash/exec_any_foglamp_command.bash kill                                                       >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp

            sleep 1
            count=$((count+1))
        else
            echo Timeout reached - N. of retries :${count}:  >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1
            exit 1
        fi
    fi
done
