import yaml
import json
import re
import time
import requests
import os
import email
import imaplib
import smtplib
import psycopg2
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from textwrap import dedent

BRANCHES_MAP = {}

# map of getmailrc file path, host and pass
RCFile_MAP = {}

MAILING_LIST = []


def load_configuration():
    with open('/home/patches/repositories_branches_map.yaml', "r", encoding="utf-8") as f:
        d = yaml.safe_load(f.read())

    for k, v in d.get("mapping").items():
        BRANCHES_MAP[k] = v.get("branches")
        RCFile_MAP["/home/patches/rc/" + k] = v.get("env")
        MAILING_LIST.append(v.get("mailing-list"))


PR_SUCCESS = "反馈：\n" \
             "您发送到{}的补丁/补丁集，已成功转换为PR！\n" \
             "PR链接地址： {}\n" \
             "邮件列表地址：{}\n" \
             "\nFeedBack:\n" \
             "The patch(es) which you have sent to {} mailing list has been converted to a pull request successfully!\n" \
             "Pull request link: {}\n" \
             "Mailing list address: {}\n"

PR_FAILED = "反馈:\n" \
            "您发送到{}的补丁/补丁集，转换为PR失败！\n" \
            "邮件列表地址：{}\n" \
            "失败原因：{}\n" \
            "建议解决方法：{}\n" \
            "\nFeedBack:\n" \
            "The patch(es) which you have sent to {} has been converted to PR failed!\n" \
            "Mailing list address: {}\n" \
            "Failed Reason: {}\n" \
            "Suggest Solution: {}\n"


def make_fork_same_with_origin(branch_name, o, r):
    """
    use this function to make the fork repository same with the source repository
    :param branch_name: origin branch
    :param o: organization
    :param r: repo name
    :return:
    """

    remotes = os.popen("git remote -v").readlines()
    remote_flag = False
    for remote in remotes:
        if remote.startswith("upstream "):
            remote_flag = False
        else:
            remote_flag = True

    same_flag = True
    if remote_flag:
        os.popen("git remote add upstream https://gitee.com/{}/{}.git".format(o, r))

    # list git branches by git branch -a
    fork_branches_list = os.popen("git branch -a").readlines()
    create_to_fork = False
    for fb in fork_branches_list:
        fb = fb.strip("\n").strip(" ").replace("* ", "")
        if fb != ("remotes/origin/" + branch_name) and fb != branch_name:
            create_to_fork = True
        else:
            create_to_fork = False
            break

    if create_to_fork:
        # create branch to fork repo
        os.popen("git fetch upstream %s" % branch_name).readlines()
        os.popen("git checkout -f -b %s upstream/%s" % (branch_name, branch_name)).readlines()
        os.popen("git push -u origin %s" % branch_name).readlines()

        same_flag = True
        return same_flag

    os.popen("git checkout -f origin/{}".format(branch_name)).readlines()
    fetch_res = os.popen("git fetch upstream {}".format(branch_name)).readlines()
    for p in fetch_res:
        if "error:" in p or "fatal:" in p:
            print("fetch upstream error %s" % p)
            same_flag = False
    merge = os.popen("git merge upstream/{}".format(branch_name)).readlines()
    for m in merge:
        if "error:" in m or "fatal:" in m:
            print("merge upstream error %s" % m)
            same_flag = False

    push_res = os.popen("git push origin HEAD:{}".format(branch_name)).readlines()
    for s in push_res:
        if "error:" in s or "fatal:" in s:
            print("push error %s" % s)
            same_flag = False

    return same_flag


def get_mail_step():
    """
    this func is used to retrieve all the emails in different email hosts
    :return:
    """
    # 兼容多仓库
    for k, v in RCFile_MAP.items():
        os.environ["GET_EMAIL"] = os.getenv(v.get("host"))
        os.popen('getmail --getmaildir="{}" --idle INBOX'.format(k)).readlines()
        time.sleep(1)


def download_patches_by_using_git_pw(ser_id):
    """
    used to download all of the patches in a series to one  patch file
    :param ser_id: the id of a series which some patches belong to
    :return:
    """
    if not os.path.exists("/home/patches/{}".format(ser_id)):
        os.popen("mkdir -p /home/patches/{}".format(ser_id))
    retry = 0
    while True:
        if retry < 3:
            os.popen("git-pw series download {} /home/patches/{}/".format(ser_id, ser_id)).readlines()
            retry += 1
        else:
            break


def get_project_and_series_information():
    """
    get the information of the series of patches which is needed to deal with
    :return:
    """
    if not os.path.exists("/home/patches/project_series.txt"):
        return []
    with open("/home/patches/project_series.txt", "r", encoding="utf-8") as f:
        infor = f.readlines()

    return infor


