# Evidence screenshots

- `compose-and-cluster.png` - Docker Compose `ps`, MicroK8s status, `kubectl get nodes`, `kubectl get pods -A`, Ubuntu, and tool versions.
- `prometheus-targets.png` - Prometheus showing `node-exporter` and `order-api` both UP.
- `grafana-metrics.png` - Grafana metrics dashboard with at least eight live panels.
- `kubernetes-logs.png` - Grafana Explore LogQL results from the MicroK8s workload, filtered by namespace/pod, with timestamps and errors.
- `email-alert.png` - Received alert email with subject and timestamp, with credentials hidden.

The `scripts/collect-evidence.sh` script writes its text output into `evidence/`.
