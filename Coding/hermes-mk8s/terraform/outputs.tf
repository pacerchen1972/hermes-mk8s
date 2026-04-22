data "ionoscloud_k8s_cluster" "this" {
  id = ionoscloud_k8s_cluster.this.id
  depends_on = [ionoscloud_k8s_node_pool.this]
}

output "cluster_id" {
  description = "MK8s cluster ID."
  value       = ionoscloud_k8s_cluster.this.id
}

output "cluster_name" {
  description = "MK8s cluster name."
  value       = ionoscloud_k8s_cluster.this.name
}

output "datacenter_id" {
  description = "VDC ID hosting the node pool."
  value       = ionoscloud_datacenter.this.id
}

output "node_pool_id" {
  description = "Node pool ID."
  value       = ionoscloud_k8s_node_pool.this.id
}

output "kubeconfig" {
  description = "Kubeconfig for the new cluster. Pipe to ~/.kube/hermes-mk8s.yaml."
  value       = data.ionoscloud_k8s_cluster.this.kube_config
  sensitive   = true
}

output "registry_endpoint" {
  description = "IONOS Container Registry endpoint for pushing/pulling the Hermes Agent image."
  value       = ionoscloud_container_registry.this.hostname
}

output "registry_name" {
  description = "Container registry name."
  value       = ionoscloud_container_registry.this.name
}
