import json
import re
import logging
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple, Literal
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from pathlib import Path
import tiktoken
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

def load_config(config_file="new_create_translation_issue.yaml"):
    """从YAML文件加载配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('translation_agent', {})
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
OLLAMA_BASE_URL = _config.get('backend', {}).get('ollama', {}).get('base_url', 'http://localhost:11434')
MODEL_NAME = _config.get('model', {}).get('name', 'Qwen/Qwen3-8B')
MODEL_TEMPERATURE = _config.get('model', {}).get('temperature', 0.1)
MODEL_MAX_RETRY = _config.get('model', {}).get('max_retry', 5)
MODEL_MAX_RETRY_OLLAMA = _config.get('model', {}).get('max_retry_ollama', 1)
PROCESSING_MAX_WORKERS = _config.get('processing', {}).get('max_workers', 8)
SINGLE_FILE_TIMEOUT = _config.get('processing', {}).get('single_file_timeout', 180)
TOTAL_SUMMARY_TIMEOUT = _config.get('processing', {}).get('total_summary_timeout', 300)
LOGGING_LEVEL = _config.get('logging', {}).get('level', 'INFO')
SILICONFLOW_API_KEY = ''
SILICONFLOW_API_BASE =''

# 配置日志
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL.upper()))
logger = logging.getLogger(__name__)

# ==================== 数据模型定义 ====================

class SingleFileSummary(BaseModel):
    """单个文件摘要的结构化输出"""
    file_path: str = Field(description="文件路径", default="")
    change_type: Literal["仅涉及标点符号的修改", "涉及到中英文文本内容的修改", "涉及到代码内容的修改", "涉及到其他内容的修改"] = Field(description="改动类型")
    potential_impact: str = Field(description="改动对其他文件潜在的影响")
    summary: str = Field(description="改动的详细摘要")
    lines_added: int = Field(description="新增行数", default=0)
    lines_deleted: int = Field(description="删除行数", default=0)

class FileChangeInfo(BaseModel):
    """文件改动信息"""
    file_path: str = Field(description="文件路径")
    change_type: Literal["仅涉及标点符号的修改", "涉及到中英文文本内容的修改", "涉及到代码内容的修改", "涉及到其他内容的修改"] = Field(description="改动类型")
    lines_changed: int = Field(description="改动行数")

class TotalSummary(BaseModel):
    """总摘要的结构化输出"""
    total_files_changed: int = Field(description="总共修改的文件数量", default=0)
    total_lines_changed: int = Field(description="总共修改的行数", default=0)
    overall_potential_impact: str = Field(description="整体改动对其他文件潜在的影响")
    overall_summary: str = Field(description="整体改动的详细摘要")
    change_type_list: List[str] = Field(description="所有文件包含的改动种类列表", default=[])
    file_changes: List[FileChangeInfo] = Field(description="每个修改文件的详细信息列表", default=[])

@dataclass
class DiffFileInfo:
    """单个文件的diff信息"""
    file_path: str
    diff_content: str
    lines_added: int
    lines_deleted: int

@dataclass
class ProcessingResult:
    """处理结果"""
    file_summaries: List[SingleFileSummary]
    total_summary: Optional[TotalSummary]
    processed_files: int
    total_files: int
    error: Optional[str] = None

# ==================== Token 统计工具 ====================

class TokenCounter:
    def __init__(self, model_name=MODEL_NAME):
        self.model_name = model_name
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.tokenizer = None
        self._init_tokenizer()

    def _init_tokenizer(self):
        """初始化tokenizer"""
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)
        except Exception:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except Exception:
                logger.warning("无法初始化tokenizer，将不会计算token数量")

    def _encode(self, text: str) -> List[int]:
        """编码文本"""
        if not isinstance(text, str):
            return []
        if self.tokenizer is None:
            # 如果没有tokenizer，使用简单的估算方法
            return [0] * (len(text) // 4)
        try:
            return self.tokenizer.encode(text)
        except Exception as e:
            logger.warning(f"编码文本时发生错误: {e}")
            # 如果编码失败，使用简单的估算方法
            return [0] * (len(text) // 4)

    def _count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self._encode(text))

    def count_prompt(self, prompt: str) -> int:
        """计算prompt的token数量"""
        tokens = self._count_tokens(prompt)
        self.prompt_tokens += tokens
        self.total_tokens += tokens
        return tokens

    def count_completion(self, completion: str) -> int:
        """计算completion的token数量"""
        tokens = self._count_tokens(completion)
        self.completion_tokens += tokens
        self.total_tokens += tokens
        return tokens

    def get_stats(self):
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }

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
                            result += decoded_bytes
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
        if base_url is None:
            base_url = OLLAMA_BASE_URL
            
        if BACKEND_TYPE == "ollama":
            return ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=MODEL_TEMPERATURE
            )
        elif BACKEND_TYPE == "siliconflow":
            return ChatOpenAI(
                model=model_name,
                api_key=SecretStr(SILICONFLOW_API_KEY),
                base_url=SILICONFLOW_API_BASE,
                temperature=MODEL_TEMPERATURE
            )
        else:
            raise ValueError(f"不支持的后端类型: {BACKEND_TYPE}")
    
    @staticmethod
    def create_llm(model_name: str = None, base_url: str = None):
        """创建LLM实例"""
        if model_name is None:
            model_name = MODEL_NAME
        if base_url is None:
            base_url = OLLAMA_BASE_URL
            
        if BACKEND_TYPE == "ollama":
            return Ollama(
                model=model_name,
                base_url=base_url,
                temperature=MODEL_TEMPERATURE
            )
        elif BACKEND_TYPE == "siliconflow":
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
    def get_single_file_prompt() -> ChatPromptTemplate:
        """获取单文件分析提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", f"""
