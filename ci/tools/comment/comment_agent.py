import json
import re
import logging
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple, Literal
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from pathlib import Path
import sys
import time
# LangChain imports
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from pydantic import BaseModel, Field, SecretStr
from langchain_community.llms import Ollama
from langchain_ollama import ChatOllama
from langchain.chains import TransformChain, SequentialChain
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
import yaml

# ==================== 配置加载 ====================

def load_config(config_file="create_comment.yaml"):
    """从YAML文件加载配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('comment_agent', {})
    except FileNotFoundError:
        print(f"配置文件 {config_file} 不存在")
        raise
    except yaml.YAMLError as e:
        print(f"解析配置文件时发生错误: {e}")
        raise

# 加载配置
_config = load_config()

# ==================== 配置常量 ====================

BACKEND_TYPE = _config.get('backend', {}).get('type', 'siliconflow')
MODEL_NAME = _config.get('model', {}).get('name', 'Qwen/Qwen3-8B')
MODEL_TEMPERATURE = _config.get('model', {}).get('temperature', 0.1)
MODEL_MAX_RETRY = _config.get('model', {}).get('max_retry', 5)
PROCESSING_MAX_WORKERS = _config.get('processing', {}).get('max_workers', 8)
SINGLE_FILE_TIMEOUT = _config.get('processing', {}).get('single_file_timeout', 180)
TOTAL_COMMENT_TIMEOUT = _config.get('processing', {}).get('total_comment_timeout', 300)
LOGGING_LEVEL = _config.get('logging', {}).get('level', 'INFO')
SILICONFLOW_API_KEY = ''
SILICONFLOW_API_BASE = ''

# 配置日志
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL.upper()))
logger = logging.getLogger(__name__)

# ==================== 数据模型定义 ====================

class PRAnalysisResult(BaseModel):
    """PR分析结果的结构化输出"""
    has_text_changes: bool = Field(description="是否涉及英文文本改动", default=False)
    text_change_type: Literal["无文本改动", "仅标点符号改动", "英文内容改动", "代码注释改动", "混合改动"] = Field(description="文本改动类型")
    has_grammar_errors: bool = Field(description="是否存在语法语病错误", default=False)
    grammar_errors: List[str] = Field(description="具体的语法语病错误列表", default=[])
    detailed_analysis: str = Field(description="详细分析说明")
    suggestions: List[str] = Field(description="改进建议列表", default=[])

class FileTextAnalysis(BaseModel):
    """单个文件的文本分析"""
    file_path: str = Field(description="文件路径", default="")
    has_text_changes: bool = Field(description="是否涉及英文文本改动", default=False)
    text_lines: List[str] = Field(description="涉及文本改动的行", default=[])
    grammar_issues: List[str] = Field(description="语法问题列表", default=[])
    analysis_details: str = Field(description="分析详情")

@dataclass
class DiffFileInfo:
    """单个文件的diff信息"""
    file_path: str
    diff_content: str
    lines_added: int
    lines_deleted: int

@dataclass
class CommentResult:
    """评论生成结果"""
    pr_analysis: Optional[PRAnalysisResult]
    file_analyses: List[FileTextAnalysis]
    processed_files: int
    total_files: int
    error: Optional[str] = None

# ==================== Token 统计工具 ====================


# ==================== 工具函数 ====================

class DiffParser:
    """Git Diff 解析器"""
    
    @staticmethod
    def parse_git_diff(diff_content: str) -> List[DiffFileInfo]:
        """
        解析git diff内容，提取每个文件的改动信息
        
        Args:
            diff_content: git diff的原始内容
 
        Returns:
            包含文件路径和对应diff内容的列表
        """

        files = []
        current_file = None
        current_diff = []
        
        lines = diff_content.strip().split('\n')
        
        for line in lines:
            # 匹配文件路径行
            if line.startswith('diff --git'):
                # 保存前一个文件的信息
                if current_file and current_diff:
                    diff_info = DiffParser._create_diff_file_info(current_file, current_diff)
                    if diff_info:
                        files.append(diff_info)
                
                # 提取文件路径 - 改进的解析逻辑
                current_file = DiffParser._extract_file_path(line)
                if current_file:
                    current_diff = [line]
                else:
                    current_diff = []
            elif current_file:
                current_diff.append(line)
        
        # 添加最后一个文件
        if current_file and current_diff:
            diff_info = DiffParser._create_diff_file_info(current_file, current_diff)
            if diff_info:
                files.append(diff_info)
        
        return files
    
    @staticmethod
    def _extract_file_path(diff_line: str) -> Optional[str]:
        """
        从git diff行中提取文件路径，支持包含汉字的文件名
        
        Args:
            diff_line: git diff的文件头行，格式如 "diff --git a/path/to/file b/path/to/file"
            
        Returns:
            提取出的文件路径，如果解析失败则返回None
        """
        try:
            # 方法1: 处理引号包围的路径（Git对特殊字符的处理）
            # 格式: diff --git "a/path/to/file" "b/path/to/file"
            quoted_pattern = r'diff --git "a/(.+?)" "b/(.+?)"'
            quoted_match = re.match(quoted_pattern, diff_line)
            
            if quoted_match:
                file_path_a = quoted_match.group(1)
                file_path_b = quoted_match.group(2)
                # 通常a和b路径相同，使用a路径（旧文件路径）
                file_path = file_path_a
            else:
                # 方法2: 使用正则表达式匹配标准的git diff格式
                # 格式: diff --git a/path/to/file b/path/to/file
                pattern = r'diff --git a/(.+?) b/(.+?)(?:\s|$)'
                match = re.match(pattern, diff_line)
                
                if match:
                    file_path_a = match.group(1)
                    file_path_b = match.group(2)
                    # 通常a和b路径相同，使用a路径（旧文件路径）
                    file_path = file_path_a
                else:
                    # 方法3: 如果正则匹配失败，尝试更简单的解析
                    # 处理可能包含空格和特殊字符的文件名
                    if ' a/' in diff_line and ' b/' in diff_line:
                        # 找到 a/ 和 b/ 的位置
                        a_pos = diff_line.find(' a/')
                        b_pos = diff_line.find(' b/')
                        
                        if a_pos != -1 and b_pos != -1 and a_pos < b_pos:
                            # 提取a/和b/之间的路径
                            a_start = a_pos + 3  # 跳过 ' a/'
                            file_path = diff_line[a_start:b_pos]
                        else:
                            return None
                    else:
                        # 方法4: 最后的备选方案，简单的字符串分割
                        parts = diff_line.split()
                        if len(parts) >= 3:
                            a_path = parts[2]
                            if a_path.startswith('a/'):
                                file_path = a_path[2:]  # 移除'a/'前缀
                            else:
                                return None
                        else:
                            return None
            
            # 处理文件名编码
            return DiffParser._decode_file_path(file_path)
            
        except Exception as e:
            logger.warning(f"解析文件路径时发生错误: {e}, diff行: {diff_line}")
            return None
    
    @staticmethod
    def _decode_file_path(file_path: str) -> str:
        """
        解码文件路径，处理各种编码情况
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            解码后的文件路径
        """
        try:
            # 首先尝试URL解码，处理Git编码的文件名
            decoded_path = urllib.parse.unquote(file_path, encoding='utf-8')
            
            # 处理Git对特殊字符的引号包装
            if decoded_path.startswith('"') and decoded_path.endswith('"'):
                decoded_path = decoded_path[1:-1]
                # Git使用反斜杠转义，需要处理转义序列
                decoded_path = decoded_path.replace('\\"', '"')
                decoded_path = decoded_path.replace('\\\\', '\\')
            
            # 无论是否有引号包装，都尝试处理八进制编码
            # 检查是否包含八进制转义序列
            if '\\' in decoded_path and re.search(r'\\[0-7]{3}', decoded_path):
                decoded_path = DiffParser._decode_octal_sequences(decoded_path)
            
            return decoded_path
            
        except Exception as e:
            logger.warning(f"解码文件路径时发生错误: {e}, 原始路径: {file_path}")
            return file_path
    
    @staticmethod
    def _decode_octal_sequences(text: str) -> str:
        """
        解码文本中的八进制转义序列
        
        Args:
            text: 包含八进制转义序列的文本
            
        Returns:
            解码后的文本
        """
        try:
            # 查找八进制转义序列模式：\xxx
            pattern = r'\\([0-7]{3})'
            
            # 找到所有八进制序列
            matches = list(re.finditer(pattern, text))
            if not matches:
                return text
            
            # 收集所有字节值
            result = ""
            last_end = 0
            bytes_buffer = []
            
            for i, match in enumerate(matches):
                # 添加匹配前的文本
                if match.start() > last_end:
                    # 如果有缓冲的字节，先处理它们
                    if bytes_buffer:
                        try:
                            decoded_bytes = bytes(bytes_buffer).decode('utf-8')
                            result += decoded_bytes
                            bytes_buffer = []
                        except UnicodeDecodeError:
                            # 如果解码失败，保持原始形式
                            for byte_val in bytes_buffer:
                                result += f"\\{oct(byte_val)[2:].zfill(3)}"
                            bytes_buffer = []
                    
                    result += text[last_end:match.start()]
                
                # 处理当前八进制序列
                octal_str = match.group(1)
                try:
                    byte_value = int(octal_str, 8)
                    bytes_buffer.append(byte_value)
                except ValueError:
                    # 如果转换失败，添加原始字符串
                    if bytes_buffer:
                        try:
                            decoded_bytes = bytes(bytes_buffer).decode('utf-8')
                            result += decoded_bytes
                            bytes_buffer = []
                        except UnicodeDecodeError:
                            for byte_val in bytes_buffer:
                                result += f"\\{oct(byte_val)[2:].zfill(3)}"
                            bytes_buffer = []
                    result += match.group(0)
                
                last_end = match.end()
                
                # 检查是否是最后一个匹配或下一个匹配不连续
                is_last = (i == len(matches) - 1)
                is_next_non_consecutive = (not is_last and 
                                         matches[i + 1].start() != match.end())
                
                if is_last or is_next_non_consecutive:
                    # 处理缓冲的字节
                    if bytes_buffer:
                        try:
                            decoded_bytes = bytes(bytes_buffer).decode('utf-8')
                        except UnicodeDecodeError:
                            # 如果解码失败，保持原始形式
                            for byte_val in bytes_buffer:
                                result += f"\\{oct(byte_val)[2:].zfill(3)}"
                        bytes_buffer = []
            
            # 添加剩余的文本
            if last_end < len(text):
                result += text[last_end:]
            
            return result
            
        except Exception as e:
            logger.warning(f"解码八进制序列时发生错误: {e}, 原始文本: {text}")
            return text
    
    @staticmethod
    def _create_diff_file_info(file_path: str, diff_lines: List[str]) -> Optional[DiffFileInfo]:
        """创建DiffFileInfo对象"""
        diff_content = '\n'.join(diff_lines)
        lines_added, lines_deleted = DiffParser._count_lines_changed(diff_content)
        
        return DiffFileInfo(
            file_path=file_path,
            diff_content=diff_content,
            lines_added=lines_added,
            lines_deleted=lines_deleted
        )
    
    @staticmethod
    def _count_lines_changed(diff_content: str) -> Tuple[int, int]:
        """统计git diff中改动的行数"""
        lines_added, lines_deleted = 0, 0
        lines = diff_content.strip().split('\n')

        for line in lines:
            # 统计新增行（以+开头，但不是+++）
            if line.startswith('+') and not line.startswith('+++'):
                lines_added += 1
            # 统计删除行（以-开头，但不是---）
            elif line.startswith('-') and not line.startswith('---'):
                lines_deleted += 1

        return lines_added, lines_deleted

# ==================== LangChain 组件 ====================

class LLMFactory:
    """LLM工厂类"""
    
    @staticmethod
    def create_chat_llm(model_name: str = None, base_url: str = None):
        """创建LLM实例"""
        if model_name is None:
            model_name = MODEL_NAME
        
        if BACKEND_TYPE == "siliconflow":
            return ChatOpenAI(
                model=model_name,
                api_key=SecretStr(SILICONFLOW_API_KEY),
                base_url=SILICONFLOW_API_BASE,
                temperature=MODEL_TEMPERATURE
            )
        else:
            raise ValueError(f"不支持的后端类型: {BACKEND_TYPE}")

class PromptTemplates:
    """提示模板集合"""
    
    @staticmethod
    def get_file_text_analysis_prompt() -> ChatPromptTemplate:
        """获取单文件文本分析提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", f"""
