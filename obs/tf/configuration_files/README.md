#Install OBS components
## requirement
openSUSE15.1 or openSUSE15.0 (x86_64)
## install(full components)
```
zypper ar -f https://download.opensuse.org/repositories/OBS:/Server:/Unstable/openSUSE_15.0/OBS:Server:Unstable.repo
zypper in -t pattern OBS_Server
/usr/lib/obs/server/setup-appliance.sh --force
```

#STEP1: Source Server Configuration
## filesystem configuration
XFS is the best choice
## move the content /srv folder into mounted volume
1.Update the ip access rule
```bash
our $ipaccess = {
   '^::1$' => 'rw',    # only the localhost can write to the backend
   '^127\..*' => 'rw', # only the localhost can write to the backend
   "^$ip\$" => 'rw',   # Permit IP of FQDN
   '^192\..*' => 'rw', # allow access from internal instance
   '.*' => 'worker',   # build results can be delivered from any client in the network
};
```
2. Update the repo/upload/service ipaddress
```bash
our $srcserver = "http://$hostname:5352";
our $reposerver = "http://<ip address of backend server>:5252";
our $serviceserver = "http://<ip address of backend server>:5152";

```
3. update the slp files
```bash
1. /etc/slp.reg.d/obs.repo_server.reg
2. /etc/slp.reg.d/obs.source_server.reg

```

3. stop all services
```$xslt
systemctl stop obssrcserver.service &&\
systemctl stop obsrepserver.service &&\
systemctl stop obsservice.service &&\
systemctl stop obsdodup.service &&\
systemctl stop obsdeltastore.service &&\
systemctl stop obsscheduler.service &&\
systemctl stop obsdispatcher.service &&\
systemctl stop obspublisher.service &&\
systemctl stop obssigner.service &&\
systemctl stop obswarden.service &&\
systemctl stop obsworker.service &&\
systemctl stop obsclouduploadworker.service &&\
systemctl stop obsclouduploadserver.service &&\
systemctl stop apache2 &&\
systemctl stop mysql &&\
systemctl stop memcached
```

3. start the obs source service
```bash
systemctl start obsstoragesetup.service
systemctl start obssrcserver.service
systemctl start obsdeltastore.service

```

#STEP2: Backend Server Configuration
## filesystem configuration
XFS is the best choice
## move the content /srv folder into mounted volume

## update the backend service config
```bash
# file: /etc/sysconfig/obs-server
config needs update
OBS_RUN_DIR communication directory base /srv/obs/run

OBS_LOG_DIR logging directory /srv/obs/log
 
OBS_BASE_DIR base directory /srv/obs
# also update the BSconfig file

our $bsdir = '/srv/obs';

```
## update the slp files
```bash
1. /etc/slp.reg.d/obs_repo_server.reg
2. /etc/slp.reg.d/obs_source_server.reg

```

## Update scheduler service to remove dependency of 'obsapisetup.service'
the file file: /usr/lib/systemd/system/obsscheduler.service
```bash
[Unit]
Description=OBS job scheduler
Requires=obsrepserver.service
Wants=obsapisetup.service
After=network.target obssrcserver.service obsrepserver.service

[Service]
Type=oneshot
RemainAfterExit=true
ExecStart=/usr/sbin/obsscheduler start
ExecStop=/usr/sbin/obsscheduler stop
KillMode=none
TimeoutStopSec=infinity

[Install]
WantedBy=multi-user.target

```
## update the BS config file
```bash
our $srcserver = "http://$hostname:5352";
our $reposerver = "http://<ip address of backend server>:5252";
our $serviceserver = "http://<ip address of backend server>:5152";
```
## update the ip access rule
```bash
our $ipaccess = {
   '^::1$' => 'rw',    # only the localhost can write to the backend
   '^127\..*' => 'rw', # only the localhost can write to the backend
   "^$ip\$" => 'rw',   # Permit IP of FQDN
   '^192\..*' => 'rw', # allow access from internal instance
   '.*' => 'worker',   # build results can be delivered from any client in the network
};
```
## restart the whole service
```bash
systemctl stop obssrcserver.service &&\
systemctl restart obsrepserver.service &&\
systemctl restart obsservice.service &&\
systemctl restart obsdodup.service &&\
systemctl stop obsdeltastore.service &&\
systemctl restart obsscheduler.service &&\
systemctl restart obsdispatcher.service &&\
systemctl restart obspublisher.service &&\
systemctl restart obssigner.service &&\
systemctl restart obswarden.service &&\
systemctl stop obsworker.service &&\
systemctl stop apache2 &&\
systemctl stop mysql &&\
systemctl stop memcached
```

