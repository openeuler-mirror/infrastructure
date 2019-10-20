#!/bin/bash

function fn_install_obsworker()
{
    if [[ ! -e /etc/sysconfig/obs-server ]];then
        tar -xvf $OBS_INSTALL_DIR/obsworker.tar.gz -C /
    fi

    ## add obsrun group
    getent group obsrun >/dev/null || groupadd -r obsrun

    ## add obsrun user
    getent passwd obsrun >/dev/null || /usr/sbin/useradd -r -g obsrun -d /usr/lib/obs -s /usr/sbin/nologin -c "User for build service backend" obsrun
}

function fn_config_obs_server_file()
{

    n=`lscpu | grep '^CPU(s):' | awk '{print $2}'`
    let n=$n/4+1
    sed -i "s/OBS_SRC_SERVER=.*/OBS_SRC_SERVER=\"${source_host}:5352\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_REPO_SERVERS=.*/OBS_REPO_SERVERS=\"${backend_host}:5252\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_INSTANCES=.*/OBS_WORKER_INSTANCES=\"$n\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_JOBS=.*/OBS_WORKER_JOBS=\"8\"/g" /etc/sysconfig/obs-server

}

function fn_config_disk()
{
    if [[ ! -e ${disk_name} ]];then
        echo "No date disk ${disk_name}"
        exit 1
    fi

    if [[ ! -d /var/cache/obs/worker/ ]];then
        mkdir -p  /var/cache/obs/worker/
    fi

    if [[ ! -e  /dev/OBS/worker ]];then

        pvcreate ${disk_name}
        vgcreate "OBS" ${disk_name}
        lvcreate  -l 100%FREE  "OBS" -n "worker"
        mkfs.ext3 /dev/OBS/worker
        echo "/dev/mapper/OBS-worker /var/cache/obs/worker  ext3 defaults 0 0" >> /etc/fstab
        mount -a
    fi
}

if [[ $# -lt 3 ]];then
    echo "please specify source host and backend host and worker disk name, for instance: ./worker.sh 172.16.1.87 172.16.1.81 /dev/vdb"
    exit 1
fi
source_host=$1
backend_host=$2
disk_name=$3
echo "Starting obs worker service with backend server ${backend_host}.."
#enable and start sshd service
echo "Enabling sshd service if not enabled"
systemctl enable sshd.service

echo "installing requirement packages"
yum install -y ntpdate vim cpio curl perl-Compress-Zlib perl-TimeDate perl-Data-Dumper perl-XML-Parser screen psmisc bash binutils bsdtar lzma util-linux openslp lvm2 perl-Digest-MD5 osc git screen tmux wget expect

echo "downloading obs worker script files"
OBS_INSTALL_DIR=/tmp/obs_worker_arm_install

[[ ! -d ${OBS_INSTALL_DIR} ]] && mkdir -p ${OBS_INSTALL_DIR}

if [[ ! -e ${OBS_INSTALL_DIR}/obsworker.tar.gz ]]; then
    curl https://gitee.com/openeuler/infrastructure/raw/master/obs/tf/configuration_files/worker/obsworker.tar.gz -o ${OBS_INSTALL_DIR}/obsworker.tar.gz
fi

echo "configure disks"
fn_config_disk

echo "unmask config"
sed -i s'/umask 0077/umask 0022/g' /etc/bashrc

echo "installing obsworker"
fn_install_obsworker

echo "updating obs worker configuration file"
fn_config_obs_server_file

echo "enabling obs worker service"
systemctl enable obsworker.service
systemctl start obsworker.service

echo "OBS worker successfully started"
