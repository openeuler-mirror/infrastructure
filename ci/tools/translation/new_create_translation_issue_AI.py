# ==================== 常量定义 ====================

# Issue类型常量
ISSUE_TYPE_TRANSLATION = "翻译"

# ==================== 数据模型定义 ====================

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TypeVar, Generic
from translation_agent import get_agent_summary

import requests
import yaml

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format='%(asctime)s [%(levelname)s] %(module)s.%(lineno)d %(name)s:\t%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class IssueTrigger:
    trigger_pr_path: str
    issue_title: str
    issue_assignee: str
    file_extension: list[str] = field(default_factory=list)


@dataclass
class Org:
    org_name: str
    issue_of_owner: str
    issue_of_repo: str
    auto_create_issue: bool
    issue_triggers: list[dict | IssueTrigger] = field(default_factory=list)
    change_content_exclude: list[str] = field(default_factory=list)

    def __post_init__(self):
        tmp_issue_triggers: list[IssueTrigger] = []
        for item in self.issue_triggers:
            tmp_issue_triggers.append(IssueTrigger(**item))
        self.issue_triggers = tmp_issue_triggers


@dataclass
class TranslationAgentConfig:
    backend: dict = field(default_factory=dict)
    model: dict = field(default_factory=dict)
    processing: dict = field(default_factory=dict)
    logging: dict = field(default_factory=dict)


@dataclass
class Config:
    orgs: list[dict | Org]
    translation_agent: dict | TranslationAgentConfig = field(default_factory=dict)

    def __post_init__(self):
        tmp_orgs: list[Org] = []
        for item in self.orgs:
            tmp_orgs.append(Org(**item))
        self.orgs = tmp_orgs
        
        if isinstance(self.translation_agent, dict) and self.translation_agent:
            self.translation_agent = TranslationAgentConfig(**self.translation_agent)


@dataclass
class ReqArgs:
    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, str] | None = field(default=None)
    data: str | None = field(default=None)
    timeout: int = field(default=180)


T = TypeVar('T')


def send_request(args: ReqArgs, t: Generic[T]) -> T:
    error_count = 0
    while error_count < 3:
        try:
            resp = requests.request(**args.__dict__)
            resp.raise_for_status()
            if type(t) is dict or type(t) is list:
                res_data: dict | list = resp.json()
            else:
                res_data: str = resp.text
        except requests.exceptions.RequestException as e:
            if e.response.status_code in [400, 401, 403, 404, 405]:
                logger.error("[ERROR] client error {}".format(e))
                break
            logger.error("[ERROR] server error: {}".format(e))
            error_count += 1
        else:
            logger.info("[OK] [{}], {}".format(args.method, args.url))
            return res_data
    return None


