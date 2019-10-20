#!/bin/bash


if [[ $# -lt 3 ]];then
    echo "please specify frontend host, source host and backend host, usage: ./source_server.sh 117.78.1.88 172.16.1.87 172.16.1.81"
    exit 1
fi
frontend_host=$1
source_host=$2
backend_host=$3
#ensure the system matches
system_info=`uname -r`
if [[ ! ${system_info} == '4.12.14-lp151.28.7-default' ]];then
    echo "this script is strictly bound to specific release `4.12.14-lp151.28.7-default`,  please ensure this script works on your system"
    exit 1
fi
echo "Starting obs source service with backend server ${backend_host}.."
#enable and start sshd service
echo "Enabling sshd service if not enabled"
systemctl enable sshd.service

echo "Disabling all service before start"
# disable all obs service first
systemctl disable obssrcserver.service
systemctl disable obsrepserver.service
systemctl disable obsservice.service
systemctl disable obsdodup.service
systemctl disable obssignd.service
systemctl disable obsservicedispatch.service
systemctl disable obsdeltastore.service
systemctl disable obsscheduler.service
systemctl disable obsdispatcher.service
systemctl disable obspublisher.service
systemctl disable obssigner.service
systemctl disable obswarden.service
systemctl disable obsworker.service
systemctl disable apache2
systemctl disable mysql
systemctl disable memcached
systemctl disable obs-api-support.target

systemctl stop obssrcserver.service
systemctl stop obsrepserver.service
systemctl stop obsservice.service
systemctl stop obsdodup.service
systemctl stop obssignd.service
systemctl stop obsservicedispatch.service
systemctl stop obsdeltastore.service
systemctl stop obsscheduler.service
systemctl stop obsdispatcher.service
systemctl stop obspublisher.service
systemctl stop obssigner.service
systemctl stop obswarden.service
systemctl stop obsworker.service
systemctl stop apache2
systemctl stop mysql
systemctl stop memcached
systemctl stop obs-api-support.target

# update configuration file
echo "Updating configuration file for obs source service"

sed -i "s/when you touch hostname or port/when you touch hostname\n\$ipaccess->{'^172\\\.16\\\..*'} = 'rw' ;/g" /usr/lib/obs/server/BSConfig.pm

sed -i "s/our \$srcserver = \"http:\/\/\$hostname:5352\";/our \$srcserver = \"http:\/\/${source_host}:5352\";/g" /usr/lib/obs/server/BSConfig.pm
sed -i "s/our \$reposerver = \"http:\/\/\$hostname:5252\";/our \$reposerver = \"http:\/\/${backend_host}:5252\";/g" /usr/lib/obs/server/BSConfig.pm
sed -i "s/our \$serviceserver = \"http:\/\/\$hostname:5152\";/our \$serviceserver = \"http:\/\/${backend_host}:5152\";/g" /usr/lib/obs/server/BSConfig.pm

sed -i "s/\$HOSTNAME/${backend_host}/g" /etc/slp.reg.d/obs.repo_server.reg
sed -i "s/\$HOSTNAME/${source_host}/g" /etc/slp.reg.d/obs.source_server.reg

# update hosts info
if ! grep -q "${frontend_host} build.openeuler.org"; then
  echo "${frontend_host} build.openeuler.org" >> /etc/hosts
fi


echo "updating the osc configuration files"
#update osc config file
if [[ ! -d /root/.config/osc ]];then
    mkdir -p  /root/.config/osc
fi

if [[ ! -e /root/.config/osc/oscrc ]];then
    rm /root/.config/osc/oscrc
    curl -o oscrc https://gitee.com/openeuler/infrastructure/raw/master/obs/tf/configuration_files/oscrc
fi

echo "Restarting source service"
# restart the frontend service
systemctl enable obsstoragesetup.service
systemctl enable obssrcserver.service
systemctl enable obsdeltastore.service
systemctl enable obsservicedispatch.service

systemctl start obsstoragesetup.service
systemctl start obssrcserver.service
systemctl start obsdeltastore.service
systemctl start obsservicedispatch.service
echo "OBS source server successfully started"
SOURCE_REPO_ID=`cat /srv/obs/projects/_repoid`
echo "Important, Please use this ID: ${SOURCE_REPO_ID} to replace the file content of '/srv/obs/projects/_repoid' and '/srv/obs/build/_repoid' in the backend server"
