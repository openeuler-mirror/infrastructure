"""moderation about text and image"""
import argparse
import json
import os
import requests
import sys
import yaml
from prettytable import PrettyTable
from multiprocessing import Pool


def get_token():
    """
    get token of huaweicloud
    :return: token of huaweicloud
    """
    url = "https://iam.cn-north-4.myhuaweicloud.com/v3/auth/tokens"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "auth": {
            "identity": {
                "methods": [
                    "password"
                ],
                "password": {
                    "user": {
                        "domain": {
                            "name": account_username
                        },
                        "name": iam_username,
                        "password": iam_password
                    }
                }
            },
            "scope": {
                "project": {
                    "name": region
                }
            }
        }
    }

    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    if r.status_code == 201:
        token = r.headers['X-Subject-Token']
        return token
    else:
        print(r.json())
        return


def moderate_text(text):
    """
    moderate text through categories and return response of json format
    :param text: text to moderate
    :return: response of json format
    """
    token = get_token()
    if not token:
        print('token required')
        exit()
    url = 'https://moderation.{}.myhuaweicloud.com/v1.0/moderation/text'.format(region)
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token
    }
    data = {
        "categories": text_categories,
        "items": [
            {
                "text": text,
                "type": "content"
            }
        ]
    }
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    return r.json()


def moderate_image(img):
    """
    moderate image through categories and ad_categories, return response of json format
    :param img: url of the image to moderate
    :return: response of json format
    """
    token = get_token()
    if not token:
        print('token required')
        exit()
    url = 'https://moderation.{}.myhuaweicloud.com/v1.0/moderation/image'.format(region)
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token
    }
    data = {
        "url": img,
        "image": "",
        "categories": image_categories,
        "ad_categories": image_ad_categories,
        "threshold": ""
    }
    r = requests.post(url, headers=headers, data=json.dumps(data))
    return r.json()


def deal_with_text(file_name, s, pt, error):
    """
    deal with single text file, add row to pretty table when moderating without pass, return count of error
    :param file_name: file name
    :param s: slice of the diff file, which contains a whole diff about a file
    :param pt: pretty table for the final report
    :param error: count of consequence that fail to pass moderation
    :return: error
    """
    pieces = []
    while len(s) > 0:
        pieces.append(s[:5000])
        s = s[5000:]
    pool = Pool()
    r = pool.map(moderate_text, pieces)
    pool.close()
    pool.join()
    sensitive_words = []
    politics = []
    ad = []
    abuse = []
    porn = []
    contraband = []
    flood = []
    for i in r:
        sensitive_words.extend(i['result']['detail'].get('sensitive_words', []))
        politics.extend(i['result']['detail'].get('politics', []))
        ad.extend(i['result']['detail'].get('ad', []))
        abuse.extend(i['result']['detail'].get('abuse', []))
        porn.extend(i['result']['detail'].get('porn', []))
        contraband.extend(i['result']['detail'].get('contraband', []))
        flood.extend(i['result']['detail'].get('flood', []))
    dic = {
        'sensitive_words': {x: sensitive_words.count(x) for x in sensitive_words},
        'politics': {x: politics.count(x) for x in politics},
        'ad': {x: ad.count(x) for x in ad},
        'abuse': {x: abuse.count(x) for x in abuse},
        'porn': {x: porn.count(x) for x in porn},
        'contraband': {x: contraband.count(x) for x in contraband},
        'flood': {x: flood.count(x) for x in flood}
    }
    attentions = []
    for i in dic.keys():
        if dic[i]:
            attentions.append("counts of {}:{}".format(i, dic[i]))
    if sensitive_words or politics or ad or abuse or porn or contraband or flood:
        pt.add_row([file_name, "\n".join(attentions)])
        error += 1
    return error


def deal_with_image(file_name, pt, error, owner, repo, number):
    """
    deal with single image file, add row to pretty table when moderating without pass, return count of error
    :param file_name: file name
    :param pt: pretty table for the final report
    :param error: count of consequence that fail to pass moderation
    :param owner: owner of the Pull Request
    :param repo: repo of the Pull Request
    :param number: number of the Pull Request
    :return: error
    """
    r = requests.get('https://gitee.com/api/v5/repos/{}/{}/pulls/{}'.format(owner, repo, number))
    giteeid = r.json()['user']['login']
    branch = r.json()['head']['ref']
    image_url = 'https://gitee.com/{}/{}/raw/{}/{}'.format(giteeid, repo, branch, file_name)
    res = moderate_image(image_url)
    print(res)
    pt.add_row([file_name, "detail: {}".format(res['result']['category_suggestions'])])
    return error


