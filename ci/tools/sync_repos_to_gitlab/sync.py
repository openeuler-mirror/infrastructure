import time

import requests
import sys
import yaml


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


def sync_to_gitlab(username, user_pass, target, gitlab_tk, repos_orgs, plat):
    groups_id = check_target_org_exists(username, user_pass, target, gitlab_tk)
    repos = get_single_group_exists_repos(groups_id, gitlab_tk)
    headers = {"Private-Token": gitlab_tk}
    undo = []
    create_repo_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects'.format(username, user_pass)
    for k in repos_orgs.keys():
        r = k.split("/")[-1]
        if r in repos:
            continue
        if r in ["tree", "Tree"]:
            if "%s1" % r in repos:
                continue
        create_data = {
            "name": r,
            "path": r,
            "import_url": k,
            "namespace_id": groups_id,
            "visibility": "public",
            "mirror": True,
        }
        if plat == "gitlab":
            create_data["import_url"] = k + ".git"
        print("import repo : ", k)
        # Tree or tree can't been created in gitlab because of the name tree(or Tree) of repo is illegal
        if k.split("/")[-1] in ["tree", "Tree"]:
            create_data["name"] = "%s1" % k.split("/")[-1]
            create_data["path"] = "%s1" % k.split("/")[-1]
        r = requests.post(url=create_repo_url, headers=headers, data=create_data)
        if r.status_code != 201:
            print(r.status_code)
            undo.append(create_data)
            continue
    if len(undo) != 0:
        for d in undo:
            r = requests.post(url=create_repo_url, headers=headers, data=d)
            if r.status_code != 201:
                print("create %s failed" % d)
                continue


def get_all_repos_in_src_org(src_platform, src_org, src_url, gitee_tk, github_tk):
    page = 1
    repo_org = {}
    if src_platform == "gitee":
        gitee_url = "https://{}.com/api/v5/orgs/{}/repos".format(src_platform, src_org)
        while True:
            data = {"page": page, "access_token": gitee_tk, "per_page": 100}
            req = requests.get(gitee_url, data)
            if req.status_code != 200:
                sys.exit(1)
            if 0 < len(req.json()) <= 100:
                for r in req.json():
                    repo_org["https://gitee.com/" + r["full_name"]] = r["full_name"].split("/")[0]
                page += 1
            if len(req.json()) == 0:
                break
    if src_platform == "github":
        headers = {"Authorization": "token %s" % github_tk}
        while True:
            data = {"per_page": 100}
            res = requests.get(url="https://api.{}.com/orgs/{}/repos?page={}".
                               format(src_platform, src_org, page), headers=headers, data=data)
            if res.status_code != 200:
                sys.exit(1)
            if 0 < len(res.json()) <= 100:
                for i in res.json():
                    repo_org["https://github.com/" + i["full_name"]] = i["full_name"].split("/")[0]
                page += 1
            if len(res.json()) == 0:
                break
    if src_platform == "gitlab":
        g_id = ""
        g_name = src_url.split("//")[-1].split("/")[1]
        while True:
            data = {"per_page": 100}
            res = requests.get(url="https://{}/api/v4/groups?page={}".
                               format(src_url.split("//")[-1].split("/")[0], page), data=data)
            if res.status_code != 200:
                print(res.status_code)
                sys.exit(1)
            if 0 < len(res.json()) <= 100:
                for i in res.json():
                    # get source gitlab group's id
                    if i["path"] == g_name:
                        g_id = i["id"]
                page += 1
            if len(res.json()) == 0:
                break
        page2 = 1
        while True:
            get_repo_id_url = "https://{}/api/v4/groups/{}/projects?page={}"\
                .format(src_url.split("//")[-1].split("/")[0], g_id, page2)
            repo_res = requests.get(url=get_repo_id_url, data=data)
            if repo_res.status_code != 200:
                print("bad request", repo_res.status_code)
            if 0 < len(repo_res.json()) <= 100:
                for j in repo_res.json():
                    repo_org[src_url + j["path"]] = j["path_with_namespace"].split("/")[0]
                page2 += 1
            if len(repo_res.json()) == 0:
                break
    return repo_org


