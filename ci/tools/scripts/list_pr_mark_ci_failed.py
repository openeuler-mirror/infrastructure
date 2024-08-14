# coding: utf-8
# 版权所有（c）华为技术有限公司 2012-2024
"""
在 openEuler 发版本之前，统计 openEuler 社区的 PR 数据

数据范围：针对 openEuler 的制品仓 src-openeuler 下的仓库的 PR 数据
过滤条件：1. 仓库必须含有版本名称的分支，例如 版本 openEuler 22.03 LTS SP4 分支名称 openEuler-22.03-LTS-SP4
        2. PR 的合入分支是版本分支
        3. PR 的标签含有 ci_failed

执行：python list_pr_mark_ci_failed.py 组织名称(eg. src-openeuler) GiteeToken Release版本名称(eg. openEuler-22.03-LTS-SP4)
输出结果：两个文件，在当前文件夹下 ./dist/list_pr_mark_ci_failed/
        1. *.txt 存储组织下的仓库
        2. result_*.csv 存储统计的 PR 数据，数据格式：组织名, 仓库名, PR地址, PR状态

对于输出的 csv 文件，需要手动导入 excel 处理
"""

import json
import os
import csv
import sys
import time
import urllib.request
from urllib import error

_gitee_base_api_uri = 'https://gitee.com/api/v5/'
_req_method_get = 'GET'

_gitee_org_repos = ['' for _ in range(1024 * 100)]
_gitee_org_repos_size = 0
_gitee_token = ''
_org_name = ''
_release_version_name = ''
_storge_file_path = ''

