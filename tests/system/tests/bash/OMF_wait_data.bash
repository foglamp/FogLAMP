#!/bin/bash

#
# the scripts has optionals parameters :
#   $1 : full=extract all the json information
#   $2 : producer token to use
#   $3 : asset code to extract from PI-Web
#

# Global constants declaration
declare EXECUTION_ENV
declare SUITE_BASEDIR
declare TEST_BASEDIR
declare RESULT_DIR
declare TEST_NAME

declare PI_SERVER
declare PI_SERVER_PORT
declare PI_SERVER_DATABASE
declare PI_SERVER_UID
declare PI_SERVER_PWD
declare OMF_PRODUCER_TOKEN

declare ASSET_CODE
declare RETRY_COUNT

# Global variables declaration
declare url_elements_list

# Reads configuration setting
source ${SUITE_BASEDIR}/suite.cfg

#
# Handles optional input parameters
#
if [[ "$1" == "full" ]]; then

    export param_full_output=1
else
    export param_full_output=0
fi

if [[ "$2" != "" ]]; then

    export param_omf_producer_token=$2
else
    export param_omf_producer_token=${OMF_PRODUCER_TOKEN}
fi

if [[ "$3" != "" ]]; then

    export param_asset_code=$3
else
    export param_asset_code=${ASSET_CODE}
fi



function pi_web_retrieves_value_ucore {

    url_assets_list=""
    url_asset=""
    value=""

    # Retrieves the asset list
    sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.701.temp 2>> ${RESULT_DIR}/$TEST_NAME.702.temp
    curl -s -u  ${PI_SERVER_UID}:${PI_SERVER_PWD} -X GET -k ${url_elements_list} |  jq --raw-output '.Items | .[] | select(.Name=="'${param_omf_producer_token}'")  | .Links | .Elements' > ${RESULT_DIR}/$TEST_NAME.700.temp
    logout
EOF
    url_assets_list=`cat ${RESULT_DIR}/$TEST_NAME.700.temp`
    echo url_assets_list :${url_assets_list}:                                                                           >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp

    if [[ "${url_assets_list}" != "" ]]; then

        # Retrieves asset information
        sudo classic << EOF                                                                                                >> ${RESULT_DIR}/$TEST_NAME.701.temp 2>> ${RESULT_DIR}/$TEST_NAME.702.temp
        curl -s -u  ${PI_SERVER_UID}:${PI_SERVER_PWD} -X GET -k ${url_assets_list} |  jq --raw-output '.Items | .[] | select(.Name=="'${param_asset_code}'") | .Links | .EndValue'  > ${RESULT_DIR}/$TEST_NAME.700.temp
        logout
EOF

        url_asset=`cat ${RESULT_DIR}/$TEST_NAME.700.temp`
        echo url_asset :${url_asset}:                                                                                   >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    fi

    if [[ "${url_asset}" != "" ]]; then

        if [[ $param_full_output == 1 ]]; then

            # Retrieves the value
            sudo classic << EOF                                                                                          >> ${RESULT_DIR}/$TEST_NAME.701.temp 2>> ${RESULT_DIR}/$TEST_NAME.702.temp
            curl -s -u  ${PI_SERVER_UID}:${PI_SERVER_PWD} -X GET -k ${url_asset} |  jq -S '.Items | .[] | select(.Name=="sensor") | .Value | .Timestamp="xxx" '  > ${RESULT_DIR}/$TEST_NAME.700.temp
            logout
EOF

        else
            # Retrieves the value
            sudo classic << EOF                                                                                          >> ${RESULT_DIR}/$TEST_NAME.701.temp 2>> ${RESULT_DIR}/$TEST_NAME.702.temp
            curl -s -u  ${PI_SERVER_UID}:${PI_SERVER_PWD} -X GET -k ${url_asset} |  jq --raw-output '.Items | .[] | select(.Name=="sensor") | .Value | .Value'  > ${RESULT_DIR}/$TEST_NAME.700.temp
            logout
EOF
        fi

        value=`cat ${RESULT_DIR}/$TEST_NAME.700.temp`
        echo value :${value}:                                                                                           >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp
    fi

    echo "${value}"
}


OMF_wait_data_ucore() {
    #
    # Drills down into PI-WEB information to extract the expected value from the PI-Server
    #

    sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.701.temp 2>> ${RESULT_DIR}/$TEST_NAME.702.temp
    curl -s -u  ${PI_SERVER_UID}:${PI_SERVER_PWD} -X GET -k https://${PI_SERVER}/piwebapi/assetservers | jq --raw-output '.Items | .[] | .Links | .Databases ' > ${RESULT_DIR}/$TEST_NAME.700.temp
    logout
EOF
    url_databases=`cat ${RESULT_DIR}/$TEST_NAME.700.temp`
    echo url_databases :${url_databases}:                                                                               >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp

    #
    sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.701.temp 2>> ${RESULT_DIR}/$TEST_NAME.702.temp
    curl -s -u  ${PI_SERVER_UID}:${PI_SERVER_PWD} -X GET -k ${url_databases} |  jq --raw-output '.Items | .[] | select(.Name=="'${PI_SERVER_DATABASE}'") | .Links | .Elements' > ${RESULT_DIR}/$TEST_NAME.700.temp
    logout
EOF

    url_elements=`cat ${RESULT_DIR}/$TEST_NAME.700.temp`
    echo url_elements :${url_elements}:                                                                                 >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp

    #
    sudo classic << EOF                                                                                                 >> ${RESULT_DIR}/$TEST_NAME.701.temp 2>> ${RESULT_DIR}/$TEST_NAME.702.temp
    curl -s -u  ${PI_SERVER_UID}:${PI_SERVER_PWD} -X GET -k ${url_elements} |  jq --raw-output '.Items | .[] | .Links | .Elements' > ${RESULT_DIR}/$TEST_NAME.700.temp
    logout
EOF

    url_elements_list=`cat ${RESULT_DIR}/$TEST_NAME.700.temp`
    echo url_elements_list :${url_elements_list}:                                                                       >> ${RESULT_DIR}/$TEST_NAME.1.temp 2>> ${RESULT_DIR}/$TEST_NAME.2.temp

    # Waits until either the data is available in the PI server or it reaches the timeout
    count=0
    while [ true ]
    do

        value=$(pi_web_retrieves_value_ucore)

        if [[ "${value}" != "" && "${value}" != *"PI Point not found"* ]]; then

            echo Value retrieved - N. of retries :${count}:                                                             >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1
            echo "${value}"
            exit 0
        else
            if [[ $count -le ${RETRY_COUNT} ]]
            then
                sleep 1
                count=$((count+1))
            else
                echo Timeout reached - N. of retries :${count}:                                                         >> $RESULT_DIR/$TEST_NAME.1.temp 2>&1
                echo ${value}
                exit 1
            fi
        fi
    done
}

#
# MAIN
#
if [[ "${EXECUTION_ENV}" == "ucore" ]]; then

    OMF_wait_data_ucore
else
    echo ERROR : functionality not implemented.
    exit 1
fi