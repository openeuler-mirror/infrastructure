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
sudo apt install -y default-jre
sudo apt install -y git

# prepare disk
if [[ ! -d /jenkins_home ]]; then
    mkfs.ext4 ${disk_name}
    mkdir /jenkins_home
    mount ${disk_name} /jenkins_home
fi

grep -q /etc/fstab -e "${disk_name}"
if [[ $? != 0 ]]; then
    echo "${disk_name} /jenkins_home  ext4 defaults 0 0" >> /etc/fstab
fi

chmod 600 ~/.ssh/authorized_keys
