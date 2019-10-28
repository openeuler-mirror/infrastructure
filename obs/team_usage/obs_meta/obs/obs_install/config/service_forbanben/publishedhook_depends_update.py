#!/usr/bin/env python2
# -*- encoding=utf-8 -*-

import os,sys
from subprocess  import *
import re
import shutil
import traceback
import hashlib
import time
from xml.dom import minidom
from xml.etree import ElementTree as ET
import logging
import logging.config

#source_host = '/usr/lib/obs/mount_from_source_host'
source_host = '/srv/obs'
publishedhook_workspace = '/usr/lib/obs/source_md5'

logging.config.fileConfig("/usr/lib/obs/service/logger.conf")
logger = logging.getLogger("publishedhook_depends_update")

def shell_cmd(s_cmd_line, inmsg=None):
    p = Popen(s_cmd_line, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    if inmsg:
        p.stdin.write(inmsg)
    out, err = p.communicate()
    return p.returncode, out, err

def parse_args(argv):
    if len(argv) == 0:
        logger.error("Usage:EulerOS:Update/standard_aarch64 /srv/obs/repos/EulerOS:/Update/standard_aarch64 aarch64/wget-1.14-15.1.h2.aarch64.rpm")
        return False

    #for line in argv:
    #    logger.info( "%s" % line )

    publish_rpmlist = []
    archs=[]
    project_build_path = '/srv/obs/build/%s' % argv[0]
    (prj,repo)=argv[0].split('/')
    base_project = '/srv/obs/build/%s_baseline' % prj

    if not os.path.exists( base_project ):
        logger.info( "Found none %s_baseline project. skipped ..." % prj )
        return True

    if len(argv) > 2:
        for line in argv[2:]:
            (arch_name,pkgname)=line.split('/')
            if arch_name not in ['src','noarch']:
                if not os.path.exists( os.path.join(project_build_path, arch_name) ):
                    cmd = "find %s -name %s | sed -n '1p'" % (project_build_path, pkgname)
                    ret, out, err = shell_cmd(cmd)
                    if ret != 0:
                        logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out, err) )
                        return False
                    else:
                        logger.info("%s" % out)
                        arch_name = out.split('/')[6]
                if arch_name not in archs:
                    archs.append(arch_name)
            if not re.match( r'.*src\.rpm', pkgname ):
                publish_rpmlist.append( pkgname )

    if len(archs) == 0:
        archs = filter( lambda x: os.path.isdir( os.path.join(project_build_path,x) ) , os.listdir(project_build_path) )
    for xxarch in archs:
        rpmlist = []
        for rpm in publish_rpmlist:
            if rpm.split('.')[-2] in [ 'noarch', xxarch ]:
                rpmlist.append(rpm)
        project = (prj,repo,xxarch,rpmlist)
        projects.append(project)

    return True

