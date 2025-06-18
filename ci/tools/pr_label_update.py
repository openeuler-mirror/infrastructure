import yaml
import requests
import json

sig_labels = [
    289886607,  # "sig/usability"
    289866749,  # "sig/lite"
    289861417,  # "sig/heterogeneous"
    289854100,  # "sig/pynative"
]

path_sig = {
    'openeuler/ccsrc/backend': 'sig/heterogeneous',
    'openeuler/ccsrc/plugin': 'sig/heterogeneous',
    'openeuler/ccsrc/ccsrc/runtime/graph_scheduler': 'sig/heterogeneous',
    'openeuler/ccsrc/runtime/hardware': 'sig/heterogeneous',
    'openeuler/lite': 'sig/ms-lite',
    'openeuler/ccsrc/pynative': 'sig/ms-pynative',
    'openeuler/ccsrc/pyboost': 'sig/ms-pynative',
    'openeuler/ccsrc/runtime/pynative': 'sig/ms-pynative',
    'openeuler/python/openeuler': 'sig/ms-usability'
}
class PR_Affiliation(object):

    def __init__(self, sig_file, v5_token, org):
        self.sig_file = sig_file
        self.token = v5_token
        self.org = org
        self.sig_affiliation = []

    def analize_sig_file(self):
        try:
            with open(self.sig_file, 'r', encoding='utf-8') as file:
                yamlfiles = yaml.safe_load(file)
                for sig in yamlfiles:
                    path = sig['path']
                    name = sig['sig']
                    label = sig['label']
                    sig_dict = {'path': path, 'name': name, 'label': label}
                    self.sig_affiliation.append(sig_dict)
        except FileNotFoundError:
            print(f"错误: 文件 '{self.sig_file}' 不存在")
            yamlfile = None
        except yaml.YAMLError as e:
            print(f"YAML 解析错误: {e}")
            yamlfile = None

    def display_sig_affiliation(self):
        for sig in self.sig_affiliation:
            print(sig['name'])
            print(sig['path'])
            print(sig['label'])
        return

    def get_repo_pr(self, repo):
        get_url = "https://gitee.com/api/v5/repos/{}/{}/pulls"
        params = {'access_token': self.token, 'state': 'merged', 'sort': 'created', 'direction': 'asc', 'page': 1, 'per_page': 1}
        t_url = get_url.format(self.org, repo)
        response = requests.get(t_url, params=params, timeout=10, verify=False)
        if response.status_code != 200:
            print("Get Pull requests from ({} - {}) failed, error code:{}.".format(self.org, repo, response.status_code))
            return None
        total_cnt = int(response.headers['total_count'])
        per_page = 100
        pr_info_list = []
        for i in range(1, total_cnt//per_page + 2):
            params = {'access_token': self.token, 'state': 'merged', 'sort': 'created', 'direction': 'asc', 'page': i, 'per_page': per_page }
            response = requests.get(t_url, params=params, timeout=10, verify=False)
            if response.status_code != 200:
                print("Get Pull requests from ({} - {}) failed, error code:{}.".format(self.org, repo,response.status_code))
                return None
            prs = json.loads(response.text)
            for pr in prs:
                pr_url = pr['html_url']
                number = pr['number']
                pr_info = {'pr_url': pr_url, 'number':number}
                pr_info_list.append(pr_info)
        return pr_info_list

    def update_repo_pr(self, repo, label):
        get_url = "https://gitee.com/api/v5/repos/{}/{}/pulls"
        add_url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}/labels'
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        data = [label]
        params = {'access_token': self.token, 'state': 'merged', 'sort': 'created', 'direction': 'asc', 'page': 1, 'per_page': 1}
        t_url = get_url.format(self.org, repo)
        response = requests.get(t_url, params=params, timeout=10, verify=False)
        if response.status_code != 200:
            print("Get Pull requests from ({} - {}) failed, error code:{}.".format(self.org, repo, response.status_code))
            return
        total_cnt = int(response.headers['total_count'])
        per_page = 100
        for i in range(14, total_cnt//per_page + 2):
            params = {'access_token': self.token, 'state': 'merged', 'sort': 'created', 'direction': 'asc', 'page': i, 'per_page': per_page }
            response = requests.get(t_url, params=params, timeout=10, verify=False)
            if response.status_code != 200:
                print("Get Pull requests from ({} - {}) failed, error code:{}.".format(self.org, repo,response.status_code))
                return
            prs = json.loads(response.text)
            for pr in prs:
                pr_url = pr['html_url']
                number = pr['number']
                post_url = add_url.format(self.org, repo, number)
                response = requests.post(post_url, params={'access_token': self.token}, headers=headers, data=json.dumps(data), timeout=10, verify=False)
                if response.status_code != 201:
                    print("Post label to requests from ({} - {}) failed, error code:{}.".format(self.org, repo, response.status_code))
                    return
                print("Add label successful pr: {}, url:{}".format(number, post_url))
        return
    def get_label_with_path(self, path):
        label = None
        for sigpath in  path_sig.keys():
            if sigpath in path:
                label = path_sig[sigpath]
                break
        return label

    def get_pr_labels(self, repo, number):
        labels = []
        commit_url = "https://gitee.com/api/v5/repos/{}/{}/pulls/{}/files"
        cmm_url = commit_url.format(self.org, repo, number)
        cmm_response = requests.get(cmm_url, params={'access_token': self.token}, timeout=10, verify=False)
        if cmm_response.status_code != 200:
            print("Post label to requests from ({} - {}) failed, error code:{}.".format(self.org, repo, cmm_response.status_code))
            return
        commits = json.loads(cmm_response.text)
        for commit in commits:
            filename = commit['filename']
            label = self.get_label_with_path(filename)
            if label and (label not in labels):
                labels.append(label)
        return labels

    def add_pr_labels(self, repo, number, labels):
        add_url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}/labels'
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        post_url = add_url.format(self.org, repo, number)
        response = requests.post(post_url, params={'access_token': self.token}, headers=headers, data=json.dumps(labels),
                                 timeout=10, verify=False)
        if response.status_code != 201:
            print("Post label to requests from ({} - {}) failed, error code:{}.".format(self.org, repo,
                                                                                        response.status_code))
            return
        print("Add label successful pr: {}, url:{}".format(number, post_url))
        return

    def pr_incluse_sig_label(self, label_array):
        for label in label_array:
            lab = label['id']
            if lab in sig_labels:
                return True
        return False

    def update_sig_pr(self, repo):
        get_url = "https://gitee.com/api/v5/repos/{}/{}/pulls"
        params = {'access_token': self.token, 'state': 'merged', 'sort': 'created', 'direction': 'asc', 'page': 1, 'per_page': 1}
        t_url = get_url.format(self.org, repo)
        response = requests.get(t_url, params=params, timeout=10, verify=False)
        if response.status_code != 200:
            print("Get Pull requests from ({} - {}) failed, error code:{}.".format(self.org, repo, response.status_code))
            return
        total_cnt = int(response.headers['total_count'])
        per_page = 100
        for i in range(1, total_cnt//per_page+2):
            params = {'access_token': self.token, 'state': 'merged', 'sort': 'created', 'direction': 'desc', 'page': i, 'per_page': per_page }
            response = requests.get(t_url, params=params, timeout=20, verify=False)
            if response.status_code != 200:
                print("Get Pull requests from ({} - {}) failed, error code:{}.".format(self.org, repo, response.status_code))
                return
            prs = json.loads(response.text)
            for index, pr in enumerate(prs):
                pr_url = pr['html_url']
                number = pr['number']
                label_array = pr['labels']
                if self.pr_incluse_sig_label(label_array):
                    continue
                print("Begin to handle pr - {} - in page:{}, index:{}".format(number, i, index))
                labels = self.get_pr_labels(repo, number)
                if labels:
                    self.add_pr_labels(repo, number, labels)
        return

    def display_pr_list(self, pr_list):
        for pr_info in pr_list:
            print("PR_URL - {}".format(pr_info['pr_url']))
            print("PR_number - {}".format(pr_info['number']))
        return

    def add_label_to_pr(self, repo, pr_list, label):
        add_url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}/labels'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8'
        }
        data = [label]
        print(data)
        params = {'access_token': self.token}

        for pr_info in pr_list:
            number = pr_info['number']
            t_url = add_url.format(self.org, repo, number)
            response = requests.post(t_url, params=params, headers=headers, data=json.dumps(data), timeout=10, verify=False)
            if response.status_code != 201:
                print(t_url)
                print("Post label to requests from ({} - {}) failed, error code:{}.".format(self.org, repo, response.status_code))
                return
            print("Add label successful pr: {}".format(number))
        return


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pr_affiliation = PR_Affiliation("sigs.yaml", "****", "openeuler")
    pr_affiliation.analize_sig_file()
    pr_affiliation.display_sig_affiliation()
    pr_list = pr_affiliation.get_repo_pr("community")
    pr_affiliation.display_pr_list(pr_list)
    pr_affiliation.update_sig_pr("openeuler")



