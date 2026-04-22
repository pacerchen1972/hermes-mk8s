# Part 3 — Deploy Hermes Agent to Kubernetes

You will now deploy Hermes Agent to your IONOS Managed Kubernetes cluster using kubectl and Kustomize. The deployment includes the namespace, persistent storage, configuration, secrets, and the StatefulSet running Hermes.

Deployment takes **2–3 minutes** (including pod startup time).

---

## Step 1 — Prepare the Secret

The `k8s/secret.yaml` file contains placeholder values. You must replace them with your actual credentials before applying.

Open the secret file:

```bash
nano k8s/secret.yaml
```

Replace the base64-encoded placeholders with your credentials:

```yaml
HERMES_API_KEY: "your-api-key-base64-encoded"
HERMES_MODEL_BASE_URL: "your-endpoint-base64-encoded"
```

To encode a value in base64:

```bash
echo -n "your-value" | base64
```

Example — encode your IONOS AI Model Hub token:

```bash
echo -n "ionos-ai-model-hub-token-abc123" | base64
```

Output:
```
aW9ub3MtYWktbW9kZWwtaHViLXRva2VuLWFiYzEyMw==
```

Update the `HERMES_API_KEY` field with this encoded value.

For `HERMES_MODEL_BASE_URL`, use the model provider endpoint:

```bash
echo -n "https://api.models.ionos.cloud/v1" | base64
```

Output:
```
aHR0cHM6Ly9hcGkubW9kZWxzLmlvbm9zLmNvbS92MQ==
```

Save and close the file after editing.

---

## Step 2 — Update the StatefulSet with Your Registry Endpoint

The StatefulSet references a placeholder for the registry endpoint. Update it with your actual endpoint.

Open the StatefulSet:

```bash
nano k8s/statefulset.yaml
```

Find the line:
```yaml
image: "{{ REGISTRY_ENDPOINT }}/hermes/hermes-agent:latest"
```

Replace `{{ REGISTRY_ENDPOINT }}` with your registry endpoint from part 2.

Example (if your endpoint is `registry.cloud.ionos.com`):
```yaml
image: "registry.cloud.ionos.com/hermes/hermes-agent:latest"
```

Save and close the file.

---

## Step 3 — Deploy with Kustomize

Deploy all resources (namespace, PVC, ConfigMap, Secret, StatefulSet) using Kustomize:

```bash
kubectl apply -k k8s/
```

This reads `k8s/kustomization.yaml` and applies all listed resources.

Expected output:
```
namespace/hermes created
persistentvolumeclaim/hermes-data created
configmap/hermes-config created
secret/hermes-secrets created
statefulset.apps/hermes-agent created
```

---

## Step 4 — Verify the Pod Is Running

Check the status of the Hermes Agent pod:

```bash
kubectl get pods -n hermes
```

Expected output (immediately after deployment):
```
NAME            READY   STATUS            RESTARTS   AGE
hermes-agent-0  0/1     ContainerCreating  0          5s
```

Wait for the pod to become `Ready`:

```bash
kubectl get pods -n hermes --watch
```

Press `Ctrl+C` to stop watching. Expected final output:
```
NAME            READY   STATUS    RESTARTS   AGE
hermes-agent-0  1/1     Running   0          45s
```

---

## Step 5 — Check the Pod Logs

Verify Hermes Agent started successfully:

```bash
kubectl logs -n hermes -l app=hermes-agent --follow
```

Expected output:
```
Starting Hermes Agent v0.10.0 in gateway mode...
Gateway listening on 0.0.0.0:8642
Ready to receive requests.
```

Press `Ctrl+C` to stop following logs.

---

## Step 6 — Verify Persistent Storage

Check that the PVC is bound and the pod's volume is mounted:

```bash
kubectl get pvc -n hermes
```

Expected output:
```
NAME                                     STATUS   VOLUME                 CAPACITY   ACCESS MODES
hermes-data-hermes-agent-0               Bound    pvc-abc123def456       100Gi      RWO
```

---

## Step 7 — Access the Gateway

Hermes Agent is running inside the cluster on port 8642. To access it locally, use kubectl port-forwarding:

```bash
kubectl port-forward -n hermes pod/hermes-agent-0 8642:8642
```

Expected output:
```
Forwarding from 127.0.0.1:8642 -> 8642
Forwarding from [::1]:8642 -> 8642
```

In another terminal, test the gateway:

```bash
curl http://localhost:8642/health
```

Expected output (if `/health` endpoint exists):
```json
{"status": "healthy", "version": "0.10.0"}
```

Or if Hermes doesn't expose `/health`, you can test with:

```bash
curl http://localhost:8642/
```

Keep the port-forward running if you want to interact with Hermes. Press `Ctrl+C` to stop port-forwarding.

---

## What Was Deployed

Your Kubernetes cluster now runs Hermes Agent with the following resources:

```
hermes (Namespace)
├── hermes-data-hermes-agent-0 (PersistentVolumeClaim, 100 Gi SSD)
├── hermes-config (ConfigMap)
│   ├── HERMES_DATA_DIR
│   ├── HERMES_PORT
│   ├── HERMES_LOG_LEVEL
│   └── ...
├── hermes-secrets (Secret)
│   ├── HERMES_API_KEY
│   ├── HERMES_MODEL_BASE_URL
│   └── TELEGRAM_BOT_TOKEN (optional)
└── hermes-agent (StatefulSet)
    └── hermes-agent-0 (Pod)
        ├── Image: registry.cloud.ionos.com/hermes/hermes-agent:latest
        ├── Port: 8642 (gateway)
        └── Volume: /opt/data (mounted to PVC)
```

---

## Troubleshooting

**"ImagePullBackOff" error**
```bash
kubectl describe pod -n hermes hermes-agent-0
```
Check if the error message mentions authentication. Ensure the registry endpoint in `statefulset.yaml` is correct and the `ionos-pcr-secret` exists:
```bash
kubectl get secrets -n hermes
```

**"CrashLoopBackOff" error**
```bash
kubectl logs -n hermes hermes-agent-0
```
Check the logs for startup errors (missing API keys, invalid configuration, etc.).

**"Pending" pod (waiting for PVC)**
```bash
kubectl describe pvc -n hermes hermes-data-hermes-agent-0
```
Ensure your cluster has a `ionos-enterprise-ssd` storage class:
```bash
kubectl get storageclass
```

**"ConnectionRefused" when accessing gateway**
- Ensure port-forwarding is active
- Verify the pod is `Running` and `Ready`
- Check logs for startup errors

---

→ Continue to **[05-next-steps.md](05-next-steps.md)**
