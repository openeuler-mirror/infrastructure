# Notice
This folder used to generate final yaml that can be used to setup the openeuler rpm repo service.
Please update the `values.yaml` at least with key and cert file before applying yaml.
```$xslt
  keyFile: "please update this with correct key file url"
  certFile: "please update this with correct cert file url"
```


# Command
```$xslt
helm template repo-chart  -f repo-chart/values.yaml --namespace repo --name openeuler  > deployment.yaml
```
