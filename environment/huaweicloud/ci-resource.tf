module "ci_network" {
  source = "./network/"

  providers = {
    huaweicloud = huaweicloud.ci
  }

  // VPC
  name = "net-community"
  cidr = "172.16.0.0/16"

  // VPC Subnet
  subnets = [
    {
      name          = "subnet-community"
      cidr          = "172.16.1.0/24"
      gateway_ip    = "172.16.1.1"
      primary_dns   = "100.125.1.250"
      secondary_dns = "100.125.136.29"
    }
  ]
}

module "ci_route" {
  source = "./network-route/"

  providers = {
    huaweicloud = huaweicloud.ci
  }

  routes = [
    {
      vpc_id    = "${split(",", module.ci_network.this_vpc_id)[0]}"
      dest_cidr = "0.0.0.0/0"
      nexthop   = "${split(",", module.servers.this_server_ips)[3]}"
    }
  ]

}

module "ci_internet" {
  source = "./internet"

  providers = {
    huaweicloud = huaweicloud.ci
  }

  bandwidths = [
    {
      name = "bandwidth-ci"
      size = "5"
    }
  ]

  eips = [
    {
      bandwidth_id = "${split(",", module.ci_internet.this_bandwidth_ids)[0]}"
    },
    {
      bandwidth_id = "${split(",", module.ci_internet.this_bandwidth_ids)[0]}"
    }
  ]
}

module "ci_security_group" {
  source = "./sg/"

  providers = {
    huaweicloud = huaweicloud.ci
  }
  // Security Group
  name        = "sg-ci"
  description = "This is ci security group"

  // Security Group Rule
  rules = [
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
      port_range_min = "443",
      port_range_max = "443",
      remote_ip_cidr = "0.0.0.0/0"
    },
    {
      direction      = "ingress",
      ethertype      = "IPv4",
      protocol       = "tcp",
      port_range_min = "22",
      port_range_max = "22",
      remote_ip_cidr = "0.0.0.0/0"
    },
    {
      direction      = "egress",
      ethertype      = "IPv4",
      protocol       = "",
      remote_ip_cidr = "0.0.0.0/0"
    }
  ]
}


module "servers" {
  source = "./ecs/"

  providers = {
    huaweicloud = huaweicloud.ci
  }

  //servers
  servers = [
    {
      name           = "backend-server"
      image          = "73503750-419d-47f0-aecf-0e9b10e88c38"
      flavor         = "sn3.4xlarge.2"
      keypair        = "KeyPair-ci"
      security_group = "${split(",", module.ci_security_group.this_security_group_id)[0]}"
      az             = "cn-north-4a"
      volume_size    = "4000"
      network        = "${split(",", module.ci_network.this_network_ids)[0]}"
    },
    {
      name           = "source-server"
      image          = "73503750-419d-47f0-aecf-0e9b10e88c38"
      flavor         = "sn3.4xlarge.2"
      keypair        = "KeyPair-ci"
      security_group = "${split(",", module.ci_security_group.this_security_group_id)[0]}"
      az             = "cn-north-4a"
      volume_size    = "1000"
      network        = "${split(",", module.ci_network.this_network_ids)[0]}"
    },
    {
      name           = "api-server"
      image          = "73503750-419d-47f0-aecf-0e9b10e88c38"
      flavor         = "s6.2xlarge.2"
      keypair        = "KeyPair-ci"
      security_group = "${split(",", module.ci_security_group.this_security_group_id)[0]}"
      az             = "cn-north-4a"
      volume_size    = "100"
      network        = "${split(",", module.ci_network.this_network_ids)[0]}"
    },
    {
      name           = "router"
      image          = "67f433d8-ed0e-4321-a8a2-a71838539e09"
      flavor         = "s6.small.1"
      keypair        = "KeyPair-ci"
      security_group = "${split(",", module.ci_security_group.this_security_group_id)[0]}"
      az             = "cn-north-4a"
      volume_size    = "40"
      network        = "${split(",", module.ci_network.this_network_ids)[0]}"
      ipv4           = "172.16.1.111"
    }
  ]
}

module "ci_server_eip_bind" {
  source = "./ecs-eip-bind/"

  providers = {
    huaweicloud = huaweicloud.ci
  }

  associates = [
    {
      eip_id    = "${split(",", module.ci_internet.this_eip_addresses)[0]}"
      server_id = "${split(",", module.servers.this_server_ids)[3]}"
    },
    {
      eip_id    = "${split(",", module.ci_internet.this_eip_addresses)[1]}"
      server_id = "${split(",", module.servers.this_server_ids)[2]}"
    }
  ]
}
