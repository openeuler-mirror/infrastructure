resource "huaweicloud_vpc_eip_v1" "this" {
  count             = "${length(var.eips)}"
  publicip {
    type = "5_bgp"
  }
  bandwidth {
    name        = "${lookup(var.eips[count.index], "bandwidth-name", null)}"
    size        = "${lookup(var.eips[count.index], "size", null)}"
    share_type  = "PER"
    charge_mode = "traffic"
  }
}
