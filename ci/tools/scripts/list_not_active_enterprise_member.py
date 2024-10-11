# coding: utf-8
# 版权所有（c）华为技术有限公司 2012-2024
"""
在 openEuler 企业成员的活跃度

数据范围：针对 openEuler 企业成员从某个时间点到当前时间点的每个月的活跃度
过滤条件：1. 每个月取个人的10条动态
        2. 10条动态中含有一条有效动态，即记录下来

执行：python list_not_active_enterprise_member.py 企业名称(eg. open_euler) 个人GiteeToken 企业GiteeToken 开始日期(eg. 2024-01-01 必须是1号)
输出结果：在当前文件夹下 ./dist/list_not_active_enterprise_member/result_*.csv
        存储统计的企业成员信息与动态数据，数据格式：成员名称, 用户id, 用户的gitee-id, 用户动态记录

对于输出的 csv 文件，需要手动导入 excel 处理
"""
import json
import os
import csv
import sys
import time
import urllib.request
import datetime
from urllib import error

_gitee_developer_api_uri = 'https://gitee.com/api/v5/'
_gitee_enterprise_api_uri = 'https://api.gitee.com/enterprises/'
_req_method_get = 'GET'
_headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}

_gitee_org_repos = ['' for _ in range(1024 * 100)]
_gitee_org_repos_size = 0
_gitee_developer_token = ''
_gitee_enterprise_token = ''
_enterprise_path = ''
_enterprise_id = 0
_release_version_name = ''
_storge_file_path = ''


def get_enterprise_id():
    query = '?access_token=' + _gitee_developer_token
    req_url = _gitee_developer_api_uri + 'enterprises/' + _enterprise_path + query
    req = urllib.request.Request(url=req_url, headers=_headers, method=_req_method_get)
    try:
        with urllib.request.urlopen(req) as res:
            data = res.read().decode('utf-8')  # str
            enterprise_info = json.loads(data)  # dict
    except error.HTTPError:
        ans_enterprise_id = 0
    except error.URLError:
        ans_enterprise_id = 0
    else:
        ans_enterprise_id = enterprise_info['id']
    return ans_enterprise_id


_enterprise_member_list = [['', '', '', '', ''] for _ in range(1024 * 10)]
_enterprise_member_list_size = 0
_start_data = ''


def get_all_enterprise_members():
    page_no = 1

    global _enterprise_member_list, _enterprise_member_list_size
    flag = True
    while flag:
        query = '?access_token=' + _gitee_enterprise_token + '&page=' + str(page_no) + '&per_page=100'
        req_url = _gitee_enterprise_api_uri + str(_enterprise_id) + '/members' + query
        req = urllib.request.Request(url=req_url, headers=_headers, method=_req_method_get)
        with urllib.request.urlopen(req) as res:
            data = res.read().decode('utf-8')  # str
            members = json.loads(data)['data']  # list [dict...]
            members_size = len(members)
            for members_i in range(members_size):
                _enterprise_member_list[_enterprise_member_list_size][0] = members[members_i]['remark']
                _enterprise_member_list[_enterprise_member_list_size][1] = members[members_i]['user']['id']
                _enterprise_member_list[_enterprise_member_list_size][2] = members[members_i]['user']['login']
                _enterprise_member_list[_enterprise_member_list_size][3] = members[members_i]['created_at'][:10]
                _enterprise_member_list_size = _enterprise_member_list_size + 1
            flag = members_size != 0
            print('正在收集成员，每次请求收集 100 个，当前成员数: ' + str(_enterprise_member_list_size))
            page_no = page_no + 1
            # flag = page_no < 1  # test


_date_range = [
    '2020-01-01'
]
_start_date_index = -1
_end_date_index = 0


def date_add_month(date_str: str):
    date_src = datetime.date.fromisoformat(date_str)
    year_value = date_src.year
    month_value = date_src.month
    if month_value == 12:
        year_value += 1
        month_value = 1
    else:
        month_value += 1
    date_result = date_src.replace(year=year_value, month=month_value, day=1)
    return date_result.strftime('%Y-%m-%d')

def check_members_all_activity(members_all_activity_i: int):
    query = ('?access_token=' + _gitee_enterprise_token + '&page=1&per_page=10&limit=10&start_date='
             + _date_range[_start_date_index])
    req_url = (_gitee_enterprise_api_uri + str(_enterprise_id) + '/members/'
               + str(_enterprise_member_list[members_all_activity_i][1]) + '/events' + query)
    req = urllib.request.Request(url=req_url, headers=_headers, method=_req_method_get)
    with urllib.request.urlopen(req) as res:
        data = res.read().decode('utf-8')  # str
        return data != '{"data":[]}'


