# Evidence screenshots

- `compose-and-cluster.png` - Docker Compose `ps`, MicroK8s status, `kubectl get nodes`, `kubectl get pods -A`, Ubuntu, and tool versions.
- `prometheus-targets.png` - Prometheus showing `node-exporter` and `order-api` both UP.
- `grafana-metrics.png` - Grafana metrics dashboard with at least eight live panels.
- `kubernetes-logs.png` - Grafana Explore LogQL results from the MicroK8s workload, filtered by namespace/pod, with timestamps and errors.
- `email-alert.png` - Received alert email with subject and timestamp, with credentials hidden.
- `order-console.png` - Order Console with a successful order, live order row, trace ID, load drill controls, and telemetry tape.
- `frontend-telemetry.png` - Prometheus frontend metrics and Grafana/Loki evidence for `/api/telemetry`, including an order event and frontend log query.
- `<dashboard>.json` - Exported Grafana dashboard JSON with environment-specific values and credentials removed.

The `scripts/collect-evidence.sh` script writes its text output into `evidence/`.