你是一个专业的代码审查和语言专家，专注于分析Gitee文档仓库的翻译PR中的英文文本内容。每条PR都是人工生成的文档改动。请忽略中文、格式和代码的审计，专注于识别英文文本变更。

注意：请忽略中文、格式和代码的审计，专注于识别英文文本变更。如果文档的变更不涉及英文文本，你只需要输出“不涉及英文改动”即可，不需要额外输出任何分析结果。
同时：对于专有名词，例如openEuler、GitHub等，你不能将其纳入英文文本变更的纠错范围内，而是应该自动识别专有名词。对于代码的相关变更，也不应该纳入分析内容范围。

你需要遵循**能不提修改意见就不提修改意见**的原则进行审查！！！

请仔细分析这个文件的改动，并按照以下要求进行分析：

**分析重点：**

1. 英文文本变更识别：
   - 检查是否涉及英文文本内容的改动
   - 区分代码逻辑变更和英文文本内容变更
   - 识别注释、文档字符串、用户显示文本等英文文本内容
   - 标识出具体的英文文本变更行

2. 语法错误检测：
   - 检查英文文本的语法、拼写错误

**分析类型判断：**
- 如果改动不涉及任何英文文本内容，标记为"无英文文本改动"
- 如果涉及代码注释的英文文本变更，标记为"代码注释改动"
- 如果涉及文档、界面文本等英文内容变更，标记为"英文内容改动"

