#Required vars
variable "domain" {
    description = "The email domain that will be served on. e.g. example.com"
    default  = "openeuler.org"
}

variable "email" {
    description = "The admin email of dns domain. e.g. example@gmail.com"
    default  = "freesky.edward@gmail.com"
}

variable "dkim_public_key" {
    description = "The DKIM public key, must be rsa more than 1024, 2048 should be plus"
}

#
#Optional vars
#

## The cluster vars
variable "keypair" {
    description = "The key pair for cce cluster node login."
    default = "KeyPair-infra"
}

variable "az" {
    description = "The AZ that system will run on"
    default = "ap-southeast-1a"
}

variable "node_flavor" {
    description = "The default flavor of cce node"
    default = "s3.xlarge.4"
}

## The dns configuation vars
variable "selector" {
    description = "The DKIM hander name"
    default = "20191010"
}

variable "sub_domain_mail" {
    description = "The sub domain that exim4 will serve on"
    default = "mail"
}

variable "sub_domain_web" {
    description = "The sub domain that mailman web will serve on"
    default = "mailweb"
}
