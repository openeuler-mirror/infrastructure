variable "loadbalancers" {
  type = list(map(string))
  description = "List of load banlancers"
  default     = []
}
