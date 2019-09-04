output "clusters_1" {
  description = "The first cluster information"
  value       = "${
    map(
      "name", "${huaweicloud_cce_cluster_v3.this.certificate_clusters.0.name}",
      "server", "${huaweicloud_cce_cluster_v3.this.certificate_clusters.0.server}",
      "certificate_authority",  "${huaweicloud_cce_cluster_v3.this.certificate_clusters.0.certificate_authority_data}"
    )
  }"
}

output "users_1" {
  description = "List first user infomation"
  value       = "${
    map(
      "name", "${huaweicloud_cce_cluster_v3.this.certificate_users.0.name}",
      "client_certificate", "${huaweicloud_cce_cluster_v3.this.certificate_users.0.client_certificate_data}",
      "client_key",  "${huaweicloud_cce_cluster_v3.this.certificate_users.0.client_key_data}"
    )
  }"
}


output "clusters" {
  description = "List the clusters"
  value = "${huaweicloud_cce_cluster_v3.this.certificate_clusters}"
}


output "users" {
  description = "List the users information"
  value = "${huaweicloud_cce_cluster_v3.this.certificate_users}"
}
