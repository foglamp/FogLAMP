#!/bin/bash

# Globals declaration
declare EXECUTION_ENV
declare SUITE_BASEDIR
declare TEST_BASEDIR
declare RESULT_DIR
declare TEST_NAME

declare FOGLAMP_SERVER
declare FOGLAMP_HTTPPort
declare SENDING_PROCESS_DATA
declare SCHEDULE_ID_OMF_PLUGIN

declare PI_SERVER
declare PI_SERVER_PORT
declare OMF_PRODUCER_TOKEN
declare OMF_TYPE_ID

declare ASSET_CODE

declare CMD_CURL

# Reads configuration setting - FogLAMP should be started to able to evaluate the schedule ID for the OMF
source ${SUITE_BASEDIR}/suite.cfg

OMF_configure_ucore () {

    # Enables the OMF plugin
    sudo classic << EOF_01                                                                                              >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    curl -s -X PUT http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/schedule/${SCHEDULE_ID_OMF_PLUGIN} -d '{ "enabled" : true }'
    logout
EOF_01

    # Waits until the OMF plugin has created the default configurations
    ${TEST_BASEDIR}/bash/wait_creation_cfg.bash "${SENDING_PROCESS_DATA}/producerToken"                                 >>  $RESULT_DIR/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp

    # Configures FogLAMP with the required settings
    sudo classic << EOF_02                                                                                              >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    curl -s -X PUT http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/category/${SENDING_PROCESS_DATA}/URL           -d '{ "value" : "https://${PI_SERVER}:${PI_SERVER_PORT}/ingress/messages"}'
    curl -s -X PUT http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/category/${SENDING_PROCESS_DATA}/producerToken -d '{ "value" : "${OMF_PRODUCER_TOKEN}" }'
    curl -s -X PUT http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/category/OMF_TYPES/type-id                     -d '{ "value" : "${OMF_TYPE_ID}" }'
    logout
EOF_02

    # Restarts FogLAMP to ensure the new configurations are used
    ${TEST_BASEDIR}/bash/exec_any_foglamp_command.bash stop  > /dev/null 2>&1

    ${TEST_BASEDIR}/bash/exec_any_foglamp_command.bash start                                                            > ${RESULT_DIR}/$TEST_NAME.0.temp 2>&1
    tail  -n1 ${RESULT_DIR}/${TEST_NAME}.0.temp

    $TEST_BASEDIR/bash/sleep.bash 10
}


#
# MAIN
#
if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

    OMF_configure_ucore
else
    echo ERROR : functionality not implemented.
    exit 1
fi
