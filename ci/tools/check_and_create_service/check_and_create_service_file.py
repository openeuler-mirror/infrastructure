import base64
import sys
import time

import requests


def get_gitee_tree(token):
    data = {"access_token": token}
    community_url = "https://gitee.com/api/v5/repos/openeuler/community/git/trees/master?recursive=1"
    res = requests.get(url=community_url, data=data)
    repo_names = []
    for i in res.json()["tree"]:
        if i["path"].startswith("sig/") and i["path"].endswith(".yaml") and str.count(i["path"], "/") > 3 \
                and str.__contains__(i["path"], "/src-openeuler/") and i["path"].split("/")[1] != "sig-recycle" \
                and i["path"].split("/")[1] != "Private":
            if i["path"].split(".yaml")[0].split("/")[-1] in ["obs_meta"]:
                continue
            repo_names.append(i["path"].split("/")[-1].split(".yaml")[0])
    return repo_names


def get_obs_tree(repo_name, token):
    data = {"access_token": token}
    obs_url = "https://gitee.com/api/v5/repos/src-openeuler/obs_meta/git/trees/master?recursive=1"
    res = requests.get(url=obs_url, data=data)
    trees = res.json()["tree"]
    dirs = ["openEuler:Factory", "openEuler:Mainline", "openEuler:Epol"]
    repo_set = set()
    missing_service_repo = []
    for i in trees:
        if i["path"].startswith("master/") and i["path"].split("/")[1] in dirs and i["path"].endswith("_service"):
            repo_set.add(i["path"].split("/")[-2])

    for r in repo_name:
        if r not in repo_set:
            missing_service_repo.append(r)

    return missing_service_repo


def write_to_obs(missing_list, token):
    for m in missing_list:
        with open("./service_template", 'r', encoding="utf-8") as f:
            file_stream = f.read()
        content = file_stream.replace("#projectname#", m)

        base64_content = base64.b64encode(content.encode('utf-8'))
        create_file = "https://gitee.com/api/v5/repos/src-openeuler/obs_meta/contents/master/" \
                      "openEuler:Factory/%s/_service" % m
        data = {
            "access_token": token,
            "content": base64_content,
            "message": "add missing _service by openeuler-ci-bot"
        }
        print("create _service for ", m)
        r = requests.post(create_file, data)
        if r.status_code != 201:
            time.sleep(0.5)
            requests.post(url=create_file, data=data)
        time.sleep(1)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Required 1 parameters! personal_token need to be transferred in sequence.')
        sys.exit(1)
    p_token = sys.argv[1]
    repo_name_list = get_gitee_tree(p_token)
    ml = get_obs_tree(repo_name_list, p_token)
    write_to_obs(ml, p_token)