#STEP3: Frontend configuration

## stop all services first
```$xslt
systemctl stop obssrcserver.service &&\
systemctl stop obsrepserver.service &&\
systemctl stop obsservice.service &&\
systemctl stop obsdodup.service &&\
systemctl stop obsdeltastore.service &&\
systemctl stop obsscheduler.service &&\
systemctl stop obsdispatcher.service &&\
systemctl stop obspublisher.service &&\
systemctl stop obssigner.service &&\
systemctl stop obswarden.service &&\
systemctl stop obsworker.service &&\
systemctl stop apache2 &&\
systemctl stop mysql &&\
systemctl stop memcached
systemctl stop obs-api-support.target
```

## memcached
1. configure memcached in clouds
```$xslt
# file /srv/www/obs/api/config/options.yml
development:
  <<: *default
  source_host: backend
  memcached_host: <ip address of memcached service>
```
## mysql

1. configure mysql connection
```$xslt
vim /srv/www/obs/api/config/database.yml
#change the host&port and identity in yaml
  username: root
  password: opensuse
  encoding: utf8mb4
  collation: utf8mb4_unicode_ci
  timeout: 15
  pool: 30
  host: <ip address>
  port: <mysql port>
```

2. configure `/etc/my.cnf` with suitable host&port&username&password to enable mysqladmin tool

3. run script to create default database and schemas
```$xslt
# file is from /usr/lib/obs/server/setup-appliance.sh
cd /srv/www/obs/api
RAILS_ENV=production bin/rails db:create db:setup writeconfiguration
```

## configure source service to allow frontend access
```$xslt
# If defined, restrict access to the backend servers (bs_repserver, bs_srcserver, bs_service)
our $ipaccess = {
   '^::1$' => 'rw',    # only the localhost can write to the backend
   '^127\..*' => 'rw', # only the localhost can write to the backend
   '^192\..*' => 'rw', # allow access from internal instance
   "^$ip\$" => 'rw',   # Permit IP of FQDN
   '.*' => 'worker',   # build results can be delivered from any client in the network
};
```
then restart the backend source service
```$xslt
systemctl restart  obssrcserver.service
systemctl restart  obsdeltastore.service
```

## update the certificate file and content
copy certs file into apache2  cert folder
```bash
frontend/certs/cert.pem  => /srv/obs/certs/cert.pem
frontend/certs/chain.pem  => /srv/obs/certs/chain.pem
frontend/certs/privkey.pem  => /srv/obs/certs/privkey.pem
```
update the apache vhost config file
```bash
file: /etc/apache2/vhosts.d/obs.conf
ServerName build.openeuler.org
......
SSLCertificateFile /srv/obs/certs/cert.pem
SSLCertificateKeyFile /srv/obs/certs/privkey.pem
SSLCertificateChainFile /srv/obs/certs/chain.pem


```

## restart the apache2
```$xslt
systemctl restart apache2
systemctl restart obs-api-support.target
systemctl restart memcached
systemctl restart mysql
``` 


#Worker Configuration
0. stop all services
```bash
systemctl stop obssrcserver.service &&\
systemctl stop obsrepserver.service &&\
systemctl stop obsservice.service &&\
systemctl stop obsdodup.service &&\
systemctl stop obsdeltastore.service &&\
systemctl stop obsscheduler.service &&\
systemctl stop obsdispatcher.service &&\
systemctl stop obspublisher.service &&\
systemctl stop obssigner.service &&\
systemctl stop obswarden.service &&\
systemctl stop obsworker.service &&\
systemctl stop apache2 &&\
systemctl stop mysql &&\
systemctl stop memcached
```
1. Update file according to backend configuration
```$xslt
file: /etc/sysconfig/obs-server
OBS_SRC_SERVER="192.168.51.51:5352"  //obs source server 
OBS_REPO_SERVERS="192.168.51.51:5252" //obs repo server
OBS_WORKER_INSTANCES="20"
```
2. update the slp files
```bash
1. /etc/slp.reg.d/obs_repo_server.reg
2. /etc/slp.reg.d/obs_source_server.reg

```
2. restart worker service
```$xslt
systemctl start obsstoragesetup.service
systemctl start obsworker.service
```






