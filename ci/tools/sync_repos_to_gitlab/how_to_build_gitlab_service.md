# 搭建Gitlab代码仓服务

## 1.下载镜像
### 镜像拉取:
postgresql:
```shell
docker pull swr.cn-north-4.myhuaweicloud.com/openeuler/public/postgres:1.15.1
```
redis:
```shell
docker pull swr.cn-north-4.myhuaweicloud.com/openeuler/public/redis:1.6.2.6
```
gitlab:
```shell
docker pull swr.cn-north-4.myhuaweicloud.com/openeuler/public/gitlab:1.15.2.2
```
## 2.参数设置

| 参数名 | 说明 | 是否必需 |
| --- | --- | --- |
|GITLAB_SECRETS_DB_KEY_BASE| 数据库中GitLab CI机密变量的加密密钥以及导入凭据.确保密钥至少有32个字符，并且不会丢失。您可以使用pwgen-Bsv1 64生成一个.如果要从GitLab CI迁移，则需要将此值设置为GitLab_CI_SECRETS_DB_KEY_BASE的值，无默认值.| 是 | 
|GITLAB_SECRETS_SECRET_KEY_BASE | 会话机密的加密密钥。确保密钥至少有64个字符，并且不会丢失。这个秘密可以以最小的影响进行轮换，主要影响是以前发送的密码重置电子邮件将不再有效。您可以使用pwgen-Bsv164生成一个。没有默认值.| 是 |
|GITLAB_SECRETS_OTP_KEY_BASE | GitLab中OTP相关内容的加密密钥。确保密钥至少有64个字符，并且不会丢失。如果您丢失或更改此密码，2FA将停止为所有用户工作。您可以使用pwgen-Bsv164生成一个。没有默认值。| 是 |
|GITLAB_ROOT_PASSWORD|首次运行时root用户的密码，默认值5iveL!fe， GitLab要求此长度至少为8个字符|是|
|GITLAB_ROOT_EMAIL|root用户邮箱|是|
|GITLAB_EMAIL|GitLab服务器的电子邮件地址，默认值为SMTP_USER，否则默认值为example@example.com|是|
|GITLAB_EMAIL_REPLY_TO|GitLab发送的电子邮件的回复地址，默认值为GITLAB_EMAIL，否则默认值为noreply@example.com.|是|
|GITLAB_INCOMING_EMAIL_ADDRESS|通过电子邮件回复的传入电子邮件地址，默认为IMAP_USER的值，否则默认为reply@example.com.请阅读电子邮件回复文档以当前设置此参数.|是|
|GITLAB_HOST|GitLab服务器的主机名,默认为localhost|是|
|GITLAB_PORT|GitLab服务器的端口，默认80|是|
|GITLAB_SSH_PORT|GitLab服务器的ssh端口号，默认22|是|
|GITLAB_NOTIFY_PUSHER| 将pusher添加到已失败的构建通知电子邮件的收件人列表中。默认为false|是|
|GITLAB_BACKUP_SCHEDULE|将定时任务设置为自动备份，可选值为禁用，每日、每周或每月。默认情况下禁用|是|
|DB_TYPE|GitLab服务后端数据库类型，在12.1版本后不支持Mysql，建议使用postgresql|是|
|DB_HOST|GitLab服务后端数据库主机ip|是|
|DB_PORT|GitLab服务后端数据库主机端口， 默认5432|是|
|DB_USER|GitLab服务后端数据库用户|是|
|DB_PASS|GitLab服务后端数据库密码|是|
|DB_NAME|GitLab服务后端数据库名|是|
|REDIS_HOST|redis主机ip|是|
|REDIS_PORT|redis端口，默认6379|是|
|SMTP_ENABLED|启用通过SMTP的邮件传递，如果定义了SMTP_USER，则默认为true，否则默认为false.|是|
|SMTP_DOMAIN|SMTP域|是|
|SMTP_HOST|SMTP服务器主机|是|
|SMTP_PORT|SMTP服务器端口|是|
|SMTP_USER|SMTP服务器用户|是|
|SMTP_PASS|SMTP服务器用户密码|是|
|SMTP_STARTTLS|启用STARTTLS，默认为true|是|
|SMTP_AUTHENTICATION|指定SMTP身份验证方法，如果设置了SMTP_USER，则默认为login|是|
|IMAP_ENABLED|启用通过IMAP发送邮件，如果定义了IMAP_USER，则默认为true，否则默认为false|是|
|IMAP_HOST|IMAP服务器主机|是|
|IMAP_PORT|IMAP服务器主机端口|是|
|IMAP_USER|IMAP服务器用户|是|
|IMAP_PASS|IMAP服务器用户密码|是|
|IMAP_SSL|启用SSL|是|
|IMAP_STARTTLS|启用STARTTLS，默认为false|是|

## 3.服务部署
### k8s部署
Step 1.在1的链接中下载镜像并在k8s环境中制定镜像信息
<br>
Step 2.将“2.参数设置”中的环境变量添加到k8s部署文件deployment.yaml中
<br>
参考配置: https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/sync_repos_to_gitlab/template-k8s-yaml/gitlab-template-deployment.yaml

### docker部署
Step 1. 部署postgresql<br>
```shell
docker run --name gitlab-postgresql -d \
    --env 'DB_NAME=gitlabhq_production' \
    --env 'DB_USER=gitlab' --env 'DB_PASS=password' \
    --env 'DB_EXTENSION=pg_trgm,btree_gist' \
    --volume /srv/docker/gitlab/postgresql:/var/lib/postgresql \
    postgresql:1.15.1
```

Step 2. 部署redis<br>
```shell
docker run --name gitlab-redis -d \
    --volume /srv/docker/gitlab/redis:/data \
    redis:1.6.2.6
```
<br>

Step 3. 部署gitlab<br>
tips:可将2中的环境变量通过--env的方式添加到服务启动的环境变量中;--volume是挂载主机数据路径到容器的数据路径，ex：主机路径:容器路径; --link可以用来链接2个容器，使得源容器（被链接的容器）和接收容器（主动去链接的容器）之间可以互相通信，并且接收容器可以获取源容器的一些数据.
```shell
docker run --name gitlab -d \
    --link gitlab-postgresql:postgresql --link gitlab-redis:redisio \
    --publish 10022:22 --publish 10080:80 \
    --env 'GITLAB_PORT=10080' --env 'GITLAB_SSH_PORT=10022' \
    --env 'GITLAB_SECRETS_DB_KEY_BASE=long-and-random-alpha-numeric-string' \
    --env 'GITLAB_SECRETS_SECRET_KEY_BASE=long-and-random-alpha-numeric-string' \
    --env 'GITLAB_SECRETS_OTP_KEY_BASE=long-and-random-alpha-numeric-string' \
    --volume /srv/docker/gitlab/gitlab:/home/git/data \
    gitlab:1.15.2.2
```