class GiteeClient:
    """
    Gitee OpenAPI 客户端
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def __init__(self, developer_token: str):
        """
        构造函数
        :param developer_token: Gitee v5 token
        """
        self.headers["Authorization"] = "Bearer {}".format(developer_token)

    def get_diff_content(self, owner: str, repo: str, number: int) -> str | None:
        req_url = "https://gitee.com/{}/{}/pulls/{}.diff".format(owner, repo, number)
        req_args = ReqArgs(method="GET", url=req_url, headers=self.headers)
        result: str | None = send_request(req_args, "")
        if result is None:
            logger.error("can not get diff file from PR: {}".format(req_url))
        return result

    def check_issue_exists(self, owner: str, repo: str, 
                           issue_titles: list[str]) -> tuple[list[str], list[str]]:
        req_url = "https://gitee.com/api/v5/repos/{}/{}/issues".format(owner, repo)
        page = 1
        existed_issues = []
        while page <= 200:
            query = {
                "per_page": 100,
                "page": page,
                "sort": "created",
                "direction": "desc",
            }
            req_args = ReqArgs(method="GET", url=req_url, params=query, headers=self.headers)
            result: list | None = send_request(req_args, [])
            if result is None:
                break
            page += 1
            for item in result:
                if not issue_titles:
                    return [], existed_issues
                if issue_titles and item.get('title') in issue_titles:
                    issue_titles.remove(item.get('title'))
                    existed_issues.append(item.get('html_url'))
            if len(result) < 100:
                break
        return issue_titles, existed_issues

    def create_issue(self, owner, repo, title, assignee, body):
        req_url = "https://gitee.com/api/v5/repos/{}/issues".format(owner)
        req_body = {
            "repo": repo,
            "title": title,
            "issue_type": ISSUE_TYPE_TRANSLATION,
            "body": body,
            "assignee": assignee,
            "push_events": False,
            "tag_push_events": False,
            "issues_events": False,
        }
        req_args = ReqArgs(method="POST", url=req_url, headers=self.headers, data=json.dumps(req_body))
        result: dict | None = send_request(req_args, {})
        return result is not None

    def add_pr_comment(self, owner, repo, number, body):
        req_url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}/comments'.format(owner, repo, number)
        req_body = {
            "body": "### Translation Feedback \n {} ".format(body)
        }
        req_args = ReqArgs(method="POST", url=req_url, headers=self.headers, data=json.dumps(req_body))
        result: dict | None = send_request(req_args, {})
        return result is None

    def check_only_marks_changed(self, owner, repo, number, check_list):
        diff_content = self.get_diff_content(owner, repo, number)

        # 检查docs/en路径下是否有对应的文件变更
        zh_files_in_en = check_zh_files_also_modified_in_en(diff_content)

        # 只检查docs/zh路径下的变更，过滤掉同时在en下修改的文件
        filtered_diff_content = filter_docs_zh_files(diff_content, zh_files_in_en)
        if not filtered_diff_content.strip():
            logger.info('No docs/zh changes found, skip mark change check')
            return

        deleted_strs, inserted_strs = get_diff_content_list(filtered_diff_content)
        if is_only_marks_changed(deleted_strs, inserted_strs, check_list):
            logger.warning('Only marks changed in docs/zh files, skip the following steps')
            sys.exit(1)
        logger.info('Not just only marks changed in docs/zh files, continue creating issue')


def get_diff_file_list(diff_content: str) -> list[str]:
    diff_files_list = []
    diff_files = [x.split(' ')[0][2:] for x in diff_content.split('diff --git ')[1:]]
    for diff_file in diff_files:
        if diff_file.endswith('\"'):
            d = re.compile(r'/[\d\s\S]+')
            diff_file = d.findall(diff_file)
            diff_file = diff_file[0].replace('/', '', 1).replace('\"', '')
            diff_files_list.append(diff_file)
        else:
            diff_files_list.append(diff_file)
    return diff_files_list


def get_diff_content_list(diff_content: str) -> tuple[str, str]:
    pieces = diff_content.split('diff --git')
    deleted_strs = ''
    inserted_strs = ''
    for piece in pieces:
        start = False
        for line in piece.splitlines():
            if line.startswith('@@'):
                start = True
                continue
            if not start:
                continue
            if line.startswith('-'):
                if len(line) == 1:
                    deleted_strs += '\n'
                else:
                    deleted_strs += line[1:]
            elif line.startswith('+'):
                if len(line) == 1:
                    inserted_strs += '\n'
                else:
                    inserted_strs += line[1:]
    return deleted_strs, inserted_strs


def is_only_marks_changed(a, b, check_list):
    s = SequenceMatcher(None, a, b)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            continue
        elif tag in ['delete', 'insert']:
            return False
        elif tag == 'replace':
            deleted = ''.join(a[i1:i2]).strip()
            inserted = ''.join(b[j1:j2]).strip()
            if deleted not in check_list or inserted not in check_list:
                return False
    return True


class Args:
    gitee_token: str
    pr_owner: str
    pr_repo: str
    pr_number: int
    siliconflow_api_key: str = ""
    siliconflow_api_base: str = "https://api.siliconflow.cn/v1"

    def validate(self):
        valid = self.gitee_token and self.pr_owner and self.pr_repo and self.pr_number
        if not valid:
            logger.error("Invalid Command Arguments")
            sys.exit(1)


def load_config_yaml(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as config_in:
        data = yaml.safe_load(config_in)

    if data is None:
        return None
    return Config(**data)


def analyze_diff_files(diff_files: list[str], issue_triggers: list[IssueTrigger],
                       issue_title_pr_mark: str) -> tuple[int, list[str], dict]:
    """
    分析diff文件，识别需要创建issue的文件（只处理docs/zh路径下的文件，不包括同时在docs/en下修改的文件）
    返回: (文件计数, 中文文件列表, 需要创建的issue字典)
    """
    file_count = 0
    zh_file = []
    need_create_issue = {}

    for trigger in issue_triggers:
        for diff_file in diff_files:
            # 只处理docs/zh路径下的文件
            if not diff_file.startswith('docs/zh/'):
                continue

            if diff_file.startswith(trigger.trigger_pr_path) and \
               diff_file.split('.')[-1] in trigger.file_extension:
                logger.info("file {} has been changed".format(diff_file))
                file_count += 1
                if "/zh" in trigger.trigger_pr_path:
                    need_create_issue["zh"] = [
                        trigger.issue_assignee,
                        "{}({}).".format(trigger.issue_title, issue_title_pr_mark)
                    ]
                    # 提取相对于docs/zh/的路径
                    relative_path = diff_file.replace("docs/zh/", "")
                    zh_file.append(relative_path)

    return file_count, zh_file, need_create_issue


def check_zh_files_also_modified_in_en(diff_content: str) -> list[str]:
    """
    检查哪些docs/zh文件在docs/en下也有修改
    返回：同时在docs/zh和docs/en下修改的文件列表（相对于docs/zh/的路径）
    """
    if not diff_content:
        return []

    # 获取所有diff文件
    all_diff_files = get_diff_file_list(diff_content)

    # 获取docs/zh和docs/en下的文件
    zh_files = [f.replace("docs/zh/", "") for f in all_diff_files if f.startswith("docs/zh/")]
    en_files = [f.replace("docs/en/", "") for f in all_diff_files if f.startswith("docs/en/")]

    # 找出同时在zh和en下修改的文件
    zh_files_in_en = []
    for zh_file in zh_files:
        if zh_file in en_files:
            zh_files_in_en.append(zh_file)
            logger.info(f"文件 {zh_file} 在docs/zh和docs/en下都有修改，将跳过摘要生成")

    return zh_files_in_en


def prepare_issue_templates(need_create_issue: dict) -> tuple[dict, list[str]]:
    """
    准备issue模板和标题列表
    """
    need_create_issue_template = {}
    need_create_issue_titles = []
    for issue_item in need_create_issue:
        need_create_issue_titles.append(need_create_issue[issue_item][1])
        need_create_issue_template[need_create_issue[issue_item][1]] = \
            need_create_issue[issue_item][0]
    return need_create_issue_template, need_create_issue_titles


def generate_issue_body(issue_summary, diff_files: list[str], pr_html_url: str) -> str:
    """
    生成issue的正文内容
    """
    issue_body = ""
    if issue_summary and not issue_summary.error:
        issue_body += f"## 🔗 相关PR链接\n\n"
        issue_body += f"- {pr_html_url}\n"
        issue_body += f"## 📊 变更统计\n\n"
        issue_body += f"- **总文件数**: {issue_summary.total_files}\n"
        issue_body += f"- **成功处理文件数**: {issue_summary.processed_files}\n"
        if issue_summary.total_files != issue_summary.processed_files:
            # 注意人工审查提醒
            issue_body += f"- **未处理文件数**: {issue_summary.total_files - issue_summary.processed_files}\n"
            issue_body += f"- **提醒：机器人未能及时自动生成所有改动的摘要，" \
                         f"请注意人工审查！**\n"
        if issue_summary.total_summary:
            total = issue_summary.total_summary
            issue_body += f"- **总改动行数**: {total.total_lines_changed}\n"
            issue_body += f"- **改动类型**: {', '.join(total.change_type_list)}\n\n"
            issue_body += f"## 🔍 整体变更摘要\n\n"
            issue_body += f"{total.overall_summary}\n\n"
            issue_body += f"## ⚠️ 整体潜在影响\n\n"
            issue_body += f"{total.overall_potential_impact}\n\n"
        if issue_summary.file_summaries:
            issue_body += f"## 📝 单文件变更详情\n\n"
            for summary in issue_summary.file_summaries:
                issue_body += f"### 📁 {summary.file_path}\n\n"
                issue_body += f"- **改动类型**: {summary.change_type}\n"
                issue_body += f"- **新增行数**: {summary.lines_added}\n"
                issue_body += f"- **删除行数**: {summary.lines_deleted}\n"
                # issue_body += f"- **潜在影响**: {summary.potential_impact}\n"
                issue_body += f"- **详细摘要**: {summary.summary}\n\n"
                issue_body += "---\n\n"
    else:
        issue_body += f"## ⚠️ 翻译变更检测\n\n"
        issue_body += f"检测到需要翻译的文件变更，但无法获取详细摘要信息。\n\n"
        issue_body += f"**变更文件数量**: {len(diff_files)}\n"
        issue_body += f"**相关PR**: {pr_html_url}\n\n"
        issue_body += f"## 📝 变更文件列表\n\n"
        for file_path in diff_files:
            issue_body += f"- {file_path}\n"
        issue_body += f"\n"

    issue_body += f"## ❗️ 本Issue的摘要内容基于AI Agent技术自动生成，" \
                 f"仅供参考，请以实际更改为准。\n\n"

    
    return issue_body


def filter_docs_zh_files(diff_content: str, exclude_files: list[str] = None) -> str:
    """
    过滤diff内容，只保留docs/zh路径下的文件变更
    :param exclude_files: 需要排除的文件列表（相对于docs/zh/的路径）
    """
    if exclude_files is None:
        exclude_files = []

    if not diff_content:
        return ""

    lines = diff_content.split('\n')
    filtered_lines = []
    current_file_section = []
    in_docs_zh_file = False
    current_file_path = ""

    for line in lines:
        if line.startswith('diff --git'):
            # 处理前一个文件
            if in_docs_zh_file and current_file_section:
                # 检查当前文件是否需要排除
                relative_path = current_file_path.replace("docs/zh/", "")
                if relative_path not in exclude_files:
                    filtered_lines.extend(current_file_section)
                    logger.info(f"包含docs/zh路径下的文件: {current_file_path}")
                else:
                    logger.info(f"排除docs/zh路径下的文件（因为在en下也有修改）: {current_file_path}")

            # 检查新文件是否在docs/zh路径下
            current_file_section = [line]
            in_docs_zh_file = False
            current_file_path = ""

            # 提取文件路径
            if ' a/' in line and ' b/' in line:
                # 找到 a/ 和 b/ 的位置
                a_pos = line.find(' a/')
                b_pos = line.find(' b/')

                if a_pos != -1 and b_pos != -1 and a_pos < b_pos:
                    # 提取a/和b/之间的路径
                    a_start = a_pos + 3  # 跳过 ' a/'
                    current_file_path = line[a_start:b_pos]

                    # 检查是否在docs/zh路径下
                    if current_file_path.startswith('docs/zh/'):
                        in_docs_zh_file = True
        else:
            # 继续当前文件的内容
            current_file_section.append(line)

    # 处理最后一个文件
    if in_docs_zh_file and current_file_section:
        # 检查当前文件是否需要排除
        relative_path = current_file_path.replace("docs/zh/", "")
        if relative_path not in exclude_files:
            filtered_lines.extend(current_file_section)
            logger.info(f"包含docs/zh路径下的文件: {current_file_path}")
        else:
            logger.info(f"排除docs/zh路径下的文件（因为在en下也有修改）: {current_file_path}")

    return '\n'.join(filtered_lines)


def process_org_item(org_item: Org, cli: GiteeClient, pr_owner: str, pr_repo: str, 
                    pr_number: int, siliconflow_api_key: str, siliconflow_api_base: str, 
                    pr_html_url: str, issue_title_pr_mark: str,
                    translation_agent_config: TranslationAgentConfig = None):
    """
    处理单个组织配置项
    """
    # 获取diff内容
    diff_content = cli.get_diff_content(pr_owner, pr_repo, pr_number)
    if diff_content is None:
        sys.exit(1)

    # 早期检查：查看diff中是否包含docs/zh路径下的文件变更
    if 'docs/zh/' not in diff_content:
        logger.info("diff内容中不包含docs/zh路径下的文件变更，无需创建翻译issue")
        return

    # 检查docs/en路径下是否有对应的文件变更
    zh_files_in_en = check_zh_files_also_modified_in_en(diff_content)
    if zh_files_in_en:
        logger.info(f"发现 {len(zh_files_in_en)} 个在docs/zh和docs/en下同时修改的文件：{zh_files_in_en}")
    else:
        logger.info("没有发现同时在docs/zh和docs/en下修改的文件")

    # 过滤只保留docs/zh路径下的文件，排除同时在docs/en下修改的文件
    filtered_diff_content = filter_docs_zh_files(diff_content, zh_files_in_en)

    # 检查是否有需要处理的docs/zh路径下的文件变更
    if not filtered_diff_content.strip():
        logger.info("没有需要处理的docs/zh路径下的文件变更，无需创建翻译issue")
        return

    diff_files = get_diff_file_list(filtered_diff_content)
    logger.info(f"解析出 {len(diff_files)} 个变更文件：{diff_files}")

    # 分析diff文件
    file_count, zh_file, need_create_issue = analyze_diff_files(
        diff_files, org_item.issue_triggers, issue_title_pr_mark)

    logger.info(f"分析完成：共找到 {file_count} 个需要处理的文件")

    # 验证是否需要创建issue
    if file_count == 0:
        logger.warning(
            "NOTE: https://gitee.com/{}/files change files out of translate range"
            .format(issue_title_pr_mark))
        return
    
    # 准备issue模板
    need_create_issue_template, need_create_issue_titles = prepare_issue_templates(need_create_issue)
    
    if not need_create_issue_titles:
        return
    
    # 检查issue是否已存在
    need_create_issue_list, existed_issue_list = cli.check_issue_exists(
        org_item.issue_of_owner, org_item.issue_of_repo, need_create_issue_titles)
    
    if not need_create_issue_list:
        feedback_comment = "所有相关的翻译issue已经存在，请检查: {}".format(
            ", ".join(existed_issue_list))
        logger.info("Warning: " + feedback_comment)
        cli.add_pr_comment(pr_owner, pr_repo, pr_number, feedback_comment)
        return
    
    # 创建issue
    for need_create_issue_item in need_create_issue_list:
        # 从配置中提取参数
        backend_config = translation_agent_config.backend if translation_agent_config else {}
        model_config = translation_agent_config.model if translation_agent_config else {}
        processing_config = translation_agent_config.processing if translation_agent_config else {}
        
        # 提取具体配置值
        backend_type = backend_config.get('type', 'siliconflow')
        model_name = model_config.get('name', 'Qwen/Qwen3-8B')
        temperature = model_config.get('temperature', 0.1)
        max_workers = processing_config.get('max_workers', 8)
        single_file_timeout = processing_config.get('single_file_timeout', 180)
        total_summary_timeout = processing_config.get('total_summary_timeout', 300)
        max_retry = model_config.get('max_retry', 5)
        max_retry_ollama = model_config.get('max_retry_ollama', 1)
        
        try:
            # 使用过滤后的diff内容生成AI摘要
            issue_summary = get_agent_summary(
                filtered_diff_content, siliconflow_api_key, siliconflow_api_base,
                model_name=model_name, backend_type=backend_type, temperature=temperature,
                max_workers=max_workers, single_file_timeout=single_file_timeout,
                total_summary_timeout=total_summary_timeout, max_retry=max_retry,
                max_retry_ollama=max_retry_ollama
            )
            issue_body = generate_issue_body(issue_summary, diff_files, pr_html_url)
            logger.info("AI Agent成功生成issue内容")
        except Exception as e:
            logger.error(f"AI Agent调用失败: {e}")
            logger.info("回退到传统方式创建issue")
            # 使用传统方式的简单issue body格式
            issue_body = "### Related PR link \n - {}".format(pr_html_url)
        
        success = cli.create_issue(org_item.issue_of_owner, org_item.issue_of_repo, 
                                   need_create_issue_item,
                                   need_create_issue_template[need_create_issue_item], issue_body)
        if success:
            logger.info(f"成功创建issue: {need_create_issue_item}")
        else:
            logger.error(f"创建issue失败: {need_create_issue_item}")
            # 添加PR评论说明创建失败
            error_comment = f"创建翻译issue失败: {need_create_issue_item}，请手动创建"
            cli.add_pr_comment(pr_owner, pr_repo, pr_number, error_comment)


def create_issue_based_on_pr_diff_and_config(conf: Config, cli: GiteeClient, 
                                             pr_owner: str, pr_repo: str,
                                             pr_number: int, siliconflow_api_key: str, 
                                             siliconflow_api_base: str):
    """
    基于PR diff和配置创建issue的主函数
    """
    pr_html_url = "https://gitee.com/{}/{}/pulls/{}".format(pr_owner, pr_repo, pr_number)
    issue_title_pr_mark = "{}/{}/pulls/{}".format(pr_owner, pr_repo, pr_number)
    
    for org_item in conf.orgs:
        if org_item.org_name != pr_owner:
            continue
        
        process_org_item(org_item, cli, pr_owner, pr_repo, pr_number, 
                        siliconflow_api_key, siliconflow_api_base, pr_html_url, 
                        issue_title_pr_mark, conf.translation_agent)          



def main():
    parser = argparse.ArgumentParser(description='Create Gitee Webhook based on the profile')
    parser.add_argument('--gitee_token', type=str, required=True, help='gitee v5 api token')
    parser.add_argument('--pr_owner', type=str, required=True, help='the PR of owner')
    parser.add_argument('--pr_repo', type=str, required=True, help='the PR of repo')
    parser.add_argument('--pr_number', type=str, required=True, help='the PR number')
    parser.add_argument('--siliconflow_api_key', type=str, default="", help='the API key of siliconflow')
    parser.add_argument('--siliconflow_api_base', type=str, 
                       default="https://api.siliconflow.cn/v1", 
                       help='the base URL of siliconflow')
    args = Args()
    parser.parse_args(args=sys.argv[1:], namespace=args)
    args.validate()

    exec_py = sys.argv[0]
    config_yaml_path = exec_py[:-2] + 'yaml'
    conf = load_config_yaml(config_yaml_path)

    cli = GiteeClient(args.gitee_token)

    pr_owner = args.pr_owner
    pr_repo = args.pr_repo
    pr_number = int(args.pr_number)
    siliconflow_api_key = args.siliconflow_api_key
    siliconflow_api_base = args.siliconflow_api_base
    create_issue_based_on_pr_diff_and_config(conf, cli, pr_owner, pr_repo, pr_number, 
                                            siliconflow_api_key, siliconflow_api_base)


if __name__ == '__main__':
    main()
