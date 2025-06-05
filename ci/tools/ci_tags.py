import requests
import sys


class Check():
    def __init__(self, owner, repo, number, access_token):
        self.owner = owner
        self.repo = repo
        self.number = number
        self.access_token = access_token

    def add_processing_tag(self):
        url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}/labels?access_token={}'.format(self.owner,
                                                                                            self.repo,
                                                                                            self.number,
                                                                                            self.access_token)
        headers = {'Content-Type': 'Application/json'}
        data = "[\"ci_processing\"]"
        r = requests.post(url, data, headers=headers)
        if r.status_code != 201:
            print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
            sys.exit(1)

    def add_successful_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(self.owner,
                                                                                                self.repo,
                                                                                                self.number,
                                                                                                self.access_token)
        headers = {'Content-Type': 'Application/json'}
        data = "[\"ci_successful\"]"
        r = requests.post(url, data, headers=headers)
        if r.status_code != 201:
            print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
            sys.exit(1)

    def add_docs_successful_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(self.owner,
                                                                                                self.repo,
                                                                                                self.number,
                                                                                                self.access_token)
        headers = {'Content-Type': 'Application/json'}
        data = "[\"docs_ci_successful\"]"
        r = requests.post(url, data, headers=headers)
        if r.status_code != 201:
            print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
            sys.exit(1)

    def add_failed_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(self.owner,
                                                                                                self.repo,
                                                                                                self.number,
                                                                                                self.access_token)
        headers = {'Content-Type': 'Application/json'}
        data = "[\"ci_failed\"]"
        r = requests.post(url, data, headers=headers)
        if r.status_code != 201:
            print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
            sys.exit(1)
    
    def add_docs_failed_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(self.owner,
                                                                                                self.repo,
                                                                                                self.number,
                                                                                                self.access_token)
        headers = {'Content-Type': 'Application/json'}
        data = "[\"docs_ci_failed\"]"
        r = requests.post(url, data, headers=headers)
        if r.status_code != 201:
            print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
            sys.exit(1)

    def remove_processing_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/ci_processing/?access_token={3}'.format(
            self.owner,
            self.repo,
            self.number,
            self.access_token)
        r = requests.delete(url)
        if r.status_code == 400:
            print('ERROR! Can not remove `ci_processing` label in a closed Pull Request.')
            sys.exit(1)
        elif r.status_code == 404:
            pass
        else:
            if r.status_code != 204:
                print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
                sys.exit(1)

    def remove_successful_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/ci_successful/?access_token={3}'.format(
            self.owner,
            self.repo,
            self.number,
            self.access_token)
        r = requests.delete(url)
        if r.status_code == 400:
            print('ERROR! Can not remove `ci_successful` label in a closed Pull Request.')
            sys.exit(1)
        elif r.status_code == 404:
            pass
        else:
            if r.status_code != 204:
                print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
                sys.exit(1)

    def remove_docs_successful_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/docs_ci_successful/?access_token={3}'.format(
            self.owner,
            self.repo,
            self.number,
            self.access_token)
        r = requests.delete(url)
        if r.status_code == 400:
            print('ERROR! Can not remove `docs_ci_successful` label in a closed Pull Request.')
            sys.exit(1)
        elif r.status_code == 404:
            pass
        else:
            if r.status_code != 204:
                print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
                sys.exit(1)

    def remove_docs_failed_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/docs_ci_failed/?access_token={3}'.format(
            self.owner,
            self.repo,
            self.number,
            self.access_token)
        r = requests.delete(url)
        if r.status_code == 400:
            print('ERROR! Can not remove `docs_ci_failed` label in a closed Pull Request.')
            sys.exit(1)
        elif r.status_code == 404:
            pass
        else:
            if r.status_code != 204:
                print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
                sys.exit(1)

    def remove_failed_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/ci_failed/?access_token={3}'.format(
            self.owner,
            self.repo,
            self.number,
            self.access_token)
        r = requests.delete(url)
        if r.status_code == 400:
            print('ERROR! Can not remove `ci_failed` label in a closed Pull Request.')
            sys.exit(1)
        elif r.status_code == 404:
            pass
        else:
            if r.status_code != 204:
                print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
                sys.exit(1)

    def remove_conflict_tag(self):
        url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels/conflicted/?access_token={3}'.format(
            self.owner,
            self.repo,
            self.number,
            self.access_token)
        r = requests.delete(url)
        if r.status_code == 400:
            print('ERROR! Can not remove `conflicted` label in a closed Pull Request.')
            sys.exit(1)
        elif r.status_code == 404:
            pass
        else:
            if r.status_code != 204:
                print('ERROR! Unexpected failure, status_code: {}'.format(r.status_code))
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
    c = Check(owner, repo, number, access_token)
    if action not in ['ATP', 'ATS', 'ATF', 'ATDP', 'ATDS', 'ATDF']:
        print('Invalid action')
        sys.exit(1)
    if action == 'ATP':
        c.remove_successful_tag()
        c.remove_failed_tag()
        c.add_processing_tag()
    if action == 'ATDP':
        c.remove_docs_successful_tag()
        c.remove_docs_failed_tag()
        c.add_processing_tag()
    if action == 'ATS':
        c.remove_processing_tag()
        c.remove_failed_tag()
        c.remove_conflict_tag()
        c.add_successful_tag()
    if action == 'ATF':
        c.remove_processing_tag()
        c.remove_successful_tag()
        c.add_failed_tag()
    if action == 'ATDS':
        c.remove_processing_tag()
        c.remove_docs_failed_tag()
        c.remove_conflict_tag()
        c.add_docs_successful_tag()
    if action == 'ATDF':
        c.remove_processing_tag()
        c.remove_docs_successful_tag()
        c.add_docs_failed_tag()
        
