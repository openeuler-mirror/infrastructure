#!/bin/bash
cpath=`pwd`
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

function obs_prj()
{
    while read line
    do
        if ! echo $line | grep 'project name'; then
            continue
        fi
        if echo $line | grep 'config="yes"'; then
            prj=`echo $line | awk -F'"' '{print $2}' | sed 's/[ \r]//g'`
            create_prj $prj
        fi
    done < version
}

function create_prj()
{
    prj=$1
    base_dir="$cpath/../projects/$prj"
    meta="$base_dir/.osc/${prj}.meta"
    if [ -f $meta ]; then
        sed -i '/<person userid/d' $meta
        sed -i '/<group groupid/d' $meta
        osc meta prj "$prj" --file="$meta"
    fi
    prjconf="$base_dir/.osc/${prj}.prjconf"
    if [ -f $prjconf ]; then
        osc meta prjconf "$prj" --file="$prjconf"
    fi
    rm -rf $prj
    osc co $prj
    for line in `ls $base_dir`
    do
        if [ "$line" == ".osc" ];then
            continue
        elif [ -f $base_dir/$line/_service ]; then
            if [ ! -d $prj/$line ]; then
                mkdir -p $prj/$line
            fi
            cp -rf $base_dir/$line/_service $prj/$line/
        else
            if [ ! -d $prj/$line ]; then
                mkdir -p $prj/$line
            fi
            cp -rf $base_dir/$line/* $prj/$line/
        fi
    done
    cd $prj
    for line in `ls`
    do
        if [ ! -d $base_dir/$line ]; then
            osc rm $line
        fi
    done
    nfiles=`osc status 2>/dev/null| grep ^? |awk '{print $2}'`
    mfiles=`osc status 2>/dev/null| grep ^M |awk '{print $2}'`
    dfiles=`osc status 2>/dev/null| grep ^D |awk '{print $2}'`
    if [ -n "$nfiles" ]; then
        osc add $nfiles
    fi
    if [ -n "$nfiles" -o -n "$mfiles" -o -n "$dfiles" ]; then
        osc ci $nfiles $mfiles $dfiles -m 'ok'
    fi
    cd -

    for pkg in `ls $prj`
    do
        if [ -f $base_dir/$pkg/.osc/_meta ]; then
        sed -i '/<person userid/d' $base_dir/$pkg/.osc/_meta
        sed -i '/<group groupid/d' $base_dir/$pkg/.osc/_meta
        osc meta pkg "$prj" "$pkg" --file="$base_dir/$pkg/.osc/_meta"
        fi
    done
}

obs_prj
