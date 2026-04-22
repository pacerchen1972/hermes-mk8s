# Part 2 — Build and Push the Container Image to IONOS PCR

You will now build a Docker image containing Hermes Agent, push it to your IONOS Private Container Registry, and create the Kubernetes secret for registry authentication.

Building and pushing takes **5–10 minutes** (depends on network speed and image size).

---

## Step 1 — Get Your Registry Endpoint

From the Terraform output, retrieve your container registry hostname:

```bash
terraform output -raw registry_endpoint
```

Expected output:
```
registry.cloud.ionos.com
```

Save this value for the next steps. From now on, replace `<REGISTRY_ENDPOINT>` with this value.

---

## Step 2 — Build the Hermes Agent Docker Image

Navigate to the repository root (where the Dockerfile is):

```bash
cd ..
```

Build the image locally:

```bash
docker build -t hermes-agent:latest .
```

This runs a multi-stage build:
- **Stage 1** (builder): Creates a temporary image with Python 3.12, uv, and Hermes Agent dependencies
- **Stage 2** (runtime): Extracts the compiled packages into a minimal image (~250 MB)

Expected output:
```
[+] Building 3.2s
...
=> exporting to image
=> => exporting layers
=> => writing image sha256:abc123def456
=> => naming to docker.io/library/hermes-agent:latest
Successfully tagged hermes-agent:latest
```

Verify the image was created:

```bash
docker image ls | grep hermes-agent
```

Expected output:
```
hermes-agent   latest   abc123def456   1 minute ago   247 MB
```

---

## Step 3 — Tag the Image for IONOS PCR

Create a tag that points to your IONOS Container Registry:

```bash
docker tag hermes-agent:latest <REGISTRY_ENDPOINT>/hermes/hermes-agent:latest
```

Replace `<REGISTRY_ENDPOINT>` with your registry endpoint from Step 1.

Example:
```bash
docker tag hermes-agent:latest registry.cloud.ionos.com/hermes/hermes-agent:latest
```

---

## Step 4 — Log In to IONOS Container Registry

Authenticate Docker with IONOS PCR using your IONOS username (email) and API token:

```bash
docker login <REGISTRY_ENDPOINT> -u <IONOS_USERNAME> -p <IONOS_API_TOKEN>
```

Replace placeholders:
- `<REGISTRY_ENDPOINT>` — your registry endpoint (e.g., `registry.cloud.ionos.com`)
- `<IONOS_USERNAME>` — your IONOS email (e.g., `rdelarrearemiro@ionos.com`)
- `<IONOS_API_TOKEN>` — your IONOS API token (from prerequisites)

Example:
```bash
docker login registry.cloud.ionos.com -u rdelarrearemiro@ionos.com -p "your-ionos-api-token"
```

Expected output:
```
Login Succeeded
```

---

## Step 5 — Push the Image to IONOS PCR

```bash
docker push <REGISTRY_ENDPOINT>/hermes/hermes-agent:latest
```

Example:
```bash
docker push registry.cloud.ionos.com/hermes/hermes-agent:latest
```

This uploads the image to your private registry. Depending on network speed, this takes **2–5 minutes**.

Expected output:
```
The push refers to repository [registry.cloud.ionos.com/hermes/hermes-agent]
Pushing layer abc123...
Pushing layer def456...
...
latest: digest sha256:xyz789 size 67891234
```

Verify the image is in the registry:

```bash
docker images --digests
```

---

## Step 6 — Create the Kubernetes Pull Secret

Kubernetes nodes need credentials to pull the image from your private registry. Create the secret:

```bash
kubectl create secret docker-registry ionos-pcr-secret \
  --namespace hermes \
  --docker-server=<REGISTRY_ENDPOINT> \
  --docker-username=<IONOS_USERNAME> \
  --docker-password=<IONOS_API_TOKEN>
```

Replace the placeholders with your actual values.

Example:
```bash
kubectl create secret docker-registry ionos-pcr-secret \
  --namespace hermes \
  --docker-server=registry.cloud.ionos.com \
  --docker-username=rdelarrearemiro@ionos.com \
  --docker-password="your-ionos-api-token"
```

> **Note:** The secret is created in the `hermes` namespace, which will be created in the next part.

Expected output:
```
secret/ionos-pcr-secret created
```

Verify the secret was created:

```bash
kubectl get secrets -n hermes
```

Expected output:
```
NAME                  TYPE                             DATA   AGE
ionos-pcr-secret      kubernetes.io/dockercfg          1      10s
```

---

## What Was Built and Pushed

Your container image is now stored in IONOS PCR:

```
IONOS Private Container Registry
└── hermes-agent:latest (247 MB)
    ├── Python 3.12-slim-bookworm runtime
    ├── Hermes Agent package
    ├── All Python dependencies
    └── Non-root user (uid 1001)
```

And your Kubernetes cluster can now authenticate with the registry via the `ionos-pcr-secret`.

---

## Troubleshooting

**"docker login: Invalid username, password, or token"**
- Double-check your IONOS email (username) and API token
- Verify the API token hasn't expired

**"denied: Your account is not able to push to this namespace"**
- Confirm that Container Registry is enabled for your IONOS account
- Check permissions in the IONOS Cloud Panel

**"Failed to pull image: ImagePullBackOff"**
- This error occurs in the next part if the registry endpoint in the StatefulSet doesn't match your actual registry
- Verify you updated the image reference correctly

---

→ Continue to **[04-deploy.md](04-deploy.md)**
