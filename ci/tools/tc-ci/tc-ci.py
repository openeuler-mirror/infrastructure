# -*- coding: utf-8 -*-
# @Time    : 2023/4/21 15:16
# @FileName: tc-ci.py
# @Software: PyCharm
import os
import shutil
import subprocess
import sys
import click
import requests
import time
import re
import datetime
import traceback
from functools import wraps
from collections import defaultdict
from urllib.parse import unquote
from enum import Enum


class Errcode:
    CODE_0 = "oEEP 文件头的类型需要为：{}"
    CODE_1 = "oEEP 文件头的状态需要为：{}"
    CODE_2 = "oEEP 文件头的编号不满足格式：oEEP-xxxx"
    CODE_3 = "oEEP 文件头的创建时间不满足格式YYYY-MM-DD"
    CODE_4 = "oEEP 文件头的修改时间不满足格式YYYY-MM-DD"
    CODE_5 = "oEEP 文件头必须在文件的第一行且必须满足---***---格式"
    CODE_6 = "oEEP 文件头的字段缺少：{}"
    CODE_7 = "oEEP 文件头的字段多余：{}"
    CODE_8 = "oEEP-0000 oEEP  索引.md文件缺少对应PR的索引"

    def __init__(self):
        pass


def is_datetime(value):
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class GitConfig(Enum):
    work_dir = "/temp/tc/"
    group = "openeuler"
    repos = "TC"
    clone_cmd = "git clone {} {}"
    merge_cmd = "git merge --no-edit pr_{n}"
    checkout_cmd = "git checkout -b working_pr_{n}"
    fetch_cmd = "git fetch {gitee_url} pull/{n}/head:pr_{n}"
    checkout_branch_cmd = "git checkout {}"
    pull_cmd = "git pull"


class GlobalConfig(Enum):
    pr_info_url = "https://gitee.com/{}/{}/pulls/{}.diff"
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0"}
    relative_index_path = "oEEP/oEEP-0000 oEEP  索引.md"
    header_type = ["特性变更", "信息整理", "流程设计"]
    header_status = ["初始化", "基本成型", "接纳", "活跃", "不活跃", "完成", "撤回", "拒绝", "被替代"]
    header_lambda = {
        "标题": lambda x: "",
        "类别": lambda x: "" if x in GlobalConfig.header_type.value else Errcode.CODE_0.format(
            ",".join(GlobalConfig.header_type.value)),
        "摘要": lambda x: "",
        "作者": lambda x: "",
        "状态": lambda x: "" if x in GlobalConfig.header_status.value else Errcode.CODE_1.format(
            ",".join(GlobalConfig.header_status.value)),
        "编号": lambda x: "" if re.match(r"oEEP-\d\d\d\d", x) else Errcode.CODE_2,
        "创建日期": lambda x: "" if is_datetime(x) else Errcode.CODE_3,
        "修订日期": lambda x: "" if is_datetime(x) else Errcode.CODE_4,
    }


def func_retry(tries=3, delay=1):
    """retry func"""

    def deco_retry(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            for i in range(tries):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    print("func_retry:{} e:{} traceback: {}".format(fn.__name__, e, traceback.format_exc()))
                    time.sleep(delay)
            else:
                raise RuntimeError("func_retry:{} over tries, failed".format(fn.__name__))

        return inner

    return deco_retry


def execute_cmd3(cmd, timeout=30, err_log=True):
    """execute cmd"""
    try:
        print("execute_cmd3 call cmd: %s" % cmd)
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, close_fds=True)
        t_wait_seconds = 0
        while True:
            if p.poll() is not None:
                break
            if timeout >= 0 and t_wait_seconds >= (timeout * 100):
                p.terminate()
                return -1, "", "execute_cmd3 exceeded time {0} seconds in executing: {1}".format(timeout, cmd)
            time.sleep(0.01)
            t_wait_seconds += 1
        out, err = p.communicate()
        ret = p.returncode
        if ret != 0 and err_log:
            print("execute_cmd3 cmd %s return %s, std output: %s, err output: %s.", cmd, ret, out, err)
        return ret, out, err
    except Exception as e:
        return -1, "", "execute_cmd3 exceeded raise, e={0}, trace={1}".format(e.args[0], traceback.format_exc())


@func_retry(tries=3, delay=2)
def request_pr_info(url):
    """request pr info"""
    ret = requests.get(url, headers=GlobalConfig.header.value, timeout=(30, 30))
    if not str(ret.status_code).startswith("2") and not str(ret.status_code).startswith("3"):
        raise Exception("request pr info failed: {}--->{}".format(url, ret.status_code))
    else:
        return ret.content


def parse_pr_info(content):
    """Parse the PR information to be submitted"""
    path_list = list()
    content = content.decode("utf-8")
    content_list = re.findall("diff --git(.*?)\n", content)
    for content in content_list:
        path = content.split("b/")[-1].strip()
        path = path.replace('"', "")
        if path.startswith("oEEP/oEEP-") and not path.startswith("oEEP/oEEP-0000"):
            path_list.append(path)
    return list(set(path_list))


def parse_index_info(content):
    """parse index from oEEP/oEEP-0000 oEEP  索引.md"""
    try:
        content = content.split("## 索引:")[-1].split("## oEEP 类型分类：")[0].strip()
        list_title = re.findall(r"\((.*?)\)", content)
        return [unquote(title, "utf-8") for title in list_title]
    except IndexError:
        return list()


def read_content(path):
    """read content from path"""
    with open(path, "r") as f:
        return f.read()


