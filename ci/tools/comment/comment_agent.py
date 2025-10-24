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
    has_text_changes: bool = Field(description="是否有文本变更", default=True)
    text_change_type: str = Field(description="文本变更类型", default="")
    has_grammar_errors: bool = Field(description="是否存在语法错误", default=False)
    grammar_errors: List[str] = Field(description="语法错误列表", default=[])
    detailed_analysis: str = Field(description="详细分析说明")
    suggestions: List[str] = Field(description="改进建议列表", default=[])

class FileTextAnalysis(BaseModel):
    """单个文件的文本分析"""
    file_path: str = Field(description="文件路径", default="")
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


# ==================== 工具函数 ====================

class DiffParser:
    """Git Diff 解析器"""
    
    @staticmethod
    def filter_docs_en_files(diff_content: str) -> str:
        """
        过滤diff内容，只保留docs/en路径下的文件变更
        """
        if not diff_content:
            return ""
        
        lines = diff_content.split('\n')
        filtered_lines = []
        current_file_section = []
        in_docs_en_file = False
        current_file_path = ""
        
        for line in lines:
            if line.startswith('diff --git'):
                # 处理前一个文件
                if in_docs_en_file and current_file_section:
                    filtered_lines.extend(current_file_section)
                    logger.info(f"包含docs/en路径下的文件: {current_file_path}")
                
                # 检查新文件是否在docs/en路径下
                current_file_section = [line]
                in_docs_en_file = False
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
                        
                        # 检查是否在docs/en路径下
                        if current_file_path.startswith('docs/en/'):
                            in_docs_en_file = True
            else:
                # 继续当前文件的内容
                current_file_section.append(line)
        
        # 处理最后一个文件
        if in_docs_en_file and current_file_section:
            filtered_lines.extend(current_file_section)
            logger.info(f"包含docs/en路径下的文件: {current_file_path}")
        
        return '\n'.join(filtered_lines)
    
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

    @staticmethod
    def is_punctuation_only_change(diff_content: str) -> bool:
        """判断一个 diff 是否仅包含标点/空白改动（不包含英文字母数字层面的实质变化）

        核心逻辑：
        - 提取added_text和removed_text
        - 只保留英文字母数字和下划线进行对比
        - 如果这部分相同，说明英文内容没变，只是标点/空白/中文改了
        - 如果这部分不同，说明有英文内容变更，不是"仅标点改动"
        
        注意：此函数主要用于过滤纯标点/空白改动，避免对这类改动进行语法检查
        """
        try:
            added_parts = []
            removed_parts = []
            for raw_line in diff_content.strip().split('\n'):
                if raw_line.startswith('+++') or raw_line.startswith('---'):
                    continue
                if raw_line.startswith('+'):
                    added_parts.append(raw_line[1:])
                elif raw_line.startswith('-'):
                    removed_parts.append(raw_line[1:])

            added_text = '\n'.join(added_parts)
            removed_text = '\n'.join(removed_parts)
            
            # 如果没有改动，返回False
            if added_text == removed_text:
                return False

            # 只保留英文字母数字和下划线
            def keep_word_chars(s: str) -> str:
                return re.sub(r'[^A-Za-z0-9_]', '', s)

            added_word_chars = keep_word_chars(added_text)
            removed_word_chars = keep_word_chars(removed_text)
            
            # 核心判断：如果英文字母数字部分完全相同，才认为是"仅标点改动"
            # 
            # 会被识别为"仅标点改动"（返回True，跳过语法检查）：
            # 1. 纯标点改动（如逗号改句号）
            # 2. 空白改动（如空格、换行）
            # 3. 中文标点改动
            # 
            # 不会被识别为"仅标点改动"（返回False，进入语法检查）：
            # 1. 新增/删除英文字母
            # 2. 英文单词拼写改动
            # 3. 英文内容的任何实质性改动
            if added_word_chars == removed_word_chars and added_text != removed_text:
                # 额外检查：如果两者都没有英文字母数字（纯中文/标点改动）
                # 并且原始文本长度差异很大，可能不只是标点改动
                if not added_word_chars and not removed_word_chars:
                    # 如果都是纯中文/标点，检查长度差异
                    # 长度差异超过10个字符，可能是中文内容的实质性改动
                    if abs(len(added_text) - len(removed_text)) > 10:
                        return False
                return True

            return False
        except Exception as e:
            logger.debug(f"判定仅标点改动时发生错误: {e}")
            return False

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
                temperature=0  # 使用0温度确保最大确定性和一致性
            )
        else:
            raise ValueError(f"不支持的后端类型: {BACKEND_TYPE}")

class FileTextAnalysisChain:
    """单文件文本分析任务链"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # 创建输出解析器
        self.output_parser = JsonOutputParser(pydantic_object=FileTextAnalysis)
        
        # 输出格式说明
        format_instructions = """
