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
    sed -i "s/OBS_SRC_SERVER=.*/OBS_SRC_SERVER=\"source.openeuler.org:5352\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_REPO_SERVERS=.*/OBS_REPO_SERVERS=\"backend.openeuler.org:5252\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_INSTANCES=.*/OBS_WORKER_INSTANCES=\"$n\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_JOBS=.*/OBS_WORKER_JOBS=\"8\"/g" /etc/sysconfig/obs-server

}

function fn_config_disk()
{
    if [[ ! -e ${disk_name} ]];then
        echo "No date disk ${disk_name}"
        exit 1
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

if [[ $# -lt 4 ]];then
    echo "please specify frontend host, source host and backend host and worker disk name, for instance: ./worker.sh 172.16.1.138 172.16.1.87 172.16.1.81 /dev/vdb"
    exit 1
fi
frontend_host=$1
source_host=$2
backend_host=$3
disk_name=$4
echo "Updating yum packages sources"
if [[ ! -e /etc/yum.repos.d/EulerOS-base.repo ]]; then
   mkdir -p /etc/yum.repos.d/repo_bak/
    mv /etc/yum.repos.d/*.repo /etc/yum.repos.d/repo_bak/
    curl -o /etc/yum.repos.d/EulerOS-base.repo http://mirrors.myhuaweicloud.com/repo/EulerOS_2_8_base.repo
fi
echo "Starting obs worker service with backend server ${backend_host}.."
#enable and start sshd service
echo "Enabling sshd service if not enabled"
systemctl enable sshd.service

echo "installing requirement packages"
yum install -y ntpdate vim cpio curl perl-Compress-Zlib perl-TimeDate perl-Data-Dumper perl-XML-Parser screen psmisc bash binutils bsdtar lzma util-linux openslp lvm2 perl-Digest-MD5 git screen tmux wget expect

echo "downloading obs worker script files"
OBS_INSTALL_DIR=/tmp/obs_worker_arm_install

[[ ! -d ${OBS_INSTALL_DIR} ]] && mkdir -p ${OBS_INSTALL_DIR}

if [[ ! -e ${OBS_INSTALL_DIR}/obsworker.tar.gz ]]; then
    curl https://openeuler.obs.cn-south-1.myhuaweicloud.com:443/infrastructure/obsworker.tar.gz -o ${OBS_INSTALL_DIR}/obsworker.tar.gz
fi

echo "Updating the cluster hosts info"
# update hosts info:
#    1. <frontend_host> build.openeuler.org
#    2. <source_host> source.openeuler.org
#    3. <backend_host> backend.openeuler.org
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

echo "configure disks"
if [[ ! -d /var/cache/obs/worker/ ]];then
    mkdir -p  /var/cache/obs/worker/
fi
fn_config_disk

echo "unmask config"
sed -i s'/umask 0077/umask 0022/g' /etc/bashrc

echo "installing obsworker"
fn_install_obsworker
systemctl disable obsworker.service
systemctl stop obsworker.service

echo "updating obs worker configuration file"
fn_config_obs_server_file

echo "enabling obs worker service"
systemctl enable obsworker.service
systemctl start obsworker.service

echo "OBS worker successfully started"