你是一个专业的Git维护专家，擅长总结社区文档的改动，请分析以下git diff中单个文件的改动，并生成结构化的摘要。

请仔细分析这个文件的改动，并按照以下要求生成摘要：

**务必注意：当你对单个文件的所有变更内容从头到尾进行过完整的分析之后，再生成你最终的结论！不要仅根据其中几行的增删改就给出你的结论！**

1. 改动类型判断（必须选择以下四种之一，请严格按照示例进行判断）：

   - "涉及到其他内容的修改"：新增二进制文件、新增依赖库等其他内容
   - "仅涉及标点符号的修改"：仅修改了标点符号的增减、删除、变动，几乎不影响理解
   - "涉及到代码内容的修改"：修改了代码逻辑、函数定义、配置结构、命令行内容、脚本实现等
   - "涉及到中英文文本内容的修改"：修改了文档内容、命令或代码注释、字符串等文本，需要对内容进行翻译或调整以使得所有语种的人都可以理解
   
**其中，你需要重点对后三种类型的修改进行区分。越靠后，修改类型判定的优先级越高。**
如果修改的内容仅仅为新增了二进制文件、新增了依赖库等其他内容，绝大部分情况都可以归类为"涉及到其他内容的修改"。
如果修改的内容不涉及中文或英文字符且不涉及代码改动，绝大部分情况都可以归类为"仅涉及标点符号的修改"，但一旦存在除了标点符号或文档格式以外的改动，则优先归为其他类别。
如果修改的内容涉及代码逻辑、函数定义、配置结构、脚本实现等可能产生现实影响的变更，或者对环境部署命令行、内容配置进行了更改或调整，但不需要对内容进行翻译或调整以使得所有语种的人都可以理解，则归类为"涉及到代码内容的修改"。
如果修改的内容涉及中文或英文字符，且需要对内容进行翻译或调整以使得所有语种的人都可以理解，可以归类为"涉及到中英文文本内容的修改"。
一个区分"涉及到代码内容的修改"和"涉及到中英文文本内容的修改"的标准是：如果当前的改动属于某一语言，如果使用者不理解该语言，则必须要对改动进行翻译才能理解，则归类为"涉及到中英文文本内容的修改"，否则归类为"涉及到代码内容的修改"。

下面我将提供几个判断示例供你参考：

示例1 - 仅涉及标点符号的修改：
```diff
- 这是一个测试文档,用于演示功能。
+ 这是一个测试文档，用于演示功能！
```
分析：只变更了逗号为中文逗号，句号为感叹号，属于"仅涉及标点符号的修改"
或者文件中：
```diff
- 这个文档的功能有进一步补充的空间。
+ 这个文档的功能有进一步补充的空间！
```
分析：只涉及中文句号和感叹号的增删改，不涉及中文字符和英文字符的改动，且不涉及代码改动，属于"仅涉及标点符号的修改"

示例2 - 涉及到代码内容的修改：
```diff
- function getUserInfo() 
+ function getUserProfile() 
```
或者在文档的代码块中：
```diff
- ```python
- def hello():
-     print("hello")
- ```
+ ```python
+ def greeting():
+     print("hello world")
+ ```
```
或者在文档的命令行代码块中
```diff
- pwd
- cat /etc/profile
+ sudo apt update
+ whoami
+ echo "hello"
```
分析：修改了函数名、逻辑或文档文本中的代码块等，但是不涉及需要翻译的内容，属于"涉及到代码内容的修改"

