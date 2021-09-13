"""
A tool used to show name, privacy type and url of the full repositories for a specified organization.
Transfer the organization and access_token when execute the script.
A csv file named after organization will be generated as the output if all params provided work.
"""
import argparse
import csv
import requests
import sys


def get_organization_repos():
    page = 1
    while True:
        url = 'https://gitee.com/api/v5/orgs/{}/repos'.format(organization)
        params = {
            'type': 'all',
            'page': page,
            'per_page': 100,
            'access_token': access_token
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(response.json())
            sys.exit(1)
        for repo in response.json():
            name = repo['full_name'].split('/')[-1]
            private = repo['private']
            public = repo['public']
            internal = repo['internal']
            url = repo['html_url'][:-4]
            privacy = None
            if private:
                privacy = 'private'
            if public:
                privacy = 'public'
            if internal:
                privacy = 'internal'
            writer.writerow([name, privacy, url])
        if len(response.json()) == 0:
            break
        page += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='A tool used to show name, privacy type and url of the full repositories for a specified '
                    'organization. Transfer the organization and access_token when execute the script. A csv file '
                    'named after organization will be generated as the output if all params provided work.') 
    parser.add_argument('-o', '--org', help='organization', required=True)
    parser.add_argument('-t', '--token', help='access_token of Gitee', required=True)
    args = parser.parse_args()
    organization = args.org
    access_token = args.token
    with open('{}.csv'.format(organization), 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['REPO', 'TYPE', 'URL'])
        get_organization_repos()

