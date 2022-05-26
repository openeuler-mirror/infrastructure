#!/bin/bash

# Whether to reinitalize base on the value of cpuNum ;
n=`lscpu | grep '^CPU(s):' | awk '{print $2}'`
if [[ $n -ne `cat /obs/cpuNum` ]];then
        /obs/obs_worker_euleros_aarch.sh
         echo -e "[`date -d today "+%Y-%m-%d %H:%M:%S"`]" "\t\t\"cpu numbers had change or the first time start-up,exectuted init;\"" >> /var/log/install_obs_worker.log
fi

# Sed the resolv add after reboot everytime 
if [[ -z `grep '100.125.1.250' /etc/resolv.conf` ]];then
        sed -i '1 i nameserver 100.125.1.250' /etc/resolv.com
fi