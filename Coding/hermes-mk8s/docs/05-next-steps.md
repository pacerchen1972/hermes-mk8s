# Part 4 — Next Steps: Production Upgrades and Integrations

Congratulations! You have a working Hermes Agent deployment on IONOS Managed Kubernetes. This section covers production-ready enhancements and optional integrations.

---

## Telegram Bot Integration

To integrate Hermes with Telegram, you need a Telegram bot token.

### Step 1 — Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Choose a bot name (e.g., "My Hermes Agent")
4. BotFather will give you a **token** (e.g., `1234567890:ABCDefGhIjKlMnOpQrStUvWxYz...`)

### Step 2 — Update the Secret

Add the token to `k8s/secret.yaml`:

```yaml
TELEGRAM_BOT_TOKEN: "base64-encoded-token-here"
```

Encode the token:

```bash
echo -n "1234567890:ABCDefGhIjKlMnOpQrStUvWxYz..." | base64
```

Update the secret and re-deploy:

```bash
kubectl apply -f k8s/secret.yaml
kubectl delete pod -n hermes hermes-agent-0
```

The pod will restart with the Telegram token loaded.

### Step 3 — Start Your Bot

1. Find your bot on Telegram (search by the name you gave @BotFather)
2. Send `/start`
3. Hermes Agent should respond — it's now connected to Telegram!

---

## IONOS AI Model Hub as Backend

The `HERMES_MODEL_BASE_URL` in your secret points to a model provider. IONOS AI Model Hub provides access to Llama 3.3 70B and other models.

### Verify Your Endpoint

If you're using IONOS AI Model Hub, confirm the endpoint in your secret:

```bash
kubectl get secret -n hermes hermes-secrets -o jsonpath='{.data.HERMES_MODEL_BASE_URL}' | base64 -d
```

Expected output:
```
https://api.models.ionos.cloud/v1
```

### Model Selection

Once Hermes is running with AI Model Hub, you can configure which model to use. Check the Hermes Agent documentation for model names and pricing:
- https://hermes-agent.nousresearch.com/docs/
- https://cloud.ionos.co.uk/ai-model-hub

---

## TLS Ingress (HTTPs)

Currently, Hermes is only accessible via `localhost:8642` (port-forward). For production, expose it securely via HTTPS using Ingress.

### Install ingress-nginx

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/cloud/deploy.yaml
```

### Install cert-manager

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml
```

### Create a ClusterIssuer

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

### Create an Ingress

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hermes-ingress
  namespace: hermes
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - hermes.yourdomain.com
      secretName: hermes-tls
  rules:
    - host: hermes.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: hermes-agent
                port:
                  number: 8642
EOF
```

Replace `hermes.yourdomain.com` with your actual domain and point DNS to the LoadBalancer IP:

```bash
kubectl get svc -n ingress-nginx
```

---

## IONOS Monitoring with Grafana

Monitor your Hermes deployment using IONOS Managed Prometheus and Grafana.

### Create Prometheus Secret

```bash
kubectl create secret generic ionos-remote-write \
  --namespace monitoring \
  --from-literal=username=<your-ionos-username> \
  --from-literal=password=<your-ionos-api-token>
```

### Deploy Grafana Alloy

```bash
kubectl apply -f https://raw.githubusercontent.com/grafana/alloy/main/example/kubernetes.yaml
```

Configure Alloy to scrape Hermes metrics and write to IONOS Prometheus.

---

## Why StatefulSet Is at 1 Replica

You may wonder why the deployment uses a `StatefulSet` with only **1 replica** instead of a `Deployment` with multiple replicas for high availability.

**Reasons:**

| Consideration | Implication |
|---|---|
| **Telegram long-polling** | Telegram bot uses long-polling (not webhooks). Multiple replicas would each poll independently, causing duplicate messages. |
| **Shared persistent memory** | Hermes stores memories (skills, user models, sessions) on disk. Multiple replicas need a shared storage backend (NFS, Redis) which adds complexity. |
| **Stateful agent identity** | The agent maintains conversations per user — a consistent pod identity (`hermes-agent-0`) is valuable for users. |

**For high availability:**
- Use a Kubernetes backup/restore strategy (Velero)
- Implement multi-region failover with Terraform-managed secondary clusters
- Use Telegram webhooks (if supported) instead of long-polling

---

## Scaling to Multiple Replicas (Advanced)

If you need horizontal scaling:

1. **Replace Telegram long-polling with webhooks** (if available)
2. **Add a shared Redis instance** in your VDC for cross-replica memory
3. **Update ConfigMap** to point to Redis
4. **Change StatefulSet replicas** from 1 to N

Example Redis backing for Hermes Agent:

```yaml
HERMES_REDIS_URL: "redis://hermes-redis:6379/0"
```

---

## Upgrade Hermes Agent

To upgrade Hermes Agent to a new version:

### Step 1 — Build the New Image

```bash
# Pull the new Dockerfile from GitHub (or use the one in your repo)
docker build -t hermes-agent:v0.11.0 .
```

### Step 2 — Push to IONOS PCR

```bash
docker tag hermes-agent:v0.11.0 <REGISTRY_ENDPOINT>/hermes/hermes-agent:v0.11.0
docker push <REGISTRY_ENDPOINT>/hermes/hermes-agent:v0.11.0
```

### Step 3 — Update StatefulSet

Edit `k8s/statefulset.yaml` and change the image tag from `latest` to `v0.11.0`:

```yaml
image: "registry.cloud.ionos.com/hermes/hermes-agent:v0.11.0"
```

### Step 4 — Apply and Redeploy

```bash
kubectl apply -k k8s/
kubectl delete pod -n hermes hermes-agent-0
```

The pod will restart with the new image.

---

## Cleanup and Teardown

When you're done experimenting, tear down the infrastructure to avoid ongoing costs.

### Delete Kubernetes Resources

```bash
kubectl delete -k k8s/
```

### Destroy Infrastructure

```bash
cd terraform
terraform destroy
```

Type `yes` to confirm. Terraform will delete:
- Virtual Data Center
- Managed Kubernetes cluster (including all nodes)
- Private Container Registry

This takes **5–10 minutes**. All data is lost (except what you backed up).

---

## Additional Resources

- **Hermes Agent Documentation:** https://hermes-agent.nousresearch.com/docs/
- **IONOS Managed Kubernetes:** https://docs.ionos.com/managed-kubernetes
- **IONOS AI Model Hub:** https://cloud.ionos.co.uk/ai-model-hub
- **Kubernetes Documentation:** https://kubernetes.io/docs/

---

## Troubleshooting Tips

| Issue | Debug Command |
|---|---|
| Pod won't start | `kubectl logs -n hermes hermes-agent-0` |
| Gateway unreachable | `kubectl port-forward -n hermes pod/hermes-agent-0 8642:8642` |
| Model provider timeout | Check API key and endpoint in `k8s/secret.yaml` |
| Telegram not responding | Verify `TELEGRAM_BOT_TOKEN` in secret and check Hermes logs |
| Storage full | `kubectl exec -n hermes hermes-agent-0 -- df -h /opt/data` |

---

Thank you for deploying Hermes Agent on IONOS Managed Kubernetes! If you have questions or encounter issues, reach out to IONOS Support or the Hermes Agent community.
