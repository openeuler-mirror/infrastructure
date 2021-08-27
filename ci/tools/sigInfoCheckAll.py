import os
import sys
import re
import requests
import yaml


def load_yaml(file_path):
    """
    Load yaml file
    :param file_path: path of the yaml file ready to load
    :return: content of the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as fp:
            content = yaml.load(fp.read(), Loader=yaml.Loader)
            return content
    except yaml.MarkedYAMLError as e:
        print('YAML FORMAT ERROR!')
        print(e)
        sys.exit(1)


def has_sig_info(signame):
    """
    Check a sig whether has sig-info.yaml
    :param signame: name of sig
    :return: True/False if has or not
    """
    if 'sig-info.yaml' in os.listdir('community/sig/{}'.format(signame)):
        return True
    else:
        print('WARNING: sig {} still has no sig-info.yaml.'.format(signame))
        return False


def check_gitee_id(gitee_id, errors):
    """
    Check validation of gitee_id
    :param gitee_id: gitee_id
    :param errors: errors count
    :return: errors
    """
    url = 'https://gitee.com/api/v5/users/{}?access_token={}'.format(gitee_id, access_token)
    r = requests.get(url)
    if r.status_code == 404:
        print('ERROR! Check gitee_id: invalid gitee_id {}.'.format(gitee_id))
        errors += 1
    return errors


def check_mentors(mentors, errors):
    """
    Check mentors
    :param mentors: mentors of sig-info.yaml
    :param errors: error count
    :return: errors
    """
    if not mentors:
        pass
    else:
        for mentor in mentors:
            try:
                gitee_id = mentor['gitee_id']
                errors = check_gitee_id(gitee_id, errors)
            except KeyError:
                print('ERROR! Check mentors: gitee_id is required for every mentor.')
                errors += 1
            try:
                email = mentor['email']
                if not email:
                    print('ERROR! Check mentors: email cannot be null for every mentor.')
                    errors += 1
                else:
                    if not re.match(r'^([a-zA-Z0-9_.-]+)+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
                        print('ERROR! Check mentors: invalid email {}.'.format(email))
                        errors += 1
            except KeyError:
                print('ERROR! Check mentors: email must be provided for evevy mentor.')
                errors += 1
    return errors


def check_maintainers(maintainers, error):
    """
    Check maintainers
    :param maintainers: maintainers of sig-info.yaml
    :param error: error count
    :return: error
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
    :param committers: committers of sig-info.yaml
    :param error: error count
    :return: error
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


def check_repositories(repositories, signame, sigslist, errors):
    """
    Check repositories
    :param repositories: repositories of sig
    :param signame: name of sig
    :param sigslist: content of all sigs
    :param errors: error count
    :return: errors
    """
    if not repositories:
        print('ERROR! Check repositories: should contain at least 1 repository.')
        errors += 1
    else:
        for i in sigslist:
            if i['name'] == signame:
                repos = i['repositories']
                for r in repositories:
                    if not (type(r) == dict and 'repo' in r.keys()):
                        print('ERROR! Check repo: every repo should be a dictionary type and at least one key should '
                              'be repo.')
                        sys.exit(1)
                    if r['repo'] not in repos:
                        print('ERROR! Check repo: no repo named {} in sig {} according to sigs.yaml.'.format(r['repo'],
                                                                                                             sig_name))
                        errors += 1
                    else:
                        if 'additional_contributors' in r.keys():
                            additional_contributors = r['additional_contributors']
                            for additional_contributor in additional_contributors:
                                try:
                                    gitee_id = additional_contributor['gitee_id']
                                    errors = check_gitee_id(gitee_id, errors)
                                except KeyError:
                                    print('ERROR! gitee_id is required in additional_contributors.')
                                    errors += 1
                                try:
                                    email = additional_contributor['email']
                                    if not email:
                                        print('ERROR! Check repositories: email cannot be null for every '
                                              'additional_contributor.')
                                        errors += 1
                                    else:
                                        if not re.match(r'^([a-zA-Z0-9_.-]+)+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$',
                                                        email):
                                            print('ERROR! Check repositories: invalid email {}.'.format(email))
                                            errors += 1
                                except KeyError:
                                    print('ERROR! Check repositories: email must be provided for evevy '
                                          'additional_contributor.')
                                    errors += 1
                for r in repos:
                    try:
                        if r not in [x['repo'] for x in repositories]:
                            print('ERROR! Check repo: repo {} belongs to sig {} according to sigs.yaml should be '
                                  'listed but missed.'.format(r, sig_name))
                            errors += 1
                    except TypeError:
                        print('ERROR! Check repo: every repo should be a dictionary type and at least one key should '
                              'be repo.')
                        sys.exit(1)
    return errors


