# -*- coding: UTF-8 -*-
import os
import requests
import re
import sys
import yaml


def check_yaml_exists(owner, repo, number):
    """
    Check exists of sig-info.yaml and sig/sigs.yaml
    """
    r = requests.get('https://gitee.com/{0}/{1}/pulls/{2}.diff'.format(owner, repo, number))
    error = 0
    count = 0
    differences = r.text
    slices = differences.split('diff --git ')[1:]
    diff_files = [x.split(' ')[0][2:] for x in slices]
    if 'sig/sigs.yaml' in diff_files:
        os.system('test -f /tmp/sigs.yaml && rm /tmp/sigs.yaml')
        os.system('wget -P /tmp https://gitee.com/openeuler/community/raw/master/sig/sigs.yaml')
        try:
            with open('/tmp/sigs.yaml', 'r') as f:
                sigs = yaml.load(f.read(), Loader=yaml.Loader)['sigs']
        except Exception as e:
            print(e)
            sys.exit(1)
        try:
            f = open('community/sig/sigs.yaml', 'r')
            modified_sigs = yaml.load(f.read(), Loader=yaml.Loader)['sigs']
            f.close()
        except Exception as e:
            print(e)
            sys.exit(1)
        os.system('diff /tmp/sigs.yaml community/sig/sigs.yaml > /tmp/diff.txt')
        remove_repos = []
        add_repos = []
        with open('/tmp/diff.txt', 'r') as f:
            for line in f.readlines():
                if line.startswith('<'):
                    remove_repos.append(line.strip().split(' ')[-1])
                if line.startswith('>'):
                    add_repos.append(line.strip().split(' ')[-1])
        os.system('rm /tmp/diff.txt')
        for diff_file in diff_files:
            if re.match(r'^sig/.+/sig-info.yaml$', diff_file):
                count += 1
                try:
                    with open(os.path.join('community', diff_file), 'r', encoding='utf-8') as f:
                        sig_info = yaml.load(f.read(), Loader=yaml.Loader)
                except Exception as e:
                    print(e)
                    sys.exit(1)
                for r in remove_repos:
                    for sig in sigs:
                        if r in sig['repositories']:
                            sig_name = sig['name']
                            if sig_name == sig_info['name']:
                                if r in sig_info['repositories']:
                                    print(
                                        'ERROR! remove repo {0} from sigs.yaml should also remove repo {0} from {1}.'.format(
                                            r, diff_file))
                            else:
                                if os.path.exists(os.path.join('community', sig_name, 'sig-info.yaml')):
                                    print(
                                        'ERROR! remove repo {0} from sigs.yaml should also remove repo {0} from {1}.'.format(
                                            r, diff_file))
                                    error += 1
                for r in add_repos:
                    for sig in modified_sigs:
                        if r in sig['repositories']:
                            sig_name = sig['name']
                            if sig_name == sig_info['name']:
                                if r not in [x['repo'] for x in sig_info['repositories']]:
                                    print(
                                        'ERROR! add repo {0} to sigs.yaml should also add repo {0} to {1}.'.format(r,
                                                                                                                  diff_file))
                                    error += 1
                            else:
                                if os.path.exists(os.path.join('community', sig_name, 'sig-info.yaml')):
                                    print(
                                        'ERROR! add repo {0} to sigs.yaml should also add repo {0} to {1}.'.format(r,
                                                                                                                  diff_file))
                                    error += 1
                check_sig_info_yaml(diff_file, modified_sigs)
        if count == 0:
            for r in remove_repos:
                for sig in sigs:
                    if r in sig['repositories']:
                        sig_info_yaml = 'sig/{}/sig-info.yaml'.format(sig['name'])
                        if os.path.exists('community/sig/{}/sig-info.yaml'.format(sig['name'])):
                            print(
                                'ERROR! remove repo {0} from sigs.yaml should also remove repo {0} from {1}, '
                                'but no sig-info.yaml changed.'.format(
                                    r, sig_info_yaml))
                            error += 1
            for r in add_repos:
                for sig in modified_sigs:
                    if r in sig['repositories']:
                        sig_info_yaml = 'sig/{}/sig-info.yaml'.format(sig['name'])
                        if os.path.exists('community/sig/{}/sig-info.yaml'.format(sig['name'])):
                            print(
                                'ERROR! add repo {0} to sigs.yaml should also add repo {0} to {1}, but no '
                                'sig-info.yaml changed.'.format(r, sig_info_yaml))
                            error += 1
        if error != 0:
            sys.exit(1)
    else:
        try:
            f = open('community/sig/sigs.yaml', 'r')
            sigs = yaml.load(f.read(), Loader=yaml.Loader)['sigs']
            f.close()
        except Exception as e:
            print('Invalid yaml: sig/sigs.yaml')
            print(e)
            sys.exit(1)
        for diff_file in diff_files:
            if re.match(r'^sig/.+/sig-info.yaml$', diff_file):
                count += 1
                check_sig_info_yaml(diff_file, sigs)
        if count == 0:
            print('Found no sig-info.yaml in Pull Request.')


def check_gitee_id(gitee_id, error):
    """
    Check validation of gitee_id
    """
    url = 'https://gitee.com/api/v5/users/{}?access_token={}'.format(gitee_id, access_token)
    r = requests.get(url)
    if r.status_code == 404:
        print('ERROR! Check gitee_id: invalid gitee_id {}.'.format(gitee_id))
        error += 1
    return error


