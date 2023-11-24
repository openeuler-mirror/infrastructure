#coding = utf-8
import math
import argparse
import requests
import json
import logging
import csv

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

class KernelCommitterRefresh(object):
    def __init__(self, token, org, logger, repo, state, csvwriter):
        self.token = token
        self.org = org
        self.perpage = 100
        self.logger = logger
        self.repo = repo
        self.state = state
        self.ci_robot_pr_ids = []
        self.ci_robot_author = "ci-robot"
        self.sync_bot_pr_dict = {}
        self.sync_bot_author = "openeuler-sync-bot"
        self.writer = csvwriter
        return


    def get_repo_open_prs(self):
        #获取项目信息
        headers = {'Content-Type': 'Application/json'}
        get_url = "https://ipb.osinfra.cn/pulls?state={}&repo={}/{}&page={}&per_page={}"
        url = get_url.format(self.state, self.org, self.repo, 1, self.perpage)
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            self.logger.error("Get repos failed, error code:{}.".format(response.status_code))
            return
        info = json.loads(response.text)
        total = info['total']
        self.logger.info("Total count: {}".format(total))
        page_cnt = math.ceil(int(total) / self.perpage)
        for page in range(1, page_cnt+1):
            url = get_url.format(self.state,  self.org, self.repo, page, self.perpage)
            response = requests.get(url, timeout=10, headers=headers)
            if response.status_code != 200:
                print("Get repos failed, error code:{}.".format(response.status_code))
                continue
            info = json.loads(response.text)
            repos = info['data']
            for repo in repos:
                if repo['author'] == self.ci_robot_author:
                    link = str(repo['link'])
                    id = link.split('/')[-1]
                    self.ci_robot_pr_ids.append(id)
                if repo['author'] == self.sync_bot_author:
                    link = str(repo['link'])
                    title = str(repo['title'])
                    parent_id = title.split(':')[0].split('-')[-1]
                    self.sync_bot_pr_dict[link] = parent_id
        self.logger.info("Need find ci-robot committers: {}".format(len(self.ci_robot_pr_ids)))
        self.logger.info("Need find sync-bot committers: {}".format(len(self.sync_bot_pr_dict)))
        return

    def get_pr_committers_with_ci_robot(self):
        get_url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}?access_token={}'
        for id in self.ci_robot_pr_ids:
            url = get_url.format(self.org, self.repo, id, self.token)
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                self.logger.error("Get enterprise id failed.error code:{}".format(response.status_code))
                continue
            info = json.loads(response.text)
            html_url = info['html_url']
            des = str(info['body'])
            committer = des.split('>')[0].split('<')[-1]
            self.logger.info("PR: {}  ,  committer: {} ".format(html_url, committer))
            self.writer.writerow([html_url, committer])
        return

    def get_pr_committers_with_sync_bot(self):
        get_url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}?access_token={}'
        for link, parent_id in self.sync_bot_pr_dict.items():
            url = get_url.format(self.org, self.repo, parent_id, self.token)
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                self.logger.error("Get enterprise id failed.error code:{}".format(response.status_code))
                continue
            info = json.loads(response.text)
            html_url = info['html_url']
            user = info['user']
            parent_committer = user['login']
            if 'ci-robot' == parent_committer:
                des = str(info['body'])
                real_committer = des.split('>')[0].split('<')[-1]
            else:
                real_committer = parent_committer
            self.logger.info("PR: {}  ,  Parent_PR: {} ,  committer: {} ".format(link, html_url, real_committer))
            self.writer.writerow([link, real_committer, html_url])

        return

def main(token, org, log_path, repo, state, csvpath):
    logger = logger_config(log_path)
    csvfile = open(csvpath, 'w')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['PR_url', 'Committer', 'Parent_url'])

    kcr = KernelCommitterRefresh(token, org, logger, repo, state, csvwriter)
    kcr.get_repo_open_prs()
    kcr.get_pr_committers_with_ci_robot()
    kcr.get_pr_committers_with_sync_bot()

    csvfile.close()
    logger.info("End END END.")
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kernel Real Committer.')
    parser.add_argument('--token', '-t', type=str, required=True, help='Gitee ID Token.')
    parser.add_argument('--org', '-o', type=str, default='openeuler', help='Gitee organization name, ex: openeuler or src-openeuler.')
    parser.add_argument('--repo', '-r', type=str, default='kernel', help='Gitee repo name,ex: kernel, infrastructure.')
    parser.add_argument('--state', '-s', type=str, default='open', help='PR status,ex: open, close.')
    parser.add_argument('--logpath', '-l', type=str, default='./log.txt', help='Log file path.')
    parser.add_argument('--csvpath', '-c', type=str, default='./committers.csv', help='The csv file path used to save committer list.')

    args = parser.parse_args()
    token = args.token
    org = args.org
    repo = args.repo
    state = args.state
    log_path = args.logpath
    csvpath = args.csvpath
    main(token, org, log_path, repo, state, csvpath)

