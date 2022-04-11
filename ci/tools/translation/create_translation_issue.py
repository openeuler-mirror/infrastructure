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
    with open(file_path, encoding="utf-8") as fp:
        try:
            content = yaml.load(fp.read(), Loader=yaml.Loader)
        except yaml.MarkedYAMLError as e:
            print(e)
            sys.exit(1)
    return content


def get_diff_files(owner, repo, number, acc_token):
    """
    get the pr's diffs
    :param owner: owner ep:openeuler
    :param repo: repo ep: docs
    :param number: pull request number
    :param acc_token: access_token
    :return: list of diffs, pull request url
    """
    param = {"access_token": acc_token}
    r = requests.get('https://gitee.com/{}/{}/pulls/{}.diff'.format(owner, repo, number), params=param)
    if r.status_code != 200:
        print(r.status_code, r.text)
        print("please check owner: {}, repo: {}, pr_number: {}".format(owner, repo, number))
        sys.exit(1)
    diff_files_list = []
    diff_files = [x.split(' ')[0][2:] for x in r.text.split('diff --git ')[1:]]
    pr_url = "https://gitee.com/{}/{}/pulls/{}".format(owner, repo, number)
    for diff_file in diff_files:
        if diff_file.endswith('\"'):
            d = re.compile(r'/[\d\s\S]+')
            diff_file = d.findall(diff_file)
            diff_file = diff_file[0].replace('/', '', 1).replace('\"', '')
            diff_files_list.append(diff_file)
        else:
            diff_files_list.append(diff_file)
    return diff_files_list, pr_url


