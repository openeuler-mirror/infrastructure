---
1.  **请问我如何在Gitee平台申请加入openEuler企业，成为组织成员？**
		
请点击[链接](https://gitee.com/open_euler?invite=10c2a5093d0832fbbe4abe4f83e13ac80d3c14b54ae76b148e7cde0b62298f898e2a5d1b1b807987439bc1f65eaa027860f010c409ba4a18108234d13d970cb1)填写相关内容后申请加入即可；

申请通常会在三个工作日内审核生效；如未及时生效可邮件通知 [infra@openeuler.sh](mailto:infra@openeuler.sh) 。

---
2.  **请问如何在openEuler社区创建代码仓库？**
		
openEuler社区代码仓库的创建、删除管理方式如下：

	a.用户通过修改仓库配置文件，提交合入申请；

	b.TC审核申请，审核通过后合入配置文件；审核过程可能会有疑问，请申请人跟踪PR状态；

	c.社区机器人CI-bot根据仓库配置文件自动创建代码仓库；

所以新增代码仓库只需要在[相应代码路径](https://gitee.com/openeuler/community/tree/master/repository)修改对应配置文件(openeuler.yaml or src-open)并提交PR申请即可，随后跟踪PR审核状态与仓库创建状态；

如果仓库配置代码合入2小时后，代码仓库尚未创建，可邮件联系 [infra@openeuler.org](mailto:infra@openeuler.org) 或者 [infrastructure仓库](https://gitee.com/openeuler/infrastructure)提issue。

---
3.  **请问提交PR后出现openeuler-cla/no红色标签，如何处理？**
		
出现该标签表示该PR中所包含的commit中，有部分贡献者没有签署openEuler社区的贡献者协议CLA。[签署地址](https://gitee.com/link?target=https%3A%2F%2Fclasign.osinfra.cn%2Fsign%2FZ2l0ZWUlMkZvcGVuZXVsZXI%3D)可以在PR评论区找到。如果是个人贡献者请选择“签署个人CLA”，如果是作为企业的员工参与贡献请选择“签署员工CLA”；作为企业员工再签署是时需要使用企业邮箱，比如 [](mailto:xxx@huawei.com)[xxx@huawei.com](mailto:xxx@huawei.com) 、[xxxx@kylinos.cn](mailto:xxxx@kylinos.cn)等。CLA检查是使用commit中信息中的commit邮箱作为检查凭证的。该邮箱可以通过git log --pretty=fuller查询到。
		

<table>
<tbody><tr>
<th>场景</th>
<th>选择</th>
<th>处理方案</th>
</tr>
<tr>
<td>commit邮箱和Gitee提交邮箱一致</td>
<td>统一用该邮箱</td>
<td>使用该邮箱直接在上述 签署地址 签署CLA即可</td>
</tr>
<tr>
<td rowspan="2">commit邮箱和Gitee提交邮箱不一致</td>
<td>希望使用commit邮箱签署</td>
<td>调整Gitee提交邮箱为commit邮箱，在Gitee个人设置页面添加commit邮箱并设置为提交邮箱，然后在上述签署地址 完成CLA签署即可</td>
</tr>
<tr>
<td>希望使用gitee提交邮箱签署</td>
<td>在git运行的本地通过 git config --global user.name **** 和 git config --global user.email ****修改配置可调整git的commit邮箱信息为gitee的提交邮箱，完成后再进入签署地址进行CLA签署</td>
</tr>
</tbody>
</table>

---
4.  **请问为什么不能fork一个src-openeuler/abcd仓库到个人账号下？**

这个问题通常是因为在您的个人账号下，已经有abcd的同名仓库，比如你之前已经从openeuler组织下fork的abcd仓库；因为码云是通过你的个人账号加仓库名寻址的，所有不允许在你个人账号下有同名仓库。

修改个人账户下已有仓库的名称和路径，然后再从 src-openeuler/abcd 仓库fork即可。

---	
5.  **请问非maintainer贡献者是否可以直接往非保护分支push代码？**
		
抱歉，非maintainer贡献者不能直接向仓库push代码，包括保护分支和非保护分支。

保护分支与非保护分支的区别在于maintainer是否可以直接push；如果是非保护分支，maintainer可以有权限直接push；如果是保护分支maintainer也没有权限直接push，只能通过评论最终由CI-bot代为合入。

---
6.  **请问maintainer可否直接push代码到仓库？**
		
该问题需要确定代码合入到仓库的具体分支属性，如果分支为保护分支，maintainer没有权限直接push代码；如果分支为非保护分支，maintainer可以直接push代码。

---
7.  **请问直接push代码到仓库和通过评论/lgtm 、/approve合入代码有何区别？**
		
通过git命令直接push代码到仓库缺少必要的审核环节，存在一定合入风险；主要应用场景是比如需要上传的文件过大超过个人仓库限制，只能通过直接push到企业仓库的非保护分支，然后再通过非保护分支往保护分支merge；

通过评论/lgtm /approve合入代码从流程上增加了评审环节，保证一份代码的合入至少需要提交者以外的一位maintainer的评审同意，即便提交者本人是maintainer也需要另一位maintainer同意。

---
8.  **请问openEuler社区仓库评论区都支持哪些命令，分别都是什么含义？**
		
目前社区仓库评论区主要支持的命令:

[https://gitee.com/openeuler/community/blob/master/en/sig-infrastructure/command.md](https://gitee.com/openeuler/community/blob/master/en/sig-infrastructure/command.md)

---
9.  **请问在华为公司内部使用git clone从码云克隆代码报超时怎么办？( Failed to connect to  [gitee.com](http://gitee.com/)  port 443: Timed out )**
		
华为公司内克隆外网代码的时候提示

fatal: unable to access ‘[https://gitee.com/openeuler/community.git/](https://gitee.com/openeuler/community.git/)’: Failed to connect to [gitee.com](http://gitee.com/) port 443: Timed out

解决方法是依次配置：

git config --global https.proxy [https://域账号:密码@proxycn2.huawei.com:8080git config --global http.proxy](https://gitee.com/link?target=https%3A%2F%2F%25E5%259F%259F%25E8%25B4%25A6%25E5%258F%25B7%3A%25E5%25AF%2586%25E7%25A0%2581%40proxycn2.huawei.com%3A8080) [http://域账号:密码@proxycn2.huawei.com:8080](https://gitee.com/link?target=http%3A%2F%2F%25E5%259F%259F%25E8%25B4%25A6%25E5%258F%25B7%3A%25E5%25AF%2586%25E7%25A0%2581%40proxycn2.huawei.com%3A8080)

git config --global http.sslVerify false

注意如果个人域账号密码中有特殊字符需要转义。

---
10.  **请问我提交PR后为什么没有触发CI构建，需要如何处理？**
		
CI未及时触发通常有两种情况：

	a. 第一种可能是网络原因或系统任务调度原因，导致从代码仓库发出的webhook通知事件没有及时到达目标服务，所以没有触发CI构建；这种情况可以通过在PR评论去评论 /retest 重新触发；

	b.第二种可能是代码仓库创建以后短时间内提交PR，此时jenkins服务器侧尚未创建CI构建工程，所以触发不到CI构建，评论 /retest 也不生效；这种情况或者稍等一下系统自动建工程，或者联系 [](mailto:infra@openeuler.org)[infra@openeuler.org](mailto:infra@openeuler.org) 处理。

---
11.  **请问如何修改一个仓库分支的属性？**
		
请在https://gitee.com/openeuler/community/tree/master/repository 下，修改配置文件openeuler.yaml和src-openeuler.yaml，找到相应的仓库名称和对应的分支，然后修改分支属性。CI-bot会自动修改该属性信息到仓库。

如果修改后1小时仍未生效，可联系infra@openeuler.org帮助。

---
12.  **请问如何操作企业仓库中的tag信息？**
		
当前仓库的所有标签：

**git tag**

查看标签v2.0详细信息：

**git show v2.0**

给指定的commit打标签v2.0：

**git tag -a v2.0 ea0982sf34**

提交单个指定标签v2.0：

**git push origin v2.0**

本地删除指定标签v2.0：

**git tag -d v2.0**

删除远程仓库中指定标签v2.0：(：前为空即删除)

说明：仓库开发者（即openEuler社区maintainer有权限push tag到企业仓库如openeuler/infrastructure等）

**git push origin :refs/tags/v2.0**

---
13.  **请问PR为什么不能关联上Issue ？**
		
PR关联ISSUE的时候找不到相关的Issue的原因一般有两个：


- 用户没有相关权限，需要加入企业组织，参考问题1；
- 希望关联的Issue和PR不归属于同一个仓库，那么需要再企业版界面操作： 
   https://e.gitee.com/open_euler/dashboard ，【代码】——>（对应仓库）——>【代码评审】——>（对应PR）——>【关联工作项】输入Issue ID即可关联；

---
14. **如何简化或去除PR以及Issue中welcome信息里的@仓库成员信息？**
- 简化welcome成员信息<br>
(1)在[基础设施仓库](https://gitee.com/openeuler/infrastructure) 提起issue，表明需要对哪个仓库进行welcome成员信息简化处理<br>
(2)提供一个名为PATH_OWNER_MAPPING.YAML的yaml格式文件到需要做简化信息处理的仓库，[文件示例](https://gitee.com/openeuler/docs/blob/master/PATH_OWNER_MAPPING.YAML) <br>
(3)文件准备好后，由基础设施团队进行配置更新<br>
- 去除welcome成员信息<br>
(1)在[基础设施仓库](https://gitee.com/openeuler/infrastructure) 提起issue，表明需要对哪个仓库进行去除welcome成员信息处理<br>
(2)基础设施团队进行配置更新<br>
---
