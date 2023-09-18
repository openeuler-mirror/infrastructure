import sys

import requests
import time


def write_empty_to_file(org_id, token, username, userpass):
    headers = {
        'Private-Token': token
    }
    projects_id = {}
    page = 1
    while True:
        gitlab_url = 'https://{}:{}@source.openeuler.sh/api/v4/groups/{}/projects'.format(username, userpass, org_id)
        params = {
            "per_page": 100,
            "page": page,
        }
        req = requests.get(url=gitlab_url, headers=headers, params=params)

        if req.status_code != 200:
            continue

        if len(req.json()) == 0:
            break
        for r in req.json():
            projects_id[r.get("id")] = r.get("web_url")
        page += 1
        time.sleep(1)

    empty_repos = []
    for pid in projects_id.keys():
        branch_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}/repository/branches'.format(username, userpass, pid)
        res = requests.get(url=branch_url, headers=headers)
        if res.status_code != 200:
            continue
        if res.status_code == 200 and len(res.json()) != 0:
            time.sleep(1)
            continue
        delete_repo_url = 'https://{}:{}@source.openeuler.sh/api/v4/projects/{}'.format(username, userpass, pid)

        res2 = requests.delete(url=delete_repo_url, headers=headers)
        if res2.status_code != 202:
            requests.delete(url=delete_repo_url, headers=headers)

        empty_repos.append(projects_id[pid] + "::" + str(org_id))
        time.sleep(1)

    with open("./sync.log", "a", encoding="utf-8") as f:
        for e in empty_repos:
            f.writelines(e + "\n")


def main():
    gitlab_token = sys.argv[1]
    user_name = sys.argv[2]
    user_pass = sys.argv[3]
    if len(sys.argv) != 4:
        print("missing args")
        sys.exit(1)

    for org in [10, 14, 9564, 8861, 8860, 8859]:
        write_empty_to_file(org, gitlab_token, user_name, user_pass)
        time.sleep(20)


if __name__ == '__main__':
    main()
