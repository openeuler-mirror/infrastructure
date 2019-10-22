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
      primary_dns   = "172.16.1.111"
      secondary_dns = "8.8.8.8"
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
      size = "10"
    }
  ]

  eips = [
    {
      bandwidth_id = "${split(",", module.ci_internet.this_bandwidth_ids)[0]}"
    },
    {
      bandwidth_id = "${split(",", module.ci_internet.this_bandwidth_ids)[0]}"
    },
    {
      bandwidth_id = "${split(",", module.ci_internet.this_bandwidth_ids)[0]}"
    },
    {
      bandwidth_id = "${split(",", module.ci_internet.this_bandwidth_ids)[0]}"
    }
  ]
}

#module "ci_nat" {
#  source = "./nat"
#
#  providers = {
#    huaweicloud = huaweicloud.ci
#  }
#
#  name        = "ci-community"
#  description = "this is a nat gateway to provide the access to internet for node"
#  spec_code   = 3
#  router_id   = "${module.ci_network.this_vpc_id}"
#  network_id  = "${split(",", module.ci_network.this_network_ids)[0]}"
#
#  rules = [
#    {
#     network_id = "${split(",", module.ci_network.this_network_ids)[0]}"
#      eip_id     = "${split(",", module.ci_internet.this_eip_ids)[2]}"
#    }
#  ]
#}

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
      port_range_min = "82",
      port_range_max = "82",
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
      direction      = "ingress",
      ethertype      = "IPv4",
      protocol       = "",
      remote_ip_cidr = "172.16.0.0/16"
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
      volume_size    = "100"
      network        = "${split(",", module.ci_network.this_network_ids)[0]}"
    },
    {
      name           = "source-server"
      image          = "73503750-419d-47f0-aecf-0e9b10e88c38"
      flavor         = "sn3.4xlarge.2"
      keypair        = "KeyPair-ci"
      security_group = "${split(",", module.ci_security_group.this_security_group_id)[0]}"
      az             = "cn-north-4a"
      volume_size    = "100"
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
      image          = "814c54ce-2128-4e06-88c9-b9c7f392d0b2"
      flavor         = "s6.small.1"
      keypair        = "KeyPair-ci"
      security_group = "${split(",", module.ci_security_group.this_security_group_id)[0]}"
      az             = "cn-north-4a"
      user_data      = "cd /root & chmod +x restart_proxy.sh & sh restart_proxy.sh"
      volume_size    = "40"
      network        = "${split(",", module.ci_network.this_network_ids)[0]}"
      ipv4           = "172.16.1.111"
    }
  ]
}

module "ci_volumes" {
  source = "./evs/"

  providers = {
    huaweicloud = huaweicloud.ci
  }

  volumes = [
    {
      name = "source_vol"
      size = "2000"
      typs = "SATA"
    },
    {
      name = "backend_vol"
      size = "4000"
      typs = "SATA"
    }
  ]

  vol_attaches = [
    {
      server_id = "${split(",", module.servers.this_server_ids)[1]}"
      volume_id = "${split(",", module.ci_volumes.this_volume_ids)[0]}"
    },
    {
      server_id = "${split(",", module.servers.this_server_ids)[0]}"
      volume_id = "${split(",", module.ci_volumes.this_volume_ids)[1]}"
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
    },
    {
      eip_id    = "${split(",", module.ci_internet.this_eip_addresses)[2]}"
      server_id = "${split(",", module.servers.this_server_ids)[0]}"
    }
  ]
}
