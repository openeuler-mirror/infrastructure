import sys

import requests


def read_log(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        url = f.readlines()

    return url


def sync_missing_to_gitlab(l: list, u_name, u_pass, gitlab_tk):
    headers = {"Private-Token": gitlab_tk}
    create_url = "https://{}:{}@source.openeuler.sh/api/v4/projects".format(u_name, u_pass)
    data = {}
    for x in l:
        x = x.strip("\n")
        url = x.split("::")[0]
        gid = x.split("::")[1].replace("\n", "")
        if url.split("//")[1].split("/")[0] == "gitlab":
            data["import_url"] = url + ".git"
            data["name"] = url.split("/")[-1]
            data["path"] = url.split("/")[-1]
            data["visibility"] = "public"
            data["namespace_id"] = gid
        else:
            data["import_url"] = url
            data["name"] = url.split("/")[-1]
            data["path"] = url.split("/")[-1]
            data["visibility"] = "public"
            data["namespace_id"] = gid
            
        if url.split("/")[-1] in ["tree", "Tree"]:
            data["name"] = "%s1" % url.split("/")[-1]
            data["path"] = "%s1" % url.split("/")[-1]
        print(create_url, data)
        r = requests.post(url=create_url, data=data, headers=headers)
        if r.status_code != 201:
            requests.post(url=create_url, data=data, headers=headers)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Required 3 parameters!')
        sys.exit(1)
    name = sys.argv[1]
    password = sys.argv[2]
    tk = sys.argv[3]
    file_list = read_log("./sync.log")
    sync_missing_to_gitlab(file_list, name, password, tk)
