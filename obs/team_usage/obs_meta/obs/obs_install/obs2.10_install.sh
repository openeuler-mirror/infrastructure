#/bin/bash
set -e
OBS_INSTALL=$(cd `dirname $0`;pwd)
DnsName='euleros-obs'
OBS_RPMS_REPO=$OBS_INSTALL/obs_repo
OBS_TAR_SCM=$OBS_INSTALL/obs_tar_scm
ISO_DIR=$OBS_INSTALL/iso
OBS_CONFIG=$OBS_INSTALL/config
OBSREPO1='OBSServer2.10.tar.gz'
OBSREPO2='opensuse_15.1_oss.tar.gz'

ISO_DIR=$OBS_INSTALL/iso
OBS_CONFIG=$OBS_INSTALL/config
OBS_WORKER_DIR=$OBS_INSTALL/obsworker


function usage()
{
    echo "`basename $0` [script_name|all]"
}

function log_info()
{
    echo "$@"
}

function log_warn()
{
    echo "[WARNING] $@"
}

function log_error()
{
    echo "[ERROR] $@"
    exit $1
}

function run_script()
{
    script=$1
    shift
    args="$@"
    log_info "Start run $script $args at `date`"
    eval $script $args
    if [ $? -ne 0 ]; then
        log_error "Run $script $args failed at `date`"
    else
        log_info "Finished run $script $args at `date`"
    fi
}

function f_main()
{
    arg1=$1
    shift
    arg2=$@
    run_script $arg1 $arg2
}

function func_prep(){
    rm -f /etc/localtime
    mkdir -p $OBS_RPMS_REPO
    case $1 in
    server|worker_x86_64)
        [ -f /srv/$OBSREPO1 ] || log_error "miss $OBSREPO1"
        [ -f /srv/$OBSREPO2 ] || log_error "miss $OBSREPO2"
        mkdir -p $OBS_RPMS_REPO/{1,2}
        tar -xf /srv/$OBSREPO1 -C $OBS_RPMS_REPO/1
        tar -xf /srv/$OBSREPO2 -C $OBS_RPMS_REPO/2
    ;;
    worker_aarch64)
    ;;
    esac
}

function func_do_repo()
{
    repo=`zypper lr | awk '{if(NR>2)print $1}'`
    if [ -n "$repo" ];then
        zypper rr $repo
    fi
    case $1 in
    server|worker_x86_64)
        zypper ar --no-gpgcheck "`find $OBS_RPMS_REPO/1 -name repodata`/.." obsrepo
        zypper ar --no-gpgcheck "`find $OBS_RPMS_REPO/2 -name repodata`/.." opensuserepo
    ;;
    worker_aarch64)
    ;;
    esac

}

function func_do_install()
{
    case $1 in
    server)
        echo "solver.allowVendorChange = true" >> /etc/zypp/zypp.conf
	zypper --non-interactive in -t pattern OBS_Server
        zypper --non-interactive install osc
    ;;
    worker_x86_64)
        zypper --non-interactive install obs-worker
    ;;
    worker_aarch64)
    ;;
    esac
}

function config_osc()
{
    # config osc
    echo "[general]" >> /root/.oscrc
    echo "apiurl = https://euleros-obs" >> /root/.oscrc
    echo "no_verify = 1" >> /root/.oscrc
    echo "[https://euleros-obs]" >> /root/.oscrc
    echo "user = Admin" >> /root/.oscrc
    echo "pass = opensuse" >> /root/.oscrc
    config_tmp=$(mktemp)	
    osc api /configuration > $config_tmp
    sed -i "s#<schedulers>#<schedulers>\n    <arch>aarch64</arch>\n    <arch>i686</arch>#g" $config_tmp
    osc api /configuration --file=$config_tmp
    rm $config_tmp
}

