# Scripts
此目录用于存放一些通用或实用的脚本

---
### compareOwnersAndDevelopers
通过比较openeuler/community各个SIG的OWNERS文件与SIG下每个repo的developers的差异，以CSV文件为输出分别列出每个差异的SIG、REPO、OWNER_EXTRAS和DEV_EXTRAS，并在控制台输出。各个仓库的管理员默认只有openeuler-ci-bot，当有其他管理员时，会在控制台输出warning信息。
#### 运行
- 确保运行路径有community/，如没有会自动克隆。
- 传入一个有足够获取权限的access_token，通过在命令行使用`-t`或`--token`传入
#### 输出参数
- SIG: SIG的名称
- REPO: 仓库的全称，如src-openeuler/python-jenkins
- OWNER_EXTRAS: OWNERS文件中未在developers中出现的maintainers或committers的集合
- DEV_EXTRAS: developers中不属于OWNERS的成员的集合

---
### showOrgRepos
通过传入组织名与access_token，获取该组织的所有仓库的信息(名称、隐私类型、首页等)，并以CSV文件作为输出。
#### 运行
- 通过`-o`或`--org`传入组织
- 通过`-t`或`--token`传入access_token，需注意access_token是否具有足够权限
#### 输出参数
- REPO: 所属于传入组织的仓库
- TYPE: 仓库的隐私类型
- URL: 仓库主页

---
### compareReposAndRepositoryYaml
通过api查询openeuler和src-openeuler的所有仓库，并与repository/下对应的yaml文件对比，找出不在yaml中的仓库，以及yaml中被重命名的仓库和yaml中被重命名且仍存在的仓库，输出json字符串。
#### 运行
- 通过`-t`或`--token`传入access_token，需注意access_token是否具有足够权限  e.g. `python3 compareReposAndRepositoryYaml.py -t *********`
#### 输出
- 不在openeuler.yaml中的仓库
- 不在src-openeuler.yaml中的仓库
- openeuler.yaml中被重命名的所有仓库
- src-openeuler.yaml中被重命名的所有仓库
- openeuler.yaml中被重命名但仍存在的所有仓库
- src-openeuler.yaml中被重命名但仍存在的所有仓库