示例3 - 涉及到中英文文本内容的修改：
```diff
- // 这是一个注释说明
+ // 这是一个更详细的注释说明
```
或者JSON中：
```diff
- "description": "用户管理模块"
+ "description": "用户账户管理模块"
```
分析：修改了注释或文档文本内容，影响用户的阅读理解，需要对内容进行翻译或调整以使得所有语种的人都可以理解，属于"涉及到中英文文本内容的修改"

示例4 - 涉及到其他内容的修改：
```diff
+ Binary file image.png added
```
或者：
```diff
+ "dependencies": 
+   "new-package": "^1.0.0"
+ 
```
分析：新增了二进制文件或依赖包等，属于"涉及到其他内容的修改"

2. 潜在影响分析：
   - 分析这个文件的改动可能对其他文件或整体系统造成的影响
   - 考虑依赖关系、接口变化、数据流等
   - 如果是配置文件的修改，考虑对系统配置的影响
   - 如果对其他文件无潜在影响，请说明无潜在影响及原因

3. 详细摘要：
   - 提炼出摘要改动文件所属的板块，并解释板块作用
   - 结合文件名和改动细节，用详细的语言描述具体的改动内容，要求准确全面，且改动内容要做到具体
   - 突出重要的改动点和影响范围，包括修改内容主要针对的对象、文档的分类等
   - 结合文件名、改动类型、潜在影响分析，对摘要做进一步补充

4. 输出格式：
  - 请用中文生成摘要
  - 要求改动类型、潜在影响、改动内容总结都包含在摘要中，不能存在空字段
  - 严格检查你的输出，对"新增"、"删除"、"修改"等字眼要严格检查，确保没有出现语义错误
  - 严格检查你的输出，确保没有出现语义错误，对于出现的数字、改动的具体内容务必保证描述完全吻合

            """),
            ("human", """
文件路径: {file_path}

Git Diff 内容:
{diff_content}

            """)
        ])
    
    @staticmethod
    def get_total_summary_prompt() -> ChatPromptTemplate:
        """获取总摘要生成提示模板"""
        return ChatPromptTemplate.from_messages([
            ("system", """
你是一个专业的Git维护专家，擅长总结社区文档的改动，请基于以下各个文件的改动摘要，生成整个git diff的总摘要。

请分析所有文件的改动，并生成一个总摘要，要求：

1. 整体改动类型统计：
   - 统计所有文件涉及到的改动类型，取并集
   - 四种改动类型说明：
     * "仅涉及标点符号的修改"：只修改了标点符号的增减、删除、变动
     * "涉及到中英文文本内容的修改"：修改了文档内容、注释等文本，但未涉及代码逻辑
     * "涉及到代码内容的修改"：修改了代码逻辑、函数定义、配置结构、命令行内容、脚本实现等
     * "涉及到其他内容的修改"：新增二进制文件、新增依赖库等其他内容
   - 将所有出现的改动类型都列出，不做优先级选择

统计示例：

示例1 - 单一类型：
文件A：仅涉及标点符号的修改
文件B：仅涉及标点符号的修改
→ 整体改动类型：["仅涉及标点符号的修改"]

示例2 - 多种类型：
文件A：仅涉及标点符号的修改
文件B：涉及到中英文文本内容的修改
→ 整体改动类型：["仅涉及标点符号的修改", "涉及到中英文文本内容的修改"]

示例3 - 复杂混合：
文件A：涉及到中英文文本内容的修改
文件B：涉及到代码内容的修改
文件C：涉及到其他内容的修改
→ 整体改动类型：["涉及到中英文文本内容的修改", "涉及到代码内容的修改", "涉及到其他内容的修改"]

2. 整体潜在影响分析：
   - 逐个总结所有文件的改动内容，并进行详细的列举，尽量涵盖所有修改内容
   - 综合分析所有文件改动对系统的整体影响
   - 考虑文件间的依赖关系和系统架构影响
   - 评估改动的风险等级和影响范围
   - 如果对其他文件无潜在影响，请说明无潜在影响及原因

3. 整体摘要详细列举：
   - 提炼出所有摘要改动文件所属的板块，并解释板块作用
   - 用详细的语言分条概括每个摘要文件的核心内容，需要具体到文件，这一部分要占到最大的篇幅，不要遗漏任何摘要文件的内容
   - 突出重要的改动点，包括修改内容主要针对的对象、文档的分类等
   - 注意：整体摘要需要总结所有文件的内容；整体摘要需要尽可能详细

