# -*- coding: utf-8 -*-
"""
A script to compare and get differences between current repositories and openeuler.yaml/src-openeuler.yaml, also show
rename_from repos and existing rename_from repos.
"""
import argparse
import json
import os
import requests
import sys
import tempfile
import time
import yaml


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


def main():
    tmpdir = tempfile.gettempdir()
    timestamp = int(time.time())
    os.system('cd {0}; mkdir {1}; cd {1}; git clone https://gitee.com/openeuler/community.git'.format(tmpdir, timestamp))
    openeuler_repos = get_openeuler_repos()  # api获取的openeuler所有仓库
    src_openeuler_repos = get_src_openeuler_repos()  # api获取的src-openeuler所有仓库
    with open('{}/{}/community/repository/openeuler.yaml'.format(tmpdir, timestamp), 'r') as f:
        o_yaml = yaml.load(f.read(), Loader=yaml.Loader)['repositories']
    openeuler_yaml_repos = []  # openeuler.yaml中的所有仓库
    openueler_rename_repos = []  # openeuler.yaml中被重命名的所有仓库
    for r in o_yaml:
        openeuler_yaml_repos.append(r['name'])
        if 'rename_from' in r.keys():
            openueler_rename_repos.append(r['rename_from'])
    with open('{}/{}/community/repository/src-openeuler.yaml'.format(tmpdir, timestamp), 'r') as f:
        src_yaml = yaml.load(f.read(), Loader=yaml.Loader)['repositories']
    os.system('rm -rf {}/{}'.format(tmpdir, timestamp))
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
    data = {
        '不在openeuler.yaml中的仓库': openeuler_extra_repos,
        '不在src-openeuler.yaml中的仓库': src_openeuler_extra_repos,
        '在openeuler.yaml中但不存在的仓库': openeuler_non_existed_repos,
        '在src-openeuler.yaml中但不存在的仓库': src_openeuler_non_existed_repos,
        'openeuler.yaml中被重命名的所有仓库': openueler_rename_repos,
        'src-openeuler.yaml中被重命名的所有仓库': src_openeuler_rename_repos,
        'openeuler.yaml中被重命名但仍存在的所有仓库': openeuler_rename_from_still_exist_repos,
        'src-openeuler.yaml中被重命名但仍存在的所有仓库': src_openeuler_rename_from_still_exist_repos
    }
    print(data)
    # 删除临时目录
    os.system('rm -rf {}/{}'.format(tmpdir, timestamp))

    issues = 0
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
    if issues != 0:
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', help='access_token', required=True)
    args = parser.parse_args()
    access_token = args.token
    main()

