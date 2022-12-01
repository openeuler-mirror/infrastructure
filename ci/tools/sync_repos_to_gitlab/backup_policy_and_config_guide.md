# Gitlab 备份仓库
## 1.备份实现逻辑
（1）对于在目标平台（gitlab）的目标组织下不存在的仓库，则调用gitlab创建仓库的api进行创建；对于已经存在的仓库进行commit对比，如果源平台（如gitee，github）的仓库与目标平台（gitlab）一致，则跳过，若不一致，则将目标平台仓库删除并重新调用gitlab创建仓库的api进行创建.
脚本链接：https://gitee.com/wh-pkgs/infrastructure/blob/master/ci/tools/sync_repos_to_gitlab/sync.py <br>
（2）重试机制：因为大规模的调取api，可能会出现一些网络等不可避免的问题，所以存在一个重试的脚本，将（1）中未正常运行更新或创建的仓库记录到文件sync.log，重试脚本读取此文件进行创建.
重试脚本链接：https://gitee.com/wh-pkgs/infrastructure/blob/master/ci/tools/sync_repos_to_gitlab/sync_missing_to_gitlab.py

## 2.运行环境和参数
环境：当前提供的是python脚本，并且将脚本作为一个定时任务运行在一个jenkins的工程中，在参数传参正确的前提下也可以手动执行.<br>

|  参数名   | 作用 | 必需 |
|  ----  | ----  | --- |
|username | gitlab平台的用户名 | √ |
|password | gitlab平台的用户密码 | √ |
|gitee_token | gitee平台的token | 可选 |
|github_token | github平台token |可选|
|gitlab_token | gitlab平台token |√|

可选表示如果备份的仓库是单一的gitee或者github，在执行脚本传参的时候，将github_token或gitee_token的值设置为空字符串即可，但不能不传参.

## 3.配置文件规范
（1）当前脚本进行仓库备份是根据一份yaml文件来处理，可以根据此规范来定制符合要求的文件，以便脚本能够正常运行.<br>
    yaml链接：https://gitee.com/for_test_job/infrastructure/blob/master/ci/tools/sync_repos_to_gitlab/sync_conf.yaml <br>
（2）参数解释：<br>

|  参数名   | 作用 |
|  ----  | ----  |
|  duration   | 表明同步仓库任务执行的时间（但当前只是展示，没有实际用途） |
|  type   | 表明需要备份的是仓库或者组织，提供两种选择，repository表示备份单一仓库，organization表示备份组织下所有仓库 |
|  source   | （1）当备份组织时，表明需要备份的组织的源信息，其中org表示组织，platform表示平台，url表示组织的链接地址<br>（2）当备份仓库时，表明需要备份的仓库的源信息，其中org表示组织，platform表示平台，url表示组织地址，repos表示仓库名列表.<br> |
|  target   | org表示备份的目标组织，platform表示备份的目标平台，url表示组织的链接地址（当前脚本只支持从gitee和github平台备份到gitlab，故target均为gitlab的信息） |

配置文件示例：
```yaml
sync_tasks:
  - task:
    - duration: "H * * 0 *"
      type: organization
      source:
      - org: opensourceways
        platform: github
        url: https://github.com/opensourceways
      target:
      - org: opensourceway
        platform: gitlab
        url: https://source.openeuler.sh/opensourceway
  - task:
    - duration: "H * * 0 *"
      type: repository
      source:
      - org: ansible
        repos:
        - ansible
        platform: github
        url: https://github.com/ansible
      target:
      - org: opensourceway
        platform: gitlab
        url: https://source.openeuler.sh/opensourceway
```