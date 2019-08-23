variable "eips" {
  type = list(map(string))
  description = "List of eips"
  default     = []
}
