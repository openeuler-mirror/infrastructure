output "this_server_ids" {
  description = "List of IDs of the servers"
  value       = "${join(",", huaweicloud_compute_instance_v2.this.*.id)}"
}


output "this_server_ips" {
  description = "List of the ips of the servers"
  value       = "${join(",", huaweicloud_compute_instance_v2.this.*.access_ip_v4)}"
}