def get_single_group_exists_repos(single_group_id, gitlab_tk):
    repo_names = []
    page = 1
    data = {"per_page": 100}
    headers = {
        'Private-Token': gitlab_tk
    }
    while True:
        url = "https://source.openeuler.sh/api/v4/groups/{}/projects?page={}".format(single_group_id, page)
        r = requests.get(url=url, headers=headers, data=data)
        if 0 < len(r.json()) <= 100:
            for i in r.json():
                repo_names.append(i["path"])
            page += 1
        if len(r.json()) == 0:
            break
    return repo_names


def check_target_org_exists(username, user_pass, target, gitlab_tk):
    group_id = ""
    create_groups_url = "https://{}:{}@source.openeuler.sh/api/v4/groups".format(username, user_pass)
    headers = {
        'Private-Token': gitlab_tk
    }
    create_data = {
        "name": target,
        "path": target,
        "visibility": "public"
    }
    page = 1
    while True:
        d = {"per_page": 100}
        url = "https://source.openeuler.sh/api/v4/groups?page={}".format(page)
        r = requests.get(url=url, headers=headers, data=d)
        if r.status_code != 200:
            print("get group %s id failed" % target)
            sys.exit(1)
        if 0 < len(r.json()) <= 100:
            for i in r.json():
                if i["path"] == target:
                    group_id = i["id"]
            page += 1
        if len(r.json()) == 0:
            break
    if group_id == "":
        r = requests.post(url=create_groups_url, headers=headers, data=create_data)
        if r.status_code != 201:
            print("create %s groups failed" % target)
            sys.exit(1)
        group_id = r.json()[0]["id"]
    return group_id


# upload the organizations' repositories from different platforms to gitlab
def refresh_organization_repos_in_gitlab(username, user_pass, single_group_id,
                                         src_platform, src_org, src_url, gitlab_tk, gitee_tk, github_tk):
    repos_id = {}
    page = 1
    data = {"per_page": 100}
    while True:
        url = "https://{}:{}@source.openeuler.sh/api/v4/groups/{}/projects?page={}" \
            .format(username, user_pass, single_group_id, page)
        r = requests.get(url=url, data=data)
        if 0 < len(r.json()) <= 100:
            for i in r.json():
                repos_id[i["path"]] = i["id"]
            page += 1
        if len(r.json()) == 0:
            break
    for rp, rid in repos_id.items():
        sha = ""
        import_url = ""
        if src_platform == "gitee":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            gitee_url = "https://gitee.com/api/v5/repos/{}/{}/commits".format(src_org, rp)
            gitee_data = {"access_token": gitee_tk}
            gitee_res = requests.get(url=gitee_url, data=gitee_data)
            if gitee_res.status_code != 200:
                continue
            gitee_import_url = gitee_res.json()[0]["html_url"].split("/commit/")[0]
            gitee_sha = gitee_res.json()[0]["sha"]
            sha = gitee_sha
            import_url = gitee_import_url
        if src_platform == "github":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            github_url = "https://api.github.com/repos/{}/{}/commits".format(src_org, rp)
            github_header = {"Authorization": "token %s" % github_tk}
            github_res = requests.get(url=github_url, headers=github_header)
            if github_res.status_code != 200:
                continue
            github_import_url = github_res.json()[0]["html_url"].split("/commit/")[0]
            github_sha = github_res.json()[0]["sha"]
            sha = github_sha
            import_url = github_import_url
        if src_platform == "gitlab":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            get_group_id = ""
            data = {"per_page": 100}
            while True:
                get_group_id_url = "https://" + src_url.split("/")[2] + "/api/v4/groups?page={}".format(page)
                get_group_res = requests.get(url=get_group_id_url, data=data)
                if get_group_res.status_code != 200:
                    continue
                if 0 < len(get_group_res.json()) <= 100:
                    for i in get_group_res.json():
                        if i["path"] == src_org:
                            get_group_id = i["id"]
                    page += 1
                if len(get_group_res.json()) == 0:
                    break
            repo_id = ""
            page2 = 1
            while True:
                get_repo_id_url = "https://{}/api/v4/groups/{}/projects?page={}".\
                    format(src_url.split("/")[2], get_group_id, page2)
                repo_res = requests.get(url=get_repo_id_url, data=data)
                if repo_res.status_code != 200:
                    continue
                if 0 < len(repo_res.json()) <= 100:
                    for j in repo_res.json():
                        if j["path"] == rp:
                            repo_id = j["id"]
                    page2 += 1
                if len(repo_res.json()) == 0:
                    break

            gitlab_url = "https://{}/api/v4/projects/{}/repository/commits".format(src_url.split("/")[2], repo_id)
            gitlab_res = requests.get(url=gitlab_url)
            if gitlab_res.status_code != 200:
                continue
            time.sleep(0.2)
            gitlab_import_url = gitlab_res.json()[0]["web_url"].split("/-/commit/")[0]
            gitlab_sha = gitlab_res.json()[0]["sha"]
            sha = gitlab_sha
            import_url = gitlab_import_url

        # get local repo's commits
        target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/commits'\
            .format(username, user_pass, rid)
        target_gitlab_res = requests.get(url=target_gitlab_url)
        if target_gitlab_res.status_code != 200:
            continue
        target_gitlab_sha = target_gitlab_res.json()[0]["id"]
        if target_gitlab_sha != sha:
            print("true, begin to delete and reload")
            headers = {
                'Private-Token': gitlab_tk
            }

            create_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects'.format(username, user_pass)
            data = {
                "name": import_url.split("/")[-1],
                "path": import_url.split("/")[-1],
                "import_url": import_url,
                "namespace_id": single_group_id,
                "visibility": "public",
                "mirror": True,
            }
            print("delete and recreate repo : ", import_url)
            if src_platform == "gitlab":
                data["import_url"] = import_url + ".git"
            # delete
            delete_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}'.format(username, user_pass, rid)
            r = requests.delete(url=delete_url, headers=headers)
            if r.status_code != 202:
                requests.delete(url=delete_url, headers=headers)
            time.sleep(0.2)
            # refresh
            n = 0
            while n < 2:
                create_res = requests.post(url=create_url, headers=headers, data=data)
                if create_res.status_code != 201:
                    print("bad create ", create_res.status_code)
                    n += 1
                else:
                    break
            time.sleep(0.3)


