# NOTE
All script files in this folder used to start up the corresponding service in OBS cluster,
There are some additional setup files (used in startup scripts) which are stored in the huawei object storage:
```
https://openeuler.obs.cn-south-1.myhuaweicloud.com:443/infrastructure/<file_name>
```
Remember to update them if required.

# Frontend
## Requirement
It's assumed the system is booted via the OpenSUSE OBS 2.10 ISO image [here](https://openbuildservice.org/download/)
## Setup environment
Frontend is used to running the api server including the memcached and mysql, please copy the `frontend.sh` file
to any folder of the destination machine and execute the command:
```bash
./frontend.sh <ip address of source service>
```
and the status of the service can be checked with command:
```bash
systemctl list-units | grep -E 'obs|memcached|mariadb|apache2'
```
the output would be like:
```bash
apache2.service                                                                loaded active running   The Apache Webserver
mariadb.service                                                                loaded active running   MySQL server
memcached.service                                                              loaded active running   memcached daemon
obs-clockwork.service                                                          loaded active running   Open Build Service Clockwork Daemon
obs-delayedjob-queue-consistency_check.service                                 loaded active running   Open Build Service DelayedJob Queue: consistency_check
obs-delayedjob-queue-default.service                                           loaded active running   Open Build Service DelayedJob Queue: default
obs-delayedjob-queue-issuetracking.service                                     loaded active running   Open Build Service DelayedJob Queue: issuetracking
obs-delayedjob-queue-mailers.service                                           loaded active running   Open Build Service DelayedJob Queue: mailers
obs-delayedjob-queue-project_log_rotate.service                                loaded active running   Open Build Service DelayedJob Queue: project_log_rotate
obs-delayedjob-queue-quick@0.service                                           loaded active running   Open Build Service DelayedJob Queue Instance: quick
obs-delayedjob-queue-quick@1.service                                           loaded active running   Open Build Service DelayedJob Queue Instance: quick
obs-delayedjob-queue-quick@2.service                                           loaded active running   Open Build Service DelayedJob Queue Instance: quick
obs-delayedjob-queue-releasetracking.service                                   loaded active running   Open Build Service DelayedJob Queue: releasetracking
obs-delayedjob-queue-staging.service                                           loaded active running   Open Build Service DelayedJob Queue: staging
obs-sphinx.service                                                             loaded active running   Open Build Service Sphinx Search Daemon
obsstoragesetup.service                                                        loaded active exited    OBS storage setup
system-obs\x2ddelayedjob\x2dqueue\x2dquick.slice                               loaded active active    system-obs\x2ddelayedjob\x2dqueue\x2dquick.slice
obs-api-support.target                                                         loaded active active    Open Build Service API Support Daemons
```

## Source Service
## Requirement
It's assumed the system is booted via the OpenSUSE OBS 2.10 ISO image [here](https://openbuildservice.org/download/)
## Setup environment
Source service is used to running the OBS source server (including obsdeltastore.service and obsservicedispatch.service)
please copy the `source_server.sh` file to any folder of the destination machine and execute the command:
```bash
./source_server.sh <ip address of source host>  <ip address of backend host>
```
and the status of the service can be checked with command:
```bash
systemctl list-units | grep obs
```
the output would include:
```bash
obsdeltastore.service                                                          loaded active running   OBS deltastore daemon
obsservicedispatch.service                                                     loaded active running   OBS source service dispatcher
obssrcserver.service                                                           loaded active running   OBS source repository server
obsstoragesetup.service                                                        loaded active exited    OBS storage setup
```

## Backend Service
## Requirement
It's assumed the system is booted via the OpenSUSE OBS 2.10 ISO image [here](https://openbuildservice.org/download/)
## Setup environment
Backend service is used to running the OBS repo server, scheduler, warden and any service used to dispatch%execute&upload builds
please copy the `backend.sh` file to any folder of the destination machine and execute the command:
```bash
./backend.sh <ip address of source host>  <ip address of backend host>
```
and the status of the service can be checked with command:
```bash
systemctl list-units | grep obs
```
the output would include:
```bash
obsapisetup.service                                                            loaded activating start     start OBS API Setup
obsdispatcher.service                                                          loaded active     running         OBS job dispatcher daemon
obsdodup.service                                                               loaded active     running         OBS dodup, updates download on demand metadata
obspublisher.service                                                           loaded active     running         OBS repository publisher
obsrepserver.service                                                           loaded active     running         OBS repository server
obsscheduler.service                                                           loaded active     exited          OBS job scheduler
obsservice.service                                                             loaded active     running         OBS source service server
obssignd.service                                                               loaded active     running         LSB: start the gpg sign daemon
obssigner.service                                                              loaded active     running         OBS signer service
obsstoragesetup.service                                                        loaded active     exited          OBS storage setup
obswarden.service                                                              loaded active     running         OBS warden, monitors the workers
system-obs\x2ddelayedjob\x2dqueue\x2dquick.slice                               loaded active     active          system-obs\x2ddelayedjob\x2dqueue\x2dquick.slice
```

## Worker Service
## Requirement
It's assumed the system is based on Centos, equal to Centos7.6 is prefered and there is additional volumes are mounted (used for obs worker working folder)
## Setup environment
Worker service is used to running the OBS worker server.
please copy the `worker.sh` file to any folder of the destination machine and execute the command:
```bash
./worker.sh <ip address of source host>  <ip address of backend host> <disk name that will be used>
```
and the status of the service can be checked with command:
```bash
systemctl list-units | grep obs
```
the output would include:
```bash
var-cache-obs-worker.mount                                                     loaded active mounted   /var/cache/obs/worker
obsworker.service                                                              loaded active running   LSB: Open Build Service worker
```
# Cluster environment
```bash
Frontend:    172.16.1.81
Source:      172.16.1.89
Backend:     172.16.1.95
Worker1:     172.16.1.80
Worker2:     172.16.1.33
Worker3:     172.16.1.99
Worker4:     172.16.1.168
Worker5:     172.16.1.151
Worker6:     172.16.1.195
Worker7:     172.16.1.127
Worker8:     172.16.1.12
Worker9:     172.16.1.14
Worker10:    172.16.1.157
```

## download full fedora packages
please see the document in folder `download_fedora_packages`

## prepare gitee projects
please see the document in folder `download_package_codes`

## when everything is ok
please trigger service rerun to create tar file for packages
```$xslt
for rpmn in `osc ls openEuler:Mainline`;do osc service remoterun openEuler:Mainline $rpmn;done
```
