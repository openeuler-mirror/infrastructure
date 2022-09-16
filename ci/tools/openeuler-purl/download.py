import json
import os.path
import sys

from loguru import logger
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import aiofiles
import requests
from tqdm import tqdm

# logging.basicConfig(level=logging.DEBUG)
logger.remove()
default_id = logger.add(sys.stderr, level="INFO", filter=lambda x: 'INFO' == x['level'].name)
logger.add("./logs/download.log", level="DEBUG", backtrace=True, diagnose=True, mode="w")
# err_id = logger.add("./logs/download_error.log", level="ERROR", backtrace=True, diagnose=True, mode="w",
#                     filter=lambda x: 'ERROR' == x['level'].name)
# debug_id = logger.add("./logs/download_debug.log", level="DEBUG", backtrace=True, diagnose=True, mode="w",
#                       filter=lambda x: 'DEBUG' == x['level'].name)

# 记录下载逻辑已处理的文件数量
global download_count


# 记录下载失败的文件列表
global down_error_packages


def get_version_list_by_name():
    """
    根据系统版本号获取不同系统版本的包根目录
    :return: 一个列表，包含不同版本号的 src.rpm 包的URL路径
    """
    version_name_list = [
        "openEuler-20.03-LTS",
        "openEuler-20.03-LTS-SP1",
        "openEuler-20.03-LTS-SP2",
        "openEuler-20.03-LTS-SP3",
        "openEuler-20.09",
        "openEuler-21.03",
        "openEuler-21.09",
        "openEuler-22.03-LTS"
    ]
    version_list = []
    for version_name in version_name_list:
        version_dict = {}
        if "openEuler-2" in version_name:
            version_dict["name"] = version_name
            urlpath = f"/{version_name}/source/Packages/"
            version_dict["source_path"] = urlpath
            version_list.append(version_dict)
    return version_list


def get_package_list(package_urlpath):
    """
    根据指定的 URL 路径获取该路径下所有的软件包名列表
    :param package_urlpath:
    :return: 一个列表，都是软件包名
    """
    base_path = f'{MIRROR_URL}{package_urlpath}'
    res = requests.get(base_path)
    soup = BeautifulSoup(res.text, features="html.parser")
    index_list = soup.select("#list tbody tr a[title]")
    package_list = []
    for index in index_list:
        package_dict = {}
        package_name = index.text
        if ".src.rpm" in package_name:
            package_dict["name"] = package_name
            urlpath = f"{base_path}{package_name}"
            package_dict["source_path"] = urlpath
            package_list.append(package_dict)
    return package_list


async def save_file(response, filepath):
    """
    异步保存文件流到指定的文件
    :param response:
    :param filepath:
    :return:
    """
    content_length = int(response.headers.get('Content-Length', 0))
    if os.path.exists(filepath):
        if os.path.getsize(filepath) != content_length:
            try:
                logger.debug(f"文件大小异常，尝试删除异常文件：{filepath}, 并重新下载")
                os.remove(filepath)
            except IOError as ie:
                logger.debug(f"删除异常文件：{filepath} 未完成，请手动检查是否删除成功！！！{ie}")
        else:
            return
    current_length = 0
    async with aiofiles.open(filepath, mode='wb') as fd:
        async for chunk in response.content.iter_chunked(n=1024):
            if chunk:
                await fd.write(chunk)
                current_length = current_length + len(chunk)


async def download_job(session, package, dest_path, semaphore):
    """
    异步任务，下载某个URL 路径下所有的 rpm src 包
    :param session:
    :param semaphore:
    :param package:
    :param dest_path:
    :return:
    """
    global download_count
    async with semaphore:
        package_name = package['name']
        filepath = os.path.join(dest_path, package_name)
        try:
            async with session.get(package["source_path"]) as response:
                await save_file(response, filepath=filepath)
        except Exception as ex:
            try:
                logger.debug(f"{package_name} 包下载异常，尝试删除异常文件。{ex}")
                if os.path.exists(filepath):
                    os.remove(filepath)
            except IOError as ie:
                logger.debug(f"删除异常文件：{package_name} 未完成，请手动检查！！！{ie}")
            finally:
                down_error_packages.append(package_name)
        finally:
            download_count += 1


async def show_bar(max_length):
    """
    进度条
    :param max_length:
    :return:
    """
    # 初始化已下载个数为 0
    global download_count
    download_count = 0
    bar = tqdm(initial=0, total=max_length, mininterval=0.1, maxinterval=0.1, nrows=16)
    bar.set_description("Download Processing: ")
    current_count = 0
    while download_count <= max_length:
        update_step = download_count - current_count
        bar.update(update_step)
        current_count = download_count
        if download_count == max_length:
            bar.close()
            return
        await asyncio.sleep(0.1)


async def save_download_error_packages(version_name, packages):
    async with aiofiles.open(f"./logs/download_error_list-{version_name}.log", "w") as fs:
        for package_name in packages:
            await fs.write(f"{package_name}\n")


async def main(limit):
    """
    异步主函数，包括四个步骤
    1. 获取所有的版本号对应的 src.rpm 包的根路径
    2. 根据对应系统版本的根路径构建下载不同的下载目录
    3. 提交对应系统版本的所有下载任务，并发运行
    4. 记录下载结果，将下载异常的包记录到对应系统版本的日志中
    :param limit:
    :return:
    """
    _version_list = get_version_list_by_name()
    logger.info("版本列表：")
    for v in _version_list:
        logger.info("  {}", v.get('name'))
    async with aiohttp.ClientSession() as session:
        for index, version in enumerate(_version_list):
            logger.info(f"开始下载第 {index + 1} 个版本：{version['name']}")
            await asyncio.sleep(1.5)
            _package_list = get_package_list(version["source_path"])
            version_path = os.path.join(DIR_PATH, version["name"])

            # 指定当前版本下载到的目录
            dest_path = os.path.join(version_path, "packages")
            os.makedirs(dest_path, exist_ok=True)
            # 信号量，用来限制并发数
            semaphore = asyncio.Semaphore(limit)
            # 每个包的下载都作为一个任务
            tasks = [download_job(session, package, dest_path, semaphore) for package in _package_list]
            job_count = len(tasks)
            # 进度条任务也加到异步任务中
            tasks.append(show_bar(job_count))
            # 提交所有任务
            await asyncio.gather(*tasks)
            if down_error_packages:
                await save_download_error_packages(version["name"], down_error_packages)
            logger.info("{} Download Finished, But Some Package Download Error, Try Manually Download It!",
                        version["name"])
            for p in down_error_packages:
                logger.info(f"  {p}")
            logger.info("You Can Also Look What Package Fail In ./logs/download_error_list-{} \n\n",
                        version["name"])


if __name__ == '__main__':
    download_count = 0
    down_error_packages = []
    with open("configs.json", "r") as f:
        configs = json.load(f)
        # 下载到的目录必须指定
        DIR_PATH = ""
        if configs.get("dir_path"):
            DIR_PATH = configs.get("dir_path")
        else:
            logger.error("dir_path is not set")
            raise "dir_path is not set"
        # 如果没有设置镜像地址和下载限制，则使用默认
        MIRROR_URL = "http://121.36.97.194"
        if configs.get("mirror_url"):
            MIRROR_URL = configs.get("mirror_url")
        DOWNLOAD_LIMIT = 30
        if configs.get('download_limit'):
            DOWNLOAD_LIMIT = configs.get("download_limit")
        asyncio.run(main(limit=DOWNLOAD_LIMIT))
