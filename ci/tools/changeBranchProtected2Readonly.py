#coding = utf-8
#@Time:     2023-11-20
#@Author:   georgecao
#@File:     changeBranchProtected2Readonly.py

import math
import yaml
import os
import sys
import requests
import json
import logging

def logger_config(log_path):
    logger = logging.getLogger('-')
    logger.setLevel(level=logging.DEBUG)
    handler = logging.FileHandler(log_path, encoding='UTF-8')
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)

    logger.addHandler(handler)
    logger.addHandler(console)
    return logger
class Branch_Protection(object):
    def __init__(self, token, v8_token, path, enterprise_name, enterprise_id, org_name, org_repo_cnt, logger):
        self.token = token
        self.v8_token = v8_token
        self.path = path
        self.enterprise = enterprise_name
        self.enterprise_id = enterprise_id
        self.org = org_name
        self.org_repo_cnt = org_repo_cnt
        self.perpage = 100
        self.br_need_change = {}
        self.repo_project_ids = {}
        self.logger = logger
        return

    def get_branch_is_protected(self, repo, br):
        re_url = "https://gitee.com/api/v5/repos/{}/{}/branches/{}?access_token={}"
        url = re_url.format(self.org, repo, br, self.token)
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            self.logger.error("Get Branch({}) type in repo({}) failed, error code:{}.".format(br, repo, response.status_code))
            return
        brinfo = json.loads(response.text)
        br_protected = int(brinfo['protected'])
        return br_protected

    def get_repo_branch_protect_info(self, repo):
        re_url = "https://gitee.com/api/v5/repos/{}/{}/branches?access_token={}"
        url = re_url.format(self.org, repo, self.token)
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            self.logger.error("Get Branch({}) type in repo({}) failed, error code:{}.".format(br, repo, response.status_code))
            return
        all_branches = json.loads(response.text)
        branch_protect_info = {}
        for brinfo in all_branches:
            br_name = brinfo['name']
            br_protected = brinfo['protected']
            branch_protect_info[br_name] = br_protected
        return branch_protect_info

    def get_local_file(self):
        files = []
        for filepatch, dirnames, filenames in os.walk(self.path):
            if(filepatch.split('/')[-2] != self.org):
                continue
            for filename in filenames:
                if (filename.split('.')[-1] != 'yaml'):
                    self.logger.error(filename)
                    continue
                tmpfile = filepatch+'/'+filename
                files.append(tmpfile)

        repo_branch_dict = {}
        repo_files = {}
        for file in files:
            try:
                f = open(file, 'rb')
                yamlfile = yaml.load(f.read(), Loader=yaml.FullLoader)
                repo_name = yamlfile['name']
                brs = (yamlfile['branches'])
                br_dict = {}
                for br in brs:
                    br_dict[br['name']] = br['type']
                repo_branch_dict[repo_name] = br_dict
                repo_files[repo_name] = file
            except OSError as reason:
                self.logger.error("file, Error: {}".format(file))
            finally:
                f.close()
        return repo_branch_dict, repo_files

    def get_branches_need_handle(self):
        all_cfg_br_dict, repo_files = self.get_local_file()
        for repo in all_cfg_br_dict.keys():
            tmp_branches = []
            all_br_type = all_cfg_br_dict[repo]
            repo_protest_info = self.get_repo_branch_protect_info(repo)
            for b in all_br_type.keys():
                if repo_protest_info[b] and all_br_type[b] == 'readonly':
                    tmp_branches.append(b)
                    self.logger.info('===repo:'+repo+', branch:'+b+' need change.')
                else:
                    file_name = repo_files[repo]
                    os.remove(file_name)
            if 0 == (len(tmp_branches)):
                continue

            self.change_branches(repo, tmp_branches)
        return

    def change_branches(self, repo, branches):
        del_url="https://gitee.com/api/v5/repos/{}/{}/branches/{}/setting?access_token={}"
        get_url="https://gitee.com/api/v5/repos/{}/{}?access_token={}"
        chg_url = "https://api.gitee.com/enterprises/{}/projects/{}/branches/{}"

        t_url = get_url.format(self.org, repo, self.token)
        response = requests.get(t_url, timeout=10)
        if response.status_code != 200:
            self.logger.error("Get project id of repo({}) failed, error code:{}.".format(repo, response.status_code))
            return
        repoinfo = json.loads(response.text)
        project_id = repoinfo['id']
        self.logger.info("Begin repo({}) , project id: {}.".format(repo, project_id))

        for br in branches:
            url = del_url.format(self.org, repo, br, self.token)
            response = requests.delete(url, timeout=10)
            if response.status_code != 204:
                self.logger.error("Delete br({}) protection rule in repo({}) failed, error code:{}."
                                  .format(br, repo, response.status_code))
                continue
            self.logger.info("Delete br({}) protection rule in repo({}) success.".format(br, repo))

            tmp_url = chg_url.format(self.enterprise_id, project_id, br)
            data_dict = {"access_token": self.v8_token, "type": "2"}
            response = requests.put(tmp_url, data=data_dict, timeout=10)
            if response.status_code != 200:
                self.logger.error("Change br({}) in repo({}) to readonly failed,org({}),project({}) error code:{} ."
                                  .format(br, repo, self.org, project_id, response.status_code))
                continue
            self.logger.info("Change br({}) readonly of repo({}) success.".format(br, repo))
        return


def get_enterprise_id(token, enterprise, logger):
    req_url="https://gitee.com/api/v5/enterprises/{}?access_token={}"
    url = req_url.format(enterprise, token)
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        logger.error("Get enterprise id failed.error code:{}".format(response.status_code))
        return
    enterprise_info = json.loads(response.text)
    enterprise_id = enterprise_info['id']
    return enterprise_id

def get_org_info(token, org, logger):
    req_url = "https://gitee.com/api/v5/orgs/{}?access_token={}"
    url = req_url.format(org, token)
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        logger.error("Get org info failed.error code:{}".format(response.status_code))
        return
    org_info = json.loads(response.text)
    repo_cnt = org_info['public_repos']
    logger.info("Repo count : {}".format(repo_cnt))
    return repo_cnt

def main(token, v8_token, path, enterprise, org, log_path):
    logger = logger_config(log_path)
    enterprise_id = get_enterprise_id(token, enterprise, logger)
    org_repo_cnt = get_org_info(token, org, logger)
    bp = Branch_Protection(token, v8_token, path, enterprise, enterprise_id, org, org_repo_cnt, logger)
    bp.get_branches_need_handle()

    logger.info("End END end.")
    return

if __name__ == '__main__':
    path = r'/***/***/community/sig'
    log_path = r'/***/***/myloglog'
    token = '***********'
    v8_token = '***********'
    enterprise = r'open_euler'
    org = r"src-openeuler"
    main(token, v8_token, path, enterprise, org, log_path)