function check_obs_service()
{
    sv_do=$1
    systemctl $sv_do mysql.service
    systemctl $sv_do apache2.service
    systemctl $sv_do memcached
    systemctl $sv_do obsrepserver.service
    systemctl $sv_do obssrcserver.service
    systemctl $sv_do obsscheduler.service
    systemctl $sv_do obsdispatcher.service
    systemctl $sv_do obspublisher.service
    systemctl $sv_do obswarden.service
    systemctl $sv_do obsservice.service
    systemctl $sv_do apache2.service
    systemctl $sv_do obsapidelayed.service
}

function func_do_customize()
{
    case $1 in
    server)
        echo CACHEDIRECTORY="/srv/cache/obs/tar_scm" > /etc/obs/services/tar_scm
        mkdir -p /srv/cache/obs/tar_scm/{incoming,repo,repourl}
        mkdir -p /srv/cache/obs/tar_scm/repo/euleros-version
        mkdir -p /usr/lib/obs/source_md5
        chmod 777 /usr/lib/obs/source_md5

        #curl "https://$HostName" &>/dev/null
        cp -f $OBS_INSTALL/config/service/* /usr/lib/obs/service/
        cp -f $OBS_INSTALL/config/BSConfig.pm /usr/lib/obs/server/
        cp -f $OBS_CONFIG/build-pkg-rpm /usr/lib/build/build-pkg-rpm
        cp -f $OBS_CONFIG/obs-server /etc/sysconfig/obs-server
        cp -f $OBS_CONFIG/setup-appliance.sh /usr/lib/obs/server/setup-appliance.sh
        #cp -f $OBS_CONFIG/configuration.xml /srv/obs/configuration.xml 
        #chown obsrun.obsrun /srv/obs/configuration.xml
    ;;
    worker_x86_64)
    ;;
    worker_aarch64)
    ;;
    esac
}

function obs_server_install()
{

    echo "export TAR_OPTIONS=--format=gnu" >> /etc/profile
    source /etc/profile
    hostnamectl set-hostname $DnsName
    #DEFAULT_ROUTE_INTERFACE=`LANG=C ip route show|perl  -e '$_=<>; ( m/^default via.*dev\s+([\w]+)\s.*/ ) && print $1'`
    #FQHOSTNAME=`LANG=C ip addr show $DEFAULT_ROUTE_INTERFACE| perl -lne '( m#^\s+inet\s+([0-9\.]+)(/\d+)?\s+.*# ) && print $1' | grep -v ^127. | head -n 1`
    echo "127.0.0.1 $DnsName" >> /etc/hosts
    hostname -F /etc/hostname 
    #prep envirement
    func_prep 'server'

    #deal with repo
    func_do_repo 'server'

    #install all needed packages
    func_do_install 'server'

    #huawei customized
    func_do_customize 'server'


    #Run obs setup wizard
    /usr/lib/obs/server/setup-appliance.sh --non-interactive
    #config osc
    config_osc
    systemctl stop obssigner
    systemctl disable obssigner
    systemctl stop obssignd
    systemctl disable obssignd
   
    log_info "====================================="
    log_info "Install OBS Server Success. Have Fun!"
    log_info "====================================="
}

function obs_worker_install()
{
    arch=$1
    server_ip=$2
    server_name=$3
    case $arch in
    x86)
        obs_worker_install_x86
    ;;
    arm)
        obs_worker_install_arm
    ;;
    esac

    n=`lscpu | grep '^CPU(s):' | awk '{print $2}'`
    ((n=$n/4+1))
    sed -i "s/OBS_SRC_SERVER=.*/OBS_SRC_SERVER=\"$server_ip:5352\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_REPO_SERVERS=.*/OBS_REPO_SERVERS=\"$server_ip:5252\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_INSTANCES=.*/OBS_WORKER_INSTANCES=\"$n\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_JOBS=.*/OBS_WORKER_JOBS=\"4\"/g" /etc/sysconfig/obs-server

    echo "$server_ip $DnsName" >> /etc/hosts

    systemctl enable obsworker.service
    systemctl start obsworker.service

    log_info "====================================="
    log_info "Install OBS Worker Success. Have Fun!"
    log_info "====================================="
}

function obs_worker_install_x86()
{
    func_prep 'worker_x86_64'
    func_do_repo 'worker_x86_64'
    func_do_install 'worker_x86_64'
}