4. 输出格式：
   - 请用中文生成摘要，整体摘要内容字段务必全面详细
   - 要求整体潜在影响、整体摘要都包含在摘要中，不能存在空字段
   - 整体摘要必须满足以下格式："本次更改涉及到XXX等文件，这些文件分别属于社区中的XXX模块。涉及到XXX的修改，可能会对XXX造成影响。总的来说，这次更改主要是XXX。"
   - 严格检查你的输出，对"新增"、"删除"、"修改"等字眼要严格检查，确保没有出现语义错误
   - 严格检查你的输出，确保没有出现语义错误，对于出现的数字、改动的具体内容务必保证描述完全吻合


            """),
            ("human", """
各个文件的改动摘要:
{file_changes}

总文件数: {total_files}
            """)
        ])

class SingleFileAnalysisChain:
    """单文件分析任务链"""
    
    def __init__(self, llm: ChatOllama | ChatOpenAI, token_counter: TokenCounter):
        self.llm = llm
        self.token_counter = token_counter
        
        # 创建输出解析器
        self.output_parser = JsonOutputParser(pydantic_object=SingleFileSummary)
        
        # 根据后端类型选择不同的链构建方式
        if BACKEND_TYPE == "ollama":
            self.prompt = PromptTemplates.get_single_file_prompt()
            self.chain = self.prompt | self.llm.with_structured_output(SingleFileSummary)
        else:
            # 为硅基流动平台添加输出格式说明
            format_instructions = """
请以JSON格式输出，包含以下字段：
{{
    "change_type": "改动类型（必须是以下之一：仅涉及标点符号的修改、涉及到中英文文本内容的修改、涉及到代码内容的修改、涉及到其他内容的修改）",
    "potential_impact": "改动对其他文件潜在的影响",
    "summary": "改动的详细摘要"
}}
"""
            # 创建新的prompt模板
            system_template = """
你是一个专业的Git维护专家，擅长总结社区文档的改动，请分析以下git diff中单个文件的改动，并生成结构化的摘要。

请仔细分析这个文件的改动，并按照以下要求生成摘要：

**务必注意：当你对单个文件的所有变更内容从头到尾进行过完整的分析之后，再生成你最终的结论！不要仅根据其中几行的增删改就给出你的结论！**

1. 改动类型判断（必须选择以下四种之一，请严格按照示例进行判断）：

   - "涉及到其他内容的修改"：新增二进制文件、新增依赖库等其他内容
   - "仅涉及标点符号的修改"：仅修改了标点符号的增减、删除、变动，几乎不影响理解
   - "涉及到代码内容的修改"：修改了代码逻辑、函数定义、配置结构、命令行内容、脚本实现等
   - "涉及到中英文文本内容的修改"：修改了文档内容、命令或代码注释、字符串等文本，需要对内容进行翻译或调整以使得所有语种的人都可以理解
   
**其中，你需要重点对后三种类型的修改进行区分。越靠后，修改类型判定的优先级越高。**
如果修改的内容仅仅为新增了二进制文件、新增了依赖库等其他内容，绝大部分情况都可以归类为"涉及到其他内容的修改"。
如果修改的内容不涉及中文或英文字符且不涉及代码改动，绝大部分情况都可以归类为"仅涉及标点符号的修改"，但一旦存在除了标点符号或文档格式以外的改动，则优先归为其他类别。
如果修改的内容涉及代码逻辑、函数定义、配置结构、脚本实现等可能产生现实影响的变更，或者对环境部署命令行、内容配置进行了更改或调整，但不需要对内容进行翻译或调整以使得所有语种的人都可以理解，则归类为"涉及到代码内容的修改"。
如果修改的内容涉及中文或英文字符，且需要对内容进行翻译或调整以使得所有语种的人都可以理解，可以归类为"涉及到中英文文本内容的修改"。
一个区分"涉及到代码内容的修改"和"涉及到中英文文本内容的修改"的标准是：如果当前的改动属于某一语言，如果使用者不理解该语言，则必须要对改动进行翻译才能理解，则归类为"涉及到中英文文本内容的修改"，否则归类为"涉及到代码内容的修改"。

下面我将提供几个判断示例供你参考：

