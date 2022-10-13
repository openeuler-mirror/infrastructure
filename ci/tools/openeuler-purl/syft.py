import asyncio
import json
import os
import ast
import sys
import urllib.parse

import aiofiles
from loguru import logger
from tqdm import tqdm

# logging.basicConfig(level=logging.DEBUG)
logger.remove()
default_id = logger.add(sys.stderr, level="INFO", filter=lambda x: 'INFO' == x['level'].name)
logger.add("./logs/syft.log", level="DEBUG", backtrace=True, diagnose=True, mode="w")
# err_id = logger.add("./logs/syft_error.log", level="ERROR", backtrace=True, diagnose=True, mode="w",
#                     filter=lambda x: 'ERROR' == x['level'].name)
# debug_id = logger.add("./logs/syft_debug.log", level="DEBUG", backtrace=True, diagnose=True, mode="w",
#                       filter=lambda x: 'DEBUG' == x['level'].name)
# 自定义日志记录器
# logger.level("ERR_FILE", no=40, color='<red><bold>', icon='❌')

# 记录已解析的文件数量
global cataloged_count

# 记录解析失败的包
global catalog_error_packages

# 记录解析结果为空的包
global catalog_none_packages


async def show_bar(max_length):
    """
    显示进度条
    :param max_length:
    :return:
    """
    # 初始化已解析个数为 0
    bar = tqdm(file=sys.stderr, initial=0, total=max_length, mininterval=0.1, maxinterval=0.1)
    bar.set_description("Processing: ")
    current_count = 0
    while cataloged_count <= max_length:
        update_step = cataloged_count - current_count
        bar.update(update_step)
        current_count = cataloged_count
        if cataloged_count == max_length:
            bar.close()
            return
        await asyncio.sleep(0.1)


