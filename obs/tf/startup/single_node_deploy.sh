#!/bin/bash

server_ip=$1
data_disk=$2
frontend_host=localhost
source_host=localhost
backend_host=localhost

function usage()
{
	echo "Please input obs server ip,and need a idle disk to create data lvm,"
	echo "Usage: sh single_node_deploy.sh [server_ip] [disk]."
	exit 1
}
[ $# -ne 2 ] && usage

#start deploy frontend server
if [[ ! -e /srv/obs/certs/fullchain.pem ]]; then
    echo "Please ensure the certificate file '/srv/obs/certs/fullchain.pem' exists"
fi
if [[ ! -e /srv/obs/certs/privkey.pem ]]; then
    echo "Please ensure the certificate file '/srv/obs/certs/privkey.pem' exists"
fi

#enable and start sshd service
echo "Enabling sshd service if not enabled"
systemctl enable sshd.service

#stop all all service befor start
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
sed -i "s/ServerName api/ServerName ${server_ip}/g" /etc/apache2/vhosts.d/obs.conf
sed -i "s/SSLCertificateFile \/srv\/obs\/certs\/server.crt/SSLCertificateFile \/srv\/obs\/certs\/fullchain.pem/g" /etc/apache2/vhosts.d/obs.conf
sed -i "s/SSLCertificateKeyFile \/srv\/obs\/certs\/server.key/SSLCertificateKeyFile \/srv\/obs\/certs\/privkey.pem/g" /etc/apache2/vhosts.d/obs.conf

#Updating the download url to point to backend server
#TODO: update this into hostname when we finally has one
sed -i "s/#{download_url}/https:\/\/${server_ip}:82/g" /srv/www/obs/api/app/views/webui2/shared/_download_repository_link.html.haml

# configure osc and api hostname
sed -i "s/our \$srcserver = \"http:\/\/\$hostname:5352\";/our \$srcserver = \"http:\/\/${source_host}:5352\";/g" /usr/lib/obs/server/BSConfig.pm

echo "updating the osc configuration files"
#update osc config file
if [[ ! -d /root/.config/osc ]];then
    mkdir -p  /root/.config/osc
fi

if [[ -e /root/.config/osc/oscrc ]];then
    rm /root/.config/osc/oscrc
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
echo "Restarting ts server for textual search engine"
pushd /srv/www/obs/api
rake ts:stop --trace RAILS_ENV="production"
rake ts:start --trace RAILS_ENV="production"
popd
echo "OBS frontend server successfully started"

#start deploy source server
# prepare the disk
if [[ ! -e  /dev/OBS/server ]];then
    pvcreate ${data_disk}
    vgcreate "OBS" ${data_disk}
    lvcreate  -l 100%FREE  "OBS" -n "server"
    mkfs.ext3 /dev/OBS/server
    echo "/dev/mapper/OBS-server /srv  ext3 defaults 0 0" >> /etc/fstab
    mkdir -p /tmp/srv
    cp -a /srv/* /tmp/srv
    mount -a
    cp -a /tmp/srv/* /srv/
    rm -rf /tmp/srv
fi

# update configuration file
echo "Updating configuration file for obs source service"
sed -i "s/\$HOSTNAME/${backend_host}/g" /etc/slp.reg.d/obs.repo_server.reg
sed -i "s/\$HOSTNAME/${source_host}/g" /etc/slp.reg.d/obs.source_server.reg

#update cache folder for scm service
echo CACHEDIRECTORY="/srv/cache/obs/tar_scm" > /etc/obs/services/tar_scm

# copy service files into
cp ./service/* /usr/lib/obs/service/
cp ./build-pkg-rpm /usr/lib/build/build-pkg-rpm
mkdir -p /usr/lib/obs/source_md5
chmod 777 /usr/lib/obs/source_md5
mkdir -p /srv/cache/obs/tar_scm/{incoming,repo,repourl}
mkdir -p /srv/cache/obs/tar_scm/repo/euleros-version

echo "Restarting source service"
# restart the frontend service
systemctl enable obsstoragesetup.service
systemctl enable obssrcserver.service
systemctl enable obsdeltastore.service
systemctl enable obsservicedispatch.service
systemctl enable obsservice.service

systemctl start obsstoragesetup.service
systemctl start obssrcserver.service
systemctl start obsdeltastore.service
systemctl start obsservicedispatch.service
systemctl start obsservice.service
echo "OBS source server successfully started"
repo_id=`cat /srv/obs/projects/_repoid`

#start deploy backend server
echo "Updating configuration file for obs backend service"
sed -i "s/After=network.target obssrcserver.service obsrepserver.service obsapisetup.service/After=network.target obssrcserver.service obsrepserver.service/g" /usr/lib/systemd/system/obsscheduler.service
systemctl daemon-reload

echo "updating the content of _repoid file"
echo -en ${repo_id} > /srv/obs/build/_repoid
echo -en ${repo_id} > /srv/obs/projects/_repoid

echo "Restarting backend service"
systemctl enable obsrepserver.service
systemctl enable obsdodup.service
systemctl enable obssignd.service
systemctl enable obsscheduler.service
systemctl enable obsdispatcher.service
systemctl enable obspublisher.service
systemctl enable obssigner.service
systemctl enable obswarden.service

systemctl start obsrepserver.service
systemctl start obsdodup.service
systemctl start obssignd.service
systemctl start obsscheduler.service
systemctl start obsdispatcher.service
systemctl start obspublisher.service
systemctl start obssigner.service
systemctl start obswarden.service
echo "OBS backend server successfully started"