def check_description(sig_info, error):
    """
    Check description
    :param sig_info: content of sig-info.yaml
    :param error: error count
    :return: error
    """
    if 'description' not in sig_info.keys():
        print('ERROR! description is a required field')
        error += 1
    else:
        print('Check description: PASS')
    return error


def check_mailing_list(sig_info, error):
    """
    Check mailing_list
    :param sig_info: content of sig-info.yaml
    :param error: error count
    :return: error
    """
    if 'mailing_list' not in sig_info.keys():
        print('ERROR! mailing_list is a required field')
        error += 1
    else:
        print('Check mailing_list: PASS')
    return error


def check_meeting_url(sig_info, error):
    """
    Check meeting_url
    :param sig_info: content of sig-info.yaml
    :param error: error count
    :return: error
    """
    if 'meeting_url' not in sig_info.keys():
        print('ERROR! meeting_url is a required field')
        error += 1
    else:
        print('Check meeting_url: PASS')
    return error


def check_sig_name(signame, sigslist, error):
    """
    Check sig name
    :param signame: name of sig in sig-info.yaml
    :param sigslist: content of all sigs
    :param error: error count
    :return: error
    """
    if signame not in [x['name'] for x in sigslist]:
        print('ERROR! sig named {} does not exist in sigs.yaml.'.format(sig_name))
        error += 1
    return error


def check_sig_info_yaml(signame, sigslist, errors):
    """
    Check sig-info.yaml, contains multiple independent check items
    :param signame: name of sig
    :param sigslist: content of all sigs
    :param errors: error count
    :return:
    """
    content = load_yaml('community/sig/{}/sig-info.yaml'.format(signame))
    trust_list = ['name', 'description', 'mailing_list', 'meeting_url', 'mature_level', 'mentors', 'maintainers',
                  'committers', 'security_contacts', 'repositories']
    for i in content.keys():
        if i not in trust_list:
            print('ERROR! Check fields: invalid field {}.'.format(i))
            errors += 1
    try:
        name = content['name']
        mentors = content['mentors'] if 'mentors' in content.keys() else None
        maintainers = content['maintainers']
        committers = content['committers'] if 'committers' in content.keys() else None
        repositories = content['repositories']
    except KeyError as e:
        print('ERROR!', e)
        sys.exit(1)
    errors = check_sig_name(name, sigslist, errors)
    errors = check_maintainers(maintainers, errors)
    errors = check_repositories(repositories, name, sigslist, errors)
    if mentors:
        errors = check_mentors(mentors, errors)
    if committers:
        errors = check_committers(committers, errors)
    return errors


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('Required 4 parameters! The owner, repo, number, access_token parameters need to be transferred in '
              'sequence.')
        sys.exit(1)
    owner = sys.argv[1]
    repo = sys.argv[2]
    number = sys.argv[3]
    access_token = sys.argv[4]
    issues = 0
    with open('community/sig/sigs.yaml', 'r') as f:
        sigs = yaml.load(f.read(), Loader=yaml.Loader)['sigs']
    for sig in sigs:
        sig_name = sig['name']
        if has_sig_info(sig_name):
            issues = check_sig_info_yaml(sig_name, sigs, issues)
    if issues != 0:
        print('Found {} errors, please check!'.format(issues))
        sys.exit(1)
    else:
        print('PASS :)')

