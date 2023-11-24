import math
import requests
import argparse
import logging
import json
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

def getRepoCommit(page, repo, token, pr_in_master, logger):
    status = 'merged'
    per_page = 100
    url = 'https://gitee.com/api/v5/repos/{}/pulls?access_token={}&state={}&sort=created&direction=desc&page={}&per_page={}'
    pr_url = url.format(repo, token, status, page, per_page)
    response = requests.get(pr_url, timeout=10)
    if response.status_code != 200:
        logger.error('Get repo error: {}.'.format(response.status_code))
        return
    total_pr = int(response.headers['total_count'])
    if 0 == total_pr:
        return 0
    if total_pr > page * per_page:
        pr_in_master = getRepoCommit(page+1, repo, token, pr_in_master, logger)
    info = json.loads(response.text)
    for pr in info:
        base = pr['base']
        base_label = base['label']
        if base_label != 'master':
            continue
        pr_in_master += 1

    return pr_in_master

def writeData2CsvFile(token, input_file, repo_dict, logger):
    print(len(repo_dict))
    with open(input_file, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Repo_Url', 'Created_At', 'PR_Cnt_in_Master'])
        for item in sorted(repo_dict.items(), key=lambda x: (x[1], x[0]), reverse=True):
            PR_cnt = getRepoCommit(1, item[0], token, 0, logger)

            if 0 == PR_cnt:
                continue
            logger.info("Repo:{:<30s}, Created_at:{:<30s}, pr_cnd:{}".format(item[0], item[1], PR_cnt))
            repo_url = 'https://gitee.com/' + item[0]
            writer.writerow([repo_url, item[1], PR_cnt])
    csvfile.close()
    return

def getRepoCntInOrg(org, token, logger):
    url = 'https://gitee.com/api/v5/orgs/{}?access_token={}'
    get_url = url.format(org, token)
    response = requests.get(get_url, timeout=10)
    if response.status_code != 200:
        logger.error('Get organization info failed: {}.'.format(response.status_code))
        return 0
    info = json.loads(response.text)
    repo_cnt = info['public_repos']
    return repo_cnt

def getOrgRepos(org, repo_cnt, logger, period):
    per_page = 100
    page_cnt = math.ceil(repo_cnt/per_page)
    repo_dict = {}
    url = 'https://ipb.osinfra.cn/repos?org={}&per_page={}&page={}'
    for i in range(page_cnt):
        page = i+1
        qurl = url.format(org, per_page, page)
        response = requests.get(qurl, timeout=10)
        if response.status_code != 200:
            logger.error('Get repo error: {}.'.format(response.status_code))
            continue
        info = json.loads(response.text)
        repos = info['data']
        for repo in repos:
            state = str(repo['status'])
            if state != '开始':
                continue
            created_at = str(repo['created_at']).strip()
            if created_at.startswith(period):
                reponame = str(repo['repo'])
                repo_dict[reponame] = created_at
    return repo_dict

def main(org, token, result_path, log_path, period):
    logger = logger_config(log_path)
    repo_cnt = getRepoCntInOrg(org, token, logger)
    repo_dict = getOrgRepos(org, repo_cnt, logger, period)
    writeData2CsvFile(token, result_path, repo_dict, logger)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get info of Repo with code commits in a period.')
    parser.add_argument('--token', '-t', type=str, required=True, help='Gitee ID Token.')
    parser.add_argument('--org', '-o', type=str, default='openeuler', help='Gitee organization name, ex: openeuler or src-openeuler.')
    parser.add_argument('--period', '-p', type=str, default='2023', help='Repo create time in which period to find.')
    parser.add_argument('--logpath', '-l', type=str, default='./log.txt', help='Log file path.')
    parser.add_argument('--result', '-r', type=str, default='./result.csv', help='result file path.')

    args = parser.parse_args()
    token = args.token
    org = args.org
    log_path = args.logpath
    result_path = args.result
    period = args.period
    main(org, token, result_path, log_path, period)
