import sys
import os
import requests
import json

import yaml

Need_LFS_Repos = ['openeuler/BiShengCLanguage', 'openeuler/OSPerformance', 'openeuler/libarchive-rust', 
                  'openeuler/opensource-intern', 'openeuler/yocto-embedded-tools', 'openeuler/hpc', 
                  'openeuler/mugen', 'openeuler/docs'
                  ]


def get_gitee_repos(gitee_token, organization):
    gitee_url = "https://gitee.com/api/v5/orgs/{}/repos".format(organization)
    page = 1
    urls_of_repos = []

    while True:
        params = {
            "access_token": gitee_token,
            "page": page,
            "per_page": 100,
        }
        res = requests.get(url=gitee_url, params=params)

        if res.status_code != 200:
            continue

        if len(res.json()) == 0:
            break

        for r in res.json():
            urls_of_repos.append(r.get("html_url").replace(".git", ""))

        page += 1

    return urls_of_repos


def import_to_github(github_token, gitee_token, gitee_owner, owner, urls):
    # check if it exists in github
    check_url = "https://api.github.com/orgs/{}/repos".format(owner)
    page = 1
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "token %s" % github_token
    }

    repos_names = []
    while True:
        params = {
            "per_page": 100,
            "page": page,
        }

        res = requests.get(url=check_url, params=params, headers=headers)

        if res.status_code != 200:
            continue

        if len(res.json()) == 0:
            break

        for r in res.json():
            repos_names.append(r.get("name"))

        page += 1

    for u in urls:
        repo = u.split("/")[-1]
        if (gitee_owner + "/" + repo) in Need_LFS_Repos:
            continue
        if repo not in repos_names:
            # create empty repo first
            create_url = "https://api.github.com/orgs/%s/repos" % owner
            data = {
                "name": repo,
                "visibility": "public"
            }

            create_response = requests.post(url=create_url, data=json.dumps(data), headers=headers)
            if create_response.status_code not in [201, 200]:
                print("create repo failed")
                continue

            # git clone
            workdir = os.popen("pwd").readlines()[0].replace("\n", "")
            clone_result = os.popen("git clone --bare %s.git" % u).readlines()
            clone_failed = False
            for c in clone_result:
                if "error" in c or "Error" in c or "fatal" in c:
                    print("git clone %s failed" % repo)
                    clone_failed = True
                    break
            if clone_failed:
                continue

            os.chdir("%s/%s.git" % (workdir, repo))

            os.popen("git push --mirror https://oauth2:%s@github.com/%s/%s" % (github_token, owner, repo)).readlines()

            os.chdir(workdir)

            os.popen("rm -rf %s.git" % repo).readlines()
            print("repo %s from gitee has been imported \n" % u)
        else:
            refresh_codes_to_github(u, github_token, gitee_token, owner)


def refresh_codes_to_github(address, hub_token, ee_token, owner):
    s = address.split("/")
    gitee_owner = s[-2]
    repo = s[-1]
    github_owner = owner

    # get gitee repo's branches
    gitee_branches_url = "https://gitee.com/api/v5/repos/{}/{}/branches".format(gitee_owner, repo)
    github_branches_url = "https://api.github.com/repos/{}/{}/branches".format(github_owner, repo)

    github_headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "token %s" % hub_token
    }

    hub_page = 1

    github_branches = {}
    while True:
        # get branches of github repo
        params = {
            "per_page": 100,
            "page": hub_page,
        }
        hub_res = requests.get(url=github_branches_url, params=params, headers=github_headers)
        if hub_res.status_code != 200:
            print("get %s branches in github failed" % repo)
            continue
        if len(hub_res.json()) == 0:
            break
        for r in hub_res.json():
            github_branches[r.get("name")] = r.get("commit").get("sha")

        hub_page += 1

    ee_res = requests.get(url=gitee_branches_url, params={"access_token": ee_token})
    if ee_res.status_code != 200:
        print("get %s branches in gitee failed" % repo)
        return
    gitee_branches = {}
    for r in ee_res.json():
        gitee_branches[r.get("name")] = r.get("commit").get("sha")

    print("compare gitee %s branches with github %s branches" % (repo, repo), gitee_branches, "+++", github_branches)
    fetch_branch, create_branch = [], []
    for b, c in gitee_branches.items():
        if b in github_branches.keys() and c not in github_branches.values():
            fetch_branch.append(b)
        elif b not in github_branches.keys():
            create_branch.append(b)
    if len(fetch_branch) > 0:
        fetch_to_refresh(address, github_owner, repo, hub_token, fetch_branch)
    if len(create_branch) > 0:
        create_new_branch_to_github(address, github_owner, repo, hub_token, create_branch)


