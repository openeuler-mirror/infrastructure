# Useage

### Prerequisites 

- download terraform 
  
```
https://releases.hashicorp.com/terraform/0.12.7/terraform_0.12.7_linux_amd64.zip 
unzip terraform_0.12.7_linux_amd64.zip
```

- create the keypaire named it ```KeyPair-infra```

- modify the account information in provider.tf

- setting service authorization for CCE if you are first time use CCE service. please go to CCE page for more detailed information.

### Running the scripts


```
terraform init
terraform apply
```

### TODO

- Add Nat configuration for cluster

- Add ELB configuration for service 