**语法检查重点：**
- 英文：主谓一致、时态、拼写、标点、语序

**输出要求：**
- 如果存在英文文本变更但变更不存在语法问题，则直接输出“不存在语法问题”，不需要任何额外输出
- 详细列出发现的语法错误（如果有）
- 不能超过100个汉字字符

            """),
            ("human", """
文件路径: {file_path}

Git Diff 内容:
{diff_content}

            """)
        ])
    
    @staticmethod
    def get_pr_analysis_prompt() -> ChatPromptTemplate:
        """获取整体PR分析提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """
你是一个专业的PR审查专家，专门分析Gitee文档仓库的翻译PR中的英文文本变更和语法问题。每条PR都是人工生成的文档改动。

请分析所有文件的改动，并生成一个综合评估，要求：

1. 整体文本变更评估：
   - 统计涉及文本变更的文件数量
   - 分析文本变更的类型分布
   - 评估变更的重要性和影响范围
   - 如果文本变更不涉及英文，或涉及英文但使用正确不需要改动，则**直接忽略**，无需对其进行总结

2. 语法错误汇总：
   - **仅汇总改动中的硬伤，如单词拼写错误、英语语法（时态语态）错误等**
   - **对于一些可以优化但称不上错误的点，以最小化改动为原则，选择忽略**
   - 提高报错阈值，忽略可优化翻译的点
   - 提供优先修复建议

3. 质量评估：
   - 对整个PR的文本质量给出评分
   - 分析文本变更的一致性
   - 评估对用户体验的影响

4. 改进建议：
   - 提供具体的修改建议
   - 推荐最佳实践
   - 建议后续的质量控制措施

**输出格式要求：**
- 提供清晰的分析结论
- 按优先级排列发现的问题
- 给出可操作的改进建议

            """),
            ("human", """
各个文件的分析结果:
{file_analyses}

总文件数: {total_files}
涉及文本变更的文件数: {text_changed_files}
            """)
        ])

