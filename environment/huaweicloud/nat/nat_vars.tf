variable "name" {
  description = "The name of the nat"
  default     = "nat_default"
}

variable "description" {
  description = "The description of the nat"
  default     = "this is the default nat"
}

variable "spec_code" {
  description = "The spec code of the nat"
  default     = "3"
}

variable "router_id" {
  description = "the vpc id of the nat"
}

variable "network_id" {
  description = "the network id of the nat"
}

variable "rules" {
  type = list(map(string))
  description = "List of rules in the nat"
  default     = []
}