def check_issue_exits(acc_token, owner, repo):
    """
    check issues exit or not
    :param acc_token: access_token
    :param owner: owner ep:openeuler
    :param repo: repo ep: docs
    :return: issues list of the repository
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
    :param owner: owner ep:openeuler
    :param repo: repo ep: docs
    :param p_number: pull request number
    :param issue_title: issue_title
    :param assignee: issue owner
    :param body: pull request url
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


def get_pr_information(owner, repo, number):
    url = "https://gitee.com/api/v5/repos/{}/{}/pulls/{}".format(owner, repo, number)
    r = requests.get(url)
    if r.status_code != 200:
        print("bad request")
        sys.exit(1)
    return json.loads(r.text)


def get_pr_issue_title(issue_url):
    r = requests.get(issue_url)
    if r.status_code != 200:
        print("bad request")
        sys.exit(1)
    res = r.json()
    if len(res) == 0:
        return ""
    return r.json()[0]["title"]


def main(owner, repo, token, number):
    """
    main function
    :param owner: owner ep:openeuler
    :param repo: repo ep: docs
    :param token: access_token
    :param number: pull request number
    :return:
    """
    content = load_yaml("translation.yaml")
    results = check_issue_exits(token, owner, repo)
    issue_related_pr_number = {}
    owner_repo_relationship = {}
    current_assignee = {}
    current_file_extension = {}
    current_issue_title = {}
    file_extension = []
    trigger_path = []
    pr_state = get_pr_information(owner, repo, number)["state"]
    pr_issue_url = get_pr_information(owner, repo, number)["issue_url"]
    pr_issue_title = get_pr_issue_title(pr_issue_url)

    try:
        repositories = content["repositories"]
    except KeyError as e:
        print(e)
        sys.exit(1)
    for r in repositories:
        owner_repo_relationship[r["repo"]] = r["owner"]

    if owner in owner_repo_relationship.values() and repo in owner_repo_relationship.keys():
        for repository in repositories:
            if owner == repository["owner"] and repo == repository["repo"] and repository["auto_create_issue"]:
                file_count = 0
                diff_files, pr_url = get_diff_files(owner, repo, number, token)
                for issue_trigger in repository["issue_triggers"]:
                    file_extension.append(issue_trigger["file_extension"])
                    trigger_path.append(issue_trigger["trigger_pr_path"])
                    for diff_file in diff_files:
                        if diff_file.startswith(issue_trigger["trigger_pr_path"]) \
                                and diff_file.split('.')[-1] in issue_trigger["file_extension"]:
                            print("file {} has been changed".format(diff_file))
                            file_count += 1
                            current_assignee[issue_trigger["trigger_pr_path"]] = issue_trigger["assign_issue"][1]["sign_to"]
                            current_file_extension[issue_trigger["trigger_pr_path"]] = issue_trigger["file_extension"]
                            current_issue_title[issue_trigger["trigger_pr_path"]] = issue_trigger["assign_issue"][0]["title"]
                        else:
                            continue

                if file_count > 0:
                    if results:
                        for result in results:
                            issue_number = result.get("title").split('.')[-1].replace('[', '').replace(']', '')
                            issue_related_pr_number[issue_number] = result.get("number")
                        if number in issue_related_pr_number.keys():
                            print("Error: issue has already created, please go to check issue: #{}"
                                  .format(issue_related_pr_number[number]))
                            sys.exit(1)
                        else:
                            for k in current_file_extension.keys():
                                if pr_issue_title.startswith("[Auto]"):
                                    continue
                                create_issue(token, owner, repo, number, current_issue_title[k],
                                             current_assignee[k], pr_url)
                    else:
                        for k in current_file_extension.keys():
                            if pr_issue_title.startswith("[Auto]"):
                                continue
                            create_issue(token, owner, repo, number, current_issue_title[k],
                                         current_assignee[k], pr_url)
                else:
                    print("NOTE: repository: {}/{}'s files in {} that end with {} are not changed"
                          .format(owner, repo, trigger_path, file_extension))
            elif owner == repository["owner"] and repo == repository["repo"] and not repository["auto_create_issue"]:
                comment_url = "https://gitee.com/api/v5/repos/{}/{}/pulls/{}/comments?page=1&per_page=100" \
                    .format(owner, repo, number)
                comment_params = {
                    "access_token": token,
                    "direction": "asc"
                }
                trigger_command = repository["trigger_command"] if repository["trigger_command"] else ""
                cancel_command = repository["cancel_command"] if repository["cancel_command"] else ""

                regex = re.compile(trigger_command)
                regex2 = re.compile(cancel_command)
                r = requests.get(comment_url, params=comment_params)
                if r.status_code != 200:
                    print("ERROR: bad request, status code: {}".format(r.status_code))
                    sys.exit(1)
                items = json.loads(r.text)
                do_translate = False
                cancel_translate = False
                maps = {}
                for i in items:
                    if regex.fullmatch(i["body"]):
                        maps[i["body"]] = i["created_at"]
                    if regex2.fullmatch(i["body"]):
                        maps[i["body"]] = i["created_at"]
                if trigger_command in maps.keys():
                    time1 = maps[trigger_command]
                else:
                    time1 = ""
                if cancel_command in maps.keys():
                    time2 = maps[cancel_command]
                else:
                    time2 = ""
                if time1 > time2:
                    do_translate = True
                if time1 < time2:
                    cancel_translate = True

                diff_files, pr_url = get_diff_files(owner, repo, number, token)
                if do_translate and pr_state == "merged":
                    if results:
                        for result in results:
                            issue_number = result.get("title").split('.')[-1].replace('[', '').replace(']', '')
                            issue_related_pr_number[issue_number] = result.get("number")
                        if number in issue_related_pr_number.keys():
                            print("Error: issue has already created, please go to check issue: #{}"
                                  .format(issue_related_pr_number[number]))
                            sys.exit(1)
                        else:
                            create_issue(token, owner, repo, number,
                                         repository["issue_triggers"]["assign_issue"][0]["title"],
                                         repository["issue_triggers"]["assign_issue"][1]["sign_to"], pr_url)
                    else:
                        create_issue(token, owner, repo, number, repository["issue_triggers"]["assign_issue"][0]["title"],
                                     repository["issue_triggers"]["assign_issue"][1]["sign_to"], pr_url)
                elif cancel_translate:
                    print("not need to create issue for pull request")

                else:
                    print("not need to create issue for pull request")
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
