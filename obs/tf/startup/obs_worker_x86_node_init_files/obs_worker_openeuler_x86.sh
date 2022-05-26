#!/bin/bash
# 2021-09-24 created;use for x86 worker node init;
# ---------------------------------------------------------------------------------------------------------------------------------------

function func_install_obsworker(){
    if [[ ! -e /etc/sysconfig/obs-server ]];then
        tar -xvf $OBS_INSTALL_DIR/obsworker.tar.gz -C /
    fi
    getent group obsrun  >/dev/null || groupadd -r obsrun
    getent passwd obsrun >/dev/null || /usr/sbin/useradd -r -g obsrun -d /usr/lib/obs -s /usr/sbin/nologin -c "User for build service backend" obsrun
}

function func_config_obs_server_file(){
    CPU_NUM=`lscpu | grep '^CPU(s):' | awk '{print $2}'`
    echo $CPU_NUM > /obs/cpuNum
    sed -i "s/OBS_WORKER_JOBS=.*/OBS_WORKER_JOBS=\"$CPU_NUM\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_INSTANCES=.*/OBS_WORKER_INSTANCES=\"6\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_SRC_SERVER=.*/OBS_SRC_SERVER=\"source.openeuler.org:5352\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_REPO_SERVERS=.*/OBS_REPO_SERVERS=\"backend.openeuler.org:5252\"/g" /etc/sysconfig/obs-server
    # sed -i "s/OBS_REPO_SERVERS=.*/OBS_REPO_SERVERS=\"backend.openeuler.org:5252 other-backend.openeuler.org:5252\"/g" /etc/sysconfig/obs-server
}

function func_config_disk(){
    if [[ ! -e ${disk_name} ]];then
        func_log_file "No date disk ${disk_name}"
        exit 1
    fi

    if [[ ! -e  /dev/OBS/worker ]];then
        pvcreate ${disk_name}
        vgcreate "OBS" ${disk_name}
        lvcreate  -l 100%FREE  "OBS" -n "worker"
        mkfs.ext4 /dev/OBS/worker
        echo "/dev/mapper/OBS-worker /var/cache/obs/worker  ext4 defaults 0 0" >> /etc/fstab
        mount -a
    fi
}

function func_log_file(){
        echo "$TIME     \"$1\"" >> $LOGFILE
}

function func_resolv_dns(){
        if [[ -z `grep '100.125.1.250' /etc/resolv.conf` ]];then
                sed -i '/^#/a \nameserver 100.125.1.250' /etc/resolv.conf
        fi
        if [[ -z `grep '100.125.1.250' /etc/resolv.conf` ]];then
                sed -i '1 i nameserver 100.125.1.250' /etc/resolv.com
        fi
}

# ---------------------------------------------------------------------------------------------------------------------------------------

# base setting
systemctl stop obsworker
TIME="[`date -d today '+%Y-%m-%d %H:%M:%S'`]"
LOGFILE=/var/log/install_obs_worker.log
if [[ ! -f $LOGFILE ]];then
        touch $LOGFILE
        echo "log file had touched."
        chmod 0666 $LOGFILE
fi
func_resolv_dns

# replace ip address for "frontend_host、source_host、backend_host、home_backend_host" in /etc/host
frontend_host=`     grep "frontend_host"      /obs/worker_ip_add | awk -F"=" '{print $2}' | sed 's/"//g'`
source_host=`       grep "source_host"        /obs/worker_ip_add | awk -F"=" '{print $2}' | sed 's/"//g'`
backend_host=`      grep "^backend_host"      /obs/worker_ip_add | awk -F"=" '{print $2}' | sed 's/"//g'`
home_backend_host=` grep "home_backend_host"  /obs/worker_ip_add | awk -F"=" '{print $2}' | sed 's/"//g'`
other_backend_host=`grep "other_backend_host" /obs/worker_ip_add | awk -F"=" '{print $2}' | sed 's/"//g'`
if ! grep -q "build.openeuler.org" /etc/hosts; then
        echo "${frontend_host} build.openeuler.org" >> /etc/hosts
else
        sed -i "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} build.openeuler.org/${frontend_host} build.openeuler.org/g" /etc/hosts
fi
if ! grep -q "source.openeuler.org" /etc/hosts; then
        echo "${source_host} source.openeuler.org" >> /etc/hosts
else
        sed -i  "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} source.openeuler.org/${source_host} source.openeuler.org/g" /etc/hosts
fi
if ! grep -q "backend.openeuler.org" /etc/hosts; then
        echo "${backend_host} backend.openeuler.org" >> /etc/hosts
else
        sed -i "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} backend.openeuler.org/${backend_host} backend.openeuler.org/g" /etc/hosts
fi

if ! grep -q "home-backend.openeuler.org" /etc/hosts; then
        echo "${home_backend_host} home-backend.openeuler.org" >> /etc/hosts
else
        sed -i  "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} home-backend.openeuler.org/${home_backend_host} home-backend.openeuler.org/g" /etc/hosts
fi

if ! grep -q "other-backend.openeuler.org" /etc/hosts; then
        echo "${other_backend_host} other-backend.openeuler.org" >> /etc/hosts
else
        sed -i "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} other-backend.openeuler.org/${other_backend_host} other-backend.openeuler.org/g" /etc/hosts
fi

yum update -y
yum install -y screen ntpdate vim cpio curl perl-Compress-Zlib perl-TimeDate perl-Data-Dumper perl-XML-Parser screen psmisc bash binutils bsdtar lzma util-linux openslp lvm2 perl-Digest-MD5 git screen tmux wget expect
# curl https://openeuler.obs.cn-south-1.myhuaweicloud.com/infrastructure/obsworker.tar.gz -o ${OBS_INSTALL_DIR}/obsworker.tar.gz
# download file from south-1 alwyas failed; so use bj4-obs-site download;

OBS_INSTALL_DIR=/tmp/obs_worker_arm_install
[[ ! -d ${OBS_INSTALL_DIR} ]] && mkdir -p ${OBS_INSTALL_DIR}
if [[ ! -e ${OBS_INSTALL_DIR}/obsworker.tar.gz ]]; then
    curl --connect-timeout 30 -m 30 https://openeuler-bj4.obs.cn-north-4.myhuaweicloud.com/obsworker.tar.gz -o ${OBS_INSTALL_DIR}/obsworker.tar.gz
    if [ ! -e "${OBS_INSTALL_DIR}/obsworker.tar.gz" ];then
            func_log_file "download obsworker.tar.gz faild"
            exit
    fi
fi

# create a data disk ,eg:/dev/vdb
disk_name=/dev/vdb
if [[ ! -e /dev/vdb ]];then
        func_log_file "not exist /dev/vdb , please add /dev/vdb as obs-worker-node data disk"
        exit
fi
if [[ ! -d /var/cache/obs/worker ]];then
    mkdir -p  /var/cache/obs/worker
fi
if [[ "str${disk_name}" != "${disk_name}" ]]; then
    func_config_disk
fi
sed -i 's/umask 0077/umask 0022/g' /etc/bashrc

# ---------------------------------------------------------------------------------------------------------------------------------------

# obs-worker-service
func_install_obsworker
func_config_obs_server_file
systemctl start  obsworker

if [ $? -eq 0 ];then
        echo "obsworker.service running,OBS worker successfully started"
else
        func_log_file "obsworker.service start faild"
fi

# x86 arch restart NetworkManger;ARM resatrt systemd-networkd and NetworkManger;
systemctl restart NetworkManager.service
systemctl restart obsworker.service
systemctl restart sshd.service
/usr/lib/systemd/systemd-sysv-install enable obsworker
func_resolv_dns