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
            print('Fail to get Pull Request info, status_code:', r.status_code)
            print(r.json())
            sys.exit(1)
        mergeable = r.json()['mergeable']
        if not mergeable:
            print('The Pull Request conflicts. Exit...')
            tag(session)
            sys.exit(1)
        else:
            print('Conflict Check PASS.')
    except requests.exceptions.RetryError:
        print('Too many retries, exit retry')
        sys.exit(1)


def tag(session):
    url = 'https://gitee.com/api/v5/repos/{0}/{1}/pulls/{2}/labels?access_token={3}'.format(owner, repo, number,
                                                                                            access_token)
    try:
        r = session.post(url, "[\"conflict\"]")
        if r.status_code != 201 and r.status_code != 502:
            print('Fail to add conflict label, status_code:', r.status_code)
            print(r.json())
            sys.exit(1)
        else:
            print('Tag conflict label successfully.')
    except requests.exceptions.RetryError:
        print('Too many retries, exit retry')
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
