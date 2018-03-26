#!/bin/bash

if [[ "${EXECUTION_ENV}" != "ucore" ]]; then

    echo ERROR : Test implemented only for the Ubuntu Core environment.
    exit 1
fi

if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

    sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    curl -s -X GET http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/backup |  jq -S '(.|.backups|.[]|.date)|="xxx"' > ${TMP_FILE_OVERWRITE} 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    logout
EOF
    cat ${TMP_FILE_OVERWRITE}
fi