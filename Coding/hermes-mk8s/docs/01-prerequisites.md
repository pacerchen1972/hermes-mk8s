# Part 0 — Prerequisites

Before you deploy Hermes Agent on IONOS Managed Kubernetes, ensure you have the required tools, credentials, and IONOS account permissions.

---

## Required Tools

You need the following CLI tools installed on your local machine:

| Tool | Version | Install |
|---|---|---|
| Terraform | ≥ 1.5.0 | [terraform.io/downloads](https://www.terraform.io/downloads.html) |
| kubectl | ≥ 1.28 | [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools/) |
| Docker | ≥ 24.0 | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop) |
| ionosctl | ≥ 0.9.0 | [ionos.com/docs/cli](https://docs.ionos.com/cli) (optional, for verification) |

---

## IONOS Account Requirements

You must have an IONOS Cloud account with:
- **Managed Kubernetes (MK8s) enabled** — available in most cloud regions
- **Container Registry (PCR) enabled** — required for storing the Hermes Agent image
- **UK datacenter access** — specifically the Worcester location (`gb/bhx`)

Verify your account permissions in the [IONOS Cloud Panel](https://cloud.ionos.co.uk):
1. Go to **Manage → Authorizations**
2. Confirm that both **Managed Kubernetes** and **Container Registry** are listed

---

## Required Credentials

You will need three credentials to complete this tutorial:

### 1. IONOS API Token

Required for Terraform to provision your infrastructure.

1. Sign in to [IONOS Cloud](https://cloud.ionos.co.uk)
2. Go to **Manage → Settings → API Tokens**
3. Click **Create API Token**
4. Copy the token (you can only see it once)
5. Store safely: `export IONOS_TOKEN="your-token-here"`

### 2. IONOS Username (Email)

Your IONOS account email — used for Docker registry authentication and kubectl secret creation.

Example: `rdelarrearemiro@ionos.com`

### 3. Model Provider API Key

Hermes Agent calls an external model API. Choose one:

**Option A: IONOS AI Model Hub** (recommended)
- Get a Studio token from: https://cloud.ionos.co.uk/ai-model-hub
- Provides access to Llama 3.3 70B and other models
- **Endpoint:** `https://api.models.ionos.cloud/v1`

**Option B: OpenRouter** (alternative)
- Sign up at: https://openrouter.ai
- Supports 200+ models with easy pay-as-you-go pricing
- **Endpoint:** `https://openrouter.ai/api/v1`

**Option C: OpenAI** (if you have existing credits)
- Get API key from: https://platform.openai.com/account/api-keys
- **Endpoint:** `https://api.openai.com/v1`

---

## Cost Estimate

Running Hermes Agent on IONOS Managed Kubernetes for one week in the Worcester datacenter:

| Resource | Cost/Month | Cost/Week |
|---|---|---|
| MK8s cluster (3-node, 2 vCPU/16 GB each) | ~€180 | ~€41 |
| SSD Premium storage (100 Gi) | ~€25 | ~€6 |
| Container Registry storage | ~€5–10 | ~€1–2 |
| **Total** | **~€210–220** | **~€48–49** |

**Teardown:** After completing this tutorial, run `terraform destroy` to avoid ongoing charges.

---

## Before You Start

Make a checklist:

- [ ] Terraform installed and working (`terraform --version`)
- [ ] kubectl installed and working (`kubectl version --client`)
- [ ] Docker installed and running (`docker --version`)
- [ ] IONOS API token exported (`echo $IONOS_TOKEN`)
- [ ] IONOS username (email) ready
- [ ] Model provider API key ready
- [ ] Git cloned this repository
- [ ] Read this README and understand the architecture

---

→ Continue to **[02-infrastructure.md](02-infrastructure.md)**