class SyftResolver:
    """
    syft 批处理解析器工作的类，处理解析流程中的各种逻辑
    """

    def __init__(self, basedir, syft_executable, template_path):
        """
        初始化必要的参数
        :param basedir:
        :param syft_executable:
        :param template_path:
        """
        self.__version_cmds_dict = None
        self.__version = None
        self.__output_dict = None
        self.__basedir = basedir
        self.__syft_executable = syft_executable
        self.__template_path = template_path

    def set_version(self, version):
        self.__version = version
        self.__output_dict = {"version": version, "data": []}
        self.__version_cmds_dict = {"version": version, "cmd_dicts": []}

    @property
    def output_dict(self):
        return self.__output_dict

    @property
    def version(self):
        return self.__version

    @property
    def basedir(self):
        return self.__basedir

    @property
    def version_cmds_dict(self):
        return self.__version_cmds_dict

    async def run_syft_async(self, semaphore, cmd_dict):
        """
        异步执行 syft 命令解析包数据
        :param semaphore: 信号量以限制并发数量
        :param cmd_dict: 要解析的文件以及解析所用的命令
         解析得到的数据结构 {"filename": string, "cmd": string}
        :return:
        """
        global cataloged_count
        async with semaphore:
            syft_output_success_purl_dict = {}
            filename = cmd_dict["filename"]
            cmd = cmd_dict["cmd"]
            proc = await asyncio.subprocess.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            stdout_str = stdout.decode("utf-8")
            # 去除不必要的 unicode 字符，避免输出到日志文件中的乱码
            stderr_str = stderr.decode("utf-8")\
                .replace("[0;90m", "")\
                .replace("[0m [0;33m", "")\
                .replace("[0m", "")
            if stderr_str:
                logger.error(f"\n{stderr_str}")
                catalog_error_packages.append(filename)
                cataloged_count += 1
                return
            begin = stdout_str.find("{")
            end = stdout_str.rfind("}") + 1
            syft_out_str = stdout_str[begin:end]
            if syft_out_str:
                # 尝试解决输出的文本中 npm 包解析时带 @ 的包名转义的问题
                # 如"pkg:npm/@types/d3-time@1.0.10" 转义 为 "pkg:npm/%40types/d3-time@1.0.10"
                syft_out_str = urllib.parse.unquote_plus(syft_out_str)
                # 删除转义字符 \, 否则会影响下面解析 json 字符串为python对象的过程
                syft_out_str = syft_out_str.replace("\\", "")
                try:
                    syft_output_success_purl_dict = ast.literal_eval(syft_out_str)
                except SyntaxError as e:
                    logger.error("analysing {} has error: {}", filename, e.text)
                    logger.error(f"stdout: {stdout_str} \n stderr: {stderr_str}")
                    catalog_error_packages.append(filename)
                    cataloged_count += 1
                    return
            else:
                logger.error("execute error: unable to get syft analysed result")
            if len(syft_output_success_purl_dict.get("purls")) != 0:
                self.output_dict["data"].append(syft_output_success_purl_dict)
            else:
                logger.debug("syft can not resolve purl in the package: {}", filename)
                catalog_none_packages.append(filename)
            cataloged_count += 1

    def dump_to_json(self, output_filepath):
        """
        异步保存内容到指定的 json 文件
        :return:
        """
        # 写入 JSON 数据
        with open(output_filepath, "w") as fs:
            json.dump(self.output_dict, fs)

    def get_versions(self):
        """
        获取包已下载的所有系统版本
        :return:
        """
        return [dirname for dirname in os.listdir(self.basedir) if "openEuler-2" in dirname]

    def set_cmds_dict(self):
        """
        获取当前系统版本所有包的解析命令
        """
        logger.info("current catalog version: {}", self.version)
        cmd_dict_list = []
        syft_exec = self.__syft_executable
        template_path = self.__template_path
        version_path = os.path.realpath(os.path.join(self.basedir, self.version))
        package_path = os.path.join(version_path, "packages")
        filename_list = os.listdir(package_path)
        for filename in filename_list:
            if ".rpm" in filename:
                cmd_dict = {}
                filepath = os.path.join(package_path, filename)
                cmd = f"{syft_exec} {filepath} -o template -t {template_path}"
                cmd_dict["filename"] = filename
                cmd_dict["cmd"] = cmd
                cmd_dict_list.append(cmd_dict)
        self.version_cmds_dict["cmd_dicts"] = cmd_dict_list

    async def save_catalog_error_packages(self, packages):
        """
        保存解析异常的包到日志
        :param packages:
        :return:
        """
        async with aiofiles.open(f"./logs/syft_catalog_error_list-{self.version}.log", "w") as fs:
            for package_name in packages:
                await fs.write(f"{package_name}\n")

    async def save_catalog_none_packages(self, packages):
        """
        保存解析结果为空的包到日志
        :param packages:
        :return:
        """
        async with aiofiles.open(f"./logs/syft_catalog_none_list-{self.version}.log", "w") as fs:
            for package_name in packages:
                await fs.write(f"{package_name}\n")

    async def run(self, limit=5):
        """
        异步主函数，包括三个步骤
        1. 根据当前系统版本的所有包，构造 syft 的解析命令语句
        2. 提交所有解析任务，并发运行
        3. 记录解析结果，将解析异常的包记录到日志中
        :param limit:
        :return:
        """
        global cataloged_count
        self.set_cmds_dict()
        semaphore = asyncio.Semaphore(limit)
        tasks = [self.run_syft_async(semaphore, cmd_dict) for cmd_dict in self.version_cmds_dict["cmd_dicts"]]
        tasks_count = len(tasks)

        # 初始化进度条显示变化需要的变量
        cataloged_count = 0

        tasks.append(show_bar(tasks_count))
        await asyncio.gather(*tasks)
        # 保存解析有问题的包到日志中
        await self.save_catalog_error_packages(catalog_error_packages)
        await self.save_catalog_none_packages(catalog_none_packages)
        logger.info("{} Catalog Finished, But Some Package Have A Some Problem When Catalogging "
                    ", Try Check Or Manually Catalog Them！！！",
                    self.version)
        logger.info("These Packages Catalog Error: ")
        for p in catalog_error_packages:
            logger.info("  {}", p)
        logger.info("\n\n")
        logger.info("These Packages Catalog Success, But Purls Item Is None: ")
        for p in catalog_none_packages:
            logger.info("  {}", p)
        logger.info("You Can Also Look What These Packages In ./logs/syft_catalog_error_list-{} "
                    "And ./logs/syft_catalog_error_list-{} \n\n",
                    self.version, self.version)


if __name__ == '__main__':
    dir_path = ""
    syft = ""
    template = ""
    syft_limit = 10
    with open("configs.json", "r") as f:
        configs = json.load(f)
        # 从配置文件中获取必要的变量
        if configs.get('dir_path'):
            dir_path = configs["dir_path"]
        else:
            logger.error("dir_path is not set")
            exit(0)
        if configs.get('syft'):
            syft = configs["syft"]
            syft = os.path.realpath(syft)
            if not os.path.exists(syft):
                logger.error("syft config is error")
                exit(0)
        else:
            logger.error("syft executable path is not set")
            exit(0)
        if configs.get('template'):
            template = configs["template"]
            template = os.path.realpath(template)
            if not os.path.exists(template):
                logger.error("template config is error")
                exit(0)
        else:
            logger.error("template path path is not set")
            exit(0)
        syft_limit = configs["syft_limit"] if configs.get('syft_limit') else 10
    resolver = SyftResolver(basedir=dir_path, syft_executable=syft, template_path=template)

    versions = resolver.get_versions()
    if not versions:
        raise "没有获取到版本，请检查工作目录！！"
    logger.info("待解析的版本列表：")
    for v in versions:
        logger.info("  {}", v)
    for ver in versions:
        # 初始化解析异常的包的存放列表
        catalog_error_packages = []
        catalog_none_packages = []
        resolver.set_version(version=ver)
        asyncio.run(resolver.run(limit=syft_limit))
        # 输出到解析结果到文件中
        output = resolver.output_dict
        output_json_path = f"{os.path.join(dir_path, ver)}/all_packages_purls.json"
        resolver.dump_to_json(output_filepath=output_json_path)
    logger.info("全部解析完成！！")
