import argparse
import os
import requests
import re
import sys
import tempfile
import time
import yaml


def check_yaml_exists(owner, repo, number, access_token):
    """check exists of sig-info.yaml"""
    r = requests.get('https://gitee.com/{0}/{1}/pulls/{2}.diff'.format(owner, repo, number))
    time.sleep(1)
    count = 0
    differences = r.text
    slices = differences.split('diff --git ')[1:]
    for slice in slices:
        file_name = slice.split(' ')[0][2:]
        if re.match(r'^sig/.+/sig-info.yaml$', file_name):
            url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}?access_token={3}'.format(owner, repo, number, access_token)
            r = requests.get(url)
            count += 1
            time.sleep(1)
            if r.status_code == 200:
                source_repo = r.json()['head']['repo']['full_name']
                source_branch = r.json()['head']['ref']
                source_url = 'https://gitee.com/{0}/raw/{1}/{2}'.format(source_repo, source_branch, file_name)
                check_sig_info_yaml(file_name, source_url)
            else:
                print(r.text)
                sys.exit(1)
    if count == 0:
        print('Found no sig-info.yaml in Pull Request.')


def check_gitee_id(gitee_id, error):
    """validate gitee_id"""
    url = 'https://gitee.com/api/v5/users/{}?access_token={}'.format(gitee_id, access_token)
    r = requests.get(url)
    time.sleep(1)
    if r.status_code == 404:
        print('ERROR! Check gitee_id: invalid gitee_id {}.'.format(gitee_id))
        error += 1
    return error


def check_mentors(mentors, error):
    """check mentors"""
    if not mentors:
        pass
    else:
        for mentor in mentors:
            try:
                gitee_id = mentor['gitee_id']
                error = check_gitee_id(gitee_id, error)
            except KeyError:
                print('ERROR! Check mentors: gitee_id is required for every mentor.')
                error += 1
    return error


def check_maintainers(maintainers, error):
    """check maintainers"""
    if not maintainers:
        print('ERROR! Check mentors: at least 1 mentor is required.')
        error += 1
    else:
        for maintainer in maintainers:
            try:
                gitee_id = maintainer['gitee_id']
                error = check_gitee_id(gitee_id, error)
            except KeyError:
                print('ERROR! Check maintainers: gitee_id is required for every maintainer.')
                error += 1
    return error


def check_committers(committers, error):
    """check committers"""
    if not committers:
        pass
    else:
        for committer in committers:
            try:
                gitee_id = committer['gitee_id']
                error = check_gitee_id(gitee_id, error)
            except KeyError:
                print('ERROR! Check committers: gitee_id is required for every committer.')
                error += 1
    return error


def check_repositories(repositories, sig_name, sigs, error):
    """check repositories"""
    if not repositories:
        print('ERROR! Check repositories: should contain at least 1 repository.')
        error += 1
    else:
        if sig_name not in [x['name'] for x in sigs]:
            print('ERROR! Check repositories: sig named {} does not exists in sigs.yaml.'.format(sig_name))
            error += 1
        else:
            for r in repositories:
                if 'repo' not in r.keys():
                    print('ERROR! Check repo: repo in repositories should be like "repo: xxx".')
                    error += 1
                else:
                    for sig in sigs:
                        if sig == sig_name and r not in sig['repositories']:
                            print('ERROR! Check repo: no repo named {} in sig {}.'.format(repo, sig_name))
                            error += 1
                        if sig == sig_name and r in sig['repositories']:
                            if 'additional_contributors' in r.keys():
                                additional_contributors = r['additional_contributors']
                                for additional_contributor in additional_contributors:
                                    gitee_id = additional_contributor['gitee_id']
                                    error = check_gitee_id(gitee_id, error)
    return error


def check_sig_info_yaml(file_name, file_url):
    """multipart validations"""
    error = 0
    tempdir = tempfile.gettempdir()
    temp_file = os.path.join(tempdir, os.path.basename(file_name))
    if not os.path.exists(temp_file):
        os.system('wget -P {0} {1}'.format(tempdir, file_url))
    try:
        with open(temp_file, 'r') as f:
            content = yaml.load(f.read(), Loader=yaml.Loader)
    except Exception as e:
        print(e)
        os.system('rm {}'.format(temp_file))
        sys.exit(1)
    try:
        name = content['name']
        description = content['description']
        mailing_list = content['mailing_list']
        meeting_url = content['meeting_url']
        mature_level = content['mature_level']
        mentors = content['mentors']
        maintainers = content['maintainers']
        committers = content['committers']
        repositories = content['repositories']
    except KeyError as e:
        print('ERROR!', e)
        os.system('rm {}'.format(temp_file))
        sys.exit(1)
    with open('community/sig/sigs.yaml', 'r') as f2:
        sigs = yaml.load(f2.read(), Loader=yaml.Loader)['sigs']
    error = check_mentors(mentors, error)
    error = check_maintainers(maintainers, error)
    error = check_committers(committers, error)
    error = check_repositories(repositories, name, sigs, error)
    if error != 0:
        print('Found {} errors, please check!'.format(error))
        os.system('rm {}'.format(temp_file))
        sys.exit(1)
    else:
        os.system('rm {}'.format(temp_file))
        print('PASS :)')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('Required 4 parameters!')
        sys.exit(1)
    owner = sys.argv[1]
    repo = sys.argv[2]
    number = sys.argv[3]
    access_token = sys.argv[4]
    check_yaml_exists(owner, repo, number, access_token)