function obs_worker_install_arm()
{
    func_prep 'worker_aarch64'
    func_do_repo 'worker_aarch64'
    func_do_install 'worker_aarch64'
}
function centos_1804_arm_worker()
{
## check parmeter
   [ $# -ne 1 ] && echo "please enter obs server ip" && exit 1
   obs_server_ip=$1

## check iso
    [ -f /opt/$CENTOS_IOS ] || log_error "miss $CENTOS_IOS"

## install obs worker
    cp -f $OBS_WORKER_DIR/etc/init.d/obsworker /etc/init.d/obsworker
    cp -f $OBS_WORKER_DIR/usr/sbin/rcobsworker /usr/sbin/rcobsworker
    cp -f $OBS_WORKER_DIR/etc/sysconfig/obs-server /etc/sysconfig/obs-server
    cp -f $OBS_WORKER_DIR/etc/rc.status /etc/rc.status

## create repo and repo conf file
    mkdir -p $OBS_INSTALL/iso/centos7.5
    mount /opt/$CENTOS_IOS $OBS_INSTALL/iso/centos7.5

    mkdir -p $OBS_RPMS_REPO
    centos_arm_repo_conf=$OBS_RPMS_REPO/centos7.5-obs-repo.conf
    [ -f  "$centos_arm_repo_conf" ] &&  rm -rf "$centos_arm_repo_conf"
    cat > "$centos_arm_repo_conf" << EOF
[main]
cachedir=/var/cache/yum/xxx
keepcache=0
debuglevel=2
logfile=/var/log/yum.log
exactarch=1
obsoletes=1
gpgcheck=0
plugins=1
installonly_limit=3
reposdir=/xxx

[centso7.5-aarch64]
name=centos7.5-aarch64
baseurl=file://$OBS_INSTALL/iso/centos7.5
enabled=1
gpgcheck=0
EOF

## install require rpms
   yum -c "$centos_arm_repo_conf" clean all
   yum -y install -c "$centos_arm_repo_conf" cpio curl perl-Compress-Zlib perl-TimeDate perl-Data-Dumper perl-XML-Parser screen psmisc bash binutils bsdtar lzma util-linux openslp lvm2 perl-Digest-MD5 expect wget


## check umask
   sed -i s'/umask 0077/umask 0022/g' /etc/bashrc

## config hostname
    DEFAULT_ROUTE_INTERFACE=`LANG=C ip route show|perl  -e '$_=<>; ( m/^default via.*dev\s+([\w]+)\s.*/ ) && print $1'`
    FQHOSTNAME=`LANG=C ip addr show $DEFAULT_ROUTE_INTERFACE| perl -lne '( m#^\s+inet\s+([0-9\.]+)(/\d+)?\s+.*# ) && print $1' | grep -v ^127. | head -n 1`
    hostname="build${FQHOSTNAME//\./b}"
    hostnamectl set-hostname ${hostname}

##  config obs_server file
    n=`lscpu | grep '^CPU(s):' | awk '{print $2}'`
    let n=$n/4+1
    sed -i "s/OBS_SRC_SERVER=.*/OBS_SRC_SERVER=\"$obs_server_ip:5352\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_REPO_SERVERS=.*/OBS_REPO_SERVERS=\"$obs_server_ip:5252\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_INSTANCES=.*/OBS_WORKER_INSTANCES=\"$n\"/g" /etc/sysconfig/obs-server
    sed -i "s/OBS_WORKER_JOBS=.*/OBS_WORKER_JOBS=\"8\"/g" /etc/sysconfig/obs-server
    sed -i "2i $obs_server_ip $DnsName ${DnsName}.huawei.com"  /etc/hosts
## disable SELinux
    ### disable SELinux temporarily
    setenforce 0
    ###  disable SELinux permanently
    sed -i 's/^SELINUX=.*/SELINUX=disabled/g' /etc/selinux/config

##  enable obsworker service
    systemctl enable obsworker.service
    systemctl restart obsworker.service
}


f_main $@