示例1 - 仅涉及标点符号的修改：
```diff
- 这是一个测试文档,用于演示功能。
+ 这是一个测试文档，用于演示功能！
```
分析：只变更了逗号为中文逗号，句号为感叹号，属于"仅涉及标点符号的修改"
或者文件中：
```diff
- 这个文档的功能有进一步补充的空间。
+ 这个文档的功能有进一步补充的空间！
```
分析：只涉及中文句号和感叹号的增删改，不涉及中文字符和英文字符的改动，且不涉及代码改动，属于"仅涉及标点符号的修改"

示例2 - 涉及到代码内容的修改：
```diff
- function getUserInfo() 
+ function getUserProfile() 
```
或者在文档的代码块中：
```diff
- ```python
- def hello():
-     print("hello")
- ```
+ ```python
+ def greeting():
+     print("hello world")
+ ```
```
或者在文档的命令行代码块中
```diff
- pwd
- cat /etc/profile
+ sudo apt update
+ whoami
+ echo "hello"
```
分析：修改了函数名、逻辑或文档文本中的代码块等，但是不涉及需要翻译的内容，属于"涉及到代码内容的修改"

示例3 - 涉及到中英文文本内容的修改：
```diff
- // 这是一个注释说明
+ // 这是一个更详细的注释说明
```
或者JSON中：
```diff
- "description": "用户管理模块"
+ "description": "用户账户管理模块"
```
分析：修改了注释或文档文本内容，影响用户的阅读理解，需要对内容进行翻译或调整以使得所有语种的人都可以理解，属于"涉及到中英文文本内容的修改"

示例4 - 涉及到其他内容的修改：
```diff
+ Binary file image.png added
```
或者：
```diff
+ "dependencies": 
+   "new-package": "^1.0.0"
+ 
```
分析：新增了二进制文件或依赖包等，属于"涉及到其他内容的修改"

2. 潜在影响分析：
   - 分析这个文件的改动可能对其他文件或整体系统造成的影响
   - 考虑依赖关系、接口变化、数据流等
   - 如果是配置文件的修改，考虑对系统配置的影响
   - 如果对其他文件无潜在影响，请说明无潜在影响及原因

3. 详细摘要：
   - 提炼出摘要改动文件所属的板块，并解释板块作用
   - 结合文件名和改动细节，用详细的语言描述具体的改动内容，要求准确全面，且改动内容要做到具体
   - 突出重要的改动点和影响范围，包括修改内容主要针对的对象、文档的分类等
   - 结合文件名、改动类型、潜在影响分析，对摘要做进一步补充

4. 输出格式：
  - 请用中文生成摘要
  - 要求改动类型、潜在影响、改动内容总结都包含在摘要中，不能存在空字段
  - 严格检查你的输出，对"新增"、"删除"、"修改"等字眼要严格检查，确保没有出现语义错误
  - 严格检查你的输出，确保没有出现语义错误，对于出现的数字、改动的具体内容务必保证描述完全吻合

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
    
    def analyze(self, diff_file_info: DiffFileInfo) -> Optional[SingleFileSummary]:
        """分析单个文件的改动"""
        max_retry = MODEL_MAX_RETRY_OLLAMA if BACKEND_TYPE == "ollama" else MODEL_MAX_RETRY
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
                try:
                    messages = self.prompt.format_messages(**prompt_args)
                    if messages and len(messages) > 0:
                        message = messages[0]
                        if hasattr(message, 'content') and message.content:
                            prompt_str = str(message.content)
                            if prompt_str:
                                self.token_counter.count_prompt(prompt_str)
                except Exception as e:
                    logger.warning(f"格式化prompt时发生错误: {e}")
                
                # 直接调用，简化超时控制
                invoke_args = {
                    "file_path": diff_file_info.file_path,
                    "diff_content": diff_file_info.diff_content,
                    "lines_added": diff_file_info.lines_added,
                    "lines_deleted": diff_file_info.lines_deleted
                }
                if BACKEND_TYPE != "ollama":
                    invoke_args["response_format"] = {"type": "json_object"}
                
                result = self.chain.invoke(invoke_args)
                # 验证结果有效性
                if isinstance(result, (dict, SingleFileSummary)):
                    if isinstance(result, dict):
                        result = SingleFileSummary(**result)
                    
                    # 检查结果完整性
                    if result and hasattr(result, 'summary') and result.summary and result.change_type:
                        # 统计completion token
                        try:
                            completion_str = str(result.summary)
                            if completion_str:
                                self.token_counter.count_completion(completion_str)
                        except Exception as e:
                            logger.warning(f"计算completion tokens时发生错误: {e}")
                        
                        # 设置准确值
                        result.file_path = diff_file_info.file_path
                        result.lines_added = diff_file_info.lines_added
                        result.lines_deleted = diff_file_info.lines_deleted
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