def config_git(git_email, git_name):
    """
    set git config
    :param git_email: committer email
    :param git_name:  committer name
    :return:
    """
    os.popen("git config --global user.email {};git config --global user.name '{}'".format(git_email, git_name))


def un_config_git():
    """
    unset git config
    :return:
    """
    # make sure not push code to git by using the before one's information while git config not work
    os.popen("git config --global --unset user.name")
    os.popen("git config --global --unset user.email")


def config_get_mail(rc_path, u_name, u_pass, email_server, path_of_sh):
    """
    make different rc files
    :param rc_path: path of the file
    :param u_name: email address
    :param u_pass: email password
    :param email_server: email server ex: pop.163.com
    :param path_of_sh: the path of a shell script which is used to parse the patch email
    :return:
    """
    file_path = "{}/getmailrc".format(rc_path)
    if os.path.exists(file_path):
        with open("{}/getmailrc".format(rc_path), "r", encoding="utf-8") as ff:
            content = ff.readlines()
            if len(content) == 0:
                os.popen("rm -f {}/getmailrc".format(rc_path)).readlines()
                os.popen("touch {}/getmailrc".format(rc_path)).readlines()
            else:
                return
    else:
        os.popen("mkdir -p %s" % rc_path).readlines()
        os.popen("touch {}".format(file_path)).readlines()

    retriever = ["[retriever]", "type = SimplePOP3SSLRetriever",
                 "server = {}".format(email_server),
                 "username = {}".format(os.getenv(u_name, "")),
                 "password = {}".format(os.getenv(u_pass, "")),
                 "port = {}".format(os.getenv("EMAIL_PORT"))
                 ]

    destination = ["[destination]", "type = MDA_external", "path = {}".format(path_of_sh), "ignore_stderr = true"]

    options = ["[options]", "delete = false", "message_log = {}/getmail.log".format(rc_path),
               "message_log_verbose = true", "read_all = false", "received = false", "delivered_to = false"]

    with open(file_path, "a", encoding="utf-8") as f:
        f.writelines([r + "\n" for r in retriever])
        f.writelines([r + "\n" for r in destination])
        f.writelines([r + "\n" for r in options])


def config_git_pw(project_name, server_link, token):
    """
    config the git-pw tools
    :param project_name: the name of project which your patches belong to
    :param server_link: patchwork service's api, ex: https://your-patchwork-address/api/1.2
    :param token: patchwork administrator's token
    :return:
    """
    os.popen("git config --global pw.server {};git config --global pw.token {};git config --global pw.project {}"
             .format(server_link, token, project_name)).readlines()


# if use the patchwork, we can make it by the following codes
# use patches
def make_branch_and_apply_patch(user, token, origin_branch, ser_id, repository_path):
    """
    make a new branch and apply patches to it
    :param user: owner of repos, ex: ci-robot...
    :param token: token of user
    :param origin_branch: origin branch, ex: openEuler-1.0-LTS
    :param ser_id: series id
    :param repository_path: path of repo
    :return: new branch, org, repo
    """
    org = repository_path.split("/")[0]
    repo_name = repository_path.split("/")[1]
    if not os.path.exists("/home/patches/{}".format(repository_path)):
        os.chdir("/home/patches/{}".format(org))
        if org == "src-openeuler":
            r = os.popen("git clone https://{}:{}@gitee.com/src-op/{}.git".format(user, token, repo_name)).readlines()
            for res in r:
                if "error:" in res or "fatal:" in res:
                    os.popen(
                        "git clone https://{}:{}@gitee.com/src-op/{}.git".format(user, token, repo_name)).readlines()
            os.chdir("/home/patches/{}".format(repository_path))
        elif org == "openeuler":
            r = os.popen("git clone https://{}:{}@gitee.com/ci-robot/{}.git".format(user, token, repo_name)).readlines()
            for res in r:
                if "error:" in res or "fatal:" in res:
                    os.popen(
                        "git clone https://{}:{}@gitee.com/ci-robot/{}.git".format(user, token, repo_name)).readlines()
            os.chdir("/home/patches/{}".format(repository_path))
    else:
        os.chdir("/home/patches/{}".format(repository_path))

    # if the codes in fork repository can not be the same with the origin, so skip it
    same = make_fork_same_with_origin(origin_branch, org, repo_name)
    if not same:
        return "", "", "", ""

    new_branch = "patch-%s" % int(time.time())
    os.popen("git checkout -b %s origin/%s" % (new_branch, origin_branch)).readlines()

    # git am
    patches_dir = "/home/patches/{}/".format(ser_id)
    am_res = os.popen("git am --abort;git am %s*.patch" % patches_dir).readlines()
    am_success = False
    am_failed_reason = ""

    for am_r in am_res:
        if am_r.__contains__("Patch failed at"):
            am_success = False
            am_failed_reason = am_r
            print("failed to apply patch, reason is %s" % am_r)
            break
        else:
            am_success = True

    if am_success:
        retry_flag = False
        push_res = os.popen("git push origin %s" % new_branch).readlines()
        for p in push_res:
            if "error:" in p or "fatal:" in p:
                time.sleep(3)
                print("git push failed, %s, try again" % p)
                os.popen("git push origin %s" % new_branch).readlines()
                retry_flag = True

        if retry_flag:
            os.popen("git push origin %s" % new_branch).readlines()
        # un_config_git()
        return new_branch, org, repo_name, am_failed_reason
    else:
        # un_config_git()
        return new_branch, org, repo_name, am_failed_reason