# upload the single repository to gitlab
def refresh_single_repo_in_gitlab(username, user_pass, single_group_id,
                                  src_platform, src_org, src_url, gitlab_tk, gitee_tk, github_tk, repos):
    repos_id = {}
    page = 1
    data = {"per_page": 100}
    while True:
        url = "https://{}:{}@source.openeuler.sh/api/v4/groups/{}/projects?page={}" \
            .format(username, user_pass, single_group_id, page)
        r = requests.get(url=url, data=data)
        if 0 < len(r.json()) <= 100:
            for i in r.json():
                for j in repos:
                    if i["path"] == j.split("/")[-1]:
                        repos_id[i["path"]] = i["id"]
            page += 1
        if len(r.json()) == 0:
            break
    for rp, rid in repos_id.items():
        sha = ""
        import_url = ""
        if src_platform == "gitee":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            gitee_url = "https://gitee.com/api/v5/repos/{}/{}/commits".format(src_org, rp)
            gitee_data = {"access_token": gitee_tk}
            gitee_res = requests.get(url=gitee_url, data=gitee_data)
            if gitee_res.status_code != 200:
                continue
            gitee_sha = gitee_res.json()[0]["sha"]
            sha = gitee_sha
            import_url = "https://gitee.com/{}/{}".format(src_org, rp)
        if src_platform == "github":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            github_url = "https://api.github.com/repos/{}/{}/commits".format(src_org, rp)
            github_header = {"Authorization": "token %s" % github_tk}
            github_res = requests.get(url=github_url, headers=github_header)
            if github_res.status_code != 200:
                continue
            github_sha = github_res.json()[0]["sha"]
            sha = github_sha
            import_url = "https://github.com/{}/{}".format(src_org, rp)
        if src_platform == "gitlab":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            get_group_id = ""
            data = {"per_page": 100}
            while True:
                get_group_id_url = "https://" + src_url.split("/")[2] + "/api/v4/groups?page={}".format(page)
                get_group_res = requests.get(url=get_group_id_url, data=data)
                if get_group_res.status_code != 200:
                    continue
                if 0 < len(get_group_res.json()) <= 100:
                    for i in get_group_res.json():
                        if i["path"] == src_org:
                            get_group_id = i["id"]
                    page += 1
                if len(get_group_res.json()) == 0:
                    break
            repo_id = ""
            page2 = 1
            while True:
                get_repo_id_url = "https://{}/api/v4/groups/{}/projects?page={}". \
                    format(src_url.split("/")[2], get_group_id, page2)
                repo_res = requests.get(url=get_repo_id_url, data=data)
                if repo_res.status_code != 200:
                    continue
                if 0 < len(repo_res.json()) <= 100:
                    for j in repo_res.json():
                        if j["path"] == rp:
                            repo_id = j["id"]
                    page2 += 1
                if len(repo_res.json()) == 0:
                    break
            gitlab_url = "https://{}/api/v4/projects/{}/repository/commits".format(src_url.split("/")[2], repo_id)
            gitlab_res = requests.get(url=gitlab_url)
            if gitlab_res.status_code != 200:
                print(gitlab_res.status_code)
                continue
            time.sleep(0.2)
            gitlab_import_url = gitlab_res.json()[0]["web_url"].split("/-/commit/")[0]
            gitlab_sha = gitlab_res.json()[0]["id"]
            sha = gitlab_sha
            import_url = gitlab_import_url

        # get local repo's commits
        target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/commits' \
            .format(username, user_pass, rid)
        target_gitlab_res = requests.get(url=target_gitlab_url)
        if target_gitlab_res.status_code != 200:
            continue
        target_gitlab_sha = target_gitlab_res.json()[0]["id"]
        if target_gitlab_sha != sha:
            headers = {
                'Private-Token': gitlab_tk
            }
            create_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects'.format(username, user_pass)
            data = {
                "name": import_url.split("/")[-1],
                "path": import_url.split("/")[-1],
                "import_url": import_url,
                "namespace_id": single_group_id,
                "visibility": "public",
                "mirror": True,
            }
            print("delete and recreate single repo : ", import_url)
            if src_platform == "gitlab":
                data["import_url"] = import_url + "git"
            # delete and refresh
            delete_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}'.format(username, user_pass, rid)
            r = requests.delete(url=delete_url, headers=headers)
            if r.status_code != 202:
                requests.delete(url=delete_url, headers=headers)
            time.sleep(0.2)
            n = 0
            while n < 2:
                create_res = requests.post(url=create_url, headers=headers, data=data)
                if create_res.status_code != 201:
                    n += 1
                else:
                    break
            time.sleep(0.3)


