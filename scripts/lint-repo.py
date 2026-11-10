#!/usr/bin/env python3
"""Portable repository checks for local use and CI."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
failures = 0


def check(name, condition, detail=""):
    global failures
    if condition:
        print(f"PASS: {name}")
    else:
        failures += 1
        print(f"FAIL: {name}{(': ' + detail) if detail else ''}")


required = [
    ".env.example", "compose.yaml", "Dockerfile", "README.md",
    "MANUAL_STEPS.md", "loki/config.yml", "prometheus/prometheus.yml",
    "kubernetes/alloy-values.yaml", "grafana/provisioning/datasources/datasources.yml",
    "grafana/dashboards/observability-metrics.json",
]
for relative in required:
    check(f"required file {relative}", (ROOT / relative).is_file())

tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
check("no tracked .env", ".env" not in tracked)
for relative in tracked:
    path = ROOT / relative
    if path.suffix in {".sh", ".yml", ".yaml", ".json"} or path.name in {"Makefile", "Dockerfile"}:
        content = subprocess.run(
            ["git", "show", f":{relative}"], cwd=ROOT, capture_output=True, check=True
        ).stdout
        check(f"LF line endings {relative}", b"\r" not in content)

for relative in (ROOT / "scripts").glob("*.sh"):
    relative = relative.relative_to(ROOT)
    mode = subprocess.run(["git", "ls-files", "-s", str(relative)], cwd=ROOT, text=True, capture_output=True, check=True).stdout
    check(f"executable {relative}", mode.startswith("100755"))

env_text = (ROOT / ".env.example").read_text()
compose_text = (ROOT / "compose.yaml").read_text()
variables = set(re.findall(r"\$\{([A-Z_]+)(?::-[^}]*)?\}", compose_text))
env_variables = set(re.findall(r"^([A-Z_]+)=", env_text, re.MULTILINE))
check("Compose variables documented", variables <= env_variables, str(sorted(variables - env_variables)))
check("no latest image tags", ":latest" not in compose_text)
db_block = compose_text.split("\n  db:", 1)[1].split("\n  app:", 1)[0] if "\n  db:" in compose_text else ""
check("Postgres is not published", "ports:" not in db_block)
check("node exporter host networking", "network_mode: host" in compose_text and "pid: host" in compose_text)
for volume in ("postgres_data", "prometheus_data", "loki_data", "grafana_data"):
    check(f"named volume {volume}", f"  {volume}:" in compose_text)

for relative in ("grafana/dashboards/observability-metrics.json", "grafana/dashboards/kubernetes-logs.json"):
    try:
        dashboard = json.loads((ROOT / relative).read_text())
        panels = dashboard.get("panels", [])
        ids = [panel.get("id") for panel in panels]
        check(f"valid dashboard {relative}", True)
        check(f"unique panel ids {relative}", len(ids) == len(set(ids)))
        check(f"datasource UIDs {relative}", all(
            panel.get("datasource", {}).get("uid") in {None, "prometheus", "loki"}
            for panel in panels
        ))
        if relative.endswith("observability-metrics.json"):
            check("metrics dashboard has 12 panels", len(panels) >= 12)
    except (OSError, json.JSONDecodeError) as exc:
        check(f"valid dashboard {relative}", False, str(exc))

alloy = (ROOT / "kubernetes/alloy-values.yaml").read_text()
check("Alloy has host placeholder", "__LOKI_HOST__" in alloy and "127.0.0.1" not in alloy and "localhost" not in alloy)
prometheus = (ROOT / "prometheus/prometheus.yml").read_text()
for job in ("node-exporter", "order-api", "prometheus"):
    check(f"Prometheus job {job}", f"job_name: {job}" in prometheus)

if not (ROOT / ".env").exists():
    print("WARN: .env is absent; Docker-backed checks are deferred to CI or Ubuntu.")
print("RESULT: PASS" if failures == 0 else f"RESULT: FAIL ({failures} failures)")
sys.exit(1 if failures else 0)
