#!/bin/bash


if [[ $# -lt 3 ]];then
    echo "please specify frontend host, source host, backend host and home-backend,usage: ./frontend.sh 172.16.1.81 172.16.1.89 172.16.1.95 172.16.1.84"
    exit 1
fi
frontend_host=$1
source_host=$2
backend_host=$3
home_backend_host=$4

if [[ ! -e /srv/obs/certs/fullchain.pem ]]; then
    echo "Please ensure the certificate file '/srv/obs/certs/fullchain.pem' exists"
fi
if [[ ! -e /srv/obs/certs/privkey.pem ]]; then
    echo "Please ensure the certificate file '/srv/obs/certs/privkey.pem' exists"
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

echo "Updating configuration file for apache service"

sed -i "s/source_host: localhost/source_host: source.openeuler.org/g" /srv/www/obs/api/config/options.yml
#TODO: update this into hostname when we finally has one
sed -i "s/frontend_host: localhost/frontend_host: ${frontend_host}/g" /srv/www/obs/api/config/options.yml
sed -i "s/ServerName api/ServerName build.openeuler.org/g" /etc/apache2/vhosts.d/obs.conf
sed -i "s/SSLCertificateFile \/srv\/obs\/certs\/server.crt/SSLCertificateFile \/srv\/obs\/certs\/fullchain.pem/g" /etc/apache2/vhosts.d/obs.conf
sed -i "s/SSLCertificateKeyFile \/srv\/obs\/certs\/server.key/SSLCertificateKeyFile \/srv\/obs\/certs\/privkey.pem/g" /etc/apache2/vhosts.d/obs.conf

#Updating the download url to point to backend server
#TODO: update this into hostname when we finally has one
sed -i "s/#{download_url}/https:\/\/${backend_host}:82/g" /srv/www/obs/api/app/views/webui2/shared/_download_repository_link.html.haml

# configure osc and api hostname
sed -i "s/our \$srcserver = \"http:\/\/\$hostname:5352\";/our \$srcserver = \"http:\/\/source.openeuler.org:5352\";/g" /usr/lib/obs/server/BSConfig.pm

echo "Updating the cluster hosts info"
# update hosts info:
#    1. <frontend_host> build.openeuler.org
#    2. <source_host> source.openeuler.org
#    3. <backend_host> backend.openeuler.org
hostnamectl set-hostname build.openeuerl.org
if ! grep -q "build.openeuler.org" /etc/hosts; then
    echo "${frontend_host} build.openeuler.org" >> /etc/hosts
else
    sed -i -e "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} build.openeuler.org/${frontend_host} build.openeuler.org/g" /etc/hosts
fi
if ! grep -q "source.openeuler.org" /etc/hosts; then
    echo "${source_host} source.openeuler.org" >> /etc/hosts
else
    sed -i -e "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} source.openeuler.org/${source_host} source.openeuler.org/g" /etc/hosts
fi
if ! grep -q "backend.openeuler.org" /etc/hosts; then
    echo "${backend_host} backend.openeuler.org" >> /etc/hosts
else
    sed -i -e "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} backend.openeuler.org/${backend_host} backend.openeuler.org/g" /etc/hosts
fi
if ! grep -q "home-backend.openeuler.org" /etc/hosts; then
    echo "${home_backend_host} home-backend.openeuler.org" >> /etc/hosts
else
    sed -i -e "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} home-backend.openeuler.org/${home_backend_host} home-backend.openeuler.org/g" /etc/hosts
fi

echo "updating the osc configuration files"
#update osc config file
if [[ ! -d /root/.config/osc ]];then
    mkdir -p  /root/.config/osc
fi

if [[ -e /root/.config/osc/oscrc ]];then
    rm /root/.config/osc/oscrc
fi
cd /root/.config/osc
curl -o oscrc https://openeuler.obs.cn-south-1.myhuaweicloud.com:443/infrastructure/oscrc

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
echo "Restarting ts server for textual search engine"
pushd /srv/www/obs/api
rake ts:stop --trace RAILS_ENV="production"
rake ts:start --trace RAILS_ENV="production"
popd

echo "OBS frontend server successfully started"
echo "Important, please update the administrator (Admin)'s password"

