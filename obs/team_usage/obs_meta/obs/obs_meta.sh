#!/bin/bash
set -ue

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
    clean_and_exit 1
}

function log_debug()
{
    echo "[DEBUG] $@"
}

function clean_and_exit()
{
    if [ $1 -ne 0 ]; then
        echo "=========error start========="
        cat $ERROR_LOG
        echo "=========error end========="
    fi
    exit $1
}

function checkout_prj_local()
{
    project=$1
    expect -c "
        set timeout -1
        spawn osc co "$project"
        expect {
            \"Enter choice*:\" {send \"2\r\"; exp_continue}
        }
    "
    osc meta prj "$project" > "${project}.meta"
    osc meta prjconf "$project" > "${project}.prjconf"
}

function back_project()
{
    project=$1
    rm -rf $project/.osc/*
    rm -rf $project/*/.osc/{_apiurl,_files,_osclib_version,_package,_project,_service}
    mv ${project}.meta $project/.osc/
    mv ${project}.prjconf $project/.osc/
}

function obs_meta_init()
{
    while read line
    do
        if ! echo $line | grep 'project name'; then
            continue
        fi
        prj=`echo $line | awk -F'"' '{print $2}' | sed 's/[ \r]//g'`
        config_flag=`echo $line | awk -F'"' '{print $4}'`
        source_flag=`echo $line | awk -F'"' '{print $6}'`
        if [ "x$config_flag" == "xyes" ]; then
            rm -rf prj_local
            mkdir prj_local
            cd prj_local
            checkout_prj_local $prj
            back_project $prj
            cd -
            rm -rf ../projects/$prj
            mv prj_local/$prj ../projects/
        fi
        if [ "x$source_flag" == "xyes" ]; then
            log_info "run build_and_wait later"
        fi
    done < version
}

obs_meta_init