# summit a pr
def make_pr_to_summit_commit(org, repo_name, source_branch, base_branch, token, pr_url_in_email_list, cover_letter,
                             receiver_email, pr_title, commit, cc_email, sub, msg_id, bugzilla):
    """
    summit a pull request and add a "/check-cla" comment to it
    :param org: org
    :param repo_name: repo name
    :param source_branch:
    :param base_branch:
    :param token:
    :param pr_url_in_email_list: the url of email list which the patches come from,
        ex:https://mailweb.openeuler.org/hyperkitty/list/kernel@openeuler.org/thread/xxxxxxx/
    :param cover_letter: content in cover
    :param receiver_email: who send the patches
    :param pr_title: title of pull request
    :param commit: name and email of patch sender
    :param cc_email: cc email
    :param sub: the first email's subject
    :param msg_id: Message-ID of email headers
    :return:
    """
    title = pr_title
    if pr_url_in_email_list or cover_letter:
        body = "PR sync from: {}\n{} \n{} \n{}".format(commit, pr_url_in_email_list, cover_letter, bugzilla)
    else:
        body = ""

    create_pr_url = "https://gitee.com/api/v5/repos/{}/{}/pulls".format(org, repo_name)

    data = {
        "access_token": token,
        "head": "ci-robot:" + source_branch,
        "base": base_branch,
        "title": title,
        "body": body,
        "prune_source_branch": "true"
    }
    if org == "src-openeuler":
        data["head"] = "src-op:" + source_branch

    res = requests.post(url=create_pr_url, data=data)

    try_times = 0
    while True:
        if res.status_code != 201:
            if try_times >= 2:
                break
            res = requests.post(url=create_pr_url, data=data)
            try_times += 1
        else:
            break

    pr_failed_reason = ""
    if res.status_code == 201:
        pull_link = res.json().get("html_url")
        content = PR_SUCCESS.format(cc_email[0], pull_link, pr_url_in_email_list,
                                    cc_email[0], pull_link, pr_url_in_email_list)
        send_mail_to_notice_developers(
            content, receiver_email, cc_email, sub, msg_id, org + "/" + repo_name
        )

        # add /check-cla comment to pr
        comment_data = {
            "access_token": token,
            "body": "/check-cla",
        }
        comment_url = "https://gitee.com/api/v5/repos/{}/{}/pulls/{}/comments". \
            format(org, repo_name, res.json().get("number"))

        rsp = requests.post(url=comment_url, data=comment_data)

        if rsp.status_code != 201:
            requests.post(url=comment_url, data=comment_data)

        return True, pr_failed_reason
    else:
        if len(res.json()) != 0:
            pr_failed_reason = res.json().get("message")
        else:
            pr_failed_reason = "Unknown error"
        return False, pr_failed_reason


