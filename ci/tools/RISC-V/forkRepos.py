"""
A tool used to fork repositories and configure members for RISC-V
"""
import argparse
import requests
import sys
import yaml


def load_yaml(file_path):
    """
    Load yaml file
    :param file_path: path of the yaml file ready to load
    :return: content of the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.load(f.read(), Loader=yaml.Loader)
            return content
    except yaml.MarkedYAMLError as e:
        print('YAML FORMAT ERROR!')
        print(e)
        sys.exit(1)


def check_diff_files():
    """
    Check the differences between the current Pull Request and master branch
    :return: a list of different files
    """
    diff_url = 'https://gitee.com/{0}/{1}/pulls/{2}.diff'.format(pr_owner, pr_repo, pr_number)
    r = requests.get(diff_url)
    if r.status_code != 200:
        print('Can not get differences from diff_url, diff_url:', diff_url)
        sys.exit(1)
    different_files = [x.split(' ')[0][2:] for x in r.text.split('diff --git ')[1:]]
    return different_files


def fork(fork_repo):
    """
    Fork a repo
    :param fork_repo: the aim repo
    :return: http response
    """
    fork_url = 'https://gitee.com/api/v5/repos/src-openeuler/{}/forks'.format(fork_repo)
    data = {
        'access_token': access_token,
        'organization': 'openeuler-risc-v'
    }
    r = requests.post(fork_url, data)
    return r


def add_maintainer(username, error_count):
    """
    Add a maintainer for the repo
    :param username: login name of maintainer
    :param error_count: count of errors
    :return: error_count
    """
    add_maintainer_url = 'https://gitee.com/api/v5/repos/openeuler-risc-v/{}/collaborators/{}'.format(repo, username)
    data = {
        'access_token': access_token,
        'permission': 'admin'
    }
    r = requests.put(add_maintainer_url, data)
    if r.status_code != 200:
        error_count += 1
        print('Fail to add maintainer {} to repo {}'.format(maintainer, repo))
        print(r.json())
    print('Set maintainer {} for repo {}'.format(maintainer, repo))
    return error_count


def add_committer(username, error_count):
    """
    Add a committer for the repo
    :param username: login name of maintainer
    :param error_count: count of errors
    :return: error_count
    """
    add_committer_url = 'https://gitee.com/api/v5/repos/openeuler-risc-v/{}/collaborators/{}'.format(repo, username)
    data = {
        'access_token': access_token,
        'permission': 'push'
    }
    r = requests.put(add_committer_url, data)
    if r.status_code != 200:
        error_count += 1
        print('Fail to add committer {} to repo {}'.format(committer, repo))
        print(r.json())
    print('Set committer {} for repo {}'.format(committer, repo))
    return error_count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A tool used to fork repositories and configure members for RISC-V')
    parser.add_argument('-o', '--owner', help='owner of Pull Request', required=True)
    parser.add_argument('-r', '--repo', help='repo of Pull Request', required=True)
    parser.add_argument('-n', '--number', help='number of Pull Request', required=True)
    parser.add_argument('-t', '--token', help='access_token', required=True)
    args = parser.parse_args()
    pr_owner = args.owner
    pr_repo = args.repo
    pr_number = args.number
    access_token = args.token
    diff_files = check_diff_files()
    if 'configuration/riscv_fork_list.yaml' not in diff_files and 'RISCV_members.yaml' not in diff_files:
        sys.exit(0)
    # get maintainers and committers
    members = load_yaml('{}/RISCV_members.yaml'.format(pr_repo))
    committers = members['Committer']
    maintainers = members['Maintainer']
    maintainers.append('openeuler-ci-bot')
    # get all repos
    pkgs = load_yaml('{}/configuration/riscv_fork_list.yaml'.format(pr_repo))
    repos = [x['name'] for x in pkgs['packages']]
    errors = 0
    for repo in repos:
        # fork repo
        response = fork(repo)
        if response.status_code == 403:
            print('\nRepo {} has been forked.'.format(repo))
        else:
            if response.status_code != 201:
                errors += 1
                print('ERROR! Fail to Fork repo {}'.format(repo))
                print(response.json())
                continue
            print('\nFork repo {} from src-openeuler to openeuler-risc-v'.format(repo))
        # add maintainers for repo
        for maintainer in maintainers:
            errors = add_maintainer(maintainer, errors)
        # add committers for repo
        for committer in committers:
            errors = add_committer(committer, errors)
    if errors != 0:
        sys.exit(1)

