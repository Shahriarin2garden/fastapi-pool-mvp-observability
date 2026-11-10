# Evidence screenshots

Expected screenshots:

- `01-compose-ps.png` - Docker Compose services running and healthy.
- `02-grafana-metrics-dashboard.png` - Grafana metrics dashboard with order and service metrics visible.
- `03-grafana-kubernetes-logs.png` - Grafana Kubernetes logs dashboard showing collected logs.
- `04-alert-firing.png` - Grafana showing the `OrderAPIDown` alert in the active state.
- `05-alert-email.png` - The configured inbox showing the alert notification email.

The `scripts/collect-evidence.sh` script writes its text output into this folder.
