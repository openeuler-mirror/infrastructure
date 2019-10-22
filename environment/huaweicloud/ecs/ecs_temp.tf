resource "huaweicloud_compute_instance_v2" "this" {
  count             = "${length(var.servers)}"
  name              = "${lookup(var.servers[count.index], "name")}"
  flavor_id         = "${lookup(var.servers[count.index], "flavor")}"
  key_pair          = "${lookup(var.servers[count.index], "keypair")}"
  security_groups   = ["${lookup(var.servers[count.index], "security_group")}"]
  availability_zone = "${lookup(var.servers[count.index], "az")}"
  user_data         = "${lookup(var.servers[count.index], "user_data", "")}"

  network {
    uuid        = "${lookup(var.servers[count.index], "network")}"
    fixed_ip_v4 = "${lookup(var.servers[count.index], "ipv4", "")}"
  }

  block_device {
    uuid                  = "${lookup(var.servers[count.index], "image")}"
    source_type           = "image"
    destination_type      = "volume"
    volume_size           = "${lookup(var.servers[count.index], "volume_size")}"
    boot_index            = 0
    delete_on_termination = true
  }

}
