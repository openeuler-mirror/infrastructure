resource "huaweicloud_dns_ptrrecord_v2" "this" {
  count       = "${length(var.ptrs)}"
  name        = "${lookup(var.ptrs[count.index], "domain", null)}"
  description = "${lookup(var.ptrs[count.index], "description", "ptr")}"
  floatingip_id = "${lookup(var.ptrs[count.index], "ip", null)}"
  ttl         = "${lookup(var.ptrs[count.index], "ttl", 3000)}"
}


resource "huaweicloud_dns_zone_v2" "this" {
  name        = "${var.domain}"
  email       = "${var.email}"
  description = "${var.description}"
  ttl         = "${var.ttl}"
  zone_type   = "${var.type}"
}


resource "huaweicloud_dns_recordset_v2" "this" {
  count       = "${length(var.records)}"
  zone_id     = "${huaweicloud_dns_zone_v2.this.id}"
  name        = "${lookup(var.records[count.index], "domain", null)}"
  description = "${lookup(var.records[count.index], "description", "")}"
  ttl         = "${lookup(var.records[count.index], "ttl", 3000)}"
  type        = "${lookup(var.records[count.index], "type", null)}"
  records     = ["${lookup(var.records[count.index], "value", null)}"]
}

