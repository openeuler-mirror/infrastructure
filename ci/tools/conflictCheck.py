"""
The script is for community CI to check whether a Pull Request is mergeable. If not, the build will fail and a label 
named conflict will be tagged under the Pull Request.
"""
import requests
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def check(session):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}?access_token={3}'.format(owner, repo, number, access_token)
    try:
        r = session.get(url)
        if r.status_code != 200 and r.status_code != 502:
            print('ERROR! Fail to get Pull Request info, status_code:', r.status_code)
            sys.exit(1)
        state = r.json()['state']
        mergeable = r.json()['mergeable']
        if state == 'closed':
            result = 'The Pull Request has been closed. Skip checking.'
            print(result)
            comment(session, result)
            sys.exit(1)
        if not mergeable:
            print('ERROR! The Pull Request conflicts. Ready to tag conflict label.')
            tag(session)
            sys.exit(1)
        else:
            print('Conflict Check PASS.')
    except requests.exceptions.RetryError:
        print('ERROR! Too many retries, exit retry')
        sys.exit(1)

def comment(session, body):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/comments'.format(owner, repo, number)
    data = {"access_token": access_token, "body": body}
    r = session.post(url, data=data)
    if r.status_code != 201:
        print(r.status_code, r.json())

def tag(session):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(owner, repo, number,
                                                                                            access_token)
    try:
        r = session.post(url, "[\"conflicted\"]")
        if r.status_code != 201 and r.status_code != 502:
            print('ERROR! Fail to tag conflict label, status_code:', r.status_code)
            sys.exit(1)
        else:
            print('Tag conflict label successfully.')
    except requests.exceptions.RetryError:
        print('ERROR! Too many retries, exit retry')
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('4 parameters are required: owner, repo, number, access_token. Please do check!')
    owner = sys.argv[1]
    repo = sys.argv[2]
    number = sys.argv[3]
    access_token = sys.argv[4]

    retries = Retry(total=5,
                    backoff_factor=0.1,
                    status_forcelist=[502])
    s = requests.Session()
    s.mount('https://', HTTPAdapter(max_retries=retries))
    check(s)

