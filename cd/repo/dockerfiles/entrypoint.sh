#!/usr/bin/env bash

if [[ $# -lt 1 ]];then
    echo "please specify the task you want to execute, 'prepare' or 'update'. "
    exit 1
fi

action=$1
if [[ ${action} == "prepare" ]]; then
    keyfile=$2
    certfile=$3
     if [[ "x${keyfile}" == "x" ]] || [[ "x${certfile}" == "x" ]];then
        echo "please specify key and cert file url to download"
        exit 1
        fi
    echo "preparing repo...."
    if [[ ! -d /etc/nginx/ssl/ ]]; then
        mkdir -p /etc/nginx/ssl/
    fi
    cd /etc/nginx/ssl/
    curl -o privkey.pem ${keyfile}
    curl -o fullchain.pem ${certfile}
elif [[ ${action} == "update" ]];then
    echo "update action not supported now"
    exit 1
else
    echo "unsupported task ${action}"
    exit 1
fi
echo "task finished"
exit 0
