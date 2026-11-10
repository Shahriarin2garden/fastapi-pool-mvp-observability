"""Generate the tracked Grafana dashboards used by the assessment."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def panel(panel_id, title, expression, panel_type="timeseries", unit="none", datasource="prometheus"):
    return {
        "id": panel_id, "title": title, "type": panel_type,
        "datasource": {"type": "prometheus" if datasource == "prometheus" else "loki", "uid": datasource},
        "targets": [{"refId": "A", "expr": expression}],
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "gridPos": {"h": 8, "w": 12, "x": (panel_id - 1) % 2 * 12, "y": (panel_id - 1) // 2 * 8},
    }


def metrics_dashboard():
    panels = [
        {"id": 1, "title": "Dashboard guide", "type": "text", "options": {"mode": "markdown", "content": "Live Ubuntu host, Order API, and database-pool telemetry. Use the traffic script to create real series."}, "gridPos": {"h": 5, "w": 24, "x": 0, "y": 0}},
        panel(2, "CPU utilisation %", '100 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100', unit="percent"),
        panel(3, "RAM utilisation %", '(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100', unit="percent"),
        panel(4, "Disk utilisation % (/)", '100 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100)', "gauge", "percent"),
        panel(5, "Network throughput", 'sum(rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br-.*"}[1m]))', unit="Bps"),
        panel(6, "Host uptime", "time() - node_boot_time_seconds", "stat", "s"),
        panel(7, "Requests per second", "sum(rate(order_requests_total[1m]))", unit="reqps"),
        panel(8, "Error (failure) rate %", '100 * sum(rate(order_requests_total{status_class="5xx"}[1m])) / clamp_min(sum(rate(order_requests_total[1m])), 1e-9)', unit="percent"),
        panel(9, "p95 latency", "histogram_quantile(0.95, sum by (le) (rate(order_request_duration_seconds_bucket[1m])))", unit="s"),
        panel(10, "Business events (orders, last 5m)", "sum by (status) (increase(orders_created_total[5m]))", "stat"),
        panel(11, "Targets up", "up", "table"),
        panel(12, "DB pool size vs max", "db_pool_size", unit="none"),
        panel(13, "DB query p95", "histogram_quantile(0.95, sum by (le) (rate(db_query_duration_seconds_bucket[1m])))", unit="s"),
    ]
    return {"uid": "obs-metrics", "title": "Observability Metrics", "refresh": "10s", "time": {"from": "now-30m", "to": "now"}, "panels": panels, "schemaVersion": 39, "version": 1}


def logs_dashboard():
    source = {"type": "loki", "uid": "loki"}
    return {
        "uid": "obs-k8s-logs", "title": "Kubernetes Logs", "refresh": "10s",
        "time": {"from": "now-30m", "to": "now"},
        "templating": {"list": [
            {"name": "namespace", "type": "query", "datasource": source, "query": "label_values(namespace)"},
            {"name": "pod", "type": "query", "datasource": source, "query": "label_values(pod)"},
        ]},
        "panels": [
            {"id": 1, "title": "All pod logs", "type": "logs", "datasource": source, "targets": [{"expr": '{namespace=~"$namespace", pod=~"$pod"}'}]},
            {"id": 2, "title": "Errors", "type": "logs", "datasource": source, "targets": [{"expr": '{namespace=~"$namespace"} |= "ERROR"'}]},
            {"id": 3, "title": "Log volume by pod", "type": "timeseries", "datasource": source, "targets": [{"expr": 'sum by (pod) (count_over_time({namespace=~"$namespace"}[1m]))'}]},
        ],
        "schemaVersion": 39, "version": 1,
    }


out = ROOT / "grafana" / "dashboards"
out.mkdir(parents=True, exist_ok=True)
(out / "observability-metrics.json").write_text(json.dumps(metrics_dashboard(), indent=2) + "\n")
(out / "kubernetes-logs.json").write_text(json.dumps(logs_dashboard(), indent=2) + "\n")
