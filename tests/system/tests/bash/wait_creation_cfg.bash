#!/bin/bash

# Globals declaration
declare EXECUTION_ENV
declare SUITE_BASEDIR
declare TEST_BASEDIR
declare RESULT_DIR
declare TEST_NAME

declare FOGLAMP_SERVER
declare FOGLAMP_HTTPPort
declare FOGLAMP_SNAP_VERSION
declare FOGLAMP_SNAP_UPDATE_VERSION
declare FOGLAMP_NAME
declare FOGLAMP_SNAP
declare FOGLAMP_PORT
declare SENDING_PROCESS_DATA
declare SCHEDULE_ID_OMF_PLUGIN

declare PI_SERVER
declare PI_SERVER_PORT
declare OMF_PRODUCER_TOKEN
declare OMF_TYPE_ID

declare SNAPS_DIRECTORY

declare ASSET_CODE
declare RETRY_COUNT



# Prepares the temporary script for the execution
if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

        # Note : the curl command itself does not produce an exit code <> 0 if the category is not available,
        #        the jq using the pipe does.
        tmp_script=${RESULT_DIR}/$TEST_NAME.999.temp

        echo '#!/bin/bash'                                                                                              > ${tmp_script}

        echo -n 'value=`'                                                                                               >> ${tmp_script}
        echo -n "curl -s -X GET http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/category/${1} | jq '.value'  "     >> ${tmp_script}
        echo '`'                                                                                                        >> ${tmp_script}

        echo 'result=$?'                                                                                                >> ${tmp_script}
        echo 'if [[ $result == 0 ]]; then'                                                                              >> ${tmp_script}
        echo 'echo ${value}  >> ' "${RESULT_DIR}/$TEST_NAME.991.temp"                                                   >> ${tmp_script}
        echo 'echo ${result} >> ' "${RESULT_DIR}/$TEST_NAME.991.temp"                                                   >> ${tmp_script}
        echo 'else '                                                                                                    >> ${tmp_script}
        echo 'echo -1 >> ' "${RESULT_DIR}/$TEST_NAME.991.temp"                                                          >> ${tmp_script}
        echo 'fi'                                                                                                       >> ${tmp_script}

        chmod 700 ${tmp_script}
fi

# It waits until either the requested FogLAMP configuration is created or it reaches the timeout.
count=0
while [ true ]
do
    if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

        sudo classic ${tmp_script}                                                                                      2>  ${RESULT_DIR}/$TEST_NAME.2.temp
        result=`tail -n1 ${RESULT_DIR}/$TEST_NAME.991.temp`

    else
        curl -s -X GET http://${FOGLAMP_SERVER}:${FOGLAMP_PORT}/foglamp/category/${1}  | jq '.value'                    > /dev/null 2>&1
        result=$?
    fi

    if [[ "$result" == "0" ]]
    then
        exit 0
    else
        if [[ $count -le ${RETRY_COUNT} ]]
        then
            sleep 1
            count=$((count+1))
        else
            exit 1
        fi
    fi
done
