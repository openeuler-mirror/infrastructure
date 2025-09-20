import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TypeVar, Generic
from comment_agent import get_comment_analysis

import requests
import yaml

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format='%(asctime)s [%(levelname)s] %(module)s.%(lineno)d %(name)s:\t%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Org:
    org_name: str
    comment_target_owner: str
    comment_target_repo: str
    auto_comment_enabled: bool = field(default=True)
    confidence_threshold: float = field(default=0.7)
    text_check_enabled: bool = field(default=True)
    grammar_check_enabled: bool = field(default=True)


@dataclass
class CommentAgentConfig:
    backend: dict = field(default_factory=dict)
    model: dict = field(default_factory=dict)
    processing: dict = field(default_factory=dict)
    logging: dict = field(default_factory=dict)


@dataclass
class Config:
    orgs: list[dict | Org]
    comment_agent: dict | CommentAgentConfig = field(default_factory=dict)

    def __post_init__(self):
        tmp_orgs: list[Org] = []
        for item in self.orgs:
            tmp_orgs.append(Org(**item))
        self.orgs = tmp_orgs
        
        if isinstance(self.comment_agent, dict) and self.comment_agent:
            self.comment_agent = CommentAgentConfig(**self.comment_agent)


@dataclass
class ReqArgs:
    method: str
    url: str
    headers: dict[str, str]
    params: dict[str, str] | None = field(default=None)
    data: str | None = field(default=None)
    timeout: int = field(default=180)


T = TypeVar('T')
content_type_is_text = "text/plain"
content_type_is_json_dict = {}
content_type_is_json_list = []


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

    def add_pr_comment(self, owner, repo, number, body):
        req_url = 'https://gitee.com/api/v5/repos/{}/{}/pulls/{}/comments'.format(owner, repo, number)
        req_body = {
            "body": "### 🤖 AI审查反馈 \n {} ".format(body)
        }
        req_args = ReqArgs(method="POST", url=req_url, headers=self.headers, data=json.dumps(req_body))
        result: dict | None = send_request(req_args, {})
        return result is not None



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


