# MicroK8s logging

Run these commands on Ubuntu after Docker Compose and `.env` are configured:

```bash
sudo snap install microk8s --classic
sudo usermod -aG microk8s "$USER" && newgrp microk8s
microk8s status --wait-ready
microk8s enable dns helm3
microk8s kubectl apply -f kubernetes/namespace.yaml -f kubernetes/workload.yaml
microk8s kubectl -n demo logs deploy/log-generator --tail=20
./scripts/render-alloy-values.sh <LAPTOP_IP>
microk8s helm3 repo add grafana https://grafana.github.io/helm-charts
microk8s helm3 repo update
microk8s helm3 install alloy grafana/alloy -n monitoring --create-namespace -f kubernetes/.rendered/alloy-values.yaml
microk8s kubectl -n monitoring get pods
```

Prove connectivity from the cluster:

```bash
microk8s kubectl run curltest --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s http://<LAPTOP_IP>:3100/ready
```

In Grafana Explore, use `{namespace="demo"}` and
`{namespace="demo", container="log-generator"} |= "ERROR"`. If no logs arrive,
inspect `microk8s kubectl -n monitoring logs deploy/alloy`, Loki `/ready`, the
rendered host address, and the firewall. `LOKI_BIND_IP=127.0.0.1` cannot be
reached from MicroK8s; use the laptop IP and restrict port 3100 to the pod CIDR.
The official Alloy chart creates the service account and RBAC needed to discover
pods and read logs by default; keep the chart's default RBAC enabled.
