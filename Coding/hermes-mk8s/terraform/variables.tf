variable "project_name" {
  description = "Short name used as prefix for all resources."
  type        = string
  default     = "hermes"
}

variable "location" {
  description = "IONOS location for the datacenter and node pool (gb/bhx = Worcester, UK)."
  type        = string
  default     = "gb/bhx"
}

variable "k8s_version" {
  description = "Kubernetes version for the MK8s cluster. Check supported versions with: ionosctl k8s version list"
  type        = string
  default     = "1.31.2"
}

variable "node_count" {
  description = "Number of worker nodes in the node pool."
  type        = number
  default     = 3
}

variable "node_cores" {
  description = "vCPU cores per node."
  type        = number
  default     = 2
}

variable "node_ram_mb" {
  description = "RAM per node in MB. 16 GB = 16384."
  type        = number
  default     = 16384
}

variable "node_root_disk_gb" {
  description = "Root disk size per node in GB (OS + container runtime). The 100 GB SSD Premium PVC for Hermes state is separate."
  type        = number
  default     = 50
}

variable "node_root_disk_type" {
  description = "Root disk type for worker nodes: SSD or HDD."
  type        = string
  default     = "SSD"
}

variable "cpu_family" {
  description = "CPU family for node pool. For gb/bhx (Worcester), INTEL_SKYLAKE or INTEL_ICELAKE are typical. Leave empty to let IONOS pick a default."
  type        = string
  default     = "INTEL_SKYLAKE"
}

variable "maintenance_day" {
  description = "Day of week for cluster/node pool maintenance window (e.g. Monday)."
  type        = string
  default     = "Sunday"
}

variable "maintenance_time" {
  description = "Start time (UTC) for maintenance window, HH:MM:SSZ."
  type        = string
  default     = "03:00:00Z"
}

variable "node_maintenance_time" {
  description = "Start time (UTC) for node pool maintenance window. Must differ from cluster maintenance_time."
  type        = string
  default     = "04:00:00Z"
}