def generate_comment_content(comment_result, pr_url: str, analysis_status: str = "success") -> str:
    """根据分析结果生成评论内容"""
    comment_body = ""
    
    # 根据分析状态添加不同的状态标识
    if analysis_status == "error":
        comment_body += "### 分析状态：处理失败\n"
        comment_body += "**分析过程中发生错误，无法生成详细反馈。请手动审查文本变更。**\n\n"
    elif analysis_status == "low_confidence":
        comment_body += "### 分析状态：置信度较低\n"
        comment_body += "**当前分析置信度较低，结果仅供参考。建议进行人工审查。**\n\n"
    elif analysis_status == "no_text_changes":
        comment_body += "### 分析状态：无文本问题\n"
        comment_body += "**AI分析结果显示本次PR未发现明显的文本变更或语法问题。无需改动。**\n\n"
    elif analysis_status == "no_grammar_errors":
        comment_body += "### 分析状态：文本质量良好\n"
        comment_body += "**检测到文本变更，但未发现明显的语法错误，文本质量良好。无需改动。**\n\n"
    else:  # success with issues
        comment_body += "### 分析状态：发现需要关注的问题\n"
        comment_body += "**AI分析发现了一些文本变更或语法问题，请查看下方详细信息。**\n\n"
    
    # 如果有分析结果，添加详细信息
    if comment_result and not comment_result.error:
        # 如果有PR整体分析
        if comment_result.pr_analysis:
            pr_analysis = comment_result.pr_analysis
            
            # 添加整体评估摘要
            comment_body += "## 整体评估\n"
            comment_body += f"- 涉及文本变更: {'是' if pr_analysis.has_text_changes else '否'}\n"
            comment_body += f"- 文本变更类型: {pr_analysis.text_change_type}\n"
            comment_body += f"- 存在语法错误: {'是' if pr_analysis.has_grammar_errors else '否'}\n\n"
            
            # 添加详细分析
            if pr_analysis.detailed_analysis:
                comment_body += "## 详细分析\n"
                comment_body += f"{pr_analysis.detailed_analysis}\n\n"
            
            # 添加语法错误列表
            if pr_analysis.grammar_errors:
                comment_body += "## 语法问题\n"
                for i, error in enumerate(pr_analysis.grammar_errors, 1):
                    comment_body += f"{i}. {error}\n"
                comment_body += "\n"
            
            # 添加改进建议
            if pr_analysis.suggestions:
                comment_body += "## 改进建议\n"
                for i, suggestion in enumerate(pr_analysis.suggestions, 1):
                    comment_body += f"{i}. {suggestion}\n"
                comment_body += "\n"
        
        # 添加文件级别的分析结果
        if comment_result.file_analyses:
            # comment_body += "## 文件分析\n"
            
            # 统计有问题的文件
            files_with_issues = [f for f in comment_result.file_analyses if f.has_text_changes or f.grammar_issues]
            files_without_issues = [f for f in comment_result.file_analyses if not f.has_text_changes and not f.grammar_issues]
            
            if files_with_issues:
                comment_body += f"### 需要关注的文件 ({len(files_with_issues)} 个)\n"
                for i, file_analysis in enumerate(files_with_issues, 1):
                    comment_body += f"\n**{i}. {file_analysis.file_path}**\n"
                    
                    if file_analysis.has_text_changes:
                        comment_body += f"- 文本变更: 检测到英文文本改动\n"
                        if file_analysis.text_lines:
                            comment_body += f"- 涉及行数: {len(file_analysis.text_lines)} 行\n"
                    
                    if file_analysis.grammar_issues:
                        comment_body += f"- 语法问题: 发现 {len(file_analysis.grammar_issues)} 个问题\n"
                        for j, issue in enumerate(file_analysis.grammar_issues, 1):
                            comment_body += f"  {j}. {issue}\n"
                    
                    if file_analysis.analysis_details:
                        comment_body += f"- 分析详情: {file_analysis.analysis_details}\n"
            
            if files_without_issues:
                comment_body += f"\n### 无问题的文件 ({len(files_without_issues)} 个)\n"
                for file_analysis in files_without_issues:
                    comment_body += f"- {file_analysis.file_path}\n"
            
            # 添加处理统计
            # comment_body += f"\n### 处理统计\n"
            # comment_body += f"- 总文件数: {comment_result.total_files}\n"
            # comment_body += f"- 成功分析: {comment_result.processed_files}\n"
            # comment_body += f"- 有文本变更: {len([f for f in comment_result.file_analyses if f.has_text_changes])}\n"
            # comment_body += f"- 有语法问题: {len([f for f in comment_result.file_analyses if f.grammar_issues])}\n"

    # 添加免责声明
    comment_body += "## 免责声明\n"
    comment_body += "本评论内容基于AI Agent技术自动生成，仅供参考。请开发者根据实际情况进行判断和修改。\n"
    
    return comment_body


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


