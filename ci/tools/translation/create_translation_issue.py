import requests
import yaml
import sys


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
    diff_files = [x.split(' ')[0][2:] for x in r.text.split('diff --git ')[1:]]
    pr_url = "https://gitee.com/{}/{}/pulls/{}".format(owner, repo, number)
    return diff_files, pr_url


def create_issue(acc_token, owner, repo, issue_title, assignee, body):
    """
    create issues
    :param acc_token: access_token
    :param owner: owner
    :param repo: repo
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
        "title": issue_title,
        "assignee": assignee,
        "issue_type": "翻译",
        "body": "Related PR link: +{}".format(body)
    }
    r = requests.post(issue_url, params=param)
    if r.status_code != 201:
        print("ERROR: bad request, status_code: {}".format(r.status_code))
        sys.exit(1)
    else:
        print("issue has been made successfully")


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
                create_issue(token, owner, repo, issue_title, assignee, pr_url)
            else:
                print("repo: {}'s files that end with {} are not changed".format(repo, file_extension))
        else:
            print("ERROR: wrong repo {} or wrong owner {}, please check!".format(repo, owner))


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
