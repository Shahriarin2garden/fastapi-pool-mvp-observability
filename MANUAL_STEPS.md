# Manual acceptance and handover checklist

Use the [main README](README.md) for architecture, setup, configuration,
verification, and security notes. This checklist records the actions that CI
cannot fully prove on a live Ubuntu/MicroK8s environment.

- [ ] Review the bootstrap dry run, then execute `scripts/bootstrap-ubuntu.sh --yes` if the host needs Docker and MicroK8s.
- [ ] Start a new login session after Docker/MicroK8s group changes; verify `docker compose version`, `microk8s status --wait-ready`, and `microk8s kubectl get nodes`.
- [ ] Copy `.env.example` to `.env`; set strong DB/Grafana passwords, the correct `NODE_EXPORTER_BIND`, a pod-routable private `LOKI_BIND_IP`, SMTP values, and `ALERT_RECIPIENT`.
- [ ] Run `make preflight`, `make up`, and `make verify`; confirm both `node-exporter` and `order-api` show UP in Prometheus Targets.
- [ ] Run `make k8s-up`; confirm the `demo` workload and Alloy are healthy, then verify pod stdout/stderr in Loki with Kubernetes labels.
- [ ] Run `make traffic` and `scripts/k8s-error-burst.sh`; confirm API counters, latency histograms, error rate, and business-event metrics change.
- [ ] Run `scripts/crosscheck.sh`; compare Linux `free`, `df`, and `uptime` with Prometheus readings, then store a sanitized output file in `evidence/`.
- [ ] Run `make alert-test`; confirm the rule enters Firing and a real SMTP email arrives. Restore the application and confirm the resolved notification.
- [ ] Capture or refresh the committed evidence images. The current files are listed in [evidence/README.md](evidence/README.md); still add a dedicated `prometheus-targets.png` and `api-metrics.png` if absent.
- [ ] If presenting the optional Order Console, place a successful order, run the failure drill, and capture frontend metrics/log evidence.
- [ ] Export dashboards from the live Grafana instance if required by the evaluator; remove environment-specific values before committing JSON.
- [ ] Review every screenshot and text artifact for passwords, SMTP credentials, tokens, private keys, public addresses, and unintended personal information.
- [ ] Complete candidate name, ID, assessment date, and final repository URL; review the diff and placeholders.
- [ ] Run `git diff --check`, `make lint`, `make test`, `make verify`, `make k8s-up`, and `make alert-test` as appropriate for the available host.
- [ ] Build the archive only after committing the exact files intended for submission: `make zip CANDIDATE_ID=<actual-id>`.
- [ ] Inspect the archive listing and ensure `.env`, credentials, private keys, generated cloud state, and unreviewed evidence are absent.

## Human-only checks

CI validates the application tests, configuration, dashboard generation, and
Compose smoke stack. It cannot prove a local MicroK8s cluster, external SMTP
inbox delivery, live cloud firewall restrictions, or that screenshots show
the correct live test window. Complete those checks during the demonstration.