def create_comment_based_on_pr_diff_and_config(conf: Config, cli: GiteeClient, pr_owner: str, pr_repo: str,
                                              pr_number: int, siliconflow_api_key: str, siliconflow_api_base: str):
    pr_html_url = "https://gitee.com/{}/{}/pulls/{}".format(pr_owner, pr_repo, pr_number)
    
    for org_item in conf.orgs:
        if org_item.org_name != pr_owner:
            continue
        
        if not org_item.auto_comment_enabled:
            logger.info(f"组织 {org_item.org_name} 未启用自动评论功能")
            continue
        
        # 移除文件筛选逻辑，对所有PR平等处理
        logger.info("开始对PR进行全面文本分析（不限制文件类型和路径）")
        
        # 获取diff内容
        diff_content = cli.get_diff_content(pr_owner, pr_repo, pr_number)
        if diff_content is None:
            logger.error("无法获取PR的diff内容")
            sys.exit(1)
        
        # 调用AI Agent进行分析
        logger.info("开始进行AI代码审查分析...")
        comment_result = get_comment_analysis(diff_content, siliconflow_api_key, siliconflow_api_base)
        
        if not comment_result:
            logger.error("AI分析失败，将发布错误状态评论")
            # 创建一个错误结果对象，确保能发布评论
            from comment_agent import CommentResult
            comment_result = CommentResult(
                pr_analysis=None,
                file_analyses=[],
                processed_files=0,
                total_files=0,
                error="AI分析过程失败"
            )
        
        # 确定分析状态和评论内容
        analysis_status = "success"
        
        if comment_result.error:
            analysis_status = "error"
            logger.info("AI分析过程出错，将发布错误状态评论")
        elif comment_result.pr_analysis:
            pr_analysis = comment_result.pr_analysis
            
            # 检查是否有文本变更或语法错误
            if pr_analysis.has_text_changes and pr_analysis.has_grammar_errors:
                analysis_status = "success"  # 有问题，正常处理
                logger.info("检测到文本变更和语法错误，将发布问题报告评论")
            elif pr_analysis.has_text_changes and not pr_analysis.has_grammar_errors:
                analysis_status = "no_grammar_errors"
                logger.info("检测到文本变更但无语法错误，将发布文本质量良好的评论")
            elif not pr_analysis.has_text_changes:
                analysis_status = "no_text_changes"
                logger.info("未检测到文本变更，将发布无文本问题的评论")
            else:
                analysis_status = "success"
                logger.info("检测到需要关注的问题，将发布详细分析评论")
        else:
            # 如果没有整体分析，检查是否有文件级别的问题
            files_with_issues = [f for f in comment_result.file_analyses if f.has_text_changes or f.grammar_issues]
            if files_with_issues:
                analysis_status = "success"
                logger.info(f"检测到 {len(files_with_issues)} 个文件有文本问题，将发布文件级别问题评论")
            else:
                analysis_status = "no_text_changes"
                logger.info("未检测到文件级别问题，将发布无问题评论")
        
        # 总是生成和发布评论
        comment_content = generate_comment_content(
            comment_result, 
            pr_html_url, 
            analysis_status
        )
        
        # 发布评论
        success = cli.add_pr_comment(pr_owner, pr_repo, pr_number, comment_content)
        if success:
            logger.info(f"AI代码审查评论发布成功 - 状态: {analysis_status}")
        else:
            logger.error(f"AI代码审查评论发布失败 - 状态: {analysis_status}")


def main():
    parser = argparse.ArgumentParser(description='Create AI-powered PR comment based on text analysis')
    parser.add_argument('--gitee_token', type=str, required=True, help='gitee v5 api token')
    parser.add_argument('--pr_owner', type=str, required=True, help='the PR of owner')
    parser.add_argument('--pr_repo', type=str, required=True, help='the PR of repo')
    parser.add_argument('--pr_number', type=str, required=True, help='the PR number')
    parser.add_argument('--siliconflow_api_key', type=str, default="", help='the API key of siliconflow')
    parser.add_argument('--siliconflow_api_base', type=str, default="https://api.siliconflow.cn/v1", help='the base URL of siliconflow')
    args = Args()
    parser.parse_args(args=sys.argv[1:], namespace=args)
    args.validate()

    exec_py = sys.argv[0]
    config_yaml_path = exec_py[:-2] + 'yaml'
    conf = load_config_yaml(config_yaml_path)

    cli = GiteeClient(args.gitee_token)

    pr_owner = args.pr_owner
    pr_repo = args.pr_repo
    pr_number = args.pr_number
    siliconflow_api_key = args.siliconflow_api_key
    siliconflow_api_base = args.siliconflow_api_base
    create_comment_based_on_pr_diff_and_config(conf, cli, pr_owner, pr_repo, pr_number, siliconflow_api_key, siliconflow_api_base)


if __name__ == '__main__':
    main()
