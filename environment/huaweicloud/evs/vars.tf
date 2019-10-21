variable "volumes" {
  type        = list(map(string))
  description = "List of volumes"
  default     = []
}


variable "vol_attaches" {
  type        = list(map(string))
  description = "List of attaches"
  default     = []
}