class TotalSummaryChain:
    """总摘要生成任务链"""
    
    def __init__(self, llm: ChatOllama | ChatOpenAI, token_counter: TokenCounter):
        self.llm = llm
        self.token_counter = token_counter
        
        # 创建输出解析器
        self.output_parser = JsonOutputParser(pydantic_object=TotalSummary)
        
        # 根据后端类型选择不同的链构建方式
        if BACKEND_TYPE == "ollama":
            self.prompt = PromptTemplates.get_total_summary_prompt()
            self.chain = self.prompt | self.llm.with_structured_output(TotalSummary)
        else:
            # 为硅基流动平台添加输出格式说明
            format_instructions = """
请以JSON格式输出，包含以下字段：
{{
    "overall_potential_impact": "整体改动对其他文件潜在的影响",
    "overall_summary": "整体改动的详细摘要"
}}
"""
            # 创建新的prompt模板
            system_template = """
你是一个专业的Git维护专家，擅长总结社区文档的改动，请基于以下各个文件的改动摘要，生成整个git diff的总摘要。

请分析所有文件的改动，并生成一个总摘要，要求：

1. 整体改动类型统计：
   - 统计所有文件涉及到的改动类型，取并集
   - 四种改动类型说明：
     * "仅涉及标点符号的修改"：只修改了标点符号的增减、删除、变动
     * "涉及到中英文文本内容的修改"：修改了文档内容、注释等文本，但未涉及代码逻辑
     * "涉及到代码内容的修改"：修改了代码逻辑、函数定义、配置结构、命令行内容、脚本实现等
     * "涉及到其他内容的修改"：新增二进制文件、新增依赖库等其他内容
   - 将所有出现的改动类型都列出，不做优先级选择

统计示例：

示例1 - 单一类型：
文件A：仅涉及标点符号的修改
文件B：仅涉及标点符号的修改
→ 整体改动类型：["仅涉及标点符号的修改"]

示例2 - 多种类型：
文件A：仅涉及标点符号的修改
文件B：涉及到中英文文本内容的修改
→ 整体改动类型：["仅涉及标点符号的修改", "涉及到中英文文本内容的修改"]

示例3 - 复杂混合：
文件A：涉及到中英文文本内容的修改
文件B：涉及到代码内容的修改
文件C：涉及到其他内容的修改
→ 整体改动类型：["涉及到中英文文本内容的修改", "涉及到代码内容的修改", "涉及到其他内容的修改"]

2. 整体潜在影响分析：
   - 逐个总结所有文件的改动内容，并进行详细的列举，尽量涵盖所有修改内容
   - 综合分析所有文件改动对系统的整体影响
   - 考虑文件间的依赖关系和系统架构影响
   - 评估改动的风险等级和影响范围
   - 如果对其他文件无潜在影响，请说明无潜在影响及原因

3. 整体摘要详细列举：
   - 提炼出所有摘要改动文件所属的板块，并解释板块作用
   - 用详细的语言分条概括每个摘要文件的核心内容，需要具体到文件，这一部分要占到最大的篇幅，不要遗漏任何摘要文件的内容
   - 突出重要的改动点，包括修改内容主要针对的对象、文档的分类等
   - 注意：整体摘要需要总结所有文件的内容；整体摘要需要尽可能详细

4. 输出格式：
   - 请用中文生成摘要，整体摘要内容字段务必全面详细
   - 要求整体潜在影响、整体摘要都包含在摘要中，不能存在空字段
   - 整体摘要必须满足以下格式："本次更改涉及到XXX等文件，这些文件分别属于社区中的XXX模块。涉及到XXX的修改，可能会对XXX造成影响。总的来说，这次更改主要是XXX。"
   - 严格检查你的输出，对"新增"、"删除"、"修改"等字眼要严格检查，确保没有出现语义错误
   - 严格检查你的输出，确保没有出现语义错误，对于出现的数字、改动的具体内容务必保证描述完全吻合

{format_instructions}
"""
            human_template = """
各个文件的改动摘要:
{file_changes}

总文件数: {total_files}
"""
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", system_template.format(format_instructions=format_instructions)),
                ("human", human_template)
            ])
            self.chain = self.prompt | self.llm | self.output_parser
    
    def generate(self, file_summaries: List[SingleFileSummary]) -> Optional[TotalSummary]:
        """生成总摘要"""
        try:
            total_files = len(file_summaries)
            total_lines = sum(s.lines_added + s.lines_deleted for s in file_summaries)
            file_changes_info = []
            # 收集所有改动类型
            all_change_types = list(set(s.change_type for s in file_summaries))
            
            for summary in file_summaries:
                file_changes_info.append({
                    'file_path': summary.file_path,
                    'change_type': summary.change_type,
                    'potential_impact': summary.potential_impact,
                    'summary': summary.summary
                })
            
            # 构造prompt字符串
            prompt_args = {
                "file_changes": json.dumps(file_changes_info, ensure_ascii=False, indent=2),
                "total_files": total_files
            }
            try:
                messages = self.prompt.format_messages(**prompt_args)
                if messages and len(messages) > 0:
                    message = messages[0]
                    if hasattr(message, 'content') and message.content:
                        prompt_str = str(message.content)
                        if prompt_str:
                            self.token_counter.count_prompt(prompt_str)
            except Exception as e:
                logger.warning(f"格式化prompt时发生错误: {e}")
            
            # 使用线程池执行器为总摘要生成添加超时控制
            timeout_executor = None
            try:
                timeout_executor = ThreadPoolExecutor(max_workers=1)
                invoke_args = {
                    "file_changes": json.dumps(file_changes_info, ensure_ascii=False, indent=2),
                    "total_files": total_files,
                    "total_lines": total_lines
                }
                if BACKEND_TYPE != "ollama":
                    # 为 SiliconFlow 添加 response_format 参数
                    invoke_args["response_format"] = {"type": "json_object"}
                
                # 提交任务并设置超时
                future = timeout_executor.submit(self.chain.invoke, invoke_args)
                try:
                    result = future.result(timeout=TOTAL_SUMMARY_TIMEOUT)
                except (FutureTimeoutError, TimeoutError) as e:
                    logger.error(f"生成总摘要超时（{TOTAL_SUMMARY_TIMEOUT}秒），放弃生成总摘要: {type(e).__name__}")
                    try:
                        future.cancel()  # 尝试取消超时的任务
                    except Exception as cancel_e:
                        logger.warning(f"取消任务时发生错误: {cancel_e}")
                    return None
            finally:
                # 确保线程池被正确关闭
                if timeout_executor:
                    try:
                        timeout_executor.shutdown(wait=False)
                    except Exception as shutdown_e:
                        logger.warning(f"关闭总摘要线程池时发生错误: {shutdown_e}")
            
            # 处理结果
            if isinstance(result, (dict, TotalSummary)):
                # 如果是dict（来自JsonOutputParser），转换为TotalSummary
                if isinstance(result, dict):
                    result = TotalSummary(**result)
                try:
                    if result and hasattr(result, 'overall_summary'):
                        summary = result.overall_summary
                        if summary:
                            completion_str = str(summary)
                            if completion_str:
                                self.token_counter.count_completion(completion_str)
                except Exception as e:
                    logger.warning(f"计算completion tokens时发生错误: {e}")
                return TotalSummary(
                    total_files_changed=total_files,
                    total_lines_changed=total_lines,
                    overall_potential_impact=result.overall_potential_impact,
                    overall_summary=result.overall_summary,
                    change_type_list=all_change_types,
                    file_changes=[
                        FileChangeInfo(
                            file_path=summary.file_path,
                            change_type=summary.change_type,
                            lines_changed=summary.lines_added + summary.lines_deleted
                        )
                        for summary in file_summaries
                    ]
                )
            else:
                logger.error(f"生成总摘要时返回类型错误: {type(result)}")
                return None
        except Exception as e:
            logger.error(f"生成总摘要时发生错误: {e}")
            return None

