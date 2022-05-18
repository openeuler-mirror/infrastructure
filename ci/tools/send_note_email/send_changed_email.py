import argparse
import re
import smtplib
import sys
from email.mime.text import MIMEText

import requests
import yaml


def load_config(file_path):
    """
       load yaml
       :param file_path: yaml file path
       :return: content of yaml
       """
    with open(file_path, encoding="utf-8") as fp:
        try:
            content = yaml.load(fp.read(), Loader=yaml.Loader)
        except yaml.MarkedYAMLError as e:
            print(e)
            sys.exit(1)
    return content


def get_diff_files(owner, repo, number, acc_token):
    """
    get the pr's diffs
    :param owner: owner ep:openeuler
    :param repo: repo ep: docs
    :param number: pull request number
    :param acc_token: access_token
    :return: list of diffs, pull request url
    """
    param = {"access_token": acc_token}
    result = requests.get('https://gitee.com/{}/{}/pulls/{}.diff'.format(owner, repo, number), params=param)
    if result.status_code != 200:
        print(result.status_code)
        print("please check owner: {}, repo: {}, pr_number: {}".format(owner, repo, number))
        sys.exit(1)
    diff_files_list = []
    diff_files = [x.split(' ')[0][2:] for x in result.text.split('diff --git ')[1:]]
    for diff_file in diff_files:
        if diff_file.endswith('\"'):
            df = re.compile(r'/[\d\s\S]+')
            diff_file = df.findall(diff_file)
            diff_file = diff_file[0].replace('/', '', 1).replace('\"', '')
            diff_files_list.append(diff_file)
        else:
            diff_files_list.append(diff_file)
    return diff_files_list


def get_template(trigger_list):
    body = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Log</title>
    </head>

    <body leftmargin="8" marginwidth="0" topmargin="8" marginheight="4">
        <table width="95%" cellpadding="0" cellspacing="0"  style="font-size: 11pt; font-family: Tahoma, Arial, Helvetica, sans-serif">
            <tr>
                This email is sent automatically, no need to reply!<br>
                <br>
                <td><font color="#CC0000">result - Files Changed</font></td>
            </tr>
            <tr>
                <td>
                <p><font color="#000000">changed files</font></p>
                <hr size="2" width="100%" align="center" /></td>
            </tr>
            <tr>
                <td>
                    <ul>
                        <li>{0}</li>
                    </ul>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """.format("{} have been changed".format(trigger_list))
    return body


def send_email(sender, receivers, smtp_host, smtp_port, smtp_user, smtp_pass, repo_url, file_list):

    html_body = get_template(file_list)
    print('get email template')
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['From'] = 'noReply<{}>'.format(sender)
    msg['To'] = receivers
    msg['Subject'] = '{} has been changed'.format(repo_url)
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        print('login success')
        server.sendmail(sender, receivers.split(','), msg.as_string())
        print('send email successfully')
    except TimeoutError as e:
        print('time out', e)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--org', help='org name', required=True)
    parser.add_argument('-r', '--repo', help='repo name', required=True)
    parser.add_argument('-n', '--number', help='pr number', required=True)
    parser.add_argument('-t', '--token', help='token', required=True)
    parser.add_argument('-h', '--host', help='host', required=True)
    parser.add_argument('-p', '--port', help='port', required=True)
    parser.add_argument('-u', '--user', help='user', required=True)
    parser.add_argument('-pw', '--pwd', help='pwd', required=True)
    args = parser.parse_args()

    org = args.org
    repo_name = args.repo
    pr_number = args.number
    acc_tk = args.token
    host = args.host
    port = args.port
    user = args.user
    password = args.pwd
    diffs = get_diff_files(org, repo_name, pr_number, acc_tk)

    repos = load_config("./watch_repo_pr.yaml")["repos"]
    for r in repos:
        v = []
        if r["repo"].split("/")[-2] == org and r["repo"].split("/")[-1] == repo_name:
            trigger_path = r["trigger_path"]
            for d in diffs:
                for t in trigger_path:
                    if d.startswith(t):
                        v.append(d)
        if len(v) > 0:
            receiver_addr = r["send_to"]
            sender_addr = user
            send_email(sender_addr, receiver_addr, host, port, user, password, r["repo"], v)
        else:
            print("%s no need to send email" % r["repo"])