# use email to notice that pr has been created
def send_mail_to_notice_developers(content, email_address, cc_address, subject, message_id, repo_path):
    """
    reply email to notice the patch sender
    :param content: content of notice email
    :param email_address: receiver's email address
    :param cc_address: cc address
    :param subject: the subject of the first patch's subject
    :param message_id: Message-ID
    :param repo_path: path of repo, ex: src-openeuler/kernel
    :return:
    """
    env_host_user = ""
    env_host_pass = ""
    for k, v in RCFile_MAP.items():
        if repo_path in k:
            env_host_user = v.get("host")
            env_host_pass = v.get("pass")
    useraccount = os.getenv("%s" % env_host_user, "")
    password = os.getenv("%s" % env_host_pass, "")
    imap_server = 'imap.163.com'
    im_server = imaplib.IMAP4_SSL(imap_server, 993)
    im_server.login(useraccount, password)

    sm_server = smtplib.SMTP(os.getenv("SEND_EMAIL_HOST", "smtp.163.com"), os.getenv("SEND_EMAIL_PORT", 25))
    sm_server.ehlo()
    sm_server.starttls()
    sm_server.login(useraccount, password)

    imaplib.Commands['ID'] = ('AUTH')
    args = ("name", "{}".format(useraccount), "contact",
            "{}".format(useraccount), "version", "1.0.0", "vendor", "myclient")
    im_server._simple_command('ID', '("' + '" "'.join(args) + '")')
    im_server.select()
    _, unseen = im_server.search(None, "UNANSWERED")
    unseen_list = unseen[0].split()

    for number in unseen_list:
        _, data = im_server.fetch(number, '(RFC822)')
        original = email.message_from_bytes(data[0][1])
        from_email = original["From"]
        if "<" in from_email and ">" in from_email:
            from_email = original["From"].split("<")[1].split(">")[0]
        else:
            from_email = from_email.strip(" ")
        if from_email == email_address[0] and original['Message-ID'] == message_id:
            sm_server.sendmail(useraccount, email_address + cc_address,
                               create_auto_reply(useraccount, email_address, content, cc_address, original).as_bytes())
            log = 'Replied to “%s” for the mail “%s”' % (original['From'],
                                                         original['Subject'])
            print(log)
            im_server.store(number, '+FLAGS', '\\Answered')

    sm_server.quit()
    sm_server.close()
    im_server.logout()


# get origin content
def create_auto_reply(from_address, to_address, body, cc_address, original):
    """
    make information
    """

    mail = MIMEMultipart('alternative')
    mail['Message-ID'] = make_msgid()
    mail['References'] = mail['In-Reply-To'] = original['Message-ID']
    mail['Subject'] = 'Re: ' + original['Subject']
    mail['From'] = "patchwork bot <{}>".format(from_address)
    mail['To'] = ",".join(to_address)
    mail['Cc'] = ",".join(cc_address)
    mail.attach(MIMEText(dedent(body), 'plain'))
    return mail


def find_bugzilla_link(ser_id):
    """
    use to get bugzilla address of patches
    :param ser_id:
    :return: content of bugzilla address
    """
    bugzilla_set = set()
    bugzillas = os.popen('grep -rn "bugzilla:" /home/patches/{}/*'.format(ser_id)).readlines()

    https_re = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    for b in bugzillas:
        res = https_re.findall(b)
        if res:
            bugzilla_set.add(res[0])

    return "\n".join(bugzilla_set)