def ci_check(pr_id, path):
    """ci check tc"""
    # 1.Get the path of the modified file from pr.diff
    print("-" * 25 + "start to parse pr-{}".format(pr_id) + "-" * 25)
    url = GlobalConfig.pr_info_url.value.format(GitConfig.group.value, GitConfig.repos.value, pr_id)
    pr_content = request_pr_info(url)
    list_file_path = parse_pr_info(pr_content)
    # 2.read content from oEEP/oEEP-0000 oEEP  索引.md
    print("-" * 25 + "start to parse oEEP/oEEP-0000 oEEP  索引.md" + "-" * 25)
    abs_index_path = os.path.join(path, GlobalConfig.relative_index_path.value)
    index_content = read_content(abs_index_path)
    list_index_path = parse_index_info(index_content)
    # 3.Read the information submitted by PR
    print("-" * 25 + "start to check pr info" + "-" * 25)
    dict_content = dict()
    for file_path in list_file_path:
        cur_path = str()
        abs_path = os.path.join(path, file_path)
        dir_name = os.path.dirname(abs_path)
        file_name = os.path.basename(abs_path)
        prefix_file_name = file_name.split(" ")[0]
        for dir_path, _, filenames in os.walk(dir_name):
            for filename in filenames:
                if filename.startswith(prefix_file_name):
                    cur_path = os.path.join(dir_path, filename)
        if not cur_path:
            print("The current path:{} is not exist.".format(file_path))
            continue
        base_name = os.path.basename(cur_path)
        dict_content[base_name] = read_content(cur_path)
    dict_error_result = defaultdict(list)
    for file_name, content in dict_content.items():
        if file_name not in list_index_path:
            dict_error_result[file_name].append(Errcode.CODE_8)
        file_hearder = re.match(r"---\n(.*\n)+---", content)
        if file_hearder:
            meta_data = file_hearder.group()
            exist_key = list()
            for meta in meta_data.split("\n"):
                if ":" not in meta:
                    continue
                key, content = meta.split(":")
                key, content = key.strip(), content.strip()
                msg = GlobalConfig.header_lambda.value.get(key) and GlobalConfig.header_lambda.value[key](content)
                if msg:
                    dict_error_result[file_name].append(msg)
                exist_key.append(key)
            need_keys = GlobalConfig.header_lambda.value.keys()
            lack = set(need_keys) - set(exist_key)
            if lack:
                msg = Errcode.CODE_6.format(",".join(list(lack)))
                dict_error_result[file_name].append(msg)
            redundancy = set(exist_key) - set(need_keys)
            if redundancy:
                msg = Errcode.CODE_7.format(",".join(list(redundancy)))
                dict_error_result[file_name].append(msg)
        else:
            dict_error_result[file_name].append(Errcode.CODE_5)
    print("-" * 25 + "start to output result" + "-" * 25)
    for file_name, err_msg in dict_error_result.items():
        print("\033[31mCheck file:{} fail!\033[0m".format(file_name))
        print("\033[31mThe reason is:{}\033[0m".format(",".join(err_msg)))
    if dict_error_result.keys():
        return True


def local_repo_name(group, repo_name, pull_id):
    """
    combine name to avoid name conflit
    """
    return "{}_{}_{}".format(group, repo_name, pull_id)


@func_retry()
def prepare_env(work_dir, group, repo_name, pull_id, local_path, branch="master"):
    """
    prepare local reposity base and PR branch
    Notice: this will change work directory,
    action related to obtain path need do before this.
    """
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    repo = group + "/" + repo_name
    gitee_url = "https://gitee.com/{repo}.git".format(repo=repo)
    if os.path.exists(local_path):
        print("WARNING: %s already exist, delete it." % local_path)
        shutil.rmtree(local_path)
    ret, out, err = execute_cmd3(GitConfig.clone_cmd.value.format(gitee_url, local_path))
    if ret != 0:
        print("Failed to git clone {}, err:{}, out:{}".format(gitee_url, err, out))
        return 1
    os.chdir(local_path)
    ret, _, _ = execute_cmd3(GitConfig.checkout_branch_cmd.value.format(branch))
    if ret != 0:
        print("Failed to checkout %s branch" % branch)
        return 1
    ret, _, _ = execute_cmd3(GitConfig.pull_cmd.value)
    if ret != 0:
        print("Failed to update to latest commit in %s branch" % branch)
        return 1
    ret, _, _ = execute_cmd3(GitConfig.fetch_cmd.value.format(gitee_url=gitee_url, n=pull_id))
    if ret != 0:
        print("Failed to fetch PR:{n}".format(n=pull_id))
        return 1
    ret, _, _ = execute_cmd3(GitConfig.checkout_cmd.value.format(n=pull_id))
    if ret != 0:
        print("Failed to create working branch working_pr_{n}".format(n=pull_id))
        return 1
    ret, _, _ = execute_cmd3(GitConfig.merge_cmd.value.format(n=pull_id))
    if ret != 0:
        print("Failed to merge PR:{n} to branch:{base}".format(n=pull_id, base=branch))
        return 1
    return 0


@click.command()
@click.option("--pr_id", help="the pr_id of git")
def main(pr_id):
    if not pr_id:
        raise RuntimeError("invalid pr_id")
    work_dir = GitConfig.work_dir.value
    group = GitConfig.group.value
    repo_name = GitConfig.repos.value
    local_repo_path = local_repo_name(group, repo_name, pr_id)
    local_path = os.path.join(work_dir, local_repo_path)
    result = prepare_env(work_dir, group, repo_name, pr_id, local_path)
    if result:
        print("prepare env failed")
        sys.exit(-1)
    result = ci_check(pr_id, local_path)
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    if result:
        sys.exit(-1)


if __name__ == '__main__':
    main()

