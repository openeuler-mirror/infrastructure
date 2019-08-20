resource "huaweicloud_cce_cluster_v3" "this" {
     name = "${var.name}"
     cluster_type= "VirtualMachine"
     flavor_id= "${var.flavor_id}"
     vpc_id= "${var.vpc_id}"
     subnet_id= "${var.subnet_id}"
     container_network_type= "overlay_l2"
     authentication_mode = "rbac"
     description= "${var.description}"
}

resource "huaweicloud_cce_node_v3" "this" {
    count = "${length(var.nodes)}"
    cluster_id= "${join("",huaweicloud_cce_cluster_v3.this.*.id)}"
    name = "${lookup(var.nodes[count.index], "name")}"
    flavor_id="${lookup(var.nodes[count.index], "flavor_id")}"
    iptype="5_bgp"
    availability_zone= "${lookup(var.nodes[count.index], "az")}"
    key_pair="${lookup(var.nodes[count.index], "ssh_key")}"
    root_volume {
     size= 40
     volumetype= "SATA"
    }
    sharetype= "PER"
    bandwidth_size= 100
    data_volumes {
      size= 100
      volumetype= "SATA"
    }
}
