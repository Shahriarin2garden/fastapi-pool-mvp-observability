# Manual steps for the human

- [ ] Run `scripts/bootstrap-ubuntu.sh` (dry run), then `scripts/bootstrap-ubuntu.sh --yes`; expected: tools install and group membership is reported.
- [ ] Copy `.env.example` to `.env`, set `NODE_EXPORTER_BIND`, `LOKI_BIND_IP`, SMTP/App Password, and `ALERT_RECIPIENT`; expected: `make preflight` has no FAIL lines.
- [ ] Add a firewall rule allowing Loki only from the MicroK8s pod CIDR; expected: the in-cluster `/ready` curl succeeds.
- [ ] Run `make up`, `make verify`, and `make k8s-up`; expected: Compose health checks, Prometheus targets, and Alloy are ready.
- [ ] Run `scripts/set-candidate.sh "CANDIDATE_NAME" "CANDIDATE_ID"`; expected: only documented placeholders are replaced.
- [ ] Run `make traffic`, `scripts/k8s-error-burst.sh`, and `make alert-test`; expected: live panels change and the alert email arrives.
- [ ] Open the FastAPI root URL and complete one order, a burst, and the failure drill; expected: live orders, trace IDs, telemetry tape, frontend Prometheus metrics, and `{app="order-ui"} | json | event="order_failure"` in Loki.
- [ ] Capture `compose-and-cluster.png`, `prometheus-targets.png`, `grafana-metrics.png`, `kubernetes-logs.png`, and `email-alert.png`.
- [ ] Capture `order-console.png`, `frontend-telemetry.png`, and an exported dashboard JSON; expected: no credentials, tokens, private keys, or recipient details are visible.
- [ ] Test keyboard-only use, responsive widths 1440/1024/768/390/320, and reduced motion; record any issue before submission.
- [ ] Run `scripts/make-zip.sh CANDIDATE_ID` after committing; expected: archive contains no `.env` or credentials.
- [ ] Push only the new repository branch with `git push -u neworigin observability-assessment`.
