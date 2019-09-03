variable "domain" {
  description = "The domain name of this dns"
}

variable "email" {
  description = "The manager's email"
}

variable "ttl" {
  description = "The ttl time"
  default = 3000
}  

variable "type" {
  description = "The DNS type, the value would be public or private"
  default = "public"
}

variable "description" {
  description = "The dns description string"
  default = ""
}

variable "records" {
  type = list(map(string))
  description = "List of each dns records"
  default = []
}

variable "ptrs" {
  type = list(map(string))
  description = "List of ptr records"
  default     = []
}