class FileTextAnalysisChain:
    """单文件文本分析任务链"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # 创建输出解析器
        self.output_parser = JsonOutputParser(pydantic_object=FileTextAnalysis)
        
        # 为硅基流动平台添加输出格式说明
        format_instructions = """
请以JSON格式输出，包含以下字段：
{{
    "has_text_changes": "是否涉及英文文本改动（布尔值）",
    "text_lines": "涉及文本改动的行（字符串列表）",
    "grammar_issues": "语法问题列表（字符串列表）",
    "analysis_details": "分析详情（字符串）"
}}
"""
        # 创建新的prompt模板
        system_template = """
你是一个专业的代码审查和语言专家，专注于分析Gitee文档仓库的翻译PR中的英文文本内容。每条PR都是人工生成的文档改动。

**核心原则：只关注必然存在明显错误的地方，其他文件都不需要关注！**

**严格过滤条件：**
1. 如果文档的变更不涉及英文文本，直接标记为"无英文文本改动"，无需任何分析
2. 如果涉及英文文本但语法完全正确，直接标记为"语法正确，无需关注"
3. 如果仅涉及标点符号的微小调整，直接标记为"仅标点符号改动，无需关注"
4. 对于专有名词（如openEuler、GitHub等），自动识别并忽略，不纳入纠错范围
5. 对于代码相关变更，不纳入分析内容范围