def check_mentors(mentors, error):
    """
    Check mentors
    """
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
            try:
                email = mentor['email']
                if not email:
                    print('ERROR! Check mentors: email cannot be null for every mentor.')
                    error += 1
                else:
                    if not re.match(r'^([a-zA-Z0-9_.-]+)+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
                        print('ERROR! Check mentors: invalid email {}.'.format(email))
                        error += 1
            except KeyError:
                print('ERROR! Check mentors: email must be provided for evevy mentor.')
                error += 1
    return error


def check_maintainers(maintainers, error):
    """
    Check maintainers
    """
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
            try:
                email = maintainer['email']
                if not email:
                    print('ERROR! Check maintainers: email cannot be null for every maintainer.')
                    error += 1
                else:
                    if not re.match(r'^([a-zA-Z0-9_.-]+)+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
                        print('ERROR! Check maintainers: invalid email {}.'.format(email))
                        error += 1
            except KeyError:
                print('ERROR! Check maintainers: email must be provided for evevy maintainer.')
                error += 1
    return error


def check_committers(committers, error):
    """
    Check committers
    """
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
            try:
                email = committer['email']
                if not email:
                    print('ERROR! Check committers: email cannot be null for every committer.')
                    error += 1
                else:
                    if not re.match(r'^([a-zA-Z0-9_.-]+)+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
                        print('ERROR! Check committers: invalid email {}.'.format(email))
                        error += 1
            except KeyError:
                print('ERROR! Check committers: email must be provided for evevy committer.')
                error += 1
    return error


def check_repositories(repositories, sig_name, sigs, error):
    """
    Check repositories
    """
    if not repositories:
        print('ERROR! Check repositories: should contain at least 1 repository.')
        error += 1
    else:
        for sig in sigs:
            if sig['name'] == sig_name:
                repos = sig['repositories']
                for r in repositories:
                    if not (type(r) == dict and 'repo' in r.keys()):
                        print('ERROR! Check repo: every repo should be a dictionary type and at least one key should be repo.')
                        sys.exit(1)
                    if r['repo'] not in repos:
                        print('ERROR! Check repo: no repo named {} in sig {} according to sigs.yaml.'.format(r['repo'],
                                                                                                             sig_name))
                        error += 1
                    else:
                        if 'additional_contributors' in r.keys():
                            additional_contributors = r['additional_contributors']
                            for additional_contributor in additional_contributors:
                                try:
                                    gitee_id = additional_contributor['gitee_id']
                                    error = check_gitee_id(gitee_id, error)
                                except KeyError:
                                    print('ERROR! gitee_id is required in additional_contributors.')
                                    error += 1
                                try:
                                    email = additional_contributor['email']
                                    if not email:
                                        print('ERROR! Check repositories: email cannot be null for every '
                                              'additional_contributor.')
                                        error += 1
                                    else:
                                        if not re.match(r'^([a-zA-Z0-9_.-]+)+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$',
                                                        email):
                                            print('ERROR! Check repositories: invalid email {}.'.format(email))
                                            error += 1
                                except KeyError:
                                    print('ERROR! Check repositories: email must be provided for evevy '
                                          'additional_contributor.')
                                    error += 1
                for r in repos:
                    try:
                        if r not in [x['repo'] for x in repositories]:
                            print(
                                'ERROR! Check repo: repo {} belongs to sig {} according to sigs.yaml should be listed '
                                'but missed.'.format(r, sig_name))
                            error += 1
                    except TypeError:
                        print('ERROR! Check repo: every repo should be a dictionary type and at least one key should be repo.')
                        sys.exit(1)
    return error


def check_sig_info_yaml(file_name, sigs):
    """
    Check sig_info.yaml
    """
    error = 0
    try:
        f = open(os.path.join('community', file_name), 'r', encoding='utf-8')
        content = yaml.load(f.read(), Loader=yaml.Loader)
        f.close()
    except Exception as e:
        print(e)
        sys.exit(1)
    trust_list = ['name', 'description', 'mailing_list', 'meeting_url', 'mature_level', 'mentors', 'maintainers',
                  'committers', 'security_contacts', 'repositories']
    for i in content.keys():
        if i not in trust_list:
            print('ERROR! Check fields: invalid field {}.'.format(i))
            error += 1
    try:
        name = content['name']
        description = content['description']
        mailing_list = content['mailing_list']
        meeting_url = content['meeting_url']
        mentors = content['mentors'] if 'mentors' in content.keys() else None
        maintainers = content['maintainers']
        committers = content['committers'] if 'committers' in content.keys() else None
        repositories = content['repositories']
    except Exception as e:
        print('ERROR!', e)
        sys.exit(1)
    if not description:
        print('ERROR! description is required for the yaml.')
        error += 1
    if not mailing_list:
        print('ERROR! mailing_list is required for the yaml.')
        error += 1
    if not meeting_url:
        print('ERROR! meeting_url is required for the yaml')
        error += 1
    if 'additional_contributors' in content.keys():
        print('ERROR! additional_contributors should belong a repo.')
        error += 1
    if name not in [x['name'] for x in sigs]:
        print('ERROR! sig named {} does not exist in sigs.yaml.'.format(name))
        error += 1
    error = check_maintainers(maintainers, error)
    error = check_repositories(repositories, name, sigs, error)
    if mentors:
        error = check_mentors(mentors, error)
    if committers:
        error = check_committers(committers, error)
    if error != 0:
        print('Found {} errors, please check!'.format(error))
        sys.exit(1)
    else:
        print('PASS :)')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(
            'Required 4 parameters! The owner, repo, number, access_token parameters need to be transferred in '
            'sequence.')
        sys.exit(1)
    owner = sys.argv[1]
    repo = sys.argv[2]
    number = sys.argv[3]
    access_token = sys.argv[4]
    check_yaml_exists(owner, repo, number)
