resource "huaweicloud_lb_loadbalancer_v2" "this" {
  count          = "${length(var.loadbalancers)}"
  name           = "${lookup(var.loadbalancers[count.index], "name", null)}"
  description    = "${lookup(var.loadbalancers[count.index], "description", "")}"
  vip_subnet_id  = "${lookup(var.loadbalancers[count.index], "subnet_id", null)}"
  admin_state_up = true
}

resource "huaweicloud_networking_floatingip_associate_v2" "this" {
  count       = "${length(var.loadbalancers)}" 
  floating_ip = "${lookup(var.loadbalancers[count.index], "eip", null)}"
  port_id     = "${huaweicloud_lb_loadbalancer_v2.this[count.index].vip_port_id}"
}