def scan_update_change(project,pkg_dict,prj_base_dict):
    publish_info = []
    ls = os.linesep
    xml_head = '<?xml version="1.0" encoding="utf-8"?>'
    project_build_path = '/srv/obs/build/%s/%s/%s' % (project[0], project[1], project[2])

    publish_info.append( xml_head )
    publish_info.append('<packages>')
    packages = filter( lambda x: not re.match(r'^:.*',x) and not re.match(r'^\..*',x), os.listdir(project_build_path) )

    pkg_rev_path = '%s/projects/%s.pkg'  % ( source_host, project[0]  )
    pkg_src_path = '%s/trees/%s' % (source_host, project[0] )
    pkg_hash_path = '%s/trees/%s'  % (source_host, project[0] )
    for package in packages:
        cmd = "sed -n '$p' %s/%s.rev" % ( pkg_rev_path, package )
        ret, out1, err = shell_cmd(cmd)
        if ret != 0:
            logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out1, err) )
            return False
        cmd = "sed -n '1p' %s/%s/%s-MD5SUMS" % ( pkg_src_path, package, out1.split('|')[2] )
        ret, out2, err = shell_cmd(cmd)
        if ret != 0:
            logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out2, err) )
            return False
        if out2.find('/SERVICE') != -1:
            srcfile = '%s/%s/%s-MD5SUMS' % (pkg_hash_path, package, out2.split('  ')[0])
            if os.path.exists(srcfile):
                cmd = "cat %s | grep '_service:'" % srcfile
            else:
                cmd = "echo 'E1001'" 
        else:
            cmd = "cat %s/%s/%s-MD5SUMS" % ( pkg_src_path, package, out1.split('|')[2] )
        ret, out3, err = shell_cmd(cmd)
        if ret != 0:
            logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out3, err) )
            return False
        if re.match(r'E100.*', out3):
            logger.info( '%s pending %s skip ...' % (package,out3) )
            pkg_hash = prj_base_dict[package][0]
            rpms = prj_base_dict[package][1]
        else:
            digest = hashlib.md5()
            digest.update(out3)
            rpms = filter( lambda x: re.match(r'.*\.rpm',x), os.listdir( os.path.join(project_build_path, package) ) )
            rpms.sort()
            digest.update( ' '.join(rpms) )
            pkg_hash = digest.hexdigest()
        rpmsStr = ' '.join(rpms)
        update_info = '<package name="%s" hash="%s" binary="%s"></package>' % (package, pkg_hash, rpmsStr)
        pkg_dict[package] = (pkg_hash,rpms)
        publish_info.append( update_info )

    cmd = "sed -n '$p' %s/_project.rev | awk -F'|' '{print $3}';sed -n '$p' %s/_project.mrev | awk -F'|' '{print $3}'" % ( pkg_rev_path, pkg_rev_path )
    ret, out, err = shell_cmd(cmd)
    if ret != 0:
        logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out, err) )
        return False
    pdigest = hashlib.md5()
    pdigest.update(out)
    pkg_hash = pdigest.hexdigest()
    update_info = '<package name="_project" hash="%s" binary=""></package>' % ( pkg_hash )
    pkg_dict['_project']  = (pkg_hash,'')
    publish_info.append( update_info )
    publish_info.append('</packages>')

    update_info_dir = '%s/%s/%s/%s' % (publishedhook_workspace, project[0], project[1], project[2])
    if not os.path.exists( update_info_dir ):
        os.makedirs( update_info_dir )
    update_info_file = '%s/update.xml' % (update_info_dir)
    fobj_update_info_file = open(update_info_file, 'w')
    fobj_update_info_file.writelines( ['%s%s' % ( update_info, ls ) for update_info in publish_info ] )
    fobj_update_info_file.close()

    return True

def check_base(project):
    check_flag = 0
    build_path='/srv/obs/build/%s_baseline/%s/%s/:full' %(project[0],project[1],project[2])
    repo_ppath='/srv/obs/build/%s/%s/%s/:repo' %(project[0],project[1],project[2])

    build_rpms = os.listdir( build_path )
    repos_rpms = filter( lambda x: not re.match(r'.*src\.rpm',x), os.listdir( repo_ppath ) )

    for rpm in build_rpms:
        if rpm not in repos_rpms:
           build_file=os.path.join(build_path,rpm)
           os.remove(build_file) 
           check_flag = 1
           logger.info( "check: should delete %s" % rpm )

    for rpm in repos_rpms:
        if rpm not in build_rpms:
            repo_file=os.path.join(repo_ppath,rpm)
            shutil.copy(repo_file,build_path)
            check_flag = 1
            logger.info( "check: shoud add %s" % rpm )

    if check_flag == 1:
        return False
    else:
        return True

