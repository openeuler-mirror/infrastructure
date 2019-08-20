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

  
