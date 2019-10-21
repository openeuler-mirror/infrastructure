output "this_volume_ids" {
  description = "List of IDs of the volumes"
  value       = "${join(",", huaweicloud_blockstorage_volume_v2.this.*.id)}"
}
