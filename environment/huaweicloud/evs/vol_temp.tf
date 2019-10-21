resource "huaweicloud_blockstorage_volume_v2" "this" {
  count             = "${length(var.volumes)}"
  name              = "${lookup(var.volumes[count.index], "name")}"
  size              = "${lookup(var.volumes[count.index], "size", "100")}"
  volume_type       = "${lookup(var.volumes[count.index], "type", "SATA")}"
  availability_zone = "${lookup(var.volumes[count.index], "az", "cn-north-4a")}"
}


resource "huaweicloud_compute_volume_attach_v2" "this" {
  count       = "${length(var.vol_attaches)}"
  instance_id = "${lookup(var.vol_attaches[count.index], "server_id")}"
  volume_id   = "${lookup(var.vol_attaches[count.index], "volume_id")}"
}
