import os
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


def write_to_log(repo_url, gid):
    with open("./sync.log", "a", encoding="utf-8", ) as f:
        f.writelines(repo_url + "::" + str(gid) + "\n")


def sync_to_gitlab(username, user_pass, target, gitlab_tk, repos_orgs, plat):
    groups_id = check_target_org_exists(username, user_pass, target, gitlab_tk)
    repos = get_single_group_exists_repos(username, user_pass, groups_id, gitlab_tk)
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
            "lfs_enabled": True
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
            print(r.status_code, r.json())
            undo.append(create_data)
        time.sleep(0.1)
    if len(undo) != 0:
        for d in undo:
            r = requests.post(url=create_repo_url, headers=headers, data=d)
            if r.status_code != 201:
                print("create %s failed" % d)
                write_to_log(d["import_url"], d["namespace_id"])
                time.sleep(0.1)


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
            get_repo_id_url = "https://{}/api/v4/groups/{}/projects?page={}" \
                .format(src_url.split("//")[-1].split("/")[0], g_id, page2)
            repo_res = requests.get(url=get_repo_id_url, data=data)
            if repo_res.status_code != 200:
                continue
            if 0 < len(repo_res.json()) <= 100:
                for j in repo_res.json():
                    repo_org[src_url + j["path"]] = j["path_with_namespace"].split("/")[0]
                page2 += 1
            if len(repo_res.json()) == 0:
                break
    return repo_org


def get_single_group_exists_repos(username, user_pass, single_group_id, gitlab_tk):
    repo_names = []
    page = 1
    data = {"per_page": 100}
    headers = {
        'Private-Token': gitlab_tk
    }
    while True:
        url = "https://{}:{}@source.openeuler.sh/api/v4/groups/{}/projects?page={}". \
            format(username, user_pass, single_group_id, page)
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
        url = "https://{}:{}@source.openeuler.sh/api/v4/groups?page={}".format(username, user_pass, page)
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
        group_id = r.json()["id"]
    return group_id


# use api to get group's name or path by group_id
def get_group_detail_by_id(username, user_pass, g_id):
    url = "https://{}:{}@source.openeuler.sh/api/v4/groups/{}".format(username, user_pass, g_id)
    req = requests.get(url=url)
    if req.status_code == 200:
        return req.json().get("path")


# use git to refresh repos in gitlab:source.openeuler.sh
def git_for_big_repos(g_name, im_url, r_name, r_id, branch_list, u_name, u_pass, gitlab_token):
    """
    :param g_name: group name
    :param im_url: import url from gitee, github, or gitlab
    :param r_name: name of repo
    :param r_id: id of repo
    :param branch_list: branches are not same with gitee, github or gitlab
    :param u_name: user name
    :param u_pass: user pass
    :param gitlab_token: token
    :return:
    """
    os.popen("rm -rf %s" % r_name)
    work_dir = os.popen("pwd").readlines()[0].replace("\n", "")
    not_exists_branches = []
    for b, v in branch_list.items():
        if v is not None:
            os.popen("git clone -b {} --depth=1 https://{}:{}@source.openeuler.sh/{}/{}.git"
                     .format(b, u_name, u_pass, g_name, r_name)).readlines()
            os.chdir("%s/%s" % (work_dir, r_name))
            os.popen("git config user.name wanghao;git config user.email shalldows@163.com")
            os.popen("git remote add upstream {}".format(im_url)).readlines()
            fetch_res = os.popen("git fetch upstream {}".format(b, b)).readlines()
            fetch_success = True
            for f in fetch_res:
                if "error:" in f or "fatal:" in f:
                    os.chdir(work_dir)
                    os.popen("rm -rf {}".format(r_name)).readlines()
                    fetch_success = False
                    break

            if not fetch_success:
                continue

            merge_res = os.popen("git merge upstream/%s --allow-unrelated-histories" % b)
            for pr in merge_res:
                if "error:" in pr or "fatal:" in pr:
                    os.chdir(work_dir)
                    os.popen("rm -rf {}".format(r_name)).readlines()
                    break
            os.popen("git push origin HEAD:%s" % b).readlines()
            os.chdir(work_dir)
            os.popen("rm -rf {}".format(r_name)).readlines()
        else:
            if b.startswith("sync"):
                continue

            not_exists_branches.append(b)

    if len(not_exists_branches) != 0:
        os.popen("git clone --depth=1 https://{}:{}@source.openeuler.sh/{}/{}.git"
                 .format(u_name, u_pass, g_name, r_name)).readlines()
        os.chdir("%s/%s" % (work_dir, r_name))

        os.popen("git config user.name wanghao;git config user.email shalldows@163.com")
        os.popen("git remote add upstream {}".format(im_url)).readlines()

        for br in not_exists_branches:
            fetch_result = os.popen("git fetch upstream %s" % br).readlines()
            should_continue = True
            for fr in fetch_result:
                if "error" in fr:
                    should_continue = False
                    break

            if not should_continue:
                continue
            res = os.popen("git checkout -b {} --track upstream/{}".format(br, br)).readlines()
            for pr in res:
                if "error:" in pr:
                    os.chdir(work_dir)
                    os.popen("rm -rf {}".format(r_name)).readlines()
                    break

            os.popen("git push origin {}".format(br)).readlines()
        os.chdir(work_dir)
        os.popen("rm -rf {}".format(r_name)).readlines()


