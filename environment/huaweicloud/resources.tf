module "network" {
  source = "./network/"

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


module "cce" {
  source = "./cce"

  name        = "cce-community"
  description = "This is cce cluster for community"
  vpc_id      = "${module.network.this_vpc_id}"
  subnet_id   = "${split(",", module.network.this_network_ids)[0]}"
  flavor_id   = "cce.s1.large"

  nodes = [
    {
      name      = "node1",
      ssh_key   = "${var.keypair}",
      az        = "${var.az}",
      flavor_id = "${var.node_flavor}"
    },
    {
      name      = "node1",
      ssh_key   = "${var.keypair}",
      az        = "${var.az}",
      flavor_id = "${var.node_flavor}"
    },
    {
      name      = "node1",
      ssh_key   = "${var.keypair}",
      az        = "${var.az}",
      flavor_id = "${var.node_flavor}"
    }
  ]
}

module "internet" {
  source = "./internet"

  bandwidths = [
    {
      name = "bandwidth-mail"
      size = "5"
    },
    {
      name = "bandwidth-website"
      size = "30"
    }
  ]

  eips = [
    {
      bandwidth_id = "${split(",", module.internet.this_bandwidth_ids)[0]}"
    },
    {
      bandwidth_id = "${split(",", module.internet.this_bandwidth_ids)[0]}"
    },
    {
      bandwidth_id = "${split(",", module.internet.this_bandwidth_ids)[0]}"
    },
    {
      bandwidth_id = "${split(",", module.internet.this_bandwidth_ids)[1]}"
    },
    { 
      bandwidth_id = "${split(",", module.internet.this_bandwidth_ids)[0]}"
    }
  ]
}

module "nat" {
  source = "./nat"

  name        = "nat-community"
  description = "this is a nat gateway to provide the access to internet for node"
  spec_code   = 3
  router_id   = "${module.network.this_vpc_id}"
  network_id  = "${split(",", module.network.this_network_ids)[0]}"

  rules = [
    {
      network_id = "${split(",", module.network.this_network_ids)[0]}"
      eip_id     = "${split(",", module.internet.this_eip_ids)[0]}"
    }
  ]
}


module "elb" {
  source = "./elb"

  loadbalancers = [
    {
      name        = "elb-web"
      description = "The load balancer of mailman-web"
      subnet_id   = "${split(",", module.network.this_subnet_ids)[0]}"
      eip         = "${split(",", module.internet.this_eip_addresses)[1]}"
    },
    {
      name        = "elb-mta"
      description = "The load balancer of mail MTA"
      subnet_id   = "${split(",", module.network.this_subnet_ids)[0]}"
      eip         = "${split(",", module.internet.this_eip_addresses)[2]}"
    },
    {
      name        = "elb-website"
      description = "The load balancer of website"
      subnet_id   = "${split(",", module.network.this_subnet_ids)[0]}"
      eip         = "${split(",", module.internet.this_eip_addresses)[3]}"
    },
    {
      name        = "elb-meetbot"
      description = "The load balancer of meetbot"
      subnet_id   = "${split(",", module.network.this_subnet_ids)[0]}"
      eip         = "${split(",", module.internet.this_eip_addresses)[4]}"
    }
  ]
}


module "dns" {
  source = "./dns"

  domain = "${var.domain}."
  email  = "${var.email}"

  records = [
    {
      domain = "${var.domain}."
      type   = "A"
      value  = "${split(",", module.internet.this_eip_addresses)[3]}"
    },
    {
      domain = "${var.sub_domain_mail}.${var.domain}."
      type   = "A"
      value  = "${split(",", module.internet.this_eip_addresses)[2]}"
    },
    {
      domain = "${var.sub_domain_web}.${var.domain}."
      type   = "A"
      value  = "${split(",", module.internet.this_eip_addresses)[1]}"
    },
    {
      domain = "${var.domain}."
      type   = "MX"
      value  = "1 ${var.sub_domain_mail}.${var.domain}."
    },
    {
      domain = "${var.domain}."
      type   = "TXT"
      value  = "\"v=spf1 a mx ip4:${split(",", module.internet.this_eip_addresses)[0]}  ~all\""
    },
    {
      domain = "_dmarc.${var.domain}."
      type   = "TXT"
      value  = "\"v=DMARC1;p=reject;sp=reject;adkim=r;aspf=r;fo=1;rf=afrf;pct=100;ruf=mailto:${var.email};ri=86400\""
    },
    {
      domain = "${var.selector}._domainkey.${var.domain}."
      type   = "TXT"
      value  = "\"v=DKIM1;k=rsa;p=${var.dkim_public_key}\""
    },
    {
      domain = "${var.domain}."
      type   = "meetings"
      value  = "${split(",", module.internet.this_eip_addresses)[4]}"
    }
  ]

  ptrs = [
    {
      domain = "${var.domain}."
      ip     = "${split(",", module.internet.this_eip_ids)[0]}"
    }
  ]
}
