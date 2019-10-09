resource "huaweicloud_vpc_eip_v1" "this" {
  count = "${length(var.eips)}"
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    id         = "${lookup(var.eips[count.index], "bandwidth_id", null)}"
    share_type = "WHOLE"
  }
}

resource "huaweicloud_vpc_bandwidth_v2" "this" {
  count = "${length(var.bandwidths)}"
  name  = "${lookup(var.bandwidths[count.index], "name", null)}"
  size  = "${lookup(var.bandwidths[count.index], "size", 5)}"
}