# upload the organizations' repositories from different platforms to gitlab
def refresh_organization_repos_in_gitlab(username, user_pass, single_group_id,
                                         src_platform, src_org, src_url, gitlab_tk, gitee_tk, github_tk):
    repos_id = {}
    page = 1
    data = {"per_page": 100}

    has_diff_commits = False

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
        # param which is used by git
        has_diff_branches_commits = {}

        import_url = ""
        if src_platform == "gitee":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")

            # get all branches and theirs commits
            branch_url = "https://gitee.com/api/v5/repos/{}/{}/branches".format(src_org, rp)
            branch_data = {"access_token": gitee_tk}
            branch_res = requests.get(url=branch_url, params=branch_data)
            if branch_res.status_code != 200:
                continue
            branches = {}
            for b in branch_res.json():
                branches[b.get("name")] = b.get("commit").get("sha")

            gitlab_branches = {}
            target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/branches' \
                .format(username, user_pass, rid)
            target_gitlab_res = requests.get(url=target_gitlab_url)
            if target_gitlab_res.status_code != 200 or len(target_gitlab_res.json()) == 0:
                continue
            for g in target_gitlab_res.json():
                gitlab_branches[g.get("name")] = g.get("commit").get("id")

            import_url = "https://gitee.com/{}/{}".format(src_org, rp)

            for b, s in branches.items():
                if s != gitlab_branches.get(b):
                    has_diff_branches_commits[b] = gitlab_branches.get(b)
                    has_diff_commits = True
                else:
                    has_diff_commits = False

        if src_platform == "github":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            github_url = "https://api.github.com/repos/{}/{}/branches".format(src_org, rp)
            github_header = {"Authorization": "token %s" % github_tk}
            github_res = requests.get(url=github_url, headers=github_header)
            if github_res.status_code != 200:
                continue

            branches = {}
            for b in github_res.json():
                branches[b.get("name")] = b.get("commit").get("sha")

            gitlab_branches = {}
            target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/branches' \
                .format(username, user_pass, rid)
            target_gitlab_res = requests.get(url=target_gitlab_url)
            if target_gitlab_res.status_code != 200 or len(target_gitlab_res.json()) == 0:
                continue
            for g in target_gitlab_res.json():
                gitlab_branches[g.get("name")] = g.get("commit").get("id")

            import_url = "https://github.com/{}/{}".format(src_org, rp)

            for b, s in branches.items():
                if s != gitlab_branches.get(b):
                    has_diff_branches_commits[b] = gitlab_branches.get(b)
                    has_diff_commits = True
                else:
                    has_diff_commits = False

        if src_platform == "gitlab":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            get_group_id = ""
            data = {"per_page": 100}
            while True:
                get_group_id_url = "https://" + src_url.split("/")[2] + "/api/v4/groups?page={}".format(page)
                get_group_res = requests.get(url=get_group_id_url, params=data)
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

            gitlab_url = "https://{}/api/v4/projects/{}/repository/branches".format(src_url.split("/")[2], repo_id)
            gitlab_res = requests.get(url=gitlab_url)
            if gitlab_res.status_code != 200:
                continue

            # get all branches and theirs newly commits
            branches = {}
            for b in gitlab_res.json():
                branches[b.get("name")] = b.get("commit").get("id")

            gitlab_branches = {}
            target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/branches' \
                .format(username, user_pass, rid)
            target_gitlab_res = requests.get(url=target_gitlab_url)
            if target_gitlab_res.status_code != 200 or len(target_gitlab_res.json()) == 0:
                continue
            for g in target_gitlab_res.json():
                gitlab_branches[g.get("name")] = g.get("commit").get("id")

            import_url = "https://{}/{}/{}".format(src_url.split("/")[2], src_org, rp)

            for b, s in branches.items():
                if s != gitlab_branches.get(b):
                    has_diff_branches_commits[b] = gitlab_branches.get(b)
                    has_diff_commits = True
                else:
                    has_diff_commits = False

            time.sleep(0.2)

        if has_diff_commits:

            print("true, begin to delete and reload")
            headers = {
                'Private-Token': gitlab_tk
            }

            # use git for a big storage repo
            single_group_name = get_group_detail_by_id(username, user_pass, single_group_id)

            # get repo's storage by api
            get_storage_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}'.format(username, user_pass, rid)
            get_storage_params = {
                "statistics": "true"
            }
            res_storage = requests.get(url=get_storage_url, params=get_storage_params, headers=headers)
            if res_storage.status_code != 200:
                res_storage = requests.get(url=get_storage_url, params=get_storage_params, headers=headers)

            storage = res_storage.json().get("statistics").get("repository_size")
            if storage is None or storage == 0:
                continue

            if storage > 1073741824:
                git_for_big_repos(single_group_name, import_url, rp, rid, has_diff_branches_commits, username,
                                  user_pass, gitlab_tk)

            else:
                create_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects'.format(username, user_pass)
                data = {
                    "name": import_url.split("/")[-1],
                    "path": import_url.split("/")[-1],
                    "import_url": import_url,
                    "namespace_id": single_group_id,
                    "visibility": "public",
                    "mirror": True,
                    "lfs_enabled": True
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
                if n == 2:
                    write_to_log(data["import_url"], data["namespace_id"])
                time.sleep(0.3)


# upload the single repository to gitlab
def refresh_single_repo_in_gitlab(username, user_pass, single_group_id,
                                  src_platform, src_org, src_url, gitlab_tk, gitee_tk, github_tk, repos):
    repos_id = {}
    page = 1
    data = {"per_page": 100}
    has_diff_commits = False

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
        # param which is used by git
        has_diff_branches_commits = {}

        import_url = ""
        if src_platform == "gitee":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")

            branch_url = "https://gitee.com/api/v5/repos/{}/{}/branches".format(src_org, rp)
            branch_data = {"access_token": gitee_tk}
            branch_res = requests.get(url=branch_url, params=branch_data)
            if branch_res.status_code != 200:
                continue
            branches = {}
            for b in branch_res.json():
                branches[b.get("name")] = b.get("commit").get("sha")

            gitlab_branches = {}
            target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/branches' \
                .format(username, user_pass, rid)
            target_gitlab_res = requests.get(url=target_gitlab_url)
            if target_gitlab_res.status_code != 200 or len(target_gitlab_res.json()) == 0:
                continue
            for g in target_gitlab_res.json():
                gitlab_branches[g.get("name")] = g.get("commit").get("id")

            import_url = "https://gitee.com/{}/{}".format(src_org, rp)

            for b, s in branches.items():
                if s != gitlab_branches.get(b):
                    has_diff_branches_commits[b] = gitlab_branches.get(b)
                    has_diff_commits = True
                else:
                    has_diff_commits = False

        if src_platform == "github":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            github_url = "https://api.github.com/repos/{}/{}/branches".format(src_org, rp)
            github_header = {"Authorization": "token %s" % github_tk}
            github_res = requests.get(url=github_url, headers=github_header)
            if github_res.status_code != 200:
                continue

            branches = {}
            for b in github_res.json():
                branches[b.get("name")] = b.get("commit").get("sha")

            gitlab_branches = {}
            target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/branches' \
                .format(username, user_pass, rid)
            target_gitlab_res = requests.get(url=target_gitlab_url)
            if target_gitlab_res.status_code != 200 or len(target_gitlab_res.json()) == 0:
                continue
            for g in target_gitlab_res.json():
                gitlab_branches[g.get("name")] = g.get("commit").get("id")

            import_url = "https://github.com/{}/{}".format(src_org, rp)

            for b, s in branches.items():
                if s != gitlab_branches.get(b):
                    has_diff_branches_commits[b] = gitlab_branches.get(b)
                    has_diff_commits = True
                else:
                    has_diff_commits = False

        if src_platform == "gitlab":
            if rp in ["tree1", "Tree1"]:
                rp = rp.replace("1", "")
            get_group_id = ""
            data = {"per_page": 100}
            while True:
                get_group_id_url = "https://" + src_url.split("/")[2] + "/api/v4/groups?page={}".format(page)
                get_group_res = requests.get(url=get_group_id_url, params=data)
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

            gitlab_url = "https://{}/api/v4/projects/{}/repository/branches".format(src_url.split("/")[2], repo_id)
            gitlab_res = requests.get(url=gitlab_url)
            if gitlab_res.status_code != 200:
                continue

            # get all branches and theirs newly commits
            branches = {}
            for b in gitlab_res.json():
                branches[b.get("name")] = b.get("commit").get("id")

            gitlab_branches = {}
            target_gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/branches' \
                .format(username, user_pass, rid)
            target_gitlab_res = requests.get(url=target_gitlab_url)
            if target_gitlab_res.status_code != 200 or len(target_gitlab_res.json()) == 0:
                continue
            for g in target_gitlab_res.json():
                gitlab_branches[g.get("name")] = g.get("commit").get("id")

            import_url = "https://{}/{}/{}".format(src_url.split("/")[2], src_org, rp)

            for b, s in branches.items():
                if s != gitlab_branches.get(b):
                    has_diff_branches_commits[b] = gitlab_branches.get(b)
                    has_diff_commits = True
                else:
                    has_diff_commits = False

            time.sleep(0.2)

        if has_diff_commits:

            print("delete and recreate single repo : ", import_url)
            headers = {
                'Private-Token': gitlab_tk
            }

            # use git for a big storage repo
            single_group_name = get_group_detail_by_id(username, user_pass, single_group_id)

            # get repo's storage by api
            get_storage_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}'.format(username, user_pass, rid)
            get_storage_params = {
                "statistics": "true"
            }
            res_storage = requests.get(url=get_storage_url, params=get_storage_params, headers=headers)
            if res_storage.status_code != 200:
                res_storage = requests.get(url=get_storage_url, params=get_storage_params, headers=headers)

            storage = res_storage.json().get("statistics").get("repository_size")
            if storage is None or storage == 0:
                continue

            if storage > 1073741824:
                git_for_big_repos(single_group_name, import_url, rp, rid, has_diff_branches_commits, username,
                                  user_pass, gitlab_tk)

            else:
                create_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects'.format(username, user_pass)
                data = {
                    "name": import_url.split("/")[-1],
                    "path": import_url.split("/")[-1],
                    "import_url": import_url,
                    "namespace_id": single_group_id,
                    "visibility": "public",
                    "mirror": True,
                    "lfs_enabled": True
                }

                if src_platform == "gitlab":
                    data["import_url"] = import_url + ".git"
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
                if n == 2:
                    write_to_log(data["import_url"], data["namespace_id"])
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
