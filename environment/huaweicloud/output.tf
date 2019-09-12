output "cce_clusters" {
    value = "${module.cce.clusters}"
}

output "cce_users" {
    value = "${module.cce.users}"
}

output "exim4_elb_id" {
    value = "${length(split(",", module.elb.this_elb_ids)) > 1 ? split(",", module.elb.this_elb_ids)[1] : null}"
}

output "web_elb_id"  {
    value = "${length(split(",", module.elb.this_elb_ids)) > 0 ? split(",", module.elb.this_elb_ids)[0] : null}"
}

output "exim4_eip" {
    value = "${length(split(",", module.internet.this_eip_addresses)) > 1? split(",", module.internet.this_eip_addresses)[2] : null}"
}

output "web_eip" {
    value = "${length(split(",", module.internet.this_eip_addresses)) > 0 ? split(",", module.internet.this_eip_addresses)[1] : null}"
}


output "exim4_domain" {
    value = "${var.sub_domain_mail}.${var.domain}"
}

output "web_domain" {
    value = "${var.sub_domain_web}.${var.domain}"
}

output "dkim_selector" {
   value = "${var.selector}"
}

