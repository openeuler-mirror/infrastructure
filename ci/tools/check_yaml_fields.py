import os
import re
import requests
import sys
import yaml


def check_white_list(k, white_list, filename):
    """
    check white list
    :param k: yaml fields
    :param white_list: white list
    :param filename: path of yaml file
    :return: errors
    """
    if k not in white_list:
        print('ERROR: The field {} not in white_list {}, please CHECK {}!'.format(k, white_list,
                                                                           os.path.join('community', filename)))
        return True
    else:
        return False


def load_yaml(file_path):
    """
    load yaml
    :param file_path: yaml path
    :return: content of yaml
    """
    with open(file_path) as fp:
        try:
            content = yaml.load(fp.read(), Loader=yaml.Loader)
        except yaml.MarkedYAMLError as e:
            print(e)
            sys.exit(1)
    return content


def get_diff_files(owner, repo, number):
    """
    get the pr's diffs
    :param owner:
    :param repo:
    :param number:
    :return: diff_files
    """
    r = requests.get('https://gitee.com/{}/{}/pulls/{}.diff'.format(owner, repo, number))
    if r.status_code != 200:
        print(r.status_code, r.text)
        sys.exit(1)
    diff_files = [x.split(' ')[0][2:] for x in r.text.split('diff --git ')[1:]]
    return diff_files


def check_repository(repo, filename, repos_white_list, branches_white_list, errors):
    """
    openeuler.yaml and src-openeuler.yaml check
    :param repo: repository
    :param filename: yaml file path
    :param repos_white_list:  white_lists['repos']
    :param branches_white_list:  white_lists['branches']
    :param errors: errors count
    :return: errors
    """
    content = load_yaml(os.path.join(repo, filename))
    if 'repositories' not in content.keys():
        print('key error, no repositories')
        sys.exit(1)
    if content.get('repositories'):
        for repo in content.get('repositories'):
            for k in repo.keys():
                if check_white_list(k, repos_white_list, filename):
                    errors += 1
            if 'branches' not in repo.keys():
                print('key error, no branches')
                sys.exit(1)
            for v in repo.get('branches'):
                for p in v.keys():
                    if check_white_list(p, branches_white_list, filename):
                        errors += 1
    else:
        print("{}'s repositories has no values".format(filename))
    return errors


def check_sigs_yaml(repo, filename, sigs_white_list, members_white_list, maturity_white_list, errors):
    """
    sigs.yaml check
    :param repo: repository
    :param filename: yaml file path
    :param sigs_white_list:  white_lists['sigs']
    :param members_white_list:  white_lists['members']
    :param maturity_white_list: white_list['maturity']
    :param errors: errors count
    :return: errors
    """
    content = load_yaml(os.path.join(repo, filename))
    if 'sigs' not in content.keys():
        print('key error, no sigs')
        sys.exit(1)
    if content.get('sigs'):
        for sig in content.get('sigs'):
            for k in sig.keys():
                if check_white_list(k, sigs_white_list, filename):
                    errors += 1
            if 'mentors' in sig.keys():
                for v in sig.get('mentors'):
                    for p in v.keys():
                        if check_white_list(p, members_white_list, filename):
                            errors += 1
            if 'maturity' in sig.keys():
                s = sig.get('maturity')
                if check_white_list(s, maturity_white_list, filename):
                    errors += 1
    else:
        print('sigs have no values')
    return errors


def check_sig_info_yaml(repo, filename, siginfo_white_list, members_white_list, repositories_white_list, errors):
    """
    siginfo.yaml check
    :param repo: repository
    :param filename: yaml file path
    :param siginfo_white_list:  white_lists['siginfo']
    :param members_white_list:  white_lists['members']
    :param repositories_white_list: white_list['repositories']
    :param errors: errors count
    :return: errors
    """
    content = load_yaml(os.path.join(repo, filename))
    for k in content.keys():
        if check_white_list(k, siginfo_white_list, filename):
            errors += 1
        if k in ['mentors', 'maintainers', 'committers'] and content.get(k):
            for i in content.get(k):
                for j in i.keys():
                    if check_white_list(j, members_white_list, filename):
                        errors += 1
        if k == 'repositories' and content.get('repositories'):
            for i in content.get('repositories'):
                if 'additional_contributors' in i.keys() and i.get('additional_contributors'):
                    for j in i['additional_contributors']:
                        for m in j.keys():
                            if check_white_list(m, members_white_list, filename):
                                errors += 1
                for s in i.keys():
                    if check_white_list(s, repositories_white_list, filename):
                        errors += 1
    return errors


def main(owner, repo, number):
    """
    main function
    :param owner: owner of pr
    :param repo: repository of pr
    :param number: pr number
    :return:
    """
    errors = 0
    white_lists = load_yaml('white_list.yaml')
    try:
        repos_white_list = white_lists['repos']
        branches_white_list = white_lists['branches']
        sigs_white_list = white_lists['sigs']
        siginfo_white_list = white_lists['siginfo']
        repositories_white_list = white_lists['repositories']
        members_white_list = white_lists['members']
        maturity_white_list = white_lists['maturity']
    except KeyError as e:
        print(e)
        sys.exit(1)
    diff_files = get_diff_files(owner, repo, number)
    for diff_file in diff_files:
        if diff_file == 'repository/src-openeuler.yaml' or diff_file == 'repository/openeuler.yaml':
            errors += check_repository(repo, diff_file, repos_white_list, branches_white_list, errors)
        if diff_file == 'sig/sigs.yaml':
            errors += check_sigs_yaml(repo, diff_file, sigs_white_list, members_white_list, maturity_white_list, errors)
        if re.match(r'^sig/.+/sig-info.yaml$', diff_file):
            sig_name = diff_file.split('/')[1]
            sigs_name_list = [x['name'] for x in load_yaml(os.path.join(repo, 'sig/sigs.yaml'))['sigs']]
            if sig_name not in sigs_name_list:
                print('{}: invalid sig name'.format(diff_file))
                errors += 1
            else:
                errors += check_sig_info_yaml(repo, diff_file, siginfo_white_list, members_white_list,
                                              repositories_white_list, errors)
    if errors != 0:
        print('ERROR: please check yaml fields!')
        sys.exit(1)
    print('PASS :)')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Required 3 parameters! The owner, repo and number need to be transferred in sequence.')
        sys.exit(1)
    pr_owner = sys.argv[1]
    pr_repo = sys.argv[2]
    pr_number = sys.argv[3]
    main(pr_owner, pr_repo, pr_number)