def main(owner, repo, number):
    """
    main function
    :param owner: owner of the Pull Request
    :param repo: repo of the Pull Request
    :param number: number of the Pull Request
    :return: error
    """
    url = 'https://gitee.com/{}/{}/pulls/{}.diff'.format(owner, repo, number)
    r = requests.get(url)
    content = r.text
    slices = content.split('diff --git ')[1:]
    error = 0
    pt = PrettyTable(['File Name', 'Attentions'])
    for s in slices:
        file_name = s.split()[0].split('/', 1)[-1]
        if suffix:
            if file_name.split('.')[-1] not in suffix:
                continue
            if file_name.split('.')[-1] in text_suffixes:
                error = deal_with_text(file_name, s, pt, error)
            if file_name.split('.')[-1] in image_suffixes:
                if file_name.endswith('.gif') and os.path.getsize(filename=os.path.join(repo, file_name)) > 200 * 1024:
                    print('{}: Gif file over 200Kb needs to be converted to video'.format(file_name))
                    pt.add_row([file_name, 'Gif file over 200Kb needs to be converted to video'])
                    error += 1
                elif os.path.getsize(filename=os.path.join(repo, file_name)) > 500 * 1024:
                    print('{}: Images larger than 500Kb are not allowed'.format(file_name))
                    pt.add_row([file_name, 'Images larger than 500Kb are not allowed'])
                    error += 1
                else:
                    error = deal_with_image(file_name, pt, error, owner, repo, number)
        else:
            if file_name.split('.')[-1] in text_suffixes:
                error = deal_with_text(file_name, s, pt, error)
            if file_name.split('.')[-1] in image_suffixes:
                if file_name.endswith('.gif') and os.path.getsize(filename=os.path.join(repo, file_name)) > 200 * 1024:
                    print('{}: Gif file over 200Kb needs to be converted to video'.format(file_name))
                    pt.add_row([file_name, 'Gif file over 200Kb needs to be converted to video'])
                    error += 1
                elif os.path.getsize(filename=os.path.join(repo, file_name)) > 500 * 1024:
                    print('{}: Images larger than 500Kb are not allowed'.format(file_name))
                    pt.add_row([file_name, 'Images larger than 500Kb are not allowed'])
                    error += 1
                else:
                    error = deal_with_image(file_name, pt, error, owner, repo, number)
    if error:
        print('The table below show attentions you may review after moderation.')
        print(pt)
    else:
        print('moderation pass :)')
    return error


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='The script is used to moderate the text and image of Pull Request.To run the script, you must '
                    'provide owner(-o),repo(-r) and number(-n) of a pull request. You can also declare a list which '
                    'limit the types of files you need to moderate by suffix(-s).')
    parser.add_argument('-o', '--owner', help='owner of pull request', required=True)
    parser.add_argument('-r', '--repo', help='repo of pull request', required=True)
    parser.add_argument('-n', '--number', help='number of pull request', type=int, required=True)
    parser.add_argument('-s', '--suffix', help='limit the suffix of files to moderate', nargs='*')
    parser.add_argument('-tc', help='limit text categories', nargs='*')
    parser.add_argument('-ic', help='limit image categories', nargs='*')
    parser.add_argument('-iac', help='limit image ad categories', nargs='*')
    args = parser.parse_args()
    owner = args.owner
    repo = args.repo
    number = args.number
    suffix = args.suffix
    text_categories = args.tc
    image_categories = args.ic
    image_ad_categories = args.iac
    if text_categories:
        for category in text_categories:
            if category not in ['ad', 'politics', 'abuse', 'porn', 'contraband', 'flood', 'sensitive_words']:
                print('Invalid category in text_categories: {}'.format(category))
                sys.exit(1)
    if image_categories:
        for category in image_categories:
            if category not in ['politics', 'terrorism', 'porn']:
                print('Invalid category in image_categories: {}'.format(category))
                sys.exit(1)
    if image_ad_categories:
        for category in image_ad_categories:
            if category not in ['qr_code', 'politics', 'abuse', 'porn', 'ad', 'contraband', 'sensitive_words']:
                print('Invalid category in image_ad_categories: {}'.format(category))
                sys.exit(1)

    fp = open('categories.yaml', 'r')
    content = yaml.load(fp.read(), Loader=yaml.Loader)
    text_suffixes = content['text_suffixes']
    image_suffixes = content['image_suffixes']
    if not text_categories:
        text_categories = content['text_categories']
    if not image_categories:
        image_categories = content['image_categories']
    if not image_ad_categories:
        image_ad_categories = content['image_ad_categories']
    fp.close()

    account_username = os.getenv('ACCOUNT_USERNAME', '')
    region = os.getenv('REGION', '')
    iam_username = os.getenv('IAM_USERNAME', '')
    iam_password = os.getenv('IAM_PASSWORD', '')
    if not (account_username and region and iam_username and iam_password):
        print('Warning! Can not get token. account_username, region, iam_username and iam_password are all required.')
        sys.exit(1)
    err = main(owner, repo, number)
    if err != 0:
        sys.exit(1)