请以JSON格式输出，包含以下字段：
{{
    "grammar_issues": "语法问题列表（字符串列表，如无问题则为空列表）",
    "analysis_details": "分析详情（字符串）"
}}
"""
        # 创建新的prompt模板
        system_template = """
你是英文语法检查专家，专门审查文档中英文文本的明显拼写和语法错误。

【核心原则：严格、一致、客观】
必须对所有文件使用完全相同的判断标准！对同类错误必须给出一致的结论！

【必须检查的错误类型】
严格按照以下标准判断，不得有任何主观性：

1. 明显的拼写错误：
   - 常见单词拼写错误（如：recieve → receive, teh → the, seperate → separate）
   - 随机字符串/无意义字符序列（如：awfawfwafaw, asvasvasv, xyzabc等）
   - 判断标准：如果一个英文字符串不是：
     * 技术文库中正确拼写的英文单词
     * 技术术语（如：JSON, API, HTTP）
     * 专有名词（如：GitHub, openEuler）
     * 缩写词（如：PR, CI, CD）
     * 文件名/路径/命令等
     则认定为拼写错误

2. 明显的时态错误：
   - He go yesterday → He went yesterday
   - She don't went → She didn't go
   - 必须是显而易见的时态不匹配

3. 严重的主谓不一致：
   - They is → They are
   - He are → He is
   - It is sings → It sings/It is singing
   - 必须是显而易见的主谓不匹配

4. 其他明显的语法错误：
   - 动词形式错误（如：He can goes → He can go）
   - 名词单复数错误（如：many book → many books）
   - 介词使用错误（如：depend in → depend on）
   - 冠词使用错误（如：a apple → an apple）
   - 语态使用错误（如：主动语态和被动语态混淆）

【完全忽略以下内容，直接输出"无需关注"】
- 任何中文文本（包括中文列表项、中文注释、中文文档）
- 所有格式问题：链接格式、大小写格式、标点符号、空格、缩进、换行
- 代码/命令/文件名/路径/配置/脚本/Shell命令（如：/etc/yum.conf, npm install）
- Markdown语法：标题、列表、表格、链接、图片
- 专有名词：GitHub、openEuler、Gitee、GVP、CVE、CWE等
- 口语化表达或技术文档中的简化表达
- 缺少冠词的表达（口语化和技术文档中常见且可接受）
- 句子结构简化（技术文档中常见且可接受）

【判定流程 - 严格执行】
对于每个新增的英文文本：
1. 是否在代码/配置/路径/命令中？→ 是 → "无需关注"
2. 是否是专有名词/技术术语/缩写？→ 是 → "无需关注"
3. 是否是标准英文单词？→ 否 → 检查是否为随机字符串
4. 如果是随机无意义字符串（无法识别字符串的含义）→ 报告为拼写错误
5. 如果是完整句子 → 检查时态、主谓一致性、动词形式、名词单复数、介词、冠词等
6. 其他情况 → "无需关注"

【一致性要求】
对于以下情况必须一致判断：
- awfawfwafaw, asvasvasv, xyzabc 等无意义的随机字符串 → 必须全部识别
- recieve, teh, seperate 等常见拼写错误 → 必须全部识别
- 同样的语法错误在不同文件中 → 必须得出相同结论

【输出要求】
- 必须使用中文输出所有分析内容
- analysis_details字段必须用中文解释问题
- grammar_issues列表中的每一项都必须用中文描述
- 对于随机字符串，明确指出"随机无意义字符串"或"拼写错误"
- 保持判断的一致性和可重复性
- 确保准确完整地识别所有问题类型，不遗漏任何明显的错误

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
        logger.info(f"开始分析文件: {diff_file_info.file_path}")
        max_retry = MODEL_MAX_RETRY
        
        for attempt in range(1, max_retry + 1):
            # 重试时采用指数退避策略
            if attempt > 1:
                delay = min(2 ** (attempt - 1), 10)  # 2, 4, 8, 10, 10...
                logger.info(f"第{attempt}次尝试，等待{delay}秒...")
                time.sleep(delay)
            
            try:
                # 调用LLM分析
                invoke_args = {
                    "file_path": diff_file_info.file_path,
                    "diff_content": diff_file_info.diff_content
                }
                result = self.chain.invoke(invoke_args)
                
                # 验证结果有效性
                if isinstance(result, dict):
                    result = FileTextAnalysis(**result)
                
                if isinstance(result, FileTextAnalysis) and result.analysis_details:
                    result.file_path = diff_file_info.file_path
                    # 确保grammar_issues为列表
                    if not result.grammar_issues:
                        result.grammar_issues = []
                    return result
                
                # 结果无效，重试
                logger.warning(f"分析返回无效结果，第{attempt}/{max_retry}次尝试")
                
            except Exception as e:
                err_str = str(e)
                # 判断是否为HTTP错误
                is_http_error = any(code in err_str for code in ["404", "500", "502", "503", "504"])
                
                if is_http_error:
                    logger.error(f"HTTP错误: {e}，第{attempt}/{max_retry}次尝试")
                    if attempt < max_retry:
                        time.sleep(10)  # HTTP错误等待更长时间
                else:
                    logger.error(f"分析错误: {e}，第{attempt}/{max_retry}次尝试")
        
        logger.error(f"分析文件 {diff_file_info.file_path} 失败，已重试{max_retry}次")
        return None

