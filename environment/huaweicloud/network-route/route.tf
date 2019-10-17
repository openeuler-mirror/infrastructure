resource "huaweicloud_networking_router_route_v2" "this" {
  count            = "${length(var.routes)}"
  router_id        = "${lookup(var.routes[count.index], "vpc_id", null)}"
  destination_cidr = "${lookup(var.routes[count.index], "dest_cidr", null)}"
  next_hop         = "${lookup(var.routes[count.index], "nexthop", null)}"
}
