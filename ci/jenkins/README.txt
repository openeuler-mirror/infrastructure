# Jenkins 

### Brief

This is an extension jenkins image for [gitee](https://gitee.com/) repository online ci server. the default gitee plugin and kubernetes plugin are installed initially.

### Usage

docker 

```
docker build -t jenkins:v0.0.1
docker run -p 8080:8080 -p 50000:50000 jenkins:v0.0.1
```


