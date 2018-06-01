#!/bin/bash

if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

    sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    curl -s -X GET http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/asset |  jq -S '.' > ${TMP_FILE_OVERWRITE}      2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    logout
EOF
    cat ${TMP_FILE_OVERWRITE}

else
    echo ERROR : functionality not implemented.
    exit 1
fi
