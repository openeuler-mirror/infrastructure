#!/bin/bash
# 2021-09-24 created

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

# ---------------------------------------------------------------------------------------------------------------------------------------

systemctl stop obsworker

# define log time template and touch log file
TIME="[`date -d today '+%Y-%m-%d %H:%M:%S'`]"
LOGFILE=/var/log/install_obs_worker.log
if [[ ! -f $LOGFILE ]];then
        touch $LOGFILE
        echo "log file had touched."
        chmod 0666 $LOGFILE
fi

if [[ -z `grep '100.125.1.250' /etc/resolv.conf` ]];then
        sed -i '/^search/a \nameserver 100.125.1.250' /etc/resolv.conf
fi
if [[ -z `grep '100.125.1.250' /etc/resolv.conf` ]];then
        sed -i '1 i nameserver 100.125.1.250' /etc/resolv.com
fi

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
        sed -i "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} source.openeuler.org/${source_host} source.openeuler.org/g" /etc/hosts
fi
if ! grep -q "backend.openeuler.org" /etc/hosts; then
        echo "${backend_host} backend.openeuler.org" >> /etc/hosts
else
        sed -i "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} backend.openeuler.org/${backend_host} backend.openeuler.org/g" /etc/hosts
fi

if ! grep -q "home-backend.openeuler.org" /etc/hosts; then
        echo "${home_backend_host} home-backend.openeuler.org" >> /etc/hosts
else
        sed -i "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} home-backend.openeuler.org/${home_backend_host} home-backend.openeuler.org/g" /etc/hosts
fi

if ! grep -q "other-backend.openeuler.org" /etc/hosts; then
        echo "${other_backend_host} other-backend.openeuler.org" >> /etc/hosts
else
        sed -i "s/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\} other-backend.openeuler.org/${other_backend_host} other-backend.openeuler.org/g" /etc/hosts
fi

# test ip address whether reach
for ip in `grep "=" /obs/worker_ip_add | awk -F"=" '{print $2}'  | sed 's/"//g'`
do
        ping -c2 $ip
        if [ $? -ne 0 ];then
                func_log_file "$ip can not reach,please ip and netwok"
                exit
        fi
done

## download config files
# backup address: curl https://openeuler.obs.cn-south-1.myhuaweicloud.com/infrastructure/obsworker.tar.gz -o ${OBS_INSTALL_DIR}/obsworker.tar.gz
# if download file faild from bj4 ; use backup address download;
OBS_INSTALL_DIR=/tmp/obs_worker_arm_install
[[ ! -d ${OBS_INSTALL_DIR} ]] && mkdir -p ${OBS_INSTALL_DIR}
if [[ ! -e ${OBS_INSTALL_DIR}/obsworker.tar.gz ]]; then
    curl --connect-timeout 20 -m 20 https://openeuler-bj4.obs.cn-north-4.myhuaweicloud.com/obsworker.tar.gz -o ${OBS_INSTALL_DIR}/obsworker.tar.gz
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

# set obs workerservice
func_install_obsworker
func_config_obs_server_file
systemctl start  obsworker
if [ $? -eq 0 ];then
        echo "obsworker.service running,OBS worker successfully started"
else
        func_log_file "obsworker.service start faild"
fi

# x86 arch restart NetworkManger;ARM resatrt systemd-networkd and NetworkManger.service;
systemctl restart systemd-networkd
systemctl restart NetworkManger.service
systemctl restart obsworker.service
systemctl restart sshd.service
/usr/lib/systemd/systemd-sysv-install enable obsworker
if [[ -z `grep '100.125.1.250' /etc/resolv.conf` ]];then
        sed -i '1 i nameserver 100.125.1.250' /etc/resolv.com
fi