**只关注以下明显错误：**
- 明显的单词拼写错误（如：recieve -> receive）
- 严重的语法错误（如：主谓不一致、时态错误）
- 明显的标点符号错误（如：缺少句号、逗号使用错误）
- 明显的语序错误

**忽略以下情况：**
- 语法正确但可以优化的表达
- 风格偏好问题
- 轻微的标点符号调整
- 术语选择的差异
- 表达方式的个人偏好

**输出要求：**
- 如果不存在明显错误，直接输出"语法正确，无需关注"
- 只有发现明显错误时才详细列出
- 不能超过100个汉字字符
- 遵循"能不提修改意见就不提修改意见"的原则

{format_instructions}
"""
        human_template = """
文件路径: {file_path}

Git Diff 内容:
{diff_content}
"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_template.format(format_instructions=format_instructions)),
            ("human", human_template)
        ])
        self.chain = self.prompt | self.llm | self.output_parser
    
    def analyze(self, diff_file_info: DiffFileInfo) -> Optional[FileTextAnalysis]:
        """分析单个文件的文本变更"""
        max_retry = MODEL_MAX_RETRY
        for attempt in range(1, max_retry + 1):
            # 如果不是第一次尝试，等待一段时间再重试，避免连续失败
            if attempt > 1:
                delay = min(attempt * 2, 10)  # 递增延迟，最多10秒
                logger.info(f"第{attempt}次尝试分析文件 {diff_file_info.file_path}，等待{delay}秒...")
                time.sleep(delay)
            
            try:
                # 构造prompt字符串
                prompt_args = {
                    "file_path": diff_file_info.file_path,
                    "diff_content": diff_file_info.diff_content
                }
                
                # 直接调用，简化超时控制
                invoke_args = {
                    "file_path": diff_file_info.file_path,
                    "diff_content": diff_file_info.diff_content
                }
                result = self.chain.invoke(invoke_args)
                # 验证结果有效性
                if isinstance(result, (dict, FileTextAnalysis)):
                    if isinstance(result, dict):
                        result = FileTextAnalysis(**result)
                    
                    # 检查结果完整性
                    if result and hasattr(result, 'analysis_details') and result.analysis_details:
                        
                        # 设置准确值
                        result.file_path = diff_file_info.file_path
                        
                        # 检查是否只关注明显错误
                        analysis_text = result.analysis_details.lower()
                        if any(phrase in analysis_text for phrase in [
                            "语法正确，无需关注", 
                            "无英文文本改动", 
                            "仅标点符号改动，无需关注",
                            "不存在语法问题"
                        ]):
                            # 如果无问题，设置has_text_changes为False
                            result.has_text_changes = False
                            result.grammar_issues = []
                        
                        return result
                
                # 结果无效，记录并重试
                logger.warning(f"分析文件 {diff_file_info.file_path} 返回无效结果，第{attempt}次尝试")
                if attempt < max_retry:
                    continue
            except Exception as e:
                err_str = str(e)
                # 检查是否为HTTP错误（如404、5xx），常见关键字有status code、HTTP、response等
                is_http_error = False
                for code in ["404", "500", "502", "503", "504"]:
                    if code in err_str:
                        is_http_error = True
                        break
                if ("status code" in err_str or "HTTP" in err_str or "response" in err_str) and any(code in err_str for code in ["404", "500", "502", "503", "504"]):
                    is_http_error = True
                if is_http_error:
                    logger.error(f"分析文件 {diff_file_info.file_path} 时发生HTTP错误: {e}，第{attempt}次尝试，10秒后重试...")
                    if attempt < max_retry:
                        time.sleep(10)
                        continue
                else:
                    logger.error(f"分析文件 {diff_file_info.file_path} 时发生错误: {e}，第{attempt}次尝试")
                # 其它异常直接进入下一次重试
                if attempt < max_retry:
                    logger.info(f"第{attempt}次尝试失败，准备重试...")
        logger.error(f"分析文件 {diff_file_info.file_path} 连续{max_retry}次均未获得结构化输出，放弃。")
        return None

