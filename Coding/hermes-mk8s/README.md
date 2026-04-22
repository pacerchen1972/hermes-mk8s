# hermes-mk8s

Deploy [Hermes Agent](https://hermes-agent.nousresearch.com/) on **IONOS Managed Kubernetes** (MK8s) in Worcester (`gb/bhx`), using **IONOS Private Container Registry** to store the image.

Hermes Agent is an autonomous, self-improving AI agent from Nous Research. It can integrate with Telegram, Discord, Slack, and other messaging platforms, and call external model APIs (IONOS AI Model Hub, OpenRouter, OpenAI, etc.).

This repository contains:
- **Terraform infrastructure as code** — provisions VDC, MK8s cluster, and container registry
- **Docker container** — multi-stage Dockerfile optimized for Hermes Agent
- **Kubernetes manifests** — namespace, PVC, ConfigMap, Secret, StatefulSet
- **Complete tutorial** — step-by-step guide to deploy Hermes on IONOS MK8s

## Architecture

```
Your Local Machine
      │
      ├─► Docker Build ──────► IONOS PCR
      │                        (Container Registry)
      │
      └─► kubectl Apply ──────► MK8s Cluster (gb/bhx Worcester)
                               ├── 3 Worker Nodes (2 vCPU, 16 GB each)
                               ├── Hermes Agent Pod (pulls from PCR)
                               └── 100 GB SSD Premium PVC
                                      │
                                      └─► External Model API
                                          (IONOS AI Model Hub,
                                           OpenRouter, OpenAI, etc.)
```

**Components:**

| Component | Details |
|---|---|
| **Datacenter** | IONOS Worcester (`gb/bhx`) — UK location opened Dec 2024 |
| **MK8s Cluster** | Managed Kubernetes, control plane hosted by IONOS |
| **Node Pool** | 3 worker nodes, 2 vCPU / 16 GB RAM each, 50 GB SSD root disk |
| **Container Registry** | IONOS Private Container Registry (PCR) for storing Hermes image |
| **Workload** | StatefulSet with 1 replica (Telegram long-polling, persistent memory) |
| **Storage** | 100 GB SSD Premium persistent volume (memories, skills, sessions, logs) |
| **Model Backend** | External API: IONOS AI Model Hub (Llama 3.3 70B), OpenRouter, OpenAI, etc. |
| **Messaging** | Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, SMS (optional integrations) |

## Repository Layout

```
hermes-mk8s/
├── README.md
├── Dockerfile                    # Multi-stage container image (python:3.12-slim-bookworm)
├── .dockerignore                 # Docker build exclusions
├── terraform/                    # Infrastructure as code (IONOS Terraform provider)
│   ├── versions.tf
│   ├── variables.tf
│   ├── main.tf                   # VDC + MK8s cluster + node pool + PCR
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── k8s/                          # Kubernetes manifests
│   ├── namespace.yaml
│   ├── pvc.yaml                  # 100 Gi SSD Premium persistent volume
│   ├── configmap.yaml            # Non-sensitive configuration
│   ├── secret.yaml               # (gitignored) API keys, model tokens
│   ├── secret.yaml.example       # Template for secret.yaml
│   ├── sealed-secret.yaml.example # (optional) Template for Sealed Secrets
│   ├── statefulset.yaml          # Hermes Agent workload (1 replica)
│   ├── pcr-pull-secret.yaml.example # Template for registry credentials
│   └── kustomization.yaml        # Kustomize bundle
└── docs/                         # Step-by-step tutorial
    ├── 01-prerequisites.md       # Tools, credentials, cost estimate
    ├── 02-infrastructure.md      # Provision infrastructure with Terraform
    ├── 03-container-image.md     # Build and push image to IONOS PCR
    ├── 04-deploy.md              # Deploy Hermes Agent to K8s
    └── 05-next-steps.md          # Production upgrades, integrations, troubleshooting
```

## Quick Start

Follow the **complete step-by-step tutorial** in the `docs/` folder:

1. **[Part 0 — Prerequisites](docs/01-prerequisites.md)** (5 min)
   - Check required tools (Terraform, kubectl, Docker)
   - Gather IONOS API token, username, model provider API key
   - Review cost estimate

2. **[Part 1 — Provision Infrastructure](docs/02-infrastructure.md)** (15 min)
   - Export IONOS credentials
   - Run `terraform init`, `terraform plan`, `terraform apply`
   - Get kubeconfig and verify kubectl access

3. **[Part 2 — Build and Push Container Image](docs/03-container-image.md)** (10 min)
   - Build Docker image: `docker build -t hermes-agent:latest .`
   - Push to IONOS PCR: `docker push <registry>/hermes/hermes-agent:latest`
   - Create Kubernetes pull secret for registry access

4. **[Part 3 — Deploy Hermes Agent](docs/04-deploy.md)** (5 min)
   - Configure API keys in `k8s/secret.yaml`
   - Apply manifests: `kubectl apply -k k8s/`
   - Verify pod is running and accessible

5. **[Part 4 — Next Steps](docs/05-next-steps.md)** (reference)
   - Optional: Telegram integration, IONOS Monitoring
   - Production upgrades: TLS Ingress, sealed-secrets
   - Scaling, upgrading, troubleshooting

---

## Usage (Summary)

```bash
# 1. Set credentials
export IONOS_TOKEN="your-token-here"

# 2. Provision infrastructure
cd terraform
terraform init
terraform plan
terraform apply
terraform output -raw kubeconfig > ~/.kube/hermes-mk8s.yaml
export KUBECONFIG=~/.kube/hermes-mk8s.yaml

# 3. Build and push container image
cd ..
docker build -t hermes-agent:latest .
docker tag hermes-agent:latest <REGISTRY_ENDPOINT>/hermes/hermes-agent:latest
docker login <REGISTRY_ENDPOINT> -u <IONOS_USERNAME> -p <IONOS_API_TOKEN>
docker push <REGISTRY_ENDPOINT>/hermes/hermes-agent:latest

# 4. Create Kubernetes pull secret
kubectl create secret docker-registry ionos-pcr-secret \
  --namespace hermes \
  --docker-server=<REGISTRY_ENDPOINT> \
  --docker-username=<IONOS_USERNAME> \
  --docker-password=<IONOS_API_TOKEN>

# 5. Update secrets and deploy
nano k8s/secret.yaml  # Add your API keys
nano k8s/statefulset.yaml  # Update registry endpoint
kubectl apply -k k8s/
kubectl get pods -n hermes -w

# 6. Access Hermes
kubectl port-forward -n hermes pod/hermes-agent-0 8642:8642
curl http://localhost:8642/
```

---

## Teardown

To delete all infrastructure and stop incurring charges:

```bash
cd terraform
terraform destroy
```

---

## Key Files

| File | Purpose |
|---|---|
| `Dockerfile` | Multi-stage build: python:3.12-slim-bookworm → Hermes Agent + deps → minimal runtime (non-root user, ~250 MB) |
| `terraform/main.tf` | Defines VDC, MK8s cluster, node pool (3 × 2vCPU/16GB), and IONOS PCR |
| `k8s/statefulset.yaml` | Deploys Hermes Agent: 1 replica, persistent volume (/opt/data), gateway mode (port 8642) |
| `k8s/secret.yaml` | API keys, model endpoint URL (base64-encoded, gitignored) |

---

## Credentials Needed

| Credential | How to Obtain |
|---|---|
| IONOS API Token | https://cloud.ionos.co.uk → Manage → Settings → API Tokens |
| IONOS Username | Your IONOS account email |
| Model Provider API Key | IONOS AI Model Hub, OpenRouter, or OpenAI |
| Telegram Bot Token (optional) | Telegram @BotFather → `/newbot` |