def check_members_month_activity(members_month_activity_i: int):
    global _enterprise_member_list, _enterprise_member_list_size
    j = _start_date_index
    event_record = ''
    while j < _end_date_index:
        query = ('?access_token=' + _gitee_enterprise_token + '&page=1&per_page=10&limit=10&start_date='
                 + _date_range[j] + '&end_date=' + _date_range[j + 1])
        req_url = (_gitee_enterprise_api_uri + str(_enterprise_id) + '/members/'
                   + str(_enterprise_member_list[members_month_activity_i][1]) + '/events' + query)
        req = urllib.request.Request(url=req_url, headers=_headers, method=_req_method_get)
        with urllib.request.urlopen(req) as res:
            data = res.read().decode('utf-8')  # str
            month_active = 'no,'
            if data == '{"data":[]}':
                event_record += month_active
            else:
                user_events = json.loads(data)['data']  # list [dict...]
                user_events_size = len(user_events)
                for k in range(user_events_size):
                    if user_events[k]['action'] not in ['kick_out', 'left', 'be_left']:
                        month_active = _date_range[j][:7] + ','
                        break
                event_record += month_active
            j += 1
    _enterprise_member_list[members_month_activity_i][4] = event_record
    print('正在收集第 ' + str(members_month_activity_i) + ' 个成员动态')


if __name__ == '__main__':
    args_len = len(sys.argv)

    if args_len != 5:
        sys.exit(
            '请输入正确的参数: python list_not_active_enterprise_member.py 企业名称 个人GiteeToken 企业GiteeToken 开始日期')

    exec_py = sys.argv[0]
    dir_path = '.' + os.sep + 'dist' + os.sep
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    _storge_file_path = dir_path + exec_py[:-3].split(os.sep)[-1]
    print('文件输出Dir: ' + _storge_file_path)
    if not os.path.exists(_storge_file_path):
        os.mkdir(_storge_file_path)

    _enterprise_path = sys.argv[1]
    if len(_enterprise_path) == 0:
        sys.exit('请输入正确的企业Path，如：open_euler')
    print('企业Path: ' + _enterprise_path)

    _gitee_developer_token = sys.argv[2]
    if len(_gitee_developer_token) == 0:
        sys.exit('请输入正确的个人 Gitee Token')
    print('个人 Gitee Token: ' + _gitee_developer_token)

    _gitee_enterprise_token = sys.argv[3]
    if len(_gitee_enterprise_token) == 0:
        sys.exit('请输入正确的企业 Gitee Token')
    print('企业 Gitee Token: ' + _gitee_enterprise_token)

    start_date = sys.argv[4]
    if len(start_date) == 0:
        sys.exit('请输入正确的开始日期，如 2023-01-01')
    print('开始日期: ' + start_date)
    end_date = datetime.date.today().replace(day=1)
    end_date_str = end_date.strftime('%Y-%m-%d')
    date_range_index = 0
    date_range_flag = True
    while date_range_flag:
        next_month_date = date_add_month(_date_range[date_range_index])
        if next_month_date > end_date_str:
            date_range_flag = False
        date_range_index += 1
        _date_range.append(next_month_date)

    for date_i in range(len(_date_range)):
        if _date_range[date_i] == str(start_date):
            _start_date_index = date_i
        if _date_range[date_i] == str(end_date):
            _end_date_index = date_i + 1
    if _start_date_index == -1:
        sys.exit('请输入正确的开始日期，必须是某年某月1号，如 2023-01-01')

    start_time = time.time()
    _enterprise_id = get_enterprise_id()
    if _enterprise_id == 0:
        print('企业ID: ' + _enterprise_id)
        sys.exit('企业ID错误')

    enterprise_member_file_path = (_storge_file_path + os.sep + _enterprise_path + '_member_' +
                                   time.strftime('%Y%m%d', time.localtime()) + '.txt')
    if not os.path.isfile(enterprise_member_file_path):
        print('收集企业成员 =====> 开始')
        get_all_enterprise_members()
        with open(enterprise_member_file_path, 'w+') as enterprise_member_file_path_out:
            enterprise_member_file_path_out.write(
                json.dumps(_enterprise_member_list[:_enterprise_member_list_size], indent=2))
        print('收集企业成员 =====> 完成，输出文件：' + enterprise_member_file_path)
    else:
        print(
            '当前已经收集过企业成员，不必重复收集。如果要再次收集，请删除文件：' + enterprise_member_file_path + ' 后，再重新执行')

    print('收集企业成员动态 =====> 开始')
    with (open(enterprise_member_file_path, 'r') as enterprise_member_file_path_in):
        _enterprise_member_list = json.load(enterprise_member_file_path_in)
        _enterprise_member_list_size = len(_enterprise_member_list)
        print('正在收集企业成员动态，成员总共 ' + str(_enterprise_member_list_size) + ' 个')
        i = 0
        page = 10
        while i < _enterprise_member_list_size:
            result = (_storge_file_path + os.sep + 'result_' + str(i + 10) + '.csv')
            if os.path.isfile(result):
                i += page
            else:
                break
        write_i = i
        while i < _enterprise_member_list_size:
            if check_members_all_activity(i):
                check_members_month_activity(i)
            if (i + 1) % page == 0:
                result = (_storge_file_path + os.sep + 'result_' + str(i + 1) + '.csv')
                with open(result, 'w+', encoding='utf-8', newline='') as result_out:
                    result_writer = csv.writer(result_out)
                    result_writer.writerows(_enterprise_member_list[write_i + 1 - page:write_i + 1])
            i += 1
            write_i = i
    print('收集企业成员动态 =====> 完成')

    print(f'cost:{time.time() - start_time:.4f}s')