class PRAnalysisChain:
    """PR整体分析任务链"""
    
    def __init__(self, llm: ChatOllama | ChatOpenAI):
        self.llm = llm
        
        # 创建输出解析器
        self.output_parser = JsonOutputParser(pydantic_object=PRAnalysisResult)
        
        # 为硅基流动平台添加输出格式说明
        format_instructions = """
请以JSON格式输出，包含以下字段：
{{
    "has_text_changes": "是否涉及英文文本改动（布尔值）",
    "text_change_type": "文本改动类型（字符串）",
    "has_grammar_errors": "是否存在语法语病错误（布尔值）",
    "grammar_errors": "具体的语法语病错误列表（字符串列表）",
    "detailed_analysis": "详细分析说明（字符串）",
    "suggestions": "改进建议列表（字符串列表）"
}}
"""
        # 创建新的prompt模板
        system_template = """
你是一个专业的PR审查专家，专门分析Pull Request中的文本变更和语法问题。

**核心原则：只关注必然存在明显错误的地方，其他文件都不需要关注！**

请基于各个文件的分析结果，生成整个PR的综合评估，要求：

1. 严格过滤文件：
   - 只统计存在明显错误的文件
   - 忽略"语法正确，无需关注"的文件
   - 忽略"无英文文本改动"的文件
   - 忽略"仅标点符号改动，无需关注"的文件

2. 只汇总明显错误：
   - 仅汇总硬伤：明显的单词拼写错误、严重的语法错误
   - 忽略可优化但称不上错误的点
   - 忽略风格偏好问题
   - 忽略轻微的标点符号调整

3. 质量评估：
   - 只对存在明显错误的文件进行质量评估
   - 如果所有文件都无问题，直接标记为"无问题文件"

4. 改进建议：
   - 只对存在明显错误的文件提供修改建议
   - 建议优先修复明显的拼写和语法错误

**输出格式要求：**
- 如果所有文件都无问题，直接输出"所有文件语法正确，无需关注"
- 只列出存在明显错误的文件
- 按优先级排列发现的问题
- 给出可操作的改进建议

{format_instructions}
"""
        human_template = """
各个文件的分析结果:
{file_analyses}

总文件数: {total_files}
涉及文本变更的文件数: {text_changed_files}
"""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_template.format(format_instructions=format_instructions)),
            ("human", human_template)
        ])
        self.chain = self.prompt | self.llm | self.output_parser
    
    def generate(self, file_analyses: List[FileTextAnalysis]) -> Optional[PRAnalysisResult]:
        """生成PR整体分析"""
        try:
            total_files = len(file_analyses)
            
            # 过滤出只关注存在明显错误的文件
            problematic_files = []
            for analysis in file_analyses:
                # 检查是否存在明显错误
                has_obvious_errors = (
                    analysis.has_text_changes and 
                    analysis.grammar_issues and 
                    len(analysis.grammar_issues) > 0 and
                    analysis.analysis_details and
                    not any(phrase in analysis.analysis_details for phrase in [
                        "语法正确，无需关注", 
                        "无英文文本改动", 
                        "仅标点符号改动，无需关注",
                        "不存在语法问题"
                    ])
                )
                
                if has_obvious_errors:
                    problematic_files.append(analysis)
            
            # 如果所有文件都无问题，直接返回无问题结果
            if not problematic_files:
                return PRAnalysisResult(
                    has_text_changes=False,
                    text_change_type="无文本改动",
                    has_grammar_errors=False,
                    grammar_errors=[],
                    detailed_analysis="所有文件语法正确，无需关注",
                    suggestions=[]
                )
            
            text_changed_files = len(problematic_files)
            
            file_analyses_info = []
            for analysis in problematic_files:
                file_analyses_info.append({
                    'file_path': analysis.file_path,
                    'has_text_changes': analysis.has_text_changes,
                    'text_lines': analysis.text_lines,
                    'grammar_issues': analysis.grammar_issues,
                    'analysis_details': analysis.analysis_details
                })
            
            # 构造prompt字符串
            prompt_args = {
                "file_analyses": json.dumps(file_analyses_info, ensure_ascii=False, indent=2),
                "total_files": total_files,
                "text_changed_files": text_changed_files
            }
            
            # 使用线程池执行器为PR分析添加超时控制
            timeout_executor = None
            try:
                timeout_executor = ThreadPoolExecutor(max_workers=1)
                invoke_args = {
                    "file_analyses": json.dumps(file_analyses_info, ensure_ascii=False, indent=2),
                    "total_files": total_files,
                    "text_changed_files": text_changed_files
                }
                result = self.chain.invoke(invoke_args)
                # 验证结果有效性
                if isinstance(result, (dict, PRAnalysisResult)):
                    # 如果是dict（来自JsonOutputParser），转换为PRAnalysisResult
                    if isinstance(result, dict):
                        result = PRAnalysisResult(**result)
                    return result
                else:
                    logger.error(f"生成PR分析时返回类型错误: {type(result)}")
                    return None
            except Exception as e:
                logger.error(f"生成PR分析时发生错误: {e}")
                return None
        except Exception as e:
            logger.error(f"生成PR分析时发生错误: {e}")
            return None

