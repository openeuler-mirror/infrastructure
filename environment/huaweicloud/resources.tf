module "network" {
  source ="./network/"

  // VPC
  name = "net-community"
  cidr = "172.16.0.0/16"

  // VPC Subnet
  subnets = [
    {
      name       = "subnet-k8s"
      cidr       = "172.16.1.0/24"
      gateway_ip = "172.16.1.1"
    }
  ]
}

module "security_group" {
  source ="./sg/"

  // Security Group
  name        = "sg-community"
  description = "This is community security group"

  // Security Group Rule
  rules = [
    {
      direction      = "ingress",
      ethertype      = "IPv4",
      protocol       = "tcp",
      port_range_min = "22",
      port_range_max = "22",
      remote_ip_cidr = "0.0.0.0/0"
    },
    {
      direction      = "ingress",
      ethertype      = "IPv4",
      protocol       = "tcp",
      port_range_min = "80",
      port_range_max = "80",
      remote_ip_cidr = "0.0.0.0/0"
    },
    {
      direction      = "ingress",
      ethertype      = "IPv4",
      protocol       = "tcp",
      port_range_min = "25",
      port_range_max = "25",
      remote_ip_cidr = "0.0.0.0/0"
    }
  ]
}

module "cce" {
  source = "./cce"
 
  name   = "cce-community"
  description = "This is comunity cce cluster"
  vpc_id = "${module.network.this_vpc_id}"
  subnet_id = "${split(",", module.network.this_network_ids)[0]}"
  flavor_id = "cce.s1.large"

  nodes = [
    {
      name    = "node1",
      ssh_key = "KeyPair-infra",
      az      = "ap-southeast-1a",
      flavor_id = "s3.xlarge.4"
    },
    {
      name    = "node2",
      ssh_key = "KeyPair-infra",
      az      = "ap-southeast-1a",
      flavor_id = "s3.xlarge.4"
    },
    {
      name    = "node3",
      ssh_key = "KeyPair-infra",
      az      = "ap-southeast-1a",
      flavor_id = "s3.xlarge.4"
    },
  ]  
}

module "internet" {
  source = "./internet"
  
  eips = [
    {
      bandwidth-name = "bandwidth-01",
      size           = "5"
    },
    {
      bandwidth-name = "bandwidth-02",
      size           = "5"
    },
    {
      bandwidth-name = "bandwidth-03",
      size           = "5"
    }, 
    {
      bandwidth-name = "bandwidth-04",
      size           = "5"
    }
  ]
}

module "nat" {
  source = "./nat"

  name = "nat-community"
  description = "this is a nat gateway to provide the access to internet for node"
  spec_code = 3
  router_id = "${module.network.this_vpc_id}"
  network_id = "${split(",", module.network.this_network_ids)[0]}"

  rules = [
    {
      network_id = "${split(",", module.network.this_network_ids)[0]}"
      eip_id = "${split(",",module.internet.this_eip_ids)[0]}"
    }
  ]
}


module "elb" {
  source = "./elb"
  
  loadbalancers = [
    {
      name  =  "elb-website"
      description = "The load balancer of website"
      type = "External"
      vpc_id = "${module.network.this_vpc_id}"
      eip    = "${split(",", module.internet.this_eip_addresses)[3]}"
    },
    {
      name  =  "elb-mailweb"
      description = "The load balancer of mailweb"
      type = "External"
      vpc_id = "${module.network.this_vpc_id}"
      eip    = "${split(",", module.internet.this_eip_addresses)[2]}"
    },
    {
      name  =  "elb-mta"
      description = "The load balancer of mail MTA"
      type = "External"
      vpc_id = "${module.network.this_vpc_id}"
      eip    = "${split(",", module.internet.this_eip_addresses)[1]}"
    }
  ]
}
  
 
module "dns" {
  source = "./dns"
  
  domain = "openeuler.org"
  email  = "freesky.edward@gmail.com"
  
  records = [
    {
      domain = "mail"
      type  =  "A"
      value = "${split(",", module.internet.this_eip_addresses)[1]}"
    },
    {
      domain = "mailweb"
      type = "A"
      value = "${split(",", module.internet.this_eip_addresses)[2]}"
    },
    {
      domain = "@"
      type = "MX"
      value = "mail.openeuler.org"
    },
    {
      domain = "@"
      type = "TXT"
      value = "v=spf1 a mx ip4:${split(",", module.internet.this_eip_addresses)[0]}  ~all"
    },
    {
      domain = "_dmarc"
      type = "TXT"
      value = "v=DMARC1;p=reject;sp=reject;adkim=r;aspf=r;fo=1;rf=afrf;pct=100;ruf=mailto:405121670@qq.com;ri=86400"
    },
    {
      domain = "${var.handler}._domainkey"
      type = "TXT"
      value = "v=DKIM1;k=rsa;p=${var.dkim_public_key}"
    }
  ]

  ptrs = [
    {
       domain = "openeuler.org"
       ip     = "${split(",", module.internet.this_eip_ids)[0]}"
    }
  ]
} 
