import requests
import sys


def add_processing_tag(owner, repo, number, access_token):
    url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}/labels?access_token={}'.format(owner,
                                                                                        repo,
                                                                                        number,
                                                                                        access_token)
    data = "[\"ci_processing\"]"
    r = requests.post(url, data)
    if r.status_code != 201:
        print(r.json())
        sys.exit(1)


def add_successful_tag(owner, repo, number, access_token):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(owner,
                                                                                            repo,
                                                                                            number,
                                                                                            access_token)
    data = "[\"ci_successful\"]"
    r = requests.post(url, data)
    if r.status_code != 201:
        print(r.json())
        sys.exit(1)


def add_failed_tag(owner, repo, number, access_token):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(owner,
                                                                                            repo,
                                                                                            number,
                                                                                            access_token)
    data = "[\"ci_failed\"]"
    r = requests.post(url, data)
    if r.status_code != 201:
        print(r.json())
        sys.exit(1)


def remove_processing_tag(owner, repo, number, access_token):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/ci_processing/?access_token={3}'.format(owner,
                                                                                                           repo,
                                                                                                           number,
                                                                                                           access_token)
    r = requests.delete(url)
    if r.status_code != 204 and r.status_code != 404:
        print(r.json())
        sys.exit(1)


def remove_successful_tag(owner, repo, number, access_token):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/ci_successful/?access_token={3}'.format(owner,
                                                                                                           repo,
                                                                                                           number,
                                                                                                           access_token)
    r = requests.delete(url)
    if r.status_code != 204 and r.status_code != 404:
        print(r.json())
        sys.exit(1)


def remove_failed_tag(owner, repo, number, access_token):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/ci_failed/?access_token={3}'.format(owner,
                                                                                                       repo,
                                                                                                       number,
                                                                                                       access_token)
    r = requests.delete(url)
    if r.status_code != 204 and r.status_code != 404:
        print(r.json())
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print('owner, repo, number, access_token and action is required, please check!')
        sys.exit(1)
    owner = sys.argv[1]
    repo = sys.argv[2]
    number = sys.argv[3]
    access_token = sys.argv[4]
    action = sys.argv[5]
    if action not in ['ATP', 'ATS', 'ATF']:
        print('Invalid action')
        sys.exit(1)
    if action == 'ATP':
        remove_successful_tag(owner, repo, number, access_token)
        remove_failed_tag(owner, repo, number, access_token)
        add_processing_tag(owner, repo, number, access_token)
    if action == 'ATS':
        remove_processing_tag(owner, repo, number, access_token)
        remove_failed_tag(owner, repo, number, access_token)
        add_successful_tag(owner, repo, number, access_token)
    if action == 'ATF':
        remove_processing_tag(owner, repo, number, access_token)
        remove_successful_tag(owner, repo, number, access_token)
        add_failed_tag(owner, repo, number, access_token)