def fetch_to_refresh(link, owner, repo, token, branch):
    current_workdir = os.popen("pwd").readlines()[0].replace("\n", "")
    repo_path = "{}/{}".format(current_workdir, repo)
    if not os.path.exists(repo_path):
        if len(branch) > 1:
            os.popen("git clone https://oauth2:{}@github.com/{}/{}".format(
                token, owner, repo
            )).readlines()
        else:
            os.popen("git clone --depth=1 https://oauth2:{}@github.com/{}/{}".format(
                token, owner, repo
            )).readlines()

    os.chdir(repo_path)
    os.popen("git remote add upstream %s" % link).readlines()

    if len(branch) > 1:
        for b in branch:
            if_continue = True
            os.popen("git checkout -f origin/%s" % b).readlines()
            r1 = os.popen("git fetch upstream %s" % b).readlines()
            for r in r1:
                if "error:" in r or "fatal:" in r:
                    print("fetch failed")
                    if_continue = False
                    break
            if not if_continue:
                continue

            os.popen("git merge upstream/%s" % b).readlines()
            os.popen("git push origin HEAD:%s" % b).readlines()
        os.chdir(current_workdir)
        os.popen("rm -rf %s" % repo).readlines()

    else:
        if_continue = True
        r1 = os.popen("git fetch upstream %s" % branch[0]).readlines()
        for r in r1:
            if "error:" in r or "fatal:" in r:
                print("fetch failed")
                if_continue = False
                break
        if if_continue:
            os.popen("git merge upstream/%s" % branch[0]).readlines()
            os.popen("git push origin HEAD:%s" % branch[0]).readlines()
        os.chdir(current_workdir)
        os.popen("rm -rf %s" % repo).readlines()


def create_new_branch_to_github(link, owner, repo, token, branch):
    current_workdir = os.popen("pwd").readlines()[0].replace("\n", "")
    repo_path = "{}/{}".format(current_workdir, repo)
    if not os.path.exists(repo_path):
        os.popen("git clone https://oauth2:{}@github.com/{}/{}".
                 format(token, owner, repo)).readlines()

    os.chdir(repo_path)
    os.popen("git remote add upstream %s" % link).readlines()
    for b in branch:
        push_or_not = True
        r1 = os.popen("git fetch upstream %s" % b).readlines()
        for r in r1:
            if "error:" in r or "fatal:" in r:
                print("fetch failed")
                push_or_not = False
                break
        if not push_or_not:
            continue
        os.popen("git checkout -b {} --track upstream/{}".format(b, b)).readlines()
        os.popen("git push origin {}".format(b)).readlines()

    os.chdir(current_workdir)
    os.popen("rm -rf %s" % repo).readlines()


def load_config_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.load(f.read(), Loader=yaml.SafeLoader)

    return data.get("organizations")


def main():
    gitee_t = sys.argv[1]
    github_t = sys.argv[2]
    config_path = sys.argv[3]

    if gitee_t == "" or github_t == "" or config_path == "":
        print("miss token params")
        sys.exit(1)

    organizations = load_config_yaml(config_path)

    if len(organizations) == 0:
        sys.exit(1)

    print("org: ", organizations)
    for organization in organizations:
        for k, v in organization.items():
            print("start migrate from gitee %s to github %s" % (k, v))
            import_to_github(github_t, gitee_t, k, v, get_gitee_repos(gitee_t, k))


if __name__ == '__main__':
    main()
