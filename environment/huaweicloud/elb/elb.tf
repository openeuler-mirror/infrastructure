resource "huaweicloud_elb_loadbalancer" "elb" {
  count          = "${length(var.loadbalancers)}"
  name           = "${lookup(var.loadbalancers[count.index], "name", null)}"
  type           = "${lookup(var.loadbalancers[count.index], "type", "External")}"
  description    = "${lookup(var.loadbalancers[count.index], "description", "")}"
  vpc_id         = "${lookup(var.loadbalancers[count.index], "vpc_id", null)}"
  admin_state_up = 1
  vip_address    = "${lookup(var.loadbalancers[count.index], "eip", null)}"
}