# ==================== 主处理类 ====================

class PRCommentAnalyzer:
    """PR评论分析器"""
    
    def __init__(self, siliconflow_api_key: str = "", siliconflow_api_base: str = "https://api.siliconflow.cn/v1", model_name: str = None, base_url: str = None):
        if model_name is None:
            model_name = MODEL_NAME
        
        # 设置siliconflow API配置
        global SILICONFLOW_API_KEY, SILICONFLOW_API_BASE
        if siliconflow_api_key:
            SILICONFLOW_API_KEY = siliconflow_api_key
        if siliconflow_api_base:
            SILICONFLOW_API_BASE = siliconflow_api_base
            
        self.llm = LLMFactory.create_chat_llm(model_name)
        self.file_analysis_chain = FileTextAnalysisChain(self.llm)
        self.pr_analysis_chain = PRAnalysisChain(self.llm)
    
    def cleanup(self):
        """清理资源，确保程序能正确退出"""
        try:
            # 清理 LLM 连接
            if hasattr(self.llm, 'client') and hasattr(self.llm.client, 'close'):
                self.llm.client.close()
            elif hasattr(self.llm, '_client') and hasattr(self.llm._client, 'close'):
                self.llm._client.close()
            
            # 如果是 ChatOpenAI，尝试关闭底层的 HTTP 客户端
            if BACKEND_TYPE == "siliconflow" and hasattr(self.llm, 'client'):
                try:
                    # 强制关闭 httpx 客户端
                    if hasattr(self.llm.client, '_client'):
                        self.llm.client._client.close()
                except Exception as e:
                    logger.debug(f"关闭 HTTP 客户端时发生错误: {e}")
            
            logger.info("资源清理完成")
        except Exception as e:
            logger.warning(f"清理资源时发生错误: {e}")
    
    def analyze_pr_diff(self, diff_content: str, max_workers: int = None) -> CommentResult:
        if max_workers is None:
            max_workers = PROCESSING_MAX_WORKERS
            
        logger.info("开始解析PR diff...")
        files = DiffParser.parse_git_diff(diff_content)
        logger.info(f"解析到 {len(files)} 个文件的改动")
        if not files:
            logger.warning("未找到任何文件改动")
            return CommentResult(
                pr_analysis=None,
                file_analyses=[],
                processed_files=0,
                total_files=0,
                error='未找到任何文件改动'
            )
        
        logger.info("开始并行处理各个文件的文本分析...")
        file_analyses = []
        # 使用更健壮的并发处理机制
        executor = None
        try:
            executor = ThreadPoolExecutor(max_workers=max_workers)
            future_to_file = {
                executor.submit(self.file_analysis_chain.analyze, file_info): file_info.file_path
                for file_info in files
            }
            
            # 设置更长的整体超时时间，避免与单个文件超时冲突
            overall_timeout = SINGLE_FILE_TIMEOUT * len(files) + 600  # 给每个文件的时间 + 额外缓冲
            
            completed_count = 0
            total_count = len(future_to_file)
            
            try:
                for future in as_completed(future_to_file, timeout=overall_timeout):
                    file_path = future_to_file[future]
                    completed_count += 1
                    try:
                        analysis = future.result(timeout=5)  # 短暂缓冲时间，因为任务已经完成
                        if analysis:
                            file_analyses.append(analysis)
                            logger.info(f"完成文件 {file_path} 的文本分析 ({completed_count}/{total_count})")
                        else:
                            logger.warning(f"文件 {file_path} 的文本分析失败 ({completed_count}/{total_count})")
                    except (FutureTimeoutError, TimeoutError) as e:
                        logger.error(f"文件 {file_path} 的文本分析获取超时，跳过该文件: {type(e).__name__} ({completed_count}/{total_count})")
                        try:
                            future.cancel()
                        except Exception as cancel_e:
                            logger.warning(f"取消任务时发生错误: {cancel_e}")
                    except Exception as e:
                        logger.error(f"处理文件 {file_path} 时发生异常: {e} ({completed_count}/{total_count})")
            except (FutureTimeoutError, TimeoutError) as overall_e:
                logger.error(f"整体处理超时({overall_timeout}秒)，已完成{completed_count}/{total_count}个文件")
                # 取消所有未完成的任务
                for future in future_to_file:
                    if not future.done():
                        try:
                            future.cancel()
                        except Exception as cancel_e:
                            logger.warning(f"取消未完成任务时发生错误: {cancel_e}")
        finally:
            # 确保线程池被正确关闭
            if executor:
                try:
                    executor.shutdown(wait=True)
                except Exception as shutdown_e:
                    logger.warning(f"关闭主线程池时发生错误: {shutdown_e}")
        
        logger.info(f"成功生成 {len(file_analyses)} 个文件的文本分析")
        logger.info("开始生成PR整体分析...")
        pr_analysis = None
        if file_analyses:
            logger.info(f"基于 {len(file_analyses)} 个成功处理的文件生成PR分析...")
            try:
                pr_analysis = self.pr_analysis_chain.generate(file_analyses)
                if pr_analysis:
                    logger.info("PR整体分析生成成功")
                else:
                    logger.warning("PR整体分析生成失败")
            except Exception as e:
                logger.error(f"生成PR分析时发生未预期的错误: {e}")
        else:
            logger.warning("没有成功处理的文件，跳过PR分析生成")
        
        return CommentResult(
            pr_analysis=pr_analysis,
            file_analyses=file_analyses,
            processed_files=len(file_analyses),
            total_files=len(files)
        )

