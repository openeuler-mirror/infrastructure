variable "eips" {
  type = list(map(string))
  description = "List of eips"
  default     = []
}


variable "bandwidths" {
  type = list(map(string))
  description = "List of bandwidths"
  default    = []
}
