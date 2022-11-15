# 仓库PR责任人细化指导
背景：当前仓库PR的welcome信息中，@的maintainers及committers过多，并且仓库目录及文件日益增多，希望对仓库目录及文件分级由不同的负责人管理，对welcome评论中成员进行精简，使得开发者更容易精准找到负责人，提升PR的处理效率.

功能：对welcome信息中的@成员部分根据PATH_OWNER_MAPPING.yaml文件中定义的规则（规则：yaml中定义了PR修改的不同文件或者不同目录下的文件对应划分不同的责任人）进行精简，并且可将精简后的成员设置为PR的负责人（此功能为可选项），此功能不影响PR合入权限.
## 1. PATH_OWNER_MAPPING.yaml文件
此文件由各仓库自行提供和维护.文件格式要求如下：
### example
```yaml
relations:
  - path:
      - sig/TC/new-op/c/community.yaml
      - en/T1
    owner:
      - gitee_id: zhangsan
        name: zhangsan
        organization: xxx
        email: zhangsan@xx.com
  - path:
      - sig/sig-Compatibility-Infra/new-op/a/app.yaml
      - zh/T1
    owner:
      - gitee_id: lisi
        name: lisi
        organization: xxx
        email: lisi@xx.com
      - gitee_id: wangwu
        name: wangwu
        organization: xxx
        email: wangwu@xx.com
```

## 2. 通知基础设施团队进行服务端配置
需要提供如下信息：<br>
branch：PATH_OWNER_MAPPING.yaml文件存放的仓库分支<br>
path：PATH_OWNER_MAPPING.yaml文件存放的仓库相对路径<br>
needAssign：是否需要将精简后的评论中@的责任人设置为PR的负责人
### example
```yaml
branch: master
path: sig/xxx/xxx/
needAssign: true
```
