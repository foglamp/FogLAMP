#!/bin/bash

# Prepares the temporary script for the execution
if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

        tmp_script=${RESULT_DIR}/$TEST_NAME.999.temp

        echo '#!/bin/bash' > ${tmp_script}
        echo -n 'value=`' >> ${tmp_script}
        echo -n "curl -s -X GET http://${FOGLAMP_SERVER}:${FOGLAMP_HTTPPort}/foglamp/category/${1}  | jq '.value' " >> ${tmp_script}
        echo '`' >> ${tmp_script}
        echo 'result=$?' >> ${tmp_script}
        echo 'echo ${value}  >  ' "${RESULT_DIR}/$TEST_NAME.991.temp" >> ${tmp_script}
        echo 'echo ${result} >> ' "${RESULT_DIR}/$TEST_NAME.991.temp" >> ${tmp_script}

        chmod 700 ${tmp_script}
fi

# It waits until either the requested FogLAMP configuration is created or it reaches the timeout.
while [ true ]
do
    if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

        sudo classic ${tmp_script} 2>  ${RESULT_DIR}/$TEST_NAME.2.temp
        result=`tail -n1 ${RESULT_DIR}/$TEST_NAME.991.temp`

    else
        curl -s -X GET http://${FOGLAMP_SERVER}:${FOGLAMP_PORT}/foglamp/category/${1}  | jq '.value'  > /dev/null 2>&1
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
