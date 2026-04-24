locals {
  name = var.project_name
  tags = {
    project = "hermes-mk8s"
    managed = "terraform"
    owner   = "rdelarrea"
  }
}

# Virtual Data Center — hosts the MK8s node pool VMs.
# (The MK8s control plane is managed by IONOS; only worker nodes live in a VDC.)
resource "ionoscloud_datacenter" "this" {
  name        = "${local.name}-vdc"
  location    = var.location
  description = "VDC for Hermes Agent on MK8s"
}

# MK8s cluster (managed control plane).
resource "ionoscloud_k8s_cluster" "this" {
  name       = "${local.name}-cluster"
  k8s_version = var.k8s_version

  maintenance_window {
    day_of_the_week = var.maintenance_day
    time            = var.maintenance_time
  }
}

# Worker node pool — 3 × (2 vCPU, 16 GB RAM, SSD root disk).
resource "ionoscloud_k8s_node_pool" "this" {
  name              = "${local.name}-pool"
  k8s_cluster_id    = ionoscloud_k8s_cluster.this.id
  datacenter_id     = ionoscloud_datacenter.this.id
  k8s_version       = ionoscloud_k8s_cluster.this.k8s_version
  node_count        = var.node_count
  cores_count       = var.node_cores
  ram_size          = var.node_ram_mb
  availability_zone = "AUTO"
  storage_type      = var.node_root_disk_type
  storage_size      = var.node_root_disk_gb
  cpu_family        = var.cpu_family

  maintenance_window {
    day_of_the_week = var.maintenance_day
    time            = var.node_maintenance_time
  }

  labels = {
    workload = "hermes"
    env      = "lab"
  }
}

# Private Container Registry — stores the Hermes Agent image for K8s nodes to pull.
resource "ionoscloud_container_registry" "this" {
  name     = "${local.name}-registry"
  location = var.registry_location

  garbage_collection_schedule {
    days = ["Saturday"]
    time = "04:00:00+00:00"
  }
}
