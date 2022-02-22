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


def get_repo_members(repository):
    """
    Get all members of the repo
    :param repository: the target repo
    :return: a json format response or nothing when the request is abnormal
    """
    url = 'https://gitee.com/api/v5/repos/openeuler-risc-v/{}/collaborators'.format(repository)
    params = {
        'access_token': access_token,
        'page': 1,
        'per_page': 100
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(r.json())
    else:
        resp = {}
        for i in r.json():
            resp[i['login']] = i['permissions']['admin']
        return resp


def delete_member(repository, username):
    """
    Remove a member from a repo
    :param repository: the target repo
    :param username: the target gitee_id
    :return: True/False when succeeded/failed
    """
    url = 'https://gitee.com/api/v5/repos/openeuler-risc-v/{}/collaborators/{}'.format(repository, username)
    params = {'access_token': access_token}
    r = requests.delete(url, params=params)
    if r.status_code != 204:
        print('Fail to delete member {} of repo {}'.format(username, repository))
        return False
    else:
        return True


def add_maintainer(repository, username, error_count):
    """
    Add a maintainer for the repo
    :param repository: the target repo
    :param username: login name of maintainer
    :param error_count: count of errors
    :return: error_count
    """
    add_maintainer_url = 'https://gitee.com/api/v5/repos/openeuler-risc-v/{}/collaborators/{}'.format(repository,
                                                                                                      username)
    data = {
        'access_token': access_token,
        'permission': 'admin'
    }
    r = requests.put(add_maintainer_url, data)
    if r.status_code != 200:
        error_count += 1
        print('Fail to add maintainer {} to repo {}'.format(username, repository))
        print(r.json())
    print('Set maintainer {} for repo {}'.format(username, repository))
    return error_count


def add_committer(repository, username, error_count):
    """
    Add a committer for the repo
    :param repository: the target repo
    :param username: login name of maintainer
    :param error_count: count of errors
    :return: error_count
    """
    add_committer_url = 'https://gitee.com/api/v5/repos/openeuler-risc-v/{}/collaborators/{}'.format(repository,
                                                                                                     username)
    data = {
        'access_token': access_token,
        'permission': 'push'
    }
    r = requests.put(add_committer_url, data)
    if r.status_code != 200:
        error_count += 1
        print('Fail to add committer {} to repo {}'.format(username, repository))
        print(r.json())
    print('Set committer {} for repo {}'.format(username, repository))
    return error_count


def main():
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
        # get all members of the repo
        repo_members = get_repo_members(repo)
        # remove unmatched members
        for member in repo_members.keys():
            if member == 'openeuler-ci-bot':
                continue
            if member not in maintainers and member not in committers:
                if delete_member(repo, member):
                    print('Delete unmatched member {} of repo {}'.format(member, repo))
        if not repo_members:
            print('Fail to get members of repo {}, skip...'.format(repo))
            continue
        # add maintainers for repo
        for maintainer in maintainers:
            if maintainer not in repo_members.keys():
                errors = add_maintainer(repo, maintainer, errors)
            else:
                if repo_members.get(maintainer):
                    print('Keep maintainer {} for repo {}'.format(maintainer, repo))
                    continue
                if delete_member(repo, maintainer):
                    print('Delete non-maintainer {} of repo {}'.format(maintainer, repo))
                    errors = add_maintainer(repo, maintainer, errors)
        # add committers for repo
        for committer in committers:
            if committer not in repo_members.keys():
                errors = add_committer(repo, committer, errors)
            else:
                if not repo_members.get(committer):
                    print('Keep committer {} for repo {}'.format(committer, repo))
                    continue
                if delete_member(repo, committer):
                    print('Delete non-committer {} of repo {}'.format(committer, repo))
                    errors = add_committer(repo, committer, errors)
    if errors != 0:
        sys.exit(1)


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
    main()

