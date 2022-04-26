# obs-developer-tools安装使用手册  <br/>
## 一、安装地址  <br/>
工具下载地址：https://developer.huaweicloud.com/tools#section-1  <br/>
![img.png](img.png) <br/>
详细操作流程请点击：用户指南  <br/>

## 二、Windows平台  <br/>
### 1、安装指南 <br/>
下载obs-browser-plus Setup 3.21.8后直接下一步安装即可  <br/>
![img_1.png](img_1.png)  <br/>
![img_2.png](img_2.png)  <br/>

### 2、Windows操作指南  <br/>
#### ①、登录  <br/>
![img_3.png](img_3.png)   <br/>

#### ②、上传文件或文件夹  <br/>
登录OBS Browser+。 <br/>
单击想要上传文件或文件夹的桶。 <br/>
单击“上传”，并选择“添加文件”或“添加文件夹”。 <br/>
![img_4.png](img_4.png)  <br/>

#### ③、下载文件或文件夹  <br/>
登录OBS Browser+。    <br/>
选中待配置的桶，选中需要下载的文件或文件夹后，单击“下载”。  <br/>
OBS对象存储支持批量下载多个文件和文件夹，按住“Ctrl”或“Shift”同时选中待下载的文件	或文件夹即可，同时支持“Ctrl+A”全选操作。操作习惯与Windows操作系统上的操作习惯保持一致。  <br/>
![img_5.png](img_5.png) <br/>

## 三、Linux平台  <br/>
### 1、安装指南  <br/>
#### ①、obsutil工具下载  <br/>
打开命令行终端，执行wget命令下载obsutil工具。  <br/>
wget https://obs-community.obs.cn-north-1.myhuaweicloud.com/obsutil/current/obsutil_linux_amd64.tar.gz  <br/>

#### ②、解压  <br/>
在软件包所在目录，执行以下解压命令。  <br/>
tar -xzvf obsutil_linux_amd64.tar.gz  <br/>

#### ③、增加obsutil文件可执行权限  <br/>
进入obsutil所在目录，执行以下命令，为obsutil增加可执行权限。  <br/>
cd obsutil_linux_amd64_5.x.x  <br/>
chmod 755 obsutil  <br/>

#### ④、拷贝obsutil、setup.sh到/usr/bin目录  <br/>
拷贝obsutil_linux_amd64_5.x.x目录下文件obsutil、setup.sh到/usr/bin目录下  <br/>
![img_6.png](img_6.png)  <br/>
cp xx/obsutil_linux_amd64_5.x.x/obsutil  /usr/bin/  <br/>
cp xx/obsutil_linux_amd64_5.x.x/setup.sh  /usr/bin/  <br/>

### 2、初始化配置  <br/> 
使用永久AK、SK进行初始化配置  <br/>
obsutil config -i=ak -k=sk -t=token -e=endpoint  <br/>
示例： <br/>
obsutil config -i=aabbcc -k=xxyyzz -e=obs.cn-north-4.myhuaweicloud.com  <br/>

### 3、操作指南   <br/>
#### ①、文件上传   <br/>
运行obsutil cp /temp/test.txt obs://bucket-test/test.txt命令，将本地test.txt文件上传至bucket-test桶中。   <br/>
命令：obsutil cp /temp/test.txt obs://bucket-test/test.txt  <br/>

Parallel:      5                   Jobs:          5  <br/>
Threshold:     52428800            PartSize:      5242880   <br/>
Exclude:                           Include:   <br/>
VerifyLength:  false               VerifyMd5:     false  <br/>
CheckpointDir: /temp/.obsutil_checkpoint  <br/>

test.txt:[==============================================] 100.00% 48.47 KB/s 0s  <br/>
Upload successfully, 4.44KB, /temp/test.txt --> obs://bucket-test1/test.txt  <br/>

#### ②、文件下载  <br/>
运行obsutil cp obs://bucket-test/test.txt /temp/test1.txt命令，将bucket-test桶中的test.txt对象下载至本地。  <br/>
命令：obsutil cp obs://bucket-test/test.txt /temp/test1.txt  <br/>

Parallel:      5                   Jobs:          5  <br/>
Threshold:     52428800            PartSize:      5242880  <br/>
Exclude:                           Include:  <br/>
VerifyLength:  false               VerifyMd5:     false  <br/>
CheckpointDir: /temp/.obsutil_checkpoint  <br/>

test.txt:[=============================================] 100.00% 775.52 KB/s 0s  <br/>
Download successfully, 4.44KB, obs://bucket-test1/test.txt --> /temp/test1.txt  <br/>

#### ③、文件夹上传  <br/>
上传文件夹至release桶REPO-for-LoongArch/test2目录中。  <br/>
命令：obsutil cp /home/worker obs://release/REPO-for-LoongArch/test2 -r -f  <br/>
![img_7.png](img_7.png)  <br/>

#### ④、文件夹下载  <br/>
从release桶REPO-for-LoongArch目录中下载文件夹test2至本地/home/worker/tmp/目录。  <br/>
命令：obsutil cp obs://release/REPO-for-LoongArch/test2  /home/worker/tmp -r -f  <br/>
![img_8.png](img_8.png)  <br/>

#### ⑤、查看下载数据  <br/>
![img_9.png](img_9.png)  <br/>