if __name__ == '__main__':
    if len(sys.argv) != 6:
        print('Required 5 parameters!')
        sys.exit(1)
    name = sys.argv[1]
    password = sys.argv[2]
    gitlab_token = sys.argv[3]
    gitee_token = sys.argv[4]
    github_token = sys.argv[5]
    tasks = load_yaml("./sync_conf.yaml")["sync_tasks"]
    for t in tasks:
        if t["task"][0]["type"] == "organization":
            source_org = t["task"][0]["source"][0]["org"]
            target_org = t["task"][0]["target"][0]["org"]
            source_platform = t["task"][0]["source"][0]["platform"]
            target_platform = t["task"][0]["target"][0]["platform"]
            source_url = t["task"][0]["source"][0]["url"]

            repos_org = get_all_repos_in_src_org(source_platform, source_org, source_url, gitee_token, github_token)
            # first time to sync to gitlab
            sync_to_gitlab(name, password, target_org, gitlab_token, repos_org, source_platform)

            # refresh organizations' repos in gitlab when they have been changed
            repos_group_id = check_target_org_exists(name, password, target_org, gitlab_token)
            refresh_organization_repos_in_gitlab(name, password, repos_group_id, source_platform, source_org,
                                                 source_url, gitlab_token, gitee_token, github_token)

        elif t["task"][0]["type"] == "repository":
            target_org = t["task"][0]["target"][0]["org"]
            source_org = t["task"][0]["source"][0]["org"]
            source_platform = t["task"][0]["source"][0]["platform"]
            target_platform = t["task"][0]["target"][0]["platform"]
            source_url = t["task"][0]["source"][0]["url"]

            repos_org = {}
            repos_url = []
            for u in t["task"][0]["source"][0]["repos"]:
                repos_url.append(source_url + "/" + u)
                repos_org[source_url + "/" + u] = target_org

            # first time to sync to gitlab
            sync_to_gitlab(name, password, target_org, gitlab_token, repos_org, source_platform)

            # refresh single repo in gitlab when it has been changed
            repos_group_id = check_target_org_exists(name, password, target_org, gitlab_token)
            refresh_single_repo_in_gitlab(name, password, repos_group_id, source_platform, source_org,
                                          source_url, gitlab_token, gitee_token, github_token, repos_url)

