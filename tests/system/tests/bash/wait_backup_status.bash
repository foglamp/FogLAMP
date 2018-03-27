#!/bin/bash

#
# Expected input parameters :
#
#   $1 = Backup Id to enquiry
#   $2 = Status of the backup achieve {RESTORED}
#

if [[ "${EXECUTION_ENV}" != "ucore" ]]; then

    echo ERROR : Test implemented only for the Ubuntu Core environment.
    exit 1
fi

backup_id=$1
backup_status=$2

function get_backup_status {

    if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

        sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
        curl -s -X GET http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/backup |  jq -S '.backups|.[]|select(.id==$1)|.status'   > ${TMP_FILE_OVERWRITE} 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
        logout
EOF
    output=$(cat ${TMP_FILE_OVERWRITE})

    fi

    echo ${output}
}

# Waits until either the backup reaches the requested status or it reaches the timeout.
count=0
while [ true ]
do

    value=$(get_backup_status $backup_id)

    if [[ "${value}" == "\"${backup_status}\"" ]]; then

        echo Backup id :$backup_id: status :${backup_status}: reached - N. of retries :${count}:                                               >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1
        echo "${value}"
        exit 0
    else
        if [[ $count -le ${RETRY_COUNT} ]]
        then
            echo Backup id :$backup_id: status :${backup_status}: not reached yet, currently :${value}: - N. of retries :${count}:                         >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1
            sleep 1
            count=$((count+1))
        else
            echo Backup id :$backup_id: status :${backup_status}: not reached, currently :${value}: - exiting - N. of retries :${count}:                         >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1
            echo "${value}"
            exit 1
        fi
    fi
done
