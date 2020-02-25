#!/bin/bash
set -e

if [[ ! -e "/etc/rsyncd.conf" ]]; then
    echo "/etc/rsyncd.conf not exists"
    exit 1
fi

#setting up sshd server
if [[ -e "/root/.ssh/authorized_keys" ]]; then
    chmod 0400 /root/.ssh/authorized_keys
    chown root:root /root/.ssh/authorized_keys
fi
exec /usr/sbin/sshd &

exec /usr/bin/rsync --no-detach --daemon --config /etc/rsyncd.conf "$@"