# ==================== 主函数 ====================

def get_comment_analysis(sample_diff, siliconflow_api_key="", siliconflow_api_base="https://api.siliconflow.cn/v1"):

    analyzer = PRCommentAnalyzer(siliconflow_api_key, siliconflow_api_base)
    result = None
    try:
        result = analyzer.analyze_pr_diff(sample_diff)
    finally:
        # 确保在函数退出前清理资源
        analyzer.cleanup()

    if not result:
        print("处理失败，无法获取结果")
        return None
    
    if result.error:
        print(f"错误: {result.error}")
    
    print("\n=== 单文件文本分析 ===")
    problematic_files = [f for f in result.file_analyses if f.has_text_changes and f.grammar_issues]
    if problematic_files:
        for analysis in problematic_files:
            print(f"文件: {analysis.file_path}")
            print(f"涉及文本变更: {analysis.has_text_changes}")
            print(f"文本变更行: {analysis.text_lines}")
            print(f"语法问题: {analysis.grammar_issues}")
            print(f"分析详情: {analysis.analysis_details}")
            print("-" * 50)
    else:
        print("所有文件语法正确，无需关注")
    
    print("=== 处理结果 ===")
    print(f"总文件数: {result.total_files}")
    print(f"成功处理文件数: {result.processed_files}")
    
    if result.pr_analysis:
        print("\n=== PR整体分析 ===")
        pr = result.pr_analysis
        print(f"涉及文本变更: {pr.has_text_changes}")
        print(f"文本变更类型: {pr.text_change_type}")
        print(f"存在语法错误: {pr.has_grammar_errors}")
        print(f"语法错误列表: {pr.grammar_errors}")
        print(f"详细分析: {pr.detailed_analysis}")
        print(f"改进建议: {pr.suggestions}")
            
    
    return result

if __name__ == "__main__":
    # 微服务接口逻辑： 传递进来的就是 sample_diff 的内容
    sample_diff = sys.argv[1]
    result = get_comment_analysis(sample_diff) 
    print(result)
