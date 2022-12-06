# 搭建repo发布服务

## 一、拉取repo发布服务相关的镜像
nginx： 
```shell
docker pull swr.cn-north-4.myhuaweicloud.com/openeuler/public/repo-nginx:1.21.0
```

## 二、K8s部署
Step1.将“一”中服务相关的3个镜像下载下来，并在K8s环境中制定镜像信息。<br>
Step2.参考模板repo-deploy-template.yaml: https://gitee.com/openeuler/infrastructure/raw/master/ci/tools/build_repo_service/repo-deploy-template.yaml 
，将其中标注的参数进行手动修改，生成一份定制化的部署文件，然后进行k8s部署。