class PRAnalysisChain:
    """PR整体分析任务链"""
    
    def __init__(self, llm: ChatOllama | ChatOpenAI):
        self.llm = llm
        
        # 创建输出解析器
        self.output_parser = JsonOutputParser(pydantic_object=PRAnalysisResult)
        
        # 输出格式说明
        format_instructions = """
请以JSON格式输出，包含以下字段：
{{
    "has_text_changes": "是否有文本变更（布尔值）",
    "text_change_type": "文本变更类型（字符串）",
    "has_grammar_errors": "是否存在语法错误（布尔值）",
    "grammar_errors": "语法错误列表（字符串列表）",
    "detailed_analysis": "详细分析说明（字符串）",
    "suggestions": "改进建议列表（字符串列表）"
}}
"""
        # 创建prompt模板
        system_template = """
你是PR审查专家，汇总各文件的英文拼写和语法检查结果。

【核心任务】
汇总所有存在语法问题的文件，包括：
- 拼写错误（随机字符串、单词拼写错误）
- 时态错误
- 主谓不一致
- 其他明显的语法错误

【输出要求】
- has_text_changes: 如果有任何文本变更则为true，否则为false
- text_change_type: 描述变更类型（如"文本变更且有语法错误"、"文本变更但无语法错误"等）
- has_grammar_errors: 如果存在语法错误则为true，否则为false
- grammar_errors: 所有语法错误的列表（用中文描述）
- detailed_analysis: 简洁明了的分析说明（不超过200字，使用中文）
- suggestions: 改进建议列表（如有问题则提供建议，无问题则为空列表）

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
    
    def generate(self, file_analyses: List[FileTextAnalysis], 
                 total_comment_timeout: int = TOTAL_COMMENT_TIMEOUT) -> Optional[PRAnalysisResult]:
        """生成PR整体分析"""
        try:
            total_files = len(file_analyses)
            
            # 只保留有语法问题的文件
            problematic_files = [f for f in file_analyses if f.grammar_issues]
            
            # 如果所有文件都无问题，直接返回
            if not problematic_files:
                return PRAnalysisResult(
                    has_text_changes=True,
                    text_change_type="文本变更但无语法错误",
                    has_grammar_errors=False,
                    grammar_errors=[],
                    detailed_analysis="所有文件无问题",
                    suggestions=[]
                )
            
            # 构造分析信息
            file_analyses_info = [
                {
                    'file_path': f.file_path,
                    'grammar_issues': f.grammar_issues,
                    'analysis_details': f.analysis_details
                }
                for f in problematic_files
            ]
            
            # 使用线程池添加超时控制
            with ThreadPoolExecutor(max_workers=1) as executor:
                invoke_args = {
                    "file_analyses": json.dumps(file_analyses_info, ensure_ascii=False, indent=2),
                    "total_files": total_files,
                    "text_changed_files": len(problematic_files)
                }
                
                future = executor.submit(self.chain.invoke, invoke_args)
                try:
                    result = future.result(timeout=total_comment_timeout)
                except (FutureTimeoutError, TimeoutError):
                    logger.error(f"生成PR分析超时（{total_comment_timeout}秒）")
                    future.cancel()
                    return None
            
            # 处理结果
            if isinstance(result, dict):
                result = PRAnalysisResult(**result)
            return result if isinstance(result, PRAnalysisResult) else None
                
        except Exception as e:
            logger.error(f"生成PR分析时发生错误: {e}")
            return None

# ==================== 主处理类 ====================

class PRCommentAnalyzer:
    """PR评论分析器"""
    
    def __init__(self, siliconflow_api_key: str = "", 
                 siliconflow_api_base: str = "https://api.siliconflow.cn/v1", 
                 model_name: str = None, base_url: str = None):
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
            
        # 早期检查：查看diff中是否包含docs/en路径下的文件变更
        if 'docs/en/' not in diff_content:
            logger.info("diff内容中不包含docs/en路径下的文件变更，无需进行语法检查")
            return CommentResult(
                pr_analysis=PRAnalysisResult(
                    has_text_changes=False,
                    text_change_type="无docs/en路径下的文件变更",
                    has_grammar_errors=False,
                    grammar_errors=[],
                    detailed_analysis="本次改动不涉及docs/en路径下的文件，无需语法检查",
                    suggestions=[]
                ),
                file_analyses=[],
                processed_files=0,
                total_files=0
            )
        
        # 过滤只保留docs/en路径下的文件
        logger.info("过滤diff内容，只保留docs/en路径下的文件...")
        filtered_diff_content = DiffParser.filter_docs_en_files(diff_content)
        
        # 检查是否有需要处理的docs/en路径下的文件变更
        if not filtered_diff_content.strip():
            logger.info("没有需要处理的docs/en路径下的文件变更，无需进行语法检查")
            return CommentResult(
                pr_analysis=PRAnalysisResult(
                    has_text_changes=False,
                    text_change_type="无文本改动",
                    has_grammar_errors=False,
                    grammar_errors=[],
                    detailed_analysis="过滤后没有docs/en路径下的文件需要检查",
                    suggestions=[]
                ),
                file_analyses=[],
                processed_files=0,
                total_files=0
            )
        
        logger.info("开始解析过滤后的PR diff...")
        files = DiffParser.parse_git_diff(filtered_diff_content)
        logger.info(f"解析到 {len(files)} 个docs/en路径下的文件改动")
        # 预过滤：仅标点/空白改动的文件不视为英文改动，跳过后续LLM分析
        filtered_files = []
        skipped_punct_files = 0
        for f in files:
            if DiffParser.is_punctuation_only_change(f.diff_content):
                skipped_punct_files += 1
                logger.info(f"跳过仅标点/空白改动的文件: {f.file_path}")
                continue
            filtered_files.append(f)
        if skipped_punct_files:
            logger.info(f"共有 {skipped_punct_files} 个文件因仅标点/空白改动被忽略")
        
        # 检查是否有文件需要分析
        if not files:
            logger.warning("未找到任何文件改动")
            return CommentResult(
                pr_analysis=None,
                file_analyses=[],
                processed_files=0,
                total_files=0,
                error='未找到任何文件改动'
            )
        
        # 如果所有文件都被过滤掉了（都是标点/空白改动）
        if not filtered_files:
            logger.info("所有文件都是标点/空白改动，无需进行语法检查")
            return CommentResult(
                pr_analysis=PRAnalysisResult(
                    has_text_changes=False,
                    text_change_type="无文本改动",
                    has_grammar_errors=False,
                    grammar_errors=[],
                    detailed_analysis="所有改动都是标点或空白改动，无需语法检查",
                    suggestions=[]
                ),
                file_analyses=[],
                processed_files=0,
                total_files=len(files)
            )
        
        logger.info(f"开始并行处理文件分析 (共{len(filtered_files)}个，并发数{max_workers})")
        file_analyses = []
        
        # 计算整体超时时间
        batches = (len(filtered_files) + max_workers - 1) // max_workers
        overall_timeout = SINGLE_FILE_TIMEOUT * batches + 60
        logger.info(f"整体超时: {overall_timeout}秒")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self.file_analysis_chain.analyze, file_info): file_info.file_path
                for file_info in filtered_files
            }
            
            completed_count = 0
            total_count = len(future_to_file)
            
            try:
                for future in as_completed(future_to_file, timeout=overall_timeout):
                    file_path = future_to_file[future]
                    completed_count += 1
                    
                    try:
                        analysis = future.result(timeout=SINGLE_FILE_TIMEOUT)
                        if analysis:
                            file_analyses.append(analysis)
                            logger.info(f"完成 {file_path} ({completed_count}/{total_count})")
                        else:
                            logger.warning(f"失败 {file_path} ({completed_count}/{total_count})")
                    except (FutureTimeoutError, TimeoutError):
                        logger.error(f"超时 {file_path} ({completed_count}/{total_count})")
                        future.cancel()
                    except Exception as e:
                        logger.error(f"异常 {file_path}: {e} ({completed_count}/{total_count})")
                        
            except (FutureTimeoutError, TimeoutError):
                logger.error(f"整体超时({overall_timeout}秒)，已完成{completed_count}/{total_count}")
                # 取消未完成的任务
                for future in future_to_file:
                    if not future.done():
                        future.cancel()
        
        logger.info(f"成功生成 {len(file_analyses)} 个文件的文本分析")
        logger.info("开始生成PR整体分析...")
        pr_analysis = None
        if file_analyses:
            logger.info(f"基于 {len(file_analyses)} 个成功处理的文件生成PR分析...")
            try:
                pr_analysis = self.pr_analysis_chain.generate(file_analyses, TOTAL_COMMENT_TIMEOUT)
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
    # 只输出有语法问题的文件
    problematic_files = [f for f in result.file_analyses 
                        if f.grammar_issues and len(f.grammar_issues) > 0]
    if problematic_files:
        for analysis in problematic_files:
            print(f"文件: {analysis.file_path}")
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
