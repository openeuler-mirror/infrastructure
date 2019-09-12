# Infrastructure setup

This folder houses  the infrastructure setup. it includes the following resources building:

- ***Network***.  setup one vpc and one subnet.
- ***Nat***.  create a nat gateway to make the k8s node accessible to internet.
- ***EIPs***. create 3 EIPs. one for mailman-web, one for mailman-exim4, one for nat
- ***Load balance***.  two LBs, one use for mailman-web. one for mailman-exim4.
- ***DNS***.  several dns records. for mailman-web and mailman-exim4 sub-domain. dkim and spf authentication.
- ***CCE***. The K8S cluster on huaweicloud.

### Usage.

The whole resources manged by [terraform](https://terraform.io) with [terraform-provider-huaweicloud](https://github.com/terraform-providers/terraform-provider-huaweicloud).

Firstly. download terraform

```
https://releases.hashicorp.com/terraform/0.12.7/terraform_0.12.7_linux_amd64.zip
unzip terraform_0.12.7_linux_amd64.zip
```

Before starting to setup the resources. please prepare the following resources.

- The huaweicloud accounts. fill the ```provider.tf ``` with your account info. please refer to [terraform doc](https://www.terraform.io/docs/providers/huaweicloud/index.html) for more detailed guide.        
- The public/private key pairs.  used to DKIM authentication. please refer to [root README](../../README.md) for more detailed guide.   
- The cloud key-pair. the key pair for node login.  ``` KeyPair-infra```  is the default name. 

Provision the resources

```
terraform init
terraform apply -var -var "dkim_public_key=<your-public-key>"
```

### Inputs

All of the following parameters can be changed according to your environment via ```terraform  -var “name=value”```. but I recommend to use the default if you are not familiar with the whole project.

```dkim_public_key```(required). the public key will register the dns records.    
 
```domain```(optional). the domain name where to publish the mail system endpoints. e.g. newto.me.
```email```(optional). the email for domain and system administration.
```keypair```(optional). the key pair name that generate on huaweicloud console which is used for node ssh authentication.     
```az```(optional). the available zone where to run the mail system. default is ```ap-southeast-1a```      
```node_flavor```(optional) the vm flavor of k8s. default value is ```s3.xlarge.4```      
```selector```(optional)  the dkim selector name in dns records. which is used to dkim authentication by email receiver.     
```sub_domain_mail```(optional) the sub domain name for mailman-exim4 server. the default value is ```mail```, that means the exim4 will serve on ```mail.<domain-name>```.    
```sub_domain_web```(optional) the sub domain name for mailman-web.  default is ```web```.    

### Outputs

After the ```terraform apply``` completely run over. the command will output the following key information that will use in next stage to run k8s command or yaml configuration.

```cce_clusters``` is a array list of the cce cluster endpoints and authentication datas. which is used to configuration ```kubectl``` command.           
```cce_users``` is a array list of the users who have the accessible to k8s cluster. which is also used to configuration ```kubectl``` command.           
```exim4_elb_id``` the elb id for exim4 service. which will use to k8s service configuration.      
```web_elb_id``` the elb id for web service. being used to web service configuration.      
```exim4_eip``` the internet ip address that exim4 will serve at.      
```web_eip``` the internet ip address that web will serve at.      
```web_domain``` the full domain name for web service. e.g. web.newto.me     
```exim4_domain``` the full domain name for exim4 service. e.g. mail.newto.me     
```dkim_selector``` the selector name that has record into dns configuration. 