def depends_update(project, prj_update_dict, prj_base_dict):
    diff_add_rpm = []
    diff_delete_rpm = []
    for key,value in prj_update_dict.items():
        if prj_base_dict.has_key(key):
            if value[0].decode("utf-8") == prj_base_dict[key][0]:
                continue
            else:
                ##Update add
                for rpm in value[1]:
                    if rpm not in diff_add_rpm:
                        if not re.match( r'.*src\.rpm', rpm ) and re.match( r'.*\.rpm', rpm ):
                            diff_add_rpm.append(rpm)
                            logger.info( "source change add  %s" % rpm )
                #Update del
                for rpm in prj_base_dict[key][1]:
                    if rpm not in diff_delete_rpm:
                        if not re.match( r'.*src\.rpm', rpm ) and re.match( r'.*\.rpm', rpm ):
                            diff_delete_rpm.append(rpm)
                            logger.info( "source change delete  %s" % rpm )
        #New add
        else:
            for rpm in value[1]:
                if rpm not in diff_add_rpm:
                    if not re.match( r'.*src\.rpm', rpm ) and re.match( r'.*\.rpm', rpm ):
                        diff_add_rpm.append(rpm)
                        logger.info( "new package add  %s" % rpm )

    for key, value in prj_base_dict.items():
        if prj_update_dict.has_key(key):
                continue
        #New del
        else:
            for rpm in value[1]:
                if rpm not in diff_delete_rpm:
                    if not re.match( r'.*src\.rpm', rpm ) and re.match( r'.*\.rpm', rpm ):
                        diff_delete_rpm.append(rpm)
                        logger.info( "deleted package delete  %s" % rpm )

    #global config change
    if prj_base_dict.has_key('_project') and prj_base_dict['_project'][0] != prj_update_dict['_project'][0]:
        logger.info( "%s project prjconfig or meta change" % project[0] )
        for rpm in project[3]:
            if rpm not in diff_add_rpm:
                diff_add_rpm.append(rpm)
                logger.info( "project config change update %s" % rpm )

    baseline_path = '/srv/obs/build/%s_baseline/%s/%s/:full' % ( project[0], project[1], project[2] )
    if not os.path.exists( baseline_path ):
        os.makedirs( baseline_path )

    #delete first
    for rpm in diff_delete_rpm:
        rpm_path = os.path.join( baseline_path, rpm )
        if os.path.exists( rpm_path ) and re.match( r'.*\.rpm', rpm_path ):
            os.remove( rpm_path )
    for rpm in diff_add_rpm:
        rpm_path = '/srv/obs/repos/%s/%s/%s/%s' % ( project[0].replace(':',':/'), project[1], rpm.split('.')[-2], rpm )
        base_rpm = os.path.join(baseline_path,rpm)
        if os.path.exists( base_rpm ) and re.match( r'.*\.rpm', base_rpm):
            os.remove( base_rpm )
        shutil.copy( rpm_path, baseline_path )

    update_baseline_info_dir = '%s/%s_baseline/%s/%s' %( publishedhook_workspace, project[0], project[1], project[2] )
    update_baseline_info_file = '%s/%s_baseline/%s/%s/update.xml' %( publishedhook_workspace, project[0], project[1], project[2] )
    update_info_file = '%s/%s/%s/%s/update.xml' %( publishedhook_workspace, project[0], project[1], project[2] )
    if not os.path.exists( update_baseline_info_dir ):
        os.makedirs( update_baseline_info_dir )
    shutil.copy( update_info_file, update_baseline_info_dir )

    return True

def rescan_repository(projects):
    for project in projects:
        cmd = '/usr/lib/obs/server/bs_admin --rescan-repository %s_baseline %s %s' % ( project[0], project[1], project[2] )
        logger.info( "%s" % cmd)
        ret, out, err = shell_cmd(cmd)
        if ret != 0:
            logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out, err) )
            return False

    return True

def parse_base_change( project, pkg_dict ):
    xml_file = '%s/%s_baseline/%s/%s/update.xml' %( publishedhook_workspace, project[0], project[1], project[2] )

    if not os.path.exists(xml_file):
        return True
    if os.path.isfile(xml_file) == False:
        logger.error(" %s is not a file" % xml_file )
        return False
    try:
        xmldoc = minidom.parse(xml_file)
    except:
        logger.error("Can't parse Xml File of %s." % (xml_file) )
        return False
    package = xmldoc.getElementsByTagName('package')   
    for i in range(0, len(package)):
        pkg_dict[package[i].attributes['name'].value] = (package[i].attributes['hash'].value,package[i].attributes['binary'].value.split(' '))

    return True

def update_baseline(projects):
    for project in projects:
        prj_update_dict = {}
        prj_base_dict = {}
        logger.info(" %s %s %s" % (project[0], project[1], project[2]))
        if not parse_base_change(project, prj_base_dict):
            logger.error("parse_base_change error")
            return False
        if not scan_update_change(project, prj_update_dict, prj_base_dict):
            logger.error("scan_update_change error")
            return False
        if not depends_update(project, prj_update_dict, prj_base_dict):
            logger.error("depends_update error")
            return False
        if not check_base(project):
            logger.error("check_base error")
            return False

    return True

if __name__ == '__main__':
    projects = []
    try:
        if not parse_args(sys.argv[1:]):
            raise Exception("parse_args failed")
    except Exception as ie:
        logger.info( "%s" % ie )
        ret, out, err = shell_cmd(notice_cmd)
        if ret != 0:
            logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out, err) )
            sys.exit(1)
    else:
        try:
            if not update_baseline(projects):
                raise Exception("update_baseline failed")
        except Exception as ie:
            traceback.print_exc()
            logger.info( "%s" % ie )
            ret, out, err = shell_cmd(notice_cmd)
            if ret != 0:
                logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out, err) )
                sys.exit(1)
        finally:
            if not rescan_repository(projects):
                if not rescan_repository(projects):
                    if not rescan_repository(projects):
                        ret, out, err = shell_cmd(notice_cmd)
                        if ret != 0:
                            logger.error( "run: %s : failed,the out is %s,the err is %s" % (cmd, out, err) )
                            sys.exit(1)
