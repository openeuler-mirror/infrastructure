#!/usr/bin/env bash


if [[ $# -lt 2 ]];then
    echo "please specify service type 'frontend', 'source' or 'backend' and operation 'start', 'stop' or 'restart'."
    exit 1
fi
service_type=$1
action=$2
case ${service_type} in
    'frontend')
        echo "starting to perform action '${action}' for service 'frontend'."
        if [[ $action == 'start' ]]; then
            systemctl start obs-api-support.target
            systemctl start mysql
            systemctl start memcached
            systemctl start apache2
            echo "started"
        elif [[ $action == 'stop' ]]; then
            systemctl stop obs-api-support.target
            systemctl stop mysql
            systemctl stop memcached
            systemctl stop apache2
            echo "stopped"
        elif [[ $action == 'restart' ]]; then
            systemctl restart obs-api-support.target
            systemctl restart mysql
            systemctl restart memcached
            systemctl restart apache2
            echo "restarted"
        else
            echo "unsupported action ${action}"
            exit 1
        fi
        ;;
    'source')
        echo "starting to perform action '${action}' for service 'source'."
         if [[ $action == 'start' ]]; then
            systemctl start obsstoragesetup.service
            systemctl start obssrcserver.service
            systemctl start obsdeltastore.service
            systemctl start obsservicedispatch.service
            systemctl start obsservice.service
            echo "started"
        elif [[ $action == 'stop' ]]; then
            systemctl stop obsstoragesetup.service
            systemctl stop obssrcserver.service
            systemctl stop obsdeltastore.service
            systemctl stop obsservicedispatch.service
            systemctl stop obsservice.service
            echo "stopped"
        elif [[ $action == 'restart' ]]; then
            systemctl restart obsstoragesetup.service
            systemctl restart obssrcserver.service
            systemctl restart obsdeltastore.service
            systemctl restart obsservicedispatch.service
            systemctl restart obsservice.service
            echo "restarted"
        else
            echo "unsupported action ${action}"
            exit 1
        fi
        ;;
    'backend')
        echo "starting to perform action '${action}' for service 'backend'."
         if [[ $action == 'start' ]]; then
            systemctl start obsrepserver.service
            systemctl start obsdodup.service
            systemctl start obssignd.service
            systemctl start obsscheduler.service
            systemctl start obsdispatcher.service
            systemctl start obspublisher.service
            systemctl start obssigner.service
            systemctl start obswarden.service
            echo "started"
        elif [[ $action == 'stop' ]]; then
            systemctl stop obsrepserver.service
            systemctl stop obsdodup.service
            systemctl stop obssignd.service
            systemctl stop obsscheduler.service
            systemctl stop obsdispatcher.service
            systemctl stop obspublisher.service
            systemctl stop obssigner.service
            systemctl stop obswarden.service
            echo "stopped"
        elif [[ $action == 'restart' ]]; then
            systemctl restart obsrepserver.service
            systemctl restart obsdodup.service
            systemctl restart obssignd.service
            systemctl restart obsscheduler.service
            systemctl restart obsdispatcher.service
            systemctl restart obspublisher.service
            systemctl restart obssigner.service
            systemctl restart obswarden.service
            echo "restarted"
        else
            echo "unsupported action ${action}"
            exit 1
        fi
        ;;
     *)
        echo "unsupported service type '${service_type}'"
        exit 1
esac
