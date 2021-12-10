import jenkins
import requests
import sys
import time
import yaml


def get_pr_state():
    """
    Get the state of a Pull Request
    :return: the state of Pull Request, e.g. merged, open, etc.
    """
    r = requests.get('https://gitee.com/api/v5/repos/{}/{}/pulls/{}?access_token={}'.format(owner, repo, number,
                                                                                            access_token))
    if r.status_code != 200:
        print(r.json())
        sys.exit(1)
    state = r.json()['state']
    return state


def check_repo_exist(added_repo):
    """
    Check whether a repository exists
    :param added_repo: target repository
    :return: True/False if the repository exists/not exists
    """
    with open('retry.yaml', 'r') as fp:
        retry_conf = yaml.load(fp.read(), Loader=yaml.Loader)
        retry = retry_conf['retry']
        interval = retry_conf['interval']
    while retry >= 0:
        r = requests.get('https://gitee.com/{}'.format(added_repo))
        if r.status_code != 200:
            if retry == 0:
                print('Repo {} has not been built yet, exit...'.format(added_repo))
                sys.exit(1)
            print('Repo {} does not exist, retry: {}'.format(added_repo, retry))
            retry -= 1
            time.sleep(interval)
        else:
            print('Repo {} is already built. Ready to create projects for it...'.format(added_repo))
            return True


def conn_jenkins():
    """
    Connect to jenkins server
    :return: jenkins server
    """
    url = 'https://jenkins.openeuler.org'
    server = jenkins.Jenkins(url, username=username, password=password, timeout=120)
    return server


def main():
    # Check whether the Pull Request is merged based on its state
    state = get_pr_state()
    if state != 'merged':
        print('This is not a merged Pull Request, exit...')
        sys.exit(0)
    # Get a list of differential file names
    r = requests.get('https://gitee.com/{}/{}/pulls/{}.diff'.format(owner, repo, number))
    if r.status_code != 200:
        print('Error! Cannot locate difference file of Pull Request. status code: {}'.format(r.status_code))
        sys.exit(1)
    slices = r.text.split('diff --git ')[1:]
    diff_files = [x.split(' ')[0][2:] for x in slices]
    # Check whether sigs/sigs.yaml exists in the list, exit if not
    if 'sig/sigs.yaml' not in diff_files:
        print('No new repos were added in this Pull Request, exit...')
        sys.exit(0)
    # Get a list of added repositories
    added_repos = []
    for diff_file in slices:
        if diff_file.split(' ')[0][2:] == 'sig/sigs.yaml':
            lines = diff_file.split('\n')
            for line in lines:
                if line.startswith('+  -'):
                    added_repos.append(line.strip().split()[2])
    if not added_repos:
        print('No new repos were added in this Pull Request, exit...')
        sys.exit(0)

    for added_repo in added_repos:
        # Check whether the repository is built already
        if not check_repo_exist(added_repo):
            continue
        # trigger build
        server = conn_jenkins()
        jobs = added_repo.split('/')[1]
        parameters = {
            'action': 'create',
            'template': 'gcc',
            'jobs': jobs,
            'exclude_jobs': '',
            'repo_server': 'repo-service.dailybuild'
        }
        if added_repo.startswith('src'):
            if server.get_info_name('multiarch/src-openeuler/trigger/{}'.format(jobs)) == jobs:
                print('Repo {} has its projects on jenkins already'.format(added_repo))
                continue
            server.build_job(name='multiarch/src-openeuler/jobs-crud/_entry', parameters=parameters)


if __name__ == '__main__':
    if len(sys.argv) != 7:
        print('6 parameters are required: owner, repo, number, access_token, username, password.')
        sys.exit(1)
    owner = sys.argv[1]
    repo = sys.argv[2]
    number = sys.argv[3]
    access_token = sys.argv[4]
    username = sys.argv[5]
    password = sys.argv[6]
    main()

