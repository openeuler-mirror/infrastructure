resource "huaweicloud_compute_floatingip_associate_v2" "this" {
  count = "${length(var.associates)}"
  floating_ip = "${lookup(var.associates[count.index], "eip_id")}"
  instance_id = "${lookup(var.associates[count.index], "server_id")}"
}
