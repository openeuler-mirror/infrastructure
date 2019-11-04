#!/usr/bin/env bash

# Usage: ./setup.sh <script-name> <ip-address> <data-disk-name>
script_name=$1
ip_address=$2
disk_name=$3
frontend_name=$4
backend_name=$5
scp ./authorized_keys root@${ip_address}:~/.ssh/
scp ./${script_name} root@${ip_address}:~/
ssh root@${ip_address}  "chmod +x ~/${script_name} && ~/${script_name} ${disk_name} ${frontend_name} ${backend_name}"
