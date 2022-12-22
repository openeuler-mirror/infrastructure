# 搭建dailybuild服务

## 一、拉取dailybuild服务相关的镜像
nginx： 
```shell
docker pull swr.cn-north-4.myhuaweicloud.com/openeuler/public/repo-nginx:1.21.0
```

## 二、docker部署
Step1.将“一”中服务相关的镜像下载下来,以及两个配置文件，配置文件保存路径自定义，Step2中挂载两个配置文件的主机路径以两个配置文件的绝对路径为准<br>
```shell
wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/build_dailybuild_service/nginx.conf -O /nginx.conf
wget https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/build_dailybuild_service/default.conf -O /default.conf
```
Step2.启动docker容器
```shell
docker run --name daily-build -d \
    -p 80:80 \
    -v /repo/openeuler:/repo/openeuler \
    -v /nginx.conf:/etc/nginx/conf/nginx.conf \
    -v /default.conf:/etc/nginx/conf/conf.d/default.conf \
    swr.cn-north-4.myhuaweicloud.com/openeuler/public/repo-nginx:1.21.0
```
