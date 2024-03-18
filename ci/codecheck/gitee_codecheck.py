import argparse
import datetime
import json
import os
import requests
import time
import sys


class CodeCheck(object):

    def __init__(self, static_key, access_token,
                 codecheck_ip='https://majun.osinfra.cn',
                 gitee_api='https://gitee.com/api/v5/repos',
                 codecheck_prefix='/api/ci-backend/ci-portal/webhook/codecheck/v1'):
        self.dynamic_token = None
        self.pr_url = None
        self.task_id = None
        self.uuid = None
        self.result = None
        self.report_url = None
        self.static_key = static_key
        self.access_token = access_token
        self.codecheck_ip = codecheck_ip
        self.gitee_api = gitee_api
        self.codecheck_prefix = codecheck_prefix

    def _get_pr_url(self):
        wh_data = json.loads(os.getenv('jsonBody', '{}'))
        if wh_data:
            self.pr_url = wh_data.get('pull_request', {}).get('html_url', '')
            print(f'[webhook {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] get pr url success')
            print(f'[webhook {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] pr --> {self.pr_url}')
        else:
            print(f'[webhook {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] get pr url failed')

    def _get_dynamic_token(self):
        try:
            token_url = f'{self.codecheck_ip}{self.codecheck_prefix}/token'
            data = {
                "static_token" : self.static_key
            }
            print(f'token_url: {self.codecheck_ip}{self.codecheck_prefix}/token')
            
            response = requests.post(token_url, data=json.dumps(data))
            if response.status_code != 200:
                print('Get unexpected response when get dynamic token: ', response.json())
                sys.exit(1)
            
            if response.json().get('code') == '200':
                self.dynamic_token = response.json().get('data')
                print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] get dynamic token success')
            else:
                print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] get dynamic token failed 1')
        except Exception as e:
            print(
                f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] get dynamic token failed 2, error: {e} ')

    def _get_create_task(self):
        try:
            task_url = f'{self.codecheck_ip}{self.codecheck_prefix}/task'
            params = {
                "pr_url" : self.pr_url,
                "token" : self.dynamic_token,
                "projectName": 'osinfra'
            }
            response = requests.post(task_url, data=json.dumps(params))
            if response.status_code != 200:
                print('Get unexpected response when create task: ', response.json())
                sys.exit(1)
            if response.json().get('code') == '200':
                self.uuid = response.json().get('uuid')
                self.task_id = response.json().get('task_id')
                print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] create task success')
            else:
                print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] create task failed '
                      f'\n[{response.json().get("msg")}]')
        except Exception as e:
            print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] create task failed '
                  f'\n[{e}]')

    def _get_task_result(self):
        expire_time = 0
        while expire_time < 1000:
            time.sleep(10)
            try:
                status_url = f'{self.codecheck_ip}{self.codecheck_prefix}/task/status'
                params = {
                    "uuid" : self.uuid,
                    "token" : self.dynamic_token,
                    "task_id": self.task_id
                }
                response = requests.post(status_url, data=json.dumps(params))
                if response.status_code != 200:
                    print('Fail to get task result: ', response.json())
                    sys.exit(1)
                if response.json().get('code') == '200':
                    self.result = response.json().get('state')
                    self.report_url = response.json().get('data')
                    print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] task success')
                    break
                elif response.json().get('code') == '100':
                    print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] task running')
                    expire_time = expire_time + 10
                    continue
                elif response.json().get('code') == '401':
                    self._get_dynamic_token()
                    print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] dynamic token expired')
                    expire_time = expire_time + 10
                    continue
                else:
                    print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] task failed '
                          f'\n[{response.json().get("msg")}]')
                    break
            except Exception as e:
                print(f'[code check {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] task failed '
                      f'\n[{e}]')
                break

    def _create_gitee_comment(self, comment_info):
        try:
            split_list = self.pr_url.split('/')
            owner = split_list[-4]
            repo = split_list[-3]
            number = split_list[-1]
            # https: // gitee.com / openMajun / mugen / pulls / 1
            comment_url = f'{self.gitee_api}/{owner}/{repo}/pulls/{number}/comments'
            post_data = {
                "access_token": self.access_token,
                "body": comment_info
            }
            response = requests.post(comment_url, data=post_data)
            if response.status_code in [200, 201, 204]:
                print(f'[gitee api {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] comment success')
            else:
                print(f'[gitee api {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] comment failed')
        except Exception as e:
            print(f'[gitee api {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] comment failed '
                  f'\n[{e}]')

    def _gitee_comment_info(self, error_info=''):

        comment = "<br>静态检查: {0}</br>".format(self.result)
        comment += " <table> <thead> <tr> <th>#</th> <th>check type</th> <th>result</th> <th>report</th> </tr> " \
                   "</thead> <tbody>"
        comment += " <tr> <td>"
        comment += "1"
        comment += "</td> <td>"
        comment += "codecheck"
        comment += "</td> <td>"
        comment += self.result
        comment += "</td> <td>"
        comment += error_info + "<a href='{0}'>>>></a>".format(self.report_url)
        comment += "</td> </tr>"
        comment += " </tbody> </table>"
        return comment

    def run(self):
        self._get_pr_url()
        error_info = ''
        if not self.pr_url:
            sys.exit()
        self._get_dynamic_token()
        if not self.dynamic_token:
            self.result = 'failed'
            error_info = 'get dynamic token error'
            self.report_url = os.path.join(os.getenv('BUILD_URL'), 'console')
            self._create_gitee_comment(self._gitee_comment_info(error_info=error_info))
            sys.exit()
        self._get_create_task()
        if not self.uuid or not self.task_id:
            self.result = 'failed'
            error_info = 'create codecheck task error'
            self.report_url = os.path.join(os.getenv('BUILD_URL'), 'console')
            self._create_gitee_comment(self._gitee_comment_info(error_info=error_info))
            sys.exit()
        self._get_task_result()
        if not self.report_url or self.result is None:
            sys.exit()
        self._create_gitee_comment(self._gitee_comment_info(error_info=error_info))


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--access_token', help='gitee access token', required=True, type=str)
    parser.add_argument('--static_key', help='codecheck static key', required=True, type=str)
    parser.add_argument('--codecheck_ip', help='codecheck ip', default='https://majun.osinfra.cn', type=str)
    parser.add_argument('--gitee_api', help='gitee api', default='https://gitee.com/api/v5/repos', type=str)
    parser.add_argument('--codecheck_prefix', help='codecheck prefix', default='/api/ci-backend/ci-portal/webhook/codecheck/v1',
                        type=str)
    return parser.parse_args()


if __name__ == '__main__':
    args = init_args()
    codecheck = CodeCheck(args.static_key, args.access_token, args.codecheck_ip, args.gitee_api, args.codecheck_prefix)
    codecheck.run()
