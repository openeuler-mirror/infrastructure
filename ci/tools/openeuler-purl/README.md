---
typora-copy-images-to: ./img/
---



# openeuler-purl

## 介绍
获取 openeuler 软件仓中所有软件包的 purl 的工具

## 软件架构

### 目录说明

- /bin：syft 的可执行文件目录位置，有 linux 和 windows 两个子目录，分别可以在两个不同的平台 (x64) 下运行。
- /examples：syft 解析得到的结果示例，all_packages_purls.json 为批处理（syft.py）得到的结果，one_package_purls.json 为单次解析得到的结果示例。
- /logs：程序的运行日志保存目录。
- /syft-dev syft 程序源码
- /img：说明文档中用到的一些图片。

## 快速使用

程序的整体运行分为四步：

- 运行初始化，安装python环境以及依赖，编写配置文件。
- 运行 download.py ，下载需要解析的 src.rpm 包到工作目录。
- 运行 syft.py，解析工作目录下所有包的 purl
- 查看运行结果，检查运行日志。

### 1. 初始化环境

安装 python，版本需要 >= 3.8。

（建议新建一个虚拟环境）接下来安装必要的依赖。进入项目根目录，执行：

```bash
pip install -r requirements.txt
```

复制 configs.temp.json ,并重命名为 configs.json , 修改其中一些必要的配置信息：

```json
{
  "dir_path": "/home/test/rpm", 
  "mirror_host": "http://121.36.97.194", 
  "syft": "./bin/linux/syft", 
  "template": "./purl.json.tmpl", 
  "download_limit": 10,
  "syft_limit": 10 
}
```

配置文件各项的作用：

- dir_path： **必须配置**。主路径，工作目录，所有的的包会在下载到此目录下，并以版本号区分，syft 解析的结果也会存储在这个目录
- mirror_host：**可选**。软件仓（镜像）的主机
- syft：**必须配置**。syft 可执行文件的位置
- template：**必须配置**。syft 解析所用模板的位置
- download_limit：**可选**。 下载src rpm包的时候同时下载的文件数量
- syft_limit：**可选**。解析src rpm包同时解析的文件数量

### 2. 下载待解析的包

在项目根目录，执行：

```bash
python download.py
```

能看到进度条则代表正在下载，耐心等待即可。

![](.\img\image-20220914174732555.png)

### 3. 开始解析

包下载结束后，同样是在项目根目录，执行：

```bash
python syft.py
```

![](.\img\image-20220914201526168.png)

执行结束后，最终结果会按系统版本输出到不同的目录：`$dir_path/$os_version/all_packages_purls.json`

## 进阶使用

### 独立解析

`syft.py` 是批处理脚本，用于大批量生成解析结果，在某些情况下（测试或者验证结果）时，可能也需要独立解析单个包结果。

单独解析一个包的命令为：

```bash
$syft_executable $rpm_source -o template -t $template_file
```

linux下：

```bash
./bin/linux/syft ~/rpm/openEuler-20.03-LTS/packages/abattis-cantarell-fonts-0.111-2.oe1.src.rpm -o template -t ./purl.json.tmpl
```

windows下：

```bash
./bin/windows/syft.exe F:\\rpm\\openEuler-20.03-LTS\\packages\\abattis-cantarell-fonts-0.111-2.oe1.src.rpm -o template -t ./purl.json.tmpl
```

### 日志文件介绍

不管是在包下载阶段或是解析阶段，程序都或多或少会出现异常情况，为了方便排错，程序记录了一些日志（项目 logs 目录下），下面介绍这些日志的作用。

首先是在下载阶段，总共会生成两种类型的日志：

- download.log：记录整个下载过程所有输出的日志，包括异常记录。
- download_error_list-`os_version`-LTS：当前 `os_version`下载失败的包列表，用于手动下载。

其次是在解析阶段，总共会生成三种类型的日志：

- syft.log：记录整个解析过程所有输出的日志，同样包括异常记录。
- syft_catalog_error_list-`os_version`-LTS.log：解析过程中，syft 解析 **输出结果为异常** 的包列表，这些包在解析时无法输出解析结果（purls）。
- syft_catalog_none_list-`os_version`-LTS.log：解析过程中，syft 解析 **输出结果为空** 的包列表，这些包在解析时能够正常解析，但是无法获取到解析的结果（purls）。

包名后缀一定要为 src.rpm，不然无法解析

1. download.py 负责下载所有包到 `$dir_path/$os_version/packages`目录下，并按系统版本号（$os_version）存放在不同的目录
2. syft.py 负责解析下载下来的包，并将解析的结果按系统版本（$os_version）输出到不同的目录下，最终的文件位置 

## FAQ

1 如果有新版本的系统，如何添加到下载并解析？

> 首先确认镜像站 `$mirror_host` 根路径（如下图所示）中能找到到该版本系统对应的文件夹名字，假设为 openEuler-23.03-LTS。
>
> ![](img/image-20220915010735394.png)
>
> 编辑 `download.py` , 在 35 行左右，找到：
>
> ```python
>     version_name_list = [
>         "openEuler-20.03-LTS",
>         "openEuler-20.03-LTS-SP1",
>         "openEuler-20.03-LTS-SP2",
>         "openEuler-20.03-LTS-SP3",
>         "openEuler-20.09",
>         "openEuler-21.03",
>         "openEuler-21.09",
>         "openEuler-22.03-LTS"
>     ]
> ```
>
> 在最后面加上 openEuler-23.03-LTS，那么在运行 `download.py` 批量下载时，便可以下载该版本系统的所有包。

2 如何自定义输出格式？

> syft 支持输出多种格式，但是数据都过于冗杂，不符合项目需求，还好 syft 支持自定义模板。
>
> 为了方便本项目需求，这边自定义了一个模板文件 `purl.json.tmpl`：
>
> ```go
> {
>  "name": "{{.Source.Target | osBase}}",
>  "purls": [
>  {{- $artifactLength := len .Artifacts -}}
>  {{- range $index, $value := .Artifacts}}
>   {{$pos := add $index 1 -}}
>   "{{$value.PURL -}}"{{if lt $pos $artifactLength}},{{else}}{{break}}{{end}}
>  {{- end}}
>  ]
> }
> 
> ```
>
> 这个模板的语法来自于 Golang [text/template](https://pkg.go.dev/text/template#hdr-Functions)。如果需要自定义，可以参考 syft 的官方文档 [使用模板](syft-dev\README.md#Using templates)

3 syft 源码的修改部分？

> syft 功能其实已经挺完善了，基本的功能已经支持我们项目的需求，我主要修改的部分为 `syft-dev/source/source.go` 这个文件，添加了对 rpm 包的解压，然后解析得到结果的逻辑。修改的部分很少，如有需要修改或者查看，可以使用 diff 工具对比 `syft/source/source.go` 和源仓库 anchore/syft 中对应文件的差异。
