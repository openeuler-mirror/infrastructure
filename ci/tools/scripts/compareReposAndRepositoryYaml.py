#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
A script to check consistency of repos and branches between config yaml and query results through the interfaces. The
script shows issues and exits abnormally when the differences exists.
"""
import argparse
import datetime
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
        print('ERROR! 检查出不在community中的openeuler仓库: {}'.format(openeuler_extra_repos))
        issues += 1
    if len(src_openeuler_extra_repos) != 0:
        print('ERROR! 检查出不在community中的src-openeuler仓库: {}'.format(src_openeuler_extra_repos))
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
    sig_name = get_sig_name(repo_full_name)
    if sig_name == 'sig-recycle':
        return branches_issues
    yaml_branches = [x['name'] for x in openeuler_repo['branches']]
    try:
        repo_branches, repo_protected_branches = get_repo_branches(repo_full_name)
    except OSError:
        return branches_issues
    for branch in yaml_branches:
        if branch not in repo_branches:
            not_exist_branches.append(branch)
        elif branch not in repo_protected_branches:
            not_protected_branches.append(branch)
    for branch in repo_protected_branches:
        if branch not in yaml_branches:
            not_configured_branches.append(branch)
    if not_exist_branches or not_configured_branches or not_protected_branches:
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
    sig_name = get_sig_name(repo_full_name)
    if sig_name == 'sig-recycle':
        return branches_issues
    yaml_branches = [x['name'] for x in src_openeuler_repo['branches']]
    try:
        repo_branches, repo_protected_branches = get_repo_branches(repo_full_name)
    except OSError:
        return branches_issues
    for branch in yaml_branches:
        if branch not in repo_branches:
            not_exist_branches.append(branch)
        elif branch not in repo_protected_branches:
            not_protected_branches.append(branch)
    for branch in repo_protected_branches:
        if branch not in yaml_branches:
            not_configured_branches.append(branch)
    if not_exist_branches or not_configured_branches or not_protected_branches:
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
    """检查分支一致性"""
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
    """检查recycle仓库的状态"""
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
            if status != '关闭' and status != 'Closed' and status != 'closed':
                print('{}的仓库状态为{}'.format(repo, status))
                error_count += 1
        else:
            print(
                'Failed to get information about repository {}, status_code: {}, reason: {}'.format(repo, r.status_code,
                                                                                                    r.json()))
    return error_count


def get_repository_members(repository):
    """获取一个仓库所有成员的gitee_id列表"""
    members = []
    page = 1
    url = 'https://gitee.com/api/v5/repos/{}/collaborators'.format(repository)
    while True:
        params = {
            'access_token': access_token,
            'page': page,
            'per_page': 100
        }
        r = requests.get(url, params=params)
        if r.status_code != 200:
            print('ERROR! Fail to get members of repo {}'.format(repository))
            print(r.status_code, r.json())
            return members
        if not r.json():
            break
        for member in r.json():
            gitee_id = member['login']
            members.append(gitee_id)
        page += 1
    return [member.lower() for member in members]


def check_members():
    """检查仓库成员一致性"""
    print('=' * 20 + ' Check members consistency ' + '=' * 20)
    errors_found = 0
    for sig in sigs:
        sig_name = sig['name']
        if sig_name == 'sig-recycle':
            continue
        repositories = sig['repositories']
        owners_path = os.path.join(sig_path, sig_name, 'OWNERS')
        with open(owners_path, 'r') as fp:
            maintainers = yaml.load(fp.read(), Loader=yaml.Loader)['maintainers']
        for repository in repositories:
            try:
                members = get_repository_members(repository)
            except OSError:
                continue
            for maintainer in maintainers:
                if maintainer.lower() not in members:
                    errors_found += 1
                    print('ERROR! Found maintainer {} of sig {} is not a member of repository {}'.format(
                        maintainer, sig_name, repository
                    ))
    print('Check members issues: {}'.format(errors_found))
    return errors_found


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

    date = int(datetime.datetime.now().strftime('%d'))
    # 控制仓库成员一致性检查执行的间隔
    if date % 2 != 0:
        issues += check_members()
    t6 = time.time()
    print('Check members consistency wasted time: {}\n'.format(t6 - t5))
    print('Total waste: {}'.format(t6 - t1))
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
    print('=' * 20 + ' Prepare ' + '=' * 20)
    tmpdir = tempfile.gettempdir()
    timestamp = int(t1)
    os.system(
        'cd {0};'
        'mkdir {1};'
        'cd {1} && echo "Temporary clone directory is $(pwd)";'
        'git clone https://gitee.com/openeuler/community.git'.format(tmpdir, timestamp))
    sig_path = os.path.join(tmpdir, str(timestamp), 'community', 'sig')
    o_yaml = []
    src_yaml = []
    sigs = []
    for i in os.listdir(sig_path):
        if i in ['README.md', 'sig-template']:
            continue
        if i not in [x['name'] for x in sigs]:
            sigs.append({'name': i, 'repositories': []})
        if 'openeuler' in os.listdir(os.path.join(sig_path, i)):
            for filesdir, _, repos in os.walk(os.path.join(sig_path, i, 'openeuler')):
                for repo in repos:
                    with open(os.path.join(filesdir, repo)) as f:
                        config_info = yaml.load(f.read(), Loader=yaml.Loader)
                        o_yaml.append(config_info)
                        for sig in sigs:
                            if sig['name'] == i:
                                repositories = sig['repositories']
                                repositories.append(os.path.join('openeuler', repo.split('.yaml')[0]))
        if 'src-openeuler' in os.listdir(os.path.join(sig_path, i)):
            for filesdir, _, src_repos in os.walk(os.path.join(sig_path, i, 'src-openeuler')):
                for src_repo in src_repos:
                    with open(os.path.join(filesdir, src_repo), 'r') as f:
                        src_config_info = yaml.load(f.read(), Loader=yaml.Loader)
                        src_yaml.append(src_config_info)
                        for sig in sigs:
                            if sig['name'] == i:
                                repositories = sig['repositories']
                                repositories.append(os.path.join('src-openeuler', src_repo.split('.yaml')[0]))
    t2 = time.time()
    print('Prepare wasted time: {}\n'.format(t2 - t1))
    main()