def get_email_content_sender_and_covert_to_pr_body(ser_id, path_of_repo):
    """
    get patch's or cover's data from DB
    :param ser_id: series id
    :param path_of_repo: path of repo, ex: openeuer/kernel
    :return:
    """
    user = os.getenv("DATABASE_USER")
    name = os.getenv("DATABASE_NAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")

    conn = psycopg2.connect(database=name, user=user, password=password, host=host, port="5432")

    cur = conn.cursor()

    cur.execute("SELECT * from patchwork_series where id={}".format(ser_id))
    series_rows = cur.fetchall()
    cover_letter_id = 0
    # all_patches_in_series = 0
    for row in series_rows:
        cover_letter_id = row[-1]
        # all_patches_in_series = row[4]

    # no cover
    patch_sender_email = ""
    patch_send_name = ""
    body = ""
    email_list_link_of_patch = ""
    title_for_pr = ""
    committer = ""
    sub = ""
    cc = []
    msg_id = ""

    if cover_letter_id is None or cover_letter_id == 0:
        cur.execute("SELECT name from patchwork_patch where series_id={}".format(ser_id))
        patches_names_rows = cur.fetchall()
        first_path_mail_name = ""
        if len(patches_names_rows) == 1:
            first_path_mail_name = patches_names_rows[0][0]
            title_for_pr = first_path_mail_name.split("]")[1]
            sub = first_path_mail_name
        else:
            for row in patches_names_rows:
                if row[0].__contains__("01/") or row[0].__contains__("1/"):
                    first_path_mail_name = row[0]

        cur.execute(
            "SELECT headers, name from patchwork_patch where series_id={}".format(ser_id))
        patches_headers_name_rows = cur.fetchall()
        patches_headers_rows = []
        for i in patches_headers_name_rows:
            if i[1] == first_path_mail_name:
                patches_headers_rows.append(i)
                break

        who_is_email_list = ""
        # new code using email
        email_msg = email.message_from_string(patches_headers_rows[0][0])
        # deal with email To
        email_to = email_msg.get("To").replace("\n\t", "")
        if "," in email_to:
            email_list = email_to.split(",")
            for e in email_list:
                if "<" in e and ">" in e:
                    if e.split("<")[1].split(">")[0] in MAILING_LIST:
                        who_is_email_list = e.split("<")[1].split(">")[0]
                else:
                    if e in MAILING_LIST:
                        who_is_email_list = e
        else:
            e = email_to
            if "<" in e and ">" in e:
                if e.split("<")[1].split(">")[0] in MAILING_LIST:
                    who_is_email_list = e.split("<")[1].split(">")[0]
            else:
                if e in MAILING_LIST:
                    who_is_email_list = e

        # deal with From
        email_from = email_msg.get("From")

        if "<" not in email_from and ">" not in email_from:
            # deal with email address like this xx@xx.com, not like X XX <xxx@xxx.com>
            e_re = re.compile(r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$')
            if e_re.match(email_from):
                patch_sender_email = email_from
                committer = patch_sender_email.split("@")[0] + " " + patch_sender_email
                patch_send_name = patch_sender_email.split("@")[0]
            else:
                e_from = email_from.split(" ")[-1]
                patch_sender_email = e_from
                committer = patch_sender_email.split("@")[0] + " " + patch_sender_email
                patch_send_name = patch_sender_email.split("@")[0]
        else:
            committer = email_from
            patch_sender_email = email_from.split("<")[1].split(">")[0]
            patch_send_name = email_from.split("<")[0].split(" ")[0] + " " + \
                              email_from.split("<")[0].split(" ")[1]

        # deal with Message-ID
        msg_id = email_msg.get("Message-ID") or email_msg.get("Message-Id")

        # deal with Archived-at
        email_list_link_of_patch = email_msg.get("Archived-At").replace(" ", "").\
            replace("\n", "").replace("<", "").replace(">", "")
        cc.append(who_is_email_list)

        if "1/" in first_path_mail_name:
            zh_reason = "补丁集缺失封面信息"
            zh_suggest = "请提供补丁集并重新发送您的补丁集到邮件列表"
            en_reason = "the cover of the patches is missing"
            en_suggest = "please checkout and apply the patches' cover and send all again"
            content = PR_FAILED.format(cc[0], email_list_link_of_patch, zh_reason, zh_suggest,
                                       cc[0], email_list_link_of_patch, en_reason, en_suggest)
            send_mail_to_notice_developers(content, [patch_sender_email], cc, sub, msg_id, path_of_repo)
            cur.close()
            conn.close()
            return "", "", "", "", "", "", "", ""

        # config git
        config_git(patch_sender_email, patch_send_name)
        cur.close()
        conn.close()

        return patch_sender_email, body, email_list_link_of_patch, title_for_pr, committer, cc, sub, msg_id

    cur.execute("SELECT * from patchwork_cover where id={}".format(cover_letter_id))
    cover_rows = cur.fetchall()
    cover_headers = ""
    cover_content = ""
    cover_name = ""
    for row in cover_rows:
        cover_name = row[5]
        cover_headers = row[3]
        cover_content = row[4]

    if cover_content == "" or cover_headers == "" or cover_name == "":
        cur.close()
        conn.close()
        return "", "", "", "", "", "", "", ""
    sub = cover_name
    title_for_pr = cover_name.split("]")[1]

    cover_who_is_email_list = ""
    # new code using email
    email_msg = email.message_from_string(cover_headers)
    # deal with email To
    email_to = email_msg.get("To").replace("\n\t", "")
    if "," in email_to:
        email_list = email_to.split(",")
        for e in email_list:
            if "<" in e and ">" in e:
                if e.split("<")[1].split(">")[0] in MAILING_LIST:
                    cover_who_is_email_list = e.split("<")[1].split(">")[0]
            else:
                if e in MAILING_LIST:
                    cover_who_is_email_list = e
    else:
        e = email_to
        if "<" in e and ">" in e:
            if e.split("<")[1].split(">")[0] in MAILING_LIST:
                cover_who_is_email_list = e.split("<")[1].split(">")[0]
        else:
            if e in MAILING_LIST:
                cover_who_is_email_list = e

    # deal with From
    email_from = email_msg.get("From")

    if "<" not in email_from and ">" not in email_from:
        # deal with email address like this xx@xx.com, not like X XX <xxx@xxx.com>
        e_re = re.compile(r'^\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$')
        if e_re.match(email_from):
            patch_sender_email = email_from
            committer = patch_sender_email.split("@")[0] + " " + patch_sender_email
            patch_send_name = patch_sender_email.split("@")[0]
        else:
            e_from = email_from.split(" ")[-1]
            patch_sender_email = e_from
            committer = patch_sender_email.split("@")[0] + " " + patch_sender_email
            patch_send_name = patch_sender_email.split("@")[0]
    else:
        committer = email_from
        patch_sender_email = email_from.split("<")[1].split(">")[0]
        patch_send_name = email_from.split("<")[0].split(" ")[0] + " " + \
                          email_from.split("<")[0].split(" ")[1]

    # deal with Message-ID
    msg_id = email_msg.get("Message-ID") or email_msg.get("Message-Id")

    # deal with Archived-at
    email_list_link_of_patch = email_msg.get("Archived-At").replace(" ", "")\
        .replace("\n", "").replace("<", "").replace(">", "")
    cc.append(cover_who_is_email_list)

    for ct in cover_content.split("\n"):
        if ct.__contains__("(+)") or ct.__contains__("(-)") or "mode" in ct or "| " in ct:
            continue
        else:
            cur.execute("select name from patchwork_patch where series_id={}".format(ser_id))
            patch_number = cur.fetchall()
            if len(patch_number) == 1:
                body = ""
            else:
                body += ct + "\n"

    # config git
    config_git(patch_sender_email, patch_send_name)

    cur.close()
    conn.close()

    return patch_sender_email, body, email_list_link_of_patch, title_for_pr, committer, cc, sub, msg_id


def check_patches_number_same_with_subject(ser_id, tag_str):
    user = os.getenv("DATABASE_USER")
    name = os.getenv("DATABASE_NAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")

    conn = psycopg2.connect(database=name, user=user, password=password, host=host, port="5432")

    cur = conn.cursor()
    cur.execute("SELECT count(*) from patchwork_patch where series_id={}".format(ser_id))
    in_db = cur.fetchall()
    patch_number_db = in_db[0][0]

    number_re = re.compile(r'\d+/\d+')
    if tag_str.count(",") < 2:
        if tag_str.count(",") == 0:
            patch_number_subject = 1
        else:
            n = tag_str.split(",")[-1]
            if number_re.match(n):
                patch_number_subject = int(n.split("/")[1])
            else:
                patch_number_subject = 1
    else:
        patch_number_subject = int(tag_str.split(",")[-1].split("/")[1])
    cur.close()
    conn.close()

    if patch_number_db != patch_number_subject:
        return False
    return True


def change_email_status_to_answered(host_pass_dict):
    """
    change all emails in email host to the 'Answered' status
    :param host_pass_dict: the map of email host and password
    :return:
    """
    useraccount = os.getenv("%s" % host_pass_dict.get("host"), "")
    password = os.getenv("%s" % host_pass_dict.get("pass"), "")
    imap_server = 'imap.163.com'
    im_server = imaplib.IMAP4_SSL(imap_server, 993)
    im_server.login(useraccount, password)

    imaplib.Commands['ID'] = ('AUTH')
    args = (
    "name", "{}".format(useraccount), "contact", "{}".format(useraccount), "version", "1.0.0", "vendor", "myclient")
    im_server._simple_command('ID', '("' + '" "'.join(args) + '")')
    im_server.select()
    _, unseen = im_server.search(None, "UNANSWERED")
    unseen_list = unseen[0].split()

    for number in unseen_list:
        im_server.store(number, '+FLAGS', '\\Answered')
    im_server.logout()


def rewrite_to_project_series_file(data_list):
    if os.path.exists("/home/patches/project_series.txt"):
        os.remove("/home/patches/project_series.txt")
    with open("/home/patches/project_series.txt", "a", encoding="utf-8") as f:
        for d in data_list:
            f.writelines(d)


def notice_dropped_patches_sender(data_string: str):
    """
    use to tell developers that their patches have been dropped because bot retries 3 times, the result is that pr can
    not been created.
    :param data_string: a information str
    :return:
    """
    series_id = data_string.split(":")[2]

    # open database connect
    user = os.getenv("DATABASE_USER")
    name = os.getenv("DATABASE_NAME")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")

    conn = psycopg2.connect(database=name, user=user, password=password, host=host, port="5432")

    cur = conn.cursor()

    cur.execute("SELECT msgid, submitter_id, headers from patchwork_patch where series_id={} LIMIT 1".format(series_id))
    patch_data = cur.fetchall()
    msgid, submitter_id, header = patch_data[0][0], patch_data[0][1], patch_data[0][2]

    archived_link = email.message_from_string(header).get("Archived-At").replace("<", "").replace(">", "")
    mailing_list = archived_link.split("/list/")[1].split("/message/")[0]

    cur.execute("SELECT email FROM patchwork_person where id={}".format(submitter_id))
    submitter_email = cur.fetchall()[0][0]

    cur.close()
    conn.close()

    zh_reason = "重试三次后仍无法创建PR，因此丢弃此补丁/补丁集"
    zh_suggest = "请确认补丁是否存在问题或者漏发，无误后重新发送至邮件列表"
    en_reason = "bot can not create PR after tried three times, so bot drop this patch(es)"
    en_suggest = "please checkout if something is wrong with your patches or you have missed some patches, " \
                 "you can send to mailing list again after you have checked"
    content = PR_FAILED.format(
        mailing_list, archived_link, zh_reason, zh_suggest, mailing_list, archived_link, en_reason, en_suggest
    )

    repo = data_string.split(":")[1].split("-")[0] + "/" + data_string.split(":")[1].split("-")[1]

    send_mail_to_notice_developers(
        content, [submitter_email], [], "", msgid, repo
    )


def check_retry_times(information: list):
    """
    use to checkout if a series of patches has been already try 3 times
    :param information: list
    :return: list
    """
    patch_to_retry_list = []
    if not os.path.exists("/home/patches/check.json"):
        os.popen("touch /home/patches/check.json")

    with open("/home/patches/check.json", "r", encoding="utf-8") as f:
        d = f.readlines()
        if len(d) == 0:
            dic = {}
            if len(information) == 0:
                return []
            for i in information:
                dic[i] = 0
                patch_to_retry_list.append(i)
            with open("/home/patches/check.json", "w", encoding="utf-8") as ff:
                json.dump(dic, ff)

            return patch_to_retry_list

        else:
            data_dic = json.loads("".join(d))
            write_to_json_dic = {}
            if len(information) == 0:
                for k, v in data_dic.items():
                    write_to_json_dic[k] = v + 1

            else:
                if len(information) == 0:
                    return []

                else:
                    for i in information:

                        v = data_dic.get(i)
                        if v is not None:
                            if v <= 2:
                                write_to_json_dic[i] = data_dic.get(i) + 1
                                patch_to_retry_list.append(i)
                            else:
                                try:
                                    notice_dropped_patches_sender(i)
                                except Exception as e:
                                    print("notice developer the action of dropping patch(es) "
                                          "from %s failed, reason: %s" % (i, e))
                                    continue
                        else:
                            write_to_json_dic[i] = 0
                            patch_to_retry_list.append(i)

            with open("/home/patches/check.json", "w", encoding="utf-8") as fw:
                json.dump(write_to_json_dic, fw)

            return patch_to_retry_list


def main():
    server = os.getenv("PATCHWORK_SERVER", "")
    server_token = os.getenv("PATCHWORK_TOKEN", "")
    repo_user = os.getenv("REPO_OWNER", "")
    not_cibot_gitee_token = os.getenv("GITEE_TOKEN_NOT_CI_BOT", "")
    mail_server = os.getenv("EMAIL_HOST", "")

    if server == "" or server_token == "" or repo_user == "" or not_cibot_gitee_token == "" or mail_server == "":
        print("args can not be empty")
        return

    load_configuration()

    # config get-mail tools
    for k, v in RCFile_MAP.items():
        config_get_mail(k, v.get("host"), v.get("pass"), mail_server,
                        "/home/patchwork/patchwork/patchwork/bin/parsemail.sh")

    # get mail from email address
    get_mail_step()

    information = get_project_and_series_information()
    if len(information) == 0:
        print("not a new series of patches which received by get-mail tool has been write to file")
        return

    infor_data = []
    for i in information:
        list_id = i.split(":")[0]
        repo = ""
        for k, v in RCFile_MAP.items():
            if os.getenv(v.get("host")) == list_id:
                repo = k.split("/")[-2] + "/" + k.split("/")[-1]

        project_name = i.split(":")[1]

        rep = repo.replace("/", "-")
        tag_name = i.split(":")[1].replace("%s-" % rep, "")

        series_id = i.split(":")[2]

        tag = ""
        try:
            tag = i.split(":")[3].split("[")[1].split("]")[0]
        except Exception as e:
            if e:
                print("execute {} failed, error: {}".format(i, e))
                continue

        # check if we have the same number of patches in db, if not, skip
        same_in_db = check_patches_number_same_with_subject(series_id, tag)
        if not same_in_db:
            infor_data.append(i)
            print("getmail did not pull all emails from %s, so skip" % i)
            continue

        branch = ""
        if tag.__contains__(","):
            if tag.count(",") == 1:
                if tag.split(",")[-1] == tag_name:
                    branch = tag.split(",")[-1]
                else:
                    branch = tag.split(",")[0]
            elif tag.count(",") >= 2:
                if tag.split(",")[-1] == tag_name:
                    branch = tag.split(",")[-1]
                elif tag.split(",")[-2] == tag_name:
                    branch = tag.split(",")[-2]
                else:
                    branch = tag.split(",")[0]
        else:
            branch = tag

        # in production environment， deploy on one branch
        branch = branch.strip(" ")

        config_git_pw(project_name, server, server_token)

        # download series of patches by series_id
        download_patches_by_using_git_pw(series_id)

        # get sender email and cover-letter-body
        sender_email, letter_body, sync_pr, title_pr, comm, cc, subject_str, message_id = get_email_content_sender_and_covert_to_pr_body(
            series_id, repo)

        # get bugzilla address in patches
        bugzilla_content = find_bugzilla_link(series_id)

        if sender_email == "" and letter_body == "" and sync_pr == "" and title_pr == "":
            print("can not get useful information for ", project_name, ", series id is ", series_id, ", repo is ", repo)
            continue

        emails_to_notify = [sender_email]
        cc_list = cc

        # use patches
        target_branch = BRANCHES_MAP.get(repo).get(branch)
        branch_not_match = False
        if target_branch is None:
            branch_not_match = True

        if branch_not_match:
            print("branch is ", branch, "can not match any branches")
            zh_reason = "补丁/补丁集的标题分支与仓库分支列表不匹配"
            zh_suggest = "请确认补丁标题中的分支是否正确，若有误则修改，无则忽略"
            en_reason = "branch in patch(es)'s title can not match any branches in repository's branch list"
            en_suggest = "please checkout if the patch(es)'s branch in title is wrong and fix it, if not ignore this"
            content = PR_FAILED.format(
                cc[0], sync_pr, zh_reason, zh_suggest, cc[0], sync_pr, en_reason, en_suggest
            )

            send_mail_to_notice_developers(
                content, emails_to_notify, cc, subject_str, message_id, repo
            )
            continue

        source_branch, organization, rp, failed_reason = make_branch_and_apply_patch(
            repo_user, not_cibot_gitee_token, target_branch, series_id, repo)

        if failed_reason != "":
            zh_reason = "应用补丁/补丁集失败，%s" % failed_reason.strip("\n")
            zh_suggest = "请查看失败原因， 确认补丁是否可以应用在当前期望分支的最新代码上"
            en_reason = "apply patch(es) failed, %s" % failed_reason.strip("\n")
            en_suggest = "please checkout if the failed patch(es) can work on the newest codes in expected branch"
            content = PR_FAILED.format(
                cc[0], sync_pr, zh_reason, zh_suggest, cc[0], sync_pr, en_reason, en_suggest
            )

            send_mail_to_notice_developers(
                content, emails_to_notify, cc, subject_str, message_id, repo
            )
            continue

        if source_branch == "" or organization == "" or rp == "":
            infor_data.append(i)

            zh_reason = "同步源码仓代码到fork仓失败"
            zh_suggest = "请稍等，机器人会在下一次任务重新执行"
            en_reason = "sync origin kernel's codes to the fork repository failed"
            en_suggest = "please wait, the bot will retry in the next interval"
            content = PR_FAILED.format(
                cc[0], sync_pr, zh_reason, zh_suggest, cc[0], sync_pr, en_reason, en_suggest
            )

            # sync codes from origin failed, so send email to tell developer what happened
            send_mail_to_notice_developers(content, emails_to_notify, cc, subject_str, message_id, repo)
            continue

        # make pr
        pr_success, reason = make_pr_to_summit_commit(organization, rp, source_branch, target_branch,
                                                      not_cibot_gitee_token,
                                                      sync_pr, letter_body, emails_to_notify, title_pr, comm, cc_list,
                                                      subject_str, message_id, bugzilla_content)

        if not pr_success and reason:
            infor_data.append(i)

            zh_reason = "调用gitee api创建PR失败， 失败原因如下： %s" % reason
            zh_suggest = "请稍等，机器人会在下一次任务重新执行"
            en_reason = "create PR failed when call gitee's api, failed reason is as follows: %s" % reason
            en_suggest = "please wait, the bot will retry in the next interval"
            content = PR_FAILED.format(
                cc[0], sync_pr, zh_reason, zh_suggest, cc[0], sync_pr, en_reason, en_suggest
            )

            # call gitee api to create PR failed, so send mail to tell developers what happened and take easy
            send_mail_to_notice_developers(content, emails_to_notify, cc, subject_str, message_id, repo)
            continue

    if len(infor_data) != 0:
        infor_data = check_retry_times(infor_data)
        rewrite_to_project_series_file(infor_data)
    else:
        os.remove("/home/patches/project_series.txt")
        # for v in RCFile_MAP.values():
        #     change_email_status_to_answered(v)


if __name__ == '__main__':
    main()
