resource "huaweicloud_nat_gateway_v2" "this" {
  name                = "${var.name}"
  description         = "${var.description}"
  spec                = "${var.spec_code}"
  router_id           = "${var.router_id}"
  internal_network_id = "${var.network_id}"
}

resource "huaweicloud_nat_snat_rule_v2" "this" {
  count          = "${length(var.rules)}"
  nat_gateway_id = "${huaweicloud_nat_gateway_v2.this.id}"
  network_id     = "${lookup(var.rules[count.index], "network_id", null)}"
  floating_ip_id = "${lookup(var.rules[count.index],"eip_id",null)}"
}