# ==================== 主处理类 ====================

class GitDiffSummarizer:
    """Git Diff 摘要生成器"""
    
    def __init__(self, siliconflow_api_key: str = "", siliconflow_api_base: str = "https://api.siliconflow.cn/v1", model_name: str = None, base_url: str = None):
        if model_name is None:
            model_name = MODEL_NAME
        if base_url is None:
            base_url = OLLAMA_BASE_URL
        
        # 设置siliconflow API配置
        global SILICONFLOW_API_KEY, SILICONFLOW_API_BASE
        if siliconflow_api_key:
            SILICONFLOW_API_KEY = siliconflow_api_key
        if siliconflow_api_base:
            SILICONFLOW_API_BASE = siliconflow_api_base
            
        self.token_counter = TokenCounter(model_name)
        self.llm = LLMFactory.create_chat_llm(model_name, base_url)
        self.single_file_chain = SingleFileAnalysisChain(self.llm, self.token_counter)
        self.total_summary_chain = TotalSummaryChain(self.llm, self.token_counter)
    
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
    
    def process_git_diff(self, diff_content: str, max_workers: int = None) -> ProcessingResult:
        if max_workers is None:
            max_workers = PROCESSING_MAX_WORKERS
            
        logger.info("开始解析git diff...")
        files = DiffParser.parse_git_diff(diff_content)
        logger.info(f"解析到 {len(files)} 个文件的改动")
        if not files:
            logger.warning("未找到任何文件改动")
            return ProcessingResult(
                file_summaries=[],
                total_summary=None,
                processed_files=0,
                total_files=0,
                error='未找到任何文件改动'
            )
        logger.info("开始并行处理各个文件的改动...")
        file_summaries = []
        # 使用更健壮的并发处理机制
        executor = None
        try:
            executor = ThreadPoolExecutor(max_workers=max_workers)
            future_to_file = {
                executor.submit(self.single_file_chain.analyze, file_info): file_info.file_path
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
                        summary = future.result(timeout=5)  # 短暂缓冲时间，因为任务已经完成
                        if summary:
                            file_summaries.append(summary)
                            logger.info(f"完成文件 {file_path} 的摘要生成 ({completed_count}/{total_count})")
                        else:
                            logger.warning(f"文件 {file_path} 的摘要生成失败 ({completed_count}/{total_count})")
                    except (FutureTimeoutError, TimeoutError) as e:
                        logger.error(f"文件 {file_path} 的摘要获取超时，跳过该文件: {type(e).__name__} ({completed_count}/{total_count})")
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
        logger.info(f"成功生成 {len(file_summaries)} 个文件的摘要")
        logger.info("开始生成总摘要...")
        total_summary = None
        if file_summaries:
            logger.info(f"基于 {len(file_summaries)} 个成功处理的文件生成总摘要...")
            try:
                total_summary = self.total_summary_chain.generate(file_summaries)
                if total_summary:
                    logger.info("总摘要生成成功")
                else:
                    logger.warning("总摘要生成失败")
            except Exception as e:
                logger.error(f"生成总摘要时发生未预期的错误: {e}")
        else:
            logger.warning("没有成功处理的文件，跳过总摘要生成")
        return ProcessingResult(
            file_summaries=file_summaries,
            total_summary=total_summary,
            processed_files=len(file_summaries),
            total_files=len(files)
        )

# ==================== 主函数 ====================

def get_agent_summary(sample_diff, siliconflow_api_key="", siliconflow_api_base="https://api.siliconflow.cn/v1"):

    summarizer = GitDiffSummarizer(siliconflow_api_key, siliconflow_api_base)
    result = None
    try:
        result = summarizer.process_git_diff(sample_diff)
    finally:
        # 确保在函数退出前清理资源
        summarizer.cleanup()

    if not result:
        print("处理失败，无法获取结果")
        return None
    
    if result.error:
        print(f"错误: {result.error}")
    print("\n=== 单文件摘要 ===")
    for summary in result.file_summaries:
        print(f"文件: {summary.file_path}")
        print(f"改动类型: {summary.change_type}")
        print(f"新增行数: {summary.lines_added}")
        print(f"删除行数: {summary.lines_deleted}")
        print(f"潜在影响: {summary.potential_impact}")
        print(f"摘要: {summary.summary}")
        print("-" * 50)
    print("=== 处理结果 ===")
    print(f"总文件数: {result.total_files}")
    print(f"成功处理文件数: {result.processed_files}")
    if result.total_summary:
        print("\n=== 总摘要 ===")
        total = result.total_summary
        print(f"总文件数: {total.total_files_changed}")
        print(f"总改动行数: {total.total_lines_changed}")
        print(f"改动类型列表: {total.change_type_list}")
        print(f"整体潜在影响: {total.overall_potential_impact}")
        print(f"整体摘要: {total.overall_summary}")
        print("\n=== 文件改动列表 ===")
        for file_change in total.file_changes:
            print(f"- {file_change.file_path}: {file_change.change_type} ({file_change.lines_changed} 行)")
            
    # 输出token统计
    stats = summarizer.token_counter.get_stats()
    print("\n=== Token消耗统计 ===")
    print(f"Prompt tokens: {stats['prompt_tokens']}")
    print(f"Completion tokens: {stats['completion_tokens']}")
    print(f"Total tokens: {stats['total_tokens']}")
    # exit()
    return result

if __name__ == "__main__":
    # 微服务接口逻辑模拟： 传递进来的就是 sample_diff 的内容
    sample_diff = sys.argv[1]
    result = get_agent_summary(sample_diff) 
    print(result)