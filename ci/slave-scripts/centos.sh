#!/usr/bin/env bash

disk_name=$1

if [[ ! -e ${disk_name} ]]; then
    echo "disk ${disk_name} not existed"
    exit 1
fi

if [[ ! -e ~/.ssh/authorized_keys ]]; then
    echo "public key file for jenkins master not exists"
    exit 1
fi

# install required tools
sudo yum install -y java-1.8.0-openjdk
sudo yum install -y git

# prepare disk
mkfs.ext4 ${disk_name}
mkdir /jenkins_home
mount ${disk_name} /jenkins_home

chmod 600 ~/.ssh/authorized_keys
