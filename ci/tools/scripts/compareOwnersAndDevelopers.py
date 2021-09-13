"""
A tool compare differences between OWNERS of sigs and developers of repos belong to the same sig for openeuler
community. Ensure community directory exists in the script execution path and transfer a token with sufficient
permissions to obtain all repository member information. A csv file named 'differences.csv' will be the output.
"""
import argparse
import codecs
import csv
import os
import requests
import sys
import yaml


def main():
    parser = argparse.ArgumentParser(
        description="A tool compare differences between OWNERS of sigs and developers of repos belong to the same sig "
                    "for openeuler community. Ensure community directory exists in the script execution path and "
                    "transfer a token with sufficient permissions to obtain all repository member information. A csv "
                    "file named 'differences.csv' will be the output."
    )
    parser.add_argument('-t', '--token', help='access_token', required=True)
    args = parser.parse_args()
    access_token = args.token
    if 'community' not in os.listdir():
        os.system('git clone https://gitee.com/openeuler/community.git')
    with open('community/sig/sigs.yaml', 'r') as f:
        sigs = yaml.load(f.read(), Loader=yaml.Loader)['sigs']
    f = codecs.open('differences.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['SIG', 'REPO', 'OWNERS_EXTRAS', 'DEV_EXTRAS'])
    for sig in sigs:
        sig_name = sig['name']
        with open('community/sig/{}/OWNERS'.format(sig_name)) as f:
            contents = yaml.load(f.read(), Loader=yaml.Loader)
        if 'committers' in contents.keys():
            maintainers = contents['maintainers']
            committers = contents['committers']
            owners = maintainers + committers
        else:
            owners = contents['maintainers']
        for full_name in sig['repositories']:
            print('repo: {}'.format(full_name))
            owner, repo = full_name.split('/')
            repos_info = []
            page = 1
            while True:
                params = {
                    'page': page,
                    'per_page': 100,
                    'access_token': access_token
                }
                url = 'https://gitee.com/api/v5/repos/{}/{}/collaborators'.format(owner, repo)
                r = requests.get(url, params=params)
                if r.status_code != 200:
                    print(r.json())
                    sys.exit(1)
                for repo_info in r.json():
                    repos_info.append(repo_info)
                if len(r.json()) < 100:
                    break
                page += 1
            repo_developers = []
            for x in repos_info:
                user = x['login']
                permissions = x['permissions']['admin']
                if permissions and user != 'openeuler-ci-bot':
                    print('WARNING! {}: unexpected administrator {}'.format(full_name, user))
                if not permissions:
                    repo_developers.append(user)
            if not repo_developers:
                print('Fail to initialize the repo. There are no members yet. repo name: {}'.format(repo))
                writer.writerow([sig_name, full_name, owners, 'No members'])
                continue
            if sorted(owners) != sorted(repo_developers):
                print('OWNERS of sig {} is different from developers of repo {}'.format(sig_name, full_name))
                print('OWNERS of sig {}: {}'.format(sig_name, owners))
                owner_extras = []
                dev_extras = []
                for x in repo_developers:
                    if x not in owners:
                        dev_extras.append(x)
                for x in owners:
                    if x not in repo_developers:
                        owner_extras.append(x)
                print('Extras of OWNERS: {}'.format(owner_extras))
                print('Extras of developers: {}'.format(dev_extras))
                writer.writerow([sig_name, full_name, owner_extras, dev_extras])
                print()


if __name__ == '__main__':
    main()

