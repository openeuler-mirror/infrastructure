# -*- coding: utf-8 -*-
# @Time    : 2023/4/21 15:16
# @Author  : Tom_zc
# @FileName: tc-ci.py
# @Software: PyCharm
import os
import sys

import click
import requests
import time
import re
import datetime
import traceback
from functools import wraps
from collections import defaultdict


class Errcode:
    CODE_0 = "oEEP 文件头的类型需要为：{}"
    CODE_1 = "oEEP 文件头的状态需要为：{}"
    CODE_2 = "oEEP 文件头的编号不满足格式：oEEP-xxxx"
    CODE_3 = "oEEP 文件头的创建时间不满足格式YYYY-MM-DD"
    CODE_4 = "oEEP 文件头的修改时间不满足格式YYYY-MM-DD"
    CODE_5 = "oEEP 文件头必须在文件的第一行且必须满足---***---格式"
    CODE_6 = "oEEP 文件头的字段缺少：{}"
    CODE_7 = "oEEP 文件头的字段多余：{}"


def is_datetime(value):
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


class Config:
    pr_info_url = "https://gitee.com/openeuler/TC/pulls/{}.diff"
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0"}
    header_type = ["特性变更", "信息整理", "流程设计"]
    header_status = ["初始化", "基本成型", "接纳", "活跃", "不活跃", "完成", "撤回", "拒绝", "被替代"]
    header_lambda = {
        "标题": lambda x: "",
        "类别": lambda x: "" if x in Config.header_type else Errcode.CODE_0.format(",".join(Config.header_type)),
        "摘要": lambda x: "",
        "作者": lambda x: "",
        "状态": lambda x: "" if x in Config.header_status else Errcode.CODE_1.format(",".join(Config.header_status)),
        "编号": lambda x: "" if re.match(r"oEEP-\d\d\d\d", x) else Errcode.CODE_2,
        "创建日期": lambda x: "" if is_datetime(x) else Errcode.CODE_3,
        "修订日期": lambda x: "" if is_datetime(x) else Errcode.CODE_4,
    }


def func_retry(tries=3, delay=1):
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


@func_retry(tries=3, delay=2)
def request_pr_info(url):
    ret = requests.get(url, headers=Config.header, timeout=(30, 30))
    if not str(ret.status_code).startswith("2") and not str(ret.status_code).startswith("3"):
        raise Exception("request pr info failed: {}--->{}".format(url, ret.status_code))
    else:
        return ret.content


def parse_pr_info(content):
    path_list = list()
    content = content.decode("utf-8")
    content_list = re.findall("diff --git(.*?)\n", content)
    for content in content_list:
        path = content.split("b/")[-1].strip()
        path = path.replace('"', "")
        if path.startswith("oEEP/oEEP-"):
            path_list.append(path)
    return list(set(path_list))


def check(pr_id, path):
    # 1.get relative path
    url = Config.pr_info_url.format(pr_id)
    pr_content = request_pr_info(url)
    list_file_path = parse_pr_info(pr_content)
    # 2.read file
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
        with open(cur_path, "r") as f:
            base_name = os.path.basename(cur_path)
            dict_content[base_name] = f.read()
    dict_error_result = defaultdict(list)
    for file_path, content in dict_content.items():
        file_hearder = re.match(r"---\n(.*\n)+---", content)
        if file_hearder:
            meta_data = file_hearder.group()
            exist_key = list()
            for meta in meta_data.split("\n"):
                if ":" not in meta:
                    continue
                key, value = meta.split(":")
                key, value = key.strip(), value.strip()
                msg = Config.header_lambda.get(key) and Config.header_lambda[key](value)
                if msg:
                    dict_error_result[file_path].append(msg)
                exist_key.append(key)
            need_keys = Config.header_lambda.keys()
            lack = set(need_keys) - set(exist_key)
            if lack:
                msg = Errcode.CODE_6.format(",".join(list(lack)))
                dict_error_result[file_path].append(msg)
            redundancy = set(exist_key) - set(need_keys)
            if redundancy:
                msg = Errcode.CODE_7.format(",".join(list(redundancy)))
                dict_error_result[file_path].append(msg)
        else:
            dict_error_result[file_path].append(Errcode.CODE_5)
    for file_path, err_msg in dict_error_result.items():
        print("\033[31mCheck file:{} fail!\033[0m".format(file_path))
        print("\033[31mThe reason is:{}\033[0m".format(",".join(err_msg)))
    if dict_error_result.keys():
        sys.exit(-1)


@click.command()
@click.option("--pr_id", help="the pr_id of git")
@click.option("--path", help="the path of clone object")
def main(pr_id, path):
    if not pr_id:
        raise RuntimeError("invalid pr_id")
    if not path or not os.path.exists(path):
        raise RuntimeError("invalid path")
    check(pr_id, path)


if __name__ == '__main__':
    main()

