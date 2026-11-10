# Manual steps for the human

- [ ] Install Docker Engine/Compose and MicroK8s on Ubuntu; verify versions.
- [ ] Copy `.env.example` to `.env`, choose local credentials, and fill SMTP/App Password and `ALERT_RECIPIENT`.
- [ ] Set `LOKI_BIND_IP` to the laptop address reachable by MicroK8s and apply the documented firewall rule.
- [ ] Run `docker compose up -d --build`, then deploy the demo workload and Alloy using [kubernetes/README.md](kubernetes/README.md).
- [ ] Run `scripts/traffic-test.sh all`, `scripts/k8s-error-burst.sh`, and the safe stop/start alert test.
- [ ] Capture the five evidence screenshots listed in `evidence/README.md`.
- [ ] Run `scripts/make-zip.sh CANDIDATE_ID` after committing; inspect the archive before submission.