_headers = {
    'Content-type': 'application-json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}


def do_req_collect_repo():
    """
    分页查询收集组织下的仓库
    """
    global _org_name, _gitee_token, _headers, _gitee_org_repos, _gitee_org_repos_size

    flag = True
    page_no = 1
    while flag:
        query = '?access_token=' + _gitee_token + '&page=' + str(page_no) + '&per_page=100'
        req_url = _gitee_base_api_uri + 'orgs/' + _org_name + '/repos' + query
        req = urllib.request.Request(url=req_url, headers=_headers, method=_req_method_get)
        with urllib.request.urlopen(req) as res:
            data = res.read().decode('utf-8')  # str
            repo = json.loads(data)  # list [dict...]
            repo_size = len(repo)
            for i in range(repo_size):
                _gitee_org_repos[_gitee_org_repos_size] = repo[i]['full_name']
                _gitee_org_repos_size = _gitee_org_repos_size + 1
            flag = data != '[]'
            print('正在收集仓库，每次请求收集 100 个，当前仓库数: ' + str(_gitee_org_repos_size))
            page_no = page_no + 1


def do_req_check_branch_exists(path: str):
    """
    检查仓库是否存在 Release 版本分支
    """
    query = '?access_token=' + _gitee_token
    req_url = _gitee_base_api_uri + 'repos/' + path + '/branches/' + _release_version_name + query
    req = urllib.request.Request(url=req_url, headers=_headers, method=_req_method_get)
    try:
        with urllib.request.urlopen(req) as res:
            _ = res.read()
    except error.HTTPError:
        branch_exist = False
    except error.URLError:
        branch_exist = False
    else:
        branch_exist = True
    return branch_exist


_ci_failed_pr = [['', '', '', ''] for _ in range(1024 * 100)]
_ci_failed_pr_size = 0


def do_req_collect_pr_mark_ci_failed(path: str):
    """
    分页查询仓库的 Release 版本分支相关联的 PR，并且 PR 带 ci_failed 标签
    """
    page_no = 1
    global _ci_failed_pr, _ci_failed_pr_size
    flag = True
    while flag:
        query = '?access_token=' + _gitee_token + '&page=' + str(
            page_no) + '&per_page=100&labels=ci_failed&state=all&base=' + _release_version_name
        req_url = _gitee_base_api_uri + 'repos/' + path + '/pulls' + query
        req = urllib.request.Request(url=req_url, headers=_headers, method=_req_method_get)
        with urllib.request.urlopen(req) as res:
            data = res.read().decode('utf-8')  # str
            pr = json.loads(data)  # list [dict...]
            pr_size = len(pr)
            if pr_size > 0:
                j = 0
                while j < pr_size:
                    pr_detail = pr[j]
                    _ci_failed_pr[_ci_failed_pr_size][0] = path.split('/')[0]
                    _ci_failed_pr[_ci_failed_pr_size][1] = path.split('/')[1]
                    _ci_failed_pr[_ci_failed_pr_size][2] = pr_detail['html_url']
                    _ci_failed_pr[_ci_failed_pr_size][3] = pr_detail['state']
                    _ci_failed_pr_size += 1
                    j += 1
                flag = True
                page_no += 1
            else:
                flag = False


if __name__ == '__main__':
    args_len = len(sys.argv)

    if args_len != 4:
        sys.exit('请输入正确的参数: python list_pr_mark_ci_failed.py 组织名称(eg. src-openeuler) GiteeToken Release版本名称(eg. openEuler-22.03-LTS-SP4)')

    exec_py = sys.argv[0]
    dir_path = '.' + os.sep + 'dist' + os.sep
    _storge_file_path = dir_path + exec_py[:-3].split(os.sep)[-1]
    print('文件输出Dir: ' + _storge_file_path)
    if not os.path.exists(_storge_file_path):
        os.mkdir(_storge_file_path)

    _org_name = sys.argv[1]
    if len(_org_name) == 0:
        sys.exit('请输入正确的组织名称')
    print('组织名称: ' + _org_name)

    _gitee_token = sys.argv[2]
    if len(_gitee_token) == 0:
        sys.exit('请输入正确的 Gitee Token')
    print('Gitee Token: ' + _gitee_token)

    _release_version_name = sys.argv[3]
    if len(_release_version_name) == 0:
        sys.exit('请输入正确的 Release 版本名称（空格需要替换成中划线，如：openEuler-22.03-LTS-SP4）')
    print('Release 版本名称: ' + _release_version_name)

    start_time = time.time()

    repo_file_path = _storge_file_path + os.sep + _org_name + '_repo_' + time.strftime('%Y%m%d',
                                                                                       time.localtime()) + '.txt'
    if not os.path.isfile(repo_file_path):
        print('开始收集组织下的仓库列表')
        do_req_collect_repo()
        with open(repo_file_path, 'w+') as repo_file_path_out:
            repo_file_path_out.write(json.dumps(_gitee_org_repos[:_gitee_org_repos_size], indent=2))
        print('完成收集组织下的仓库列表，输出文件：' + repo_file_path)
    else:
        print('当前已经收集过组织下的仓库，不必重复收集。如果要再次收集，请删除文件：' + repo_file_path + ' 后，再重新执行')

    with open(repo_file_path, 'r') as repo_file_path_in:
        list_repo_release = json.load(repo_file_path_in)
        length_list_repo_release = len(list_repo_release)
        i = 0
        while i < length_list_repo_release:
            if i % 50 == 0:
                print('正在收集带 ci_failed 标签 的 PR，仓库总共 ' + str(
                    length_list_repo_release) + ' 个，当前正在进行第 ' + str(i + 1) + ' 个')
            if do_req_check_branch_exists(list_repo_release[i]):
                do_req_collect_pr_mark_ci_failed(list_repo_release[i])
            i += 1

    result = _storge_file_path + os.sep + 'result_' + time.strftime('%Y%m%d-%H%M%S', time.localtime()) + '.csv'
    if os.path.isfile(result):
        os.remove(result)
    with open(result, 'w+', encoding='utf-8', newline='') as result_out:
        result_writer = csv.writer(result_out)
        result_writer.writerow(['组织名', '仓库名', 'PR地址', 'PR状态'])
        result_writer.writerows(_ci_failed_pr[:_ci_failed_pr_size])

    print(f'cost:{time.time() - start_time:.4f}s')
    print('完成收集工作，最终结果输出文件：' + result)
