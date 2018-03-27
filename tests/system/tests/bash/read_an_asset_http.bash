#!/bin/bash

if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

    sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    curl -s http://localhost:8081/foglamp/asset/$1                                                                      > ${RESULT_DIR}/$TEST_NAME.100.temp
EOF
    cat ${RESULT_DIR}/$TEST_NAME.100.temp

elif [[ "${EXECUTION_ENV}" == "" || "${EXECUTION_ENV}" == "userver" ]]; then

    curl -s http://localhost:8081/foglamp/asset/$1

fi


