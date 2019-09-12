output "this_elb_ids" {
  description = "List of IDs of the elbs"
  value       = "${join(",",huaweicloud_lb_loadbalancer_v2.this.*.id)}"
}

output "this_port_ids" {
  description = "List of the port ids of all elbs"
  value       = "${join(",",huaweicloud_lb_loadbalancer_v2.this.*.vip_port_id)}"
}
