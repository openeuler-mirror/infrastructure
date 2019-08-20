variable "name" {
  description = "The name of the cluster"
  default     = "test"
}


variable "description" {
  description = "The description of the cluster"
  default     = "This is cce cluster"
}


variable "flavor_id" {
  description = "The flavor id of the cluster"
  default     = "cce.s1.large"
}


variable "vpc_id" {
  description = "The vpc id that cluster in"
  default     = ""
}


variable "subnet_id" {
  description = "The subnet id that cluster in"
  default     = ""
}

variable "nodes" {
  type = list(map(string))
  description = "List of cluster node"
  default     = []
}
