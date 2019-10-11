# Notice
This yaml in this folder are initially based on 
the [jenkins chart](https://github.com/helm/charts/tree/master/stable/jenkins) 
commit: 322baa4a944f63443f7fd83ac4838dc8ce756aa0
#Changes have made:
1. 
2. 


# Command to generate the final yaml
```$xslt
helm template ./jenkins --namespace jenkins-system -f jenkins/values.yaml -f jenkins/hw_override.yaml --name openeuler
```