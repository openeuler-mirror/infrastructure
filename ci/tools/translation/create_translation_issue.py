import requests
import yaml
import sys
import json
import re


def load_yaml(file_path):
    """
    load yaml
    :param file_path: yaml file path
    :return: content of yaml
    """
    with open(file_path) as fp:
        try:
            content = yaml.load(fp.read(), Loader=yaml.Loader)
        except yaml.MarkedYAMLError as e:
            print(e)
            sys.exit(1)
    return content


def get_diff_files(owner, repo, number):
    """
    get the pr's diffs
    :param owner: owner
    :param repo: repo
    :param number: pr number
    :return: diff_files, pr_url
    """
    r = requests.get('https://gitee.com/{}/{}/pulls/{}.diff'.format(owner, repo, number))
    if r.status_code != 200:
        print(r.status_code, r.text)
        print("please check owner: {}, repo: {}, pr_number: {}".format(owner, repo, number))
        sys.exit(1)
    diff_files_list = []
    diff_files = [x.split(' ')[0][2:] for x in r.text.split('diff --git ')[1:]]
    pr_url = "https://gitee.com/{}/{}/pulls/{}".format(owner, repo, number)
    for diff_file in diff_files:
        if diff_file.endswith('\"'):
            d = re.compile(r'/\\[\d\s\S]+')
            diff_file = d.findall(diff_file)
            diff_file = diff_file[0].replace('/', '').replace('\"', '')
            diff_files_list.append(diff_file)
        else:
            diff_files_list.append(diff_file)
    return diff_files_list, pr_url


def check_issue_exits(acc_token, owner, repo):
    """
    check issues exit or not
    :param acc_token: acc_token
    :param owner: owner
    :param repo: repo
    :return:
    """
    get_all_issue_url = "https://gitee.com/api/v5/repos/{}/{}/issues".format(owner, repo)
    page = 1
    response_lists = []
    results = []
    while True:
        param = {
            "access_token": acc_token,
            "state": "open",
            "sort": "created",
            "direction": "desc",
            "page": page,
            "per_page": 100
        }
        r = requests.get(get_all_issue_url, params=param)

        if r.status_code != 200:
            print("Error: bad request, status code: {}".format(r.status_code))
            sys.exit(1)
        if json.loads(r.text):
            response_lists.append(json.loads(r.text))
        if len(json.loads(r.text)) < 100:
            break
        page += 1
    for response_list in response_lists:
        for rsp in response_list:
            results.append(rsp)
    return results


def create_issue(acc_token, owner, repo, p_number, issue_title, assignee, body):
    """
    create issues
    :param acc_token: access_token
    :param owner: owner
    :param repo: repo
    :param p_number: p_number
    :param issue_title: issue_title
    :param assignee: issue owner
    :param body: pr_url
    :return:
    """
    issue_url = 'https://gitee.com/api/v5/repos/{}/issues'.format(owner)
    param = {
        "access_token": acc_token,
        "owner": owner,
        "repo": repo,
        "title": issue_title + "[{}]".format(p_number),
        "assignee": assignee,
        "issue_type": "翻译",
        "body": "Related PR link: +{}".format(body)
    }
    r = requests.post(issue_url, params=param)
    if r.status_code != 201:
        print("ERROR: bad request, status code: {}".format(r.status_code))
        sys.exit(1)
    else:
        if json.loads(r.text).get("number"):
            print("issue has been made successfully, issue number is #{}".format(json.loads(r.text).get("number")))
        else:
            param2 = {
                "access_token": acc_token,
                "owner": owner,
                "repo": repo,
                "title": issue_title + "[{}]".format(p_number),
                "issue_type": "翻译",
                "body": "Related PR link: +{}".format(body)
            }
            res = requests.post(issue_url, params=param2)
            if res.status_code != 201:
                print("Error: bad request, status code: {}".format(res.status_code))
                sys.exit(1)
            print("issue has been made successfully, issue number is #{}".format(json.loads(res.text).get("number")))


def main(owner, repo, token, number):
    """
    main function
    :param owner: owner
    :param repo: repo
    :param token: access_token
    :param number: pull request number
    :return:
    """
    content = load_yaml("translation.yaml")

    issue_related_pr_number = {}
    results = check_issue_exits(token, owner, repo)
    try:
        file_extension = content["file_extension"]
        repositories = content["repositories"]
        issue_title = content["issue_title"]
        assignee = content["sign_to"]
    except KeyError as e:
        print(e)
        sys.exit(1)
    for i in repositories:
        if repo == i["repo"] and owner == i["owner"]:
            file_count = 0
            diff_files, pr_url = get_diff_files(owner, repo, number)
            for diff_file in diff_files:
                if diff_file.split('.')[-1] in file_extension:
                    print("file {} has been changed".format(diff_file))
                    file_count += 1
                else:
                    continue
            if file_count > 0:
                if results:
                    for result in results:
                        issue_related_pr_number[result.get("title").split('.')[-1].replace('[', '').replace(']', '')]\
                            = result.get("number")
                    if number in issue_related_pr_number.keys():
                        print("Error: issue has already created, please go to check issue: #{}"
                                .format(issue_related_pr_number.get(number)))
                        sys.exit(1)
                    else:
                        create_issue(token, owner, repo, number, issue_title, assignee, pr_url)
                else:
                    create_issue(token, owner, repo, number, issue_title, assignee, pr_url)
            else:
                print("repo: {}'s files that end with {} are not changed".format(repo, file_extension))
        else:
            print("ERROR: wrong repo {} or wrong owner {}, please check!".format(repo, owner))
            sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('Required 4 parameters! The pr_owner, pr_repo, access_token and pr_number '
              'need to be transferred in sequence.')
        sys.exit(1)
    pr_owner = sys.argv[1]
    pr_repo = sys.argv[2]
    access_token = sys.argv[3]
    pr_number = sys.argv[4]
    main(pr_owner, pr_repo, access_token, pr_number)
