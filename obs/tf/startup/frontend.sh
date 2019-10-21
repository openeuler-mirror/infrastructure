#!/bin/bash


if [[ $# -lt 2 ]];then
    echo "please specify frontend host, source host,usage: ./frontend.sh 117.78.1.88 172.16.1.87"
    exit 1
fi
frontend_host=$1
source_host=$2
#ensure the system matches
system_info=`uname -r`
if [[ ! ${system_info} == '4.12.14-lp151.28.7-default' ]];then
    echo "this script is strictly bound to specific release `4.12.14-lp151.28.7-default`,  please ensure this script works on your system"
    exit 1
fi

echo "Starting obs api service with source server ${source_host}.."
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

# downloading cert files
cd /srv/obs/certs
curl -o fullchain.pem https://gitee.com/openeuler/infrastructure/raw/master/obs/tf/configuration_files/frontend/certs/fullchain.pem
curl -o privkey.pem https://gitee.com/openeuler/infrastructure/raw/master/obs/tf/configuration_files/frontend/certs/privkey.pem
# update configuration file
echo "Updating configuration file for apache service"

sed -i "s/source_host: localhost/source_host: ${source_host}/g" /srv/www/obs/api/config/options.yml
sed -i "s/ServerName api/ServerName build.openeuler.org/g" /etc/apache2/vhosts.d/obs.conf
sed -i "s/SSLCertificateFile \/srv\/obs\/certs\/server.crt/SSLCertificateFile \/srv\/obs\/certs\/fullchain.pem/g" /etc/apache2/vhosts.d/obs.conf
sed -i "s/SSLCertificateKeyFile \/srv\/obs\/certs\/server.key/SSLCertificateKeyFile \/srv\/obs\/certs\/privkey.pem/g" /etc/apache2/vhosts.d/obs.conf

# configure osc and api hostname
sed -i "s/our \$srcserver = \"http:\/\/\$hostname:5352\";/our \$srcserver = \"http:\/\/${source_host}:5352\";/g" /usr/lib/obs/server/BSConfig.pm
hostnamectl set-hostname build.openeuerl.org


# update hosts info
if ! grep -q "${frontend_host} build.openeuler.org" /etc/hosts; then
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

echo "Restarting frontend service"
# restart the frontend service
systemctl enable obs-api-support.target
systemctl enable mysql
systemctl enable memcached
systemctl enable apache2

systemctl start obs-api-support.target
systemctl start mysql
systemctl start memcached
systemctl start apache2

echo "OBS frontend server successfully started"
