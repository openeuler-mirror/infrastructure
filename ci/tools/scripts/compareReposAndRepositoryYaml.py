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
    oe_repos = []
    while True:
        repos_by_page = get_repos_by_page('openeuler', page)
        if not repos_by_page:
            return oe_repos
        oe_repos.extend(repos_by_page)
        page += 1
    return o_repos


def get_src_openeuler_repos():
    """分页获取src-openeuler的所有仓库"""
    page = 1
    soe_repos = []
    while True:
        repos_by_page = get_repos_by_page('src-openeuler', page)
        if not repos_by_page:
            return soe_repos
        soe_repos.extend(repos_by_page)
        page += 1
    return soe_repos


def get_repos_by_page(org, page):
    """按页获取组织的仓库"""
    print('Get {} repos by page: {}'.format(org, page))
    url = 'https://gitee.com/api/v5/orgs/{}/repos'.format(org)
    params = {
        'type': 'all',
        'page': page,
        'per_page': 100,
        'access_token': access_token
    }
    res = []
    try:
        r = requests.get(url, params=params)
        if r.status_code != 200:
            time.sleep(10)
            get_repos_by_page(org, page)
        if len(r.json()) == 0:
            return res
        for repo in r.json():
            res.append(repo['path'])
        return res
    except:
        time.sleep(10)
        get_repos_by_page(org, page)


def get_repo_branches(repository):
    """获取仓库所有分支和所有保护分支"""
    url = 'https://gitee.com/api/v5/repos/{}/branches?access_token={}'.format(repository, access_token)
    try:
        r = requests.get(url)
        if r.status_code != 200:
            time.sleep(10)
            get_repo_branches(repository)
        repo_branches = [x['name'] for x in r.json()]
        repo_protected_branches = [x['name'] for x in r.json() if x['protected']]
        return repo_branches, repo_protected_branches
    except:
        time.sleep(10)
        get_repo_branches(repository)


def check_repos_consistency(issues):
    """检查仓库一致性"""
    print('=' * 20 + ' Check repos consistency ' + '=' * 20)
    openeuler_repos = get_openeuler_repos()  # api获取的openeuler所有仓库
    src_openeuler_repos = get_src_openeuler_repos()  # api获取的src-openeuler所有仓库
    print(len(openeuler_repos), len(src_openeuler_repos))

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


def get_sig_name(repository):
    """获取仓库所属sig"""
    for s in sigs:
        if repository in s['repositories']:
            return s['name']


def convert_branch_name_string(branch_name_list):
    """将有数字的分支名转换为字符串"""
    return [str(branch_name) if isinstance(branch_name, (int, float)) else branch_name
            for branch_name in branch_name_list]


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
    yaml_branches = convert_branch_name_string(yaml_branches)
    try:
        repo_branches, repo_protected_branches = get_repo_branches(repo_full_name)
    except:
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
    yaml_branches = convert_branch_name_string(yaml_branches)
    try:
        repo_branches, repo_protected_branches = get_repo_branches(repo_full_name)
    except:
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
    pool = ThreadPool(10)
    res1 = pool.map(check_euler_branches, o_yaml)
    pool.close()
    pool.join()
    pool2 = ThreadPool(10)
    res2 = pool2.map(check_src_euler_branches, src_yaml)
    pool2.close()
    pool2.join()
    branches_issues = len(res1) - res1.count(0) + len(res2) - res2.count(0)
    return branches_issues


def check_recycle_repos_status():
    """检查recycle仓库的状态"""
    print('=' * 20 + ' Check recycle repos status ' + '=' * 20)
    recycle_repos = []
    for s in sigs:
        if s['name'] == 'sig-recycle':
            recycle_repos = s['repositories']
    error_count = 0
    for repository in recycle_repos:
        r = requests.get('https://gitee.com/api/v5/repos/{}?access_token={}'.format(repository, access_token))
        if r.status_code == 200:
            status = r.json()['status']
            if status != '关闭' and status != 'Closed' and status != 'closed':
                print('{}的仓库状态为{}'.format(repository, status))
                error_count += 1
        else:
            print(
                'Failed to get information about repository {}, status_code: {}, reason: {}'.format(repository,
                                                                                                    r.status_code,
                                                                                                    r.json()))
    return error_count


def get_repository_members(repository):
    """获取一个仓库所有成员的gitee_id列表"""
    members = []
    page = 1
    while True:
        members_by_page = get_members_by_page(repository, page)
        if not members_by_page:
            return members
        for member in members_by_page:
            if member.lower() not in members:
                members.append(member.lower())
        page += 1


def get_members_by_page(repository, page):
    res = []
    url = 'https://gitee.com/api/v5/repos/{}/collaborators'.format(repository)
    params = {
        'access_token': access_token,
        'page': page,
        'per_page': 100
    }
    try:
        r = requests.get(url, params=params)
        if r.status_code != 200:
            time.sleep(10)
            get_members_by_page(repository, page)
        if not r.json():
            return res
        for member in r.json():
            gitee_id = member['login']
            res.append(gitee_id)
        return res
    except:
        time.sleep(10)
        get_members_by_page(repository, page)


def check_members():
    """检查仓库成员一致性"""
    print('=' * 20 + ' Check members consistency ' + '=' * 20)
    errors_found = 0
    for s in sigs:
        sig_name = s['name']
        if sig_name == 'sig-recycle':
            continue
        sig_repositories = s['repositories']
        owners_path = os.path.join(sig_path, sig_name, 'OWNERS')
        if os.path.exists(owners_path):
            with open(owners_path, 'r') as fp:
                maintainers = yaml.load(fp.read(), Loader=yaml.Loader)['maintainers']
        else:
            sig_info_file = os.path.join(sig_path, sig_name, 'sig-info.yaml')
            with open(sig_info_file, 'r') as fp:
                sig_info = yaml.load(fp.read(), Loader=yaml.Loader)
                owners = sig_info['maintainers']
                if owners:
                    maintainers = [maintainer['gitee_id'] for maintainer in owners]
        for repository in sig_repositories:
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


def update_repo_label(repository, label):
    url = 'https://gitee.com/api/v5/repos/{}/project_labels?access_token={}'.format(repository, access_token)
    data = json.dumps(["{}".format(label)])
    errors = 0
    try:
        res = requests.put(url, data=data)
        if res.status_code != 200:
            print('Failed to update label! sig: {}, repo: {}, status_code: {}'.format(label,
                                                                                      repository,
                                                                                      res.status_code))
            errors += 1
    except ConnectionError as e:
        print('ConnectionError! sig: {}, repo: {}'.format(label, repository))
        print(e)
        errors += 1
    except OSError as e2:
        print('OSError! sig: {}, repo: {}'.format(label, repository))
        print(e2)
        errors += 1
    return errors


def update_all_repos_label():
    print('=' * 20 + ' Update all repos label ' + '=' * 20)
    update_label_errors = 0
    for s in sigs:
        sig_name = s['name']
        if sig_name == 'sig-recycle':
            continue
        sig_repos = s['repositories']
        for sig_repo in sig_repos:
            update_label_errors += update_repo_label(sig_repo, sig_name)
    return update_label_errors


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

    weekday = datetime.datetime.today().isoweekday()
    if weekday == 6:
        issues += update_all_repos_label()
    t7 = time.time()
    print('Update all repos label: {}\n'.format(t7 - t6))
    print('Total waste: {}'.format(t7 - t1))
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
        if i in ['README.md', 'sig-template', 'create_sig_info_template.py']:
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
