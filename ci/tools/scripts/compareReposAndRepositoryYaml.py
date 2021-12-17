#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
A script to check consistency of repos and branches between config yaml and query results through the interfaces. The
script shows issues and exits abnormally when the differences exists.
"""
import argparse
import json
import os
import requests
import sys
import tempfile
import time
import yaml
from multiprocessing.dummy import Pool as ThreadPool


def get_openeuler_repos():
    """分页获取openeuler的所有仓库"""
    page = 1
    o_repos = []
    while page < 999:
        url = 'https://gitee.com/api/v5/orgs/openeuler/repos'
        params = {
            'type': 'all',
            'page': page,
            'per_page': 100,
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if len(response.json()) == 0:
            break
        try:
            for repo in response.json():
                o_repos.append(repo['path'])
            print('Get openeuler repos: 第{}页获取完毕!'.format(page))
        except json.decoder.JSONDecodeError:
            return o_repos
        page += 1
    return o_repos


def get_src_openeuler_repos():
    """分页获取src-openeuler的所有仓库"""
    page = 1
    src_repos = []
    while page < 999:
        url = 'https://gitee.com/api/v5/orgs/src-openeuler/repos'
        params = {
            'type': 'all',
            'page': page,
            'per_page': 100,
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if len(response.json()) == 0:
            break
        try:
            for repo in response.json():
                src_repos.append(repo['path'])
            print('Get src-openeuler repos: 第{}页获取完毕!'.format(page))
        except json.decoder.JSONDecodeError:
            return src_repos
        page += 1
    return src_repos


def get_repo_branches(repo):
    """获取仓库所有分支和所有保护分支"""
    url = 'https://gitee.com/api/v5/repos/{}/branches?access_token={}'.format(repo, access_token)
    r = requests.get(url)
    repo_branches = [x['name'] for x in r.json()]
    repo_protected_branches = [x['name'] for x in r.json() if x['protected']]
    return repo_branches, repo_protected_branches


def check_repos_consistency(issues):
    """检查仓库一致性"""
    print('=' * 20 + ' Check repos consistency ' + '=' * 20)
    openeuler_repos = get_openeuler_repos()  # api获取的openeuler所有仓库
    src_openeuler_repos = get_src_openeuler_repos()  # api获取的src-openeuler所有仓库

    openeuler_yaml_repos = []  # openeuler.yaml中的所有仓库
    openueler_rename_repos = []  # openeuler.yaml中被重命名的所有仓库
    for r in o_yaml:
        openeuler_yaml_repos.append(r['name'])
        if 'rename_from' in r.keys():
            openueler_rename_repos.append(r['rename_from'])

    src_openeuler_yaml_repos = []  # src-openeuler.yaml中的所有仓库
    src_openeuler_rename_repos = []  # src-openeuler.yaml中被重命名的所有仓库
    for r in src_yaml:
        src_openeuler_yaml_repos.append(r['name'])
        if 'rename_from' in r.keys():
            src_openeuler_rename_repos.append(r['rename_from'])
    # 对比当前所有仓库与yaml中所有仓库的差异
    openeuler_extra_repos = []  # 不在openeuler.yaml中的所有仓库
    src_openeuler_extra_repos = []  # 不在src-openeuler.yaml中的所有仓库
    openeuler_non_existed_repos = []  # 在openeuler.yaml中但不存在的仓库
    src_openeuler_non_existed_repos = []  # 在src-openeuler.yaml中但不存在的仓库

    for openeuler_repo in openeuler_repos:
        if openeuler_repo not in openeuler_yaml_repos:
            openeuler_extra_repos.append(openeuler_repo)
    for src_openeuler_repo in src_openeuler_repos:
        if src_openeuler_repo not in src_openeuler_yaml_repos:
            src_openeuler_extra_repos.append(src_openeuler_repo)
    for openeuler_yaml_repo in openeuler_yaml_repos:
        if openeuler_yaml_repo not in openeuler_repos:
            openeuler_non_existed_repos.append(openeuler_yaml_repo)
    for src_openeuler_yaml_repo in src_openeuler_yaml_repos:
        if src_openeuler_yaml_repo not in src_openeuler_repos:
            src_openeuler_non_existed_repos.append(src_openeuler_yaml_repo)
    # 找出仍存在的rename_from仓库
    openeuler_rename_from_still_exist_repos = []  # openeuler.yaml中被重命名但仍存在的所有仓库
    src_openeuler_rename_from_still_exist_repos = []  # src-openeuler.yaml中被重命名但仍存在的所有仓库
    for r in openueler_rename_repos:
        if r in openeuler_extra_repos:
            openeuler_rename_from_still_exist_repos.append(r)
    for r in src_openeuler_rename_repos:
        if r in src_openeuler_extra_repos:
            src_openeuler_rename_from_still_exist_repos.append(r)
    if len(openeuler_extra_repos) != 0:
        print('ERROR! 检查出不在openeuler.yaml中的仓库: {}'.format(openeuler_extra_repos))
        issues += 1
    if len(src_openeuler_extra_repos) != 0:
        print('ERROR! 检查出不在src-openeuler.yaml中的仓库: {}'.format(src_openeuler_extra_repos))
        issues += 1
    if len(openeuler_non_existed_repos) != 0:
        print('ERROR! 检查出在openeuler.yaml中但不存在的仓库: {}'.format(openeuler_non_existed_repos))
        issues += 1
    if len(src_openeuler_non_existed_repos) != 0:
        print('ERROR! 检查出在src-openeuler.yaml中但不存在的仓库: {}'.format(src_openeuler_non_existed_repos))
        issues += 1
    if len(openeuler_rename_from_still_exist_repos) != 0:
        print('WARNING! openeuler.yaml中有被重命名但仍存在的仓库: {}'.format(openeuler_rename_from_still_exist_repos))
    if len(src_openeuler_rename_from_still_exist_repos) != 0:
        print('WARNING! src-openeuler.yaml中有被重命名但仍存在仓库: {}'.format(src_openeuler_rename_from_still_exist_repos))
    return issues


def get_sig_name(repo):
    """获取仓库所属sig"""
    for sig in sigs:
        if repo in sig['repositories']:
            return sig['name']


def check_euler_branches(openeuler_repo):
    """openeuler.yaml中仓库的分支一致性检查"""
    branches_issues = 0
    not_exist_branches = []
    not_configured_branches = []
    not_protected_branches = []
    repo_full_name = os.path.join('openeuler', openeuler_repo['name'])
    yaml_branches = [x['name'] for x in openeuler_repo['branches']]
    repo_branches, repo_protected_branches = get_repo_branches(repo_full_name)
    for branch in yaml_branches:
        if branch not in repo_branches:
            not_exist_branches.append(branch)
        elif branch not in repo_protected_branches:
            not_protected_branches.append(branch)
    for branch in repo_protected_branches:
        if branch not in yaml_branches:
            not_configured_branches.append(branch)
    if not_exist_branches or not_configured_branches or not_protected_branches:
        sig_name = get_sig_name(repo_full_name)
        if not_exist_branches:
            print('ERROR! 配置多，仓库少 [{}]{}: {}'.format(sig_name, repo_full_name, not_exist_branches))
            branches_issues += 1
        if not_configured_branches:
            print('ERROR! 仓库多，配置少 [{}]{}: {}'.format(sig_name, repo_full_name, not_configured_branches))
            branches_issues += 1
        if not_protected_branches:
            print('ERROR! 非保护分支 [{}]{}: {}'.format(sig_name, repo_full_name, not_protected_branches))
            branches_issues += 1
    return branches_issues


def check_src_euler_branches(src_openeuler_repo):
    """src-openeuler.yaml中仓库的分支一致性检查"""
    branches_issues = 0
    not_exist_branches = []
    not_configured_branches = []
    not_protected_branches = []
    repo_full_name = os.path.join('src-openeuler', src_openeuler_repo['name'])
    yaml_branches = [x['name'] for x in src_openeuler_repo['branches']]
    repo_branches, repo_protected_branches = get_repo_branches(repo_full_name)
    for branch in yaml_branches:
        if branch not in repo_branches:
            not_exist_branches.append(branch)
        elif branch not in repo_protected_branches:
            not_protected_branches.append(branch)
    for branch in repo_protected_branches:
        if branch not in yaml_branches:
            not_configured_branches.append(branch)
    if not_exist_branches or not_configured_branches or not_protected_branches:
        sig_name = get_sig_name(repo_full_name)
        if not_exist_branches:
            print('ERROR! 配置多，仓库少 [{}]{}: {}'.format(sig_name, repo_full_name, not_exist_branches))
            branches_issues += 1
        if not_configured_branches:
            print('ERROR! 仓库多，配置少 [{}]{}: {}'.format(sig_name, repo_full_name, not_configured_branches))
            branches_issues += 1
        if not_protected_branches:
            print('ERROR! 非保护分支 [{}]{}: {}'.format(sig_name, repo_full_name, not_protected_branches))
            branches_issues += 1
    return branches_issues


def check_branch_consistency():
    print('=' * 20 + ' Check branches consistency ' + '=' * 20)
    pool = ThreadPool(50)
    res1 = pool.map(check_euler_branches, o_yaml)
    pool.close()
    pool.join()
    pool2 = ThreadPool(50)
    res2 = pool2.map(check_src_euler_branches, src_yaml)
    pool2.close()
    pool2.join()
    branches_issues = len(res1) - res1.count(0) + len(res2) - res2.count(0)
    return branches_issues


def check_recycle_repos_status():
    print('=' * 20 + ' Check recycle repos status ' + '=' * 20)
    repos = []
    for sig in sigs:
        if sig['name'] == 'sig-recycle':
            repos = sig['repositories']
    error_count = 0
    for repo in repos:
        r = requests.get('https://gitee.com/api/v5/repos/{}?access_token={}'.format(repo, access_token))
        if r.status_code == 200:
            status = r.json()['status']
            print('{}的仓库状态为{}'.format(repo, status))
            if status == '开始' or status == 'Started':
                error_count += 1
    return error_count


def main():
    issues = 0
    issues += check_repos_consistency(issues)
    t3 = time.time()
    print('Check repos consistency wasted time: {}\n'.format(t3 - t2))
    issues += check_branch_consistency()
    t4 = time.time()
    print('Check branches consistency wasted time: {}\n'.format(t4 - t3))
    issues += check_recycle_repos_status()
    t5 = time.time()
    print('Check recycle repos status wasted time: {}\n'.format(t5 - t4))
    print('Total waste: {}'.format(t5 - t1))
    # 删除临时目录
    os.system('rm -rf {}/{}'.format(tmpdir, timestamp))
    print('Clean up temporary clone directory.')

    if issues != 0:
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', help='access_token', required=True)
    args = parser.parse_args()
    access_token = args.token
    t1 = time.time()
    print('=' * 20 + 'Prepare' + '=' * 20)
    tmpdir = tempfile.gettempdir()
    timestamp = int(t1)
    os.system(
        'cd {0};'
        'mkdir {1};'
        'cd {1} && echo "Temporary clone directory is $(pwd)";'
        'git clone https://gitee.com/openeuler/community.git'.format(tmpdir, timestamp))
    o_yaml_path = '{}/{}/community/repository/openeuler.yaml'.format(tmpdir, timestamp)
    src_yaml_path = '{}/{}/community/repository/src-openeuler.yaml'.format(tmpdir, timestamp)
    yaml_repos_path = '{}/{}/community/sig/sigs.yaml'.format(tmpdir, timestamp)
    print('\nReading {}'.format(o_yaml_path))
    with open(o_yaml_path, 'r') as f:
        o_yaml = yaml.load(f.read(), Loader=yaml.Loader)['repositories']
    print('Reading {}'.format(src_yaml_path))
    with open(src_yaml_path, 'r') as f:
        src_yaml = yaml.load(f.read(), Loader=yaml.Loader)['repositories']
    with open(yaml_repos_path, 'r') as f:
        sigs = yaml.load(f.read(), Loader=yaml.Loader)['sigs']
    t2 = time.time()
    print('Prepare wasted time: {}\n'.format(t2 - t1))
    main()

