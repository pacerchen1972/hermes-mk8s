# Part 1 — Provision Infrastructure with Terraform

You will now provision the IONOS infrastructure: a Virtual Data Center (VDC), Managed Kubernetes cluster with 3 worker nodes, and a Private Container Registry.

Provisioning takes **10–15 minutes**.

---

## Step 1 — Export Your IONOS API Token

Terraform needs your API token to authenticate with IONOS Cloud.

```bash
export IONOS_TOKEN="your-api-token-here"
```

Verify the token is set:

```bash
echo $IONOS_TOKEN
```

Expected output:
```
your-api-token-here
```

---

## Step 2 — Navigate to the Terraform Directory

```bash
cd terraform
```

---

## Step 3 — Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully configured!
```

---

## Step 4 — Create a Terraform Variables File

Copy the example variables file and adjust location if needed:

```bash
cp terraform.tfvars.example terraform.tfvars
```

The default values point to **Worcester (`gb/bhx`)** and provision:
- 3 worker nodes (2 vCPU, 16 GB RAM each)
- 50 GB SSD root disk per node
- Kubernetes 1.33.3

You can edit `terraform.tfvars` to customize any values:

```bash
nano terraform.tfvars
```

---

## Step 5 — Preview the Infrastructure

```bash
terraform plan
```

This shows all resources that will be created without actually creating them.

Expected output:
```
Plan: 4 to add, 0 to change, 0 to destroy.
```

The 4 resources are:
1. `ionoscloud_datacenter.this` — VDC named `hermes-vdc`
2. `ionoscloud_k8s_cluster.this` — MK8s cluster named `hermes-cluster`
3. `ionoscloud_k8s_node_pool.this` — Node pool with 3 nodes
4. `ionoscloud_container_registry.this` — Private registry named `hermes-registry`

---

## Step 6 — Apply the Configuration

```bash
terraform apply
```

Terraform will prompt:
```
Do you want to perform these actions?
```

Type `yes` to confirm.

Provisioning begins. This takes **10–15 minutes**. Monitor progress in the IONOS Cloud Panel:

1. Go to https://cloud.ionos.co.uk
2. Navigate to **Compute → Managed Kubernetes**
3. Watch the cluster status change from `Deploying` → `Active`

When complete, you will see:

```
Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

cluster_id = "abc123def456"
cluster_name = "hermes-cluster"
datacenter_id = "def456abc123"
node_pool_id = "ghi789jkl012"
registry_endpoint = "registry.cloud.ionos.com"
registry_name = "hermes-registry"
```

---

## Step 7 — Connect kubectl to Your Cluster

Export the kubeconfig so kubectl can connect:

```bash
terraform output -raw kubeconfig > ~/.kube/hermes-mk8s.yaml
```

Set the kubeconfig path:

```bash
export KUBECONFIG=~/.kube/hermes-mk8s.yaml
```

Verify kubectl can reach the cluster:

```bash
kubectl cluster-info
```

Expected output:
```
Kubernetes control plane is running at https://abc123.ionos.cloud:6443
```

---

## What Was Created

Your IONOS Cloud infrastructure now includes:

```
hermes-vdc (Virtual Data Center)
├── hermes-cluster (Managed Kubernetes)
│   └── hermes-pool (Node Pool)
│       ├── hermes-pool-x1wk (Node 1: 2 vCPU, 16 GB, 50 GB SSD)
│       ├── hermes-pool-x2km (Node 2: 2 vCPU, 16 GB, 50 GB SSD)
│       └── hermes-pool-x3pq (Node 3: 2 vCPU, 16 GB, 50 GB SSD)
└── hermes-registry (Container Registry)
```

All resources are in the Worcester datacenter (`gb/bhx`).

---

## Troubleshooting

**"API token invalid"**
- Ensure `IONOS_TOKEN` is set: `echo $IONOS_TOKEN`
- Verify the token hasn't expired (create a new one if unsure)

**"Quota exceeded"**
- Your account may lack sufficient quotas for MK8s or PCR
- Check https://cloud.ionos.co.uk → **Account → Quotas**

**"Cluster stuck in Deploying"**
- Wait up to 20 minutes for provisioning to complete
- If still stuck, contact IONOS Support

---

→ Continue to **[03-container-image.md](03-container-image.md)**
