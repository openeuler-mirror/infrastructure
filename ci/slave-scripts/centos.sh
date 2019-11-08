#!/usr/bin/env bash

disk_name=$1
frontend_host=$2
backend_host=$3

if [[ ! -e ${disk_name} ]]; then
    echo "disk ${disk_name} not existed"
    exit 1
fi

if [[ ! -e ~/.ssh/authorized_keys ]]; then
    echo "public key file for jenkins master not exists"
    exit 1
fi

if [[ ! -e /etc/yum.repos.d/OSC.repo ]]; then
     curl -o /etc/yum.repos.d/OSC.repo http://download.opensuse.org/repositories/openSUSE:/Tools/CentOS_7/openSUSE:Tools.repo
fi
# install required tools
sudo yum install -y java-1.8.0-openjdk
sudo yum install -y git
sudo yum install -y expect
sudo yum install -y osc
sudo yum install -y 'perl(XML::Parser)'
sudo yum install -y 'perl(Data::Dumper)'
sudo yum install -y build

#update osc config file
if [[ ! -d /root/.config/osc ]];then
    mkdir -p  /root/.config/osc
fi

if [[ -e /root/.config/osc/oscrc ]];then
    rm /root/.config/osc/oscrc
fi
cd /root/.config/osc
curl -o oscrc https://openeuler.obs.cn-south-1.myhuaweicloud.com:443/infrastructure/oscrc

sed -i "s/#no_verify = 1/no_verify = 1/g" /root/.config/osc/oscrc

# update /etc/hosts
echo "Updating the cluster hosts info"
# update hosts info:
#    1. <frontend_host> build.openeuler.org
if ! grep -q "build.openeuler.org" /etc/hosts; then
    echo "${frontend_host} build.openeuler.org" >> /etc/hosts
else
    sed -i -e "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} build.openeuler.org/${frontend_host} build.openeuler.org/g" /etc/hosts
fi
if ! grep -q "backend.openeuler.org" /etc/hosts; then
    echo "${backend_host} backend.openeuler.org" >> /etc/hosts
else
    sed -i -e "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} backend.openeuler.org/${backend_host} backend.openeuler.org/g" /etc/hosts
fi

# prepare disk
if [[ ! -d /jenkins_home ]]; then
    mkfs.ext4 ${disk_name}
    mkdir /jenkins_home
    mount ${disk_name} /jenkins_home
fi

chmod 600 ~/.ssh/authorized_keys
