## 如何申请同步上游仓库？

### 背景
当前社区有部分SIG组的项目，前期已经在github等托管平台开源，希望将github等托管平台的代码仓作为上游，同步到gitee的openEuler组织下。
### 操作流程
1. 在openEuler Gitee组织上申请建仓：community仓库提交建仓pr，描述清楚建仓需求，仓库情况等。可参考[PR](https://gitee.com/openeuler/community/pulls/5361)
2. 申请成为仓库管理员，即admin权限。该权限才能执行后续仓库同步操作。申请流程可以参考[PR](https://gitee.com/openeuler/community/pulls/5399)；
3. 提交issue通知基础设施团队更新仓库配置：在 [Infrastructure仓库](https://gitee.com/openeuler/infrastructure) 提交issue，描述同步上游的需求，并给出上游仓库链接。可参考[issue](https://gitee.com/openeuler/infrastructure/issues/I903Z9?from=project-issue)；
4. 如果issue未及时答复，可以联系基础设施团队，email: infra@openeuler.sh
