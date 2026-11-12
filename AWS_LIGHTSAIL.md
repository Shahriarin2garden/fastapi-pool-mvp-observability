# AWS Lightsail demo (the path that works in the restricted sandbox)

The Lightsail target is an optional cloud demonstration path, not the
assignment's laptop-local reference topology. It uses a single Ubuntu VM and
AWS CloudShell automation; it does not make the deployment highly available
or production-ready.

## Architecture

Same Compose stack as the EC2/local target, on one Lightsail VM:

- **Blueprint**: Ubuntu 24.04
- **Bundle**: `small_3_2` (2 vCPU, 2 GiB, 60 GB SSD; verify current regional price before launch)
- **Region**: `ap-southeast-2` — the sandbox SCP denies Lightsail *creation*
  in us-east-1 but allows it in ap-southeast-2 (the account's home region),
  where bundles use the `_3_2` suffix
- cloud-init user-data installs Docker + Compose, clones the repo, writes
  `.env` (random DB/Grafana passwords) and runs `docker compose up` with the
  public-binding override (`COMPOSE_FILE=compose.yaml:compose.ec2.yaml`)
- The automation requires `LIGHTSAIL_ALLOWED_CIDR` and rejects IPv4
  ranges broader than `/24`; use the operator's public IP as `/32` where
  possible. It opens TCP 22, 8001, and 3000 only to that allowlist. The SSH
  rule also includes Lightsail's `lightsail-connect` browser-console alias.
  Port 80 is not opened because the Compose stack does not publish it. Do not
  expose Prometheus (9090), Node Exporter (9100), or Loki (3100) publicly.
  The script calls `put-instance-public-ports`, which replaces the full
  public-port rule set and closes ports omitted from the request; see the
  [AWS CLI reference](https://docs.aws.amazon.com/cli/latest/reference/lightsail/put-instance-public-ports.html).
- Example:
  ```bash
  export LIGHTSAIL_ALLOWED_CIDR="203.0.113.10/32" # replace with your approved public IP
  make lightsail-up
  ```
- Existing instances must have their effective firewall inspected and
  restricted. Rerunning `make lightsail-up` reapplies the allowlist whether the
  VM was already running or had to be resumed first.

## Cost

Check current Lightsail pricing for the selected region and bundle before
creating an instance. Stopping the VM pauses compute charges, but attached
storage and other billable resources may continue to incur charges.

## Daily loop (from CloudShell, inside the cloned repo)

```bash
export LIGHTSAIL_ALLOWED_CIDR="203.0.113.10/32" # replace with your approved public IP
make lightsail-up
make lightsail-stop
make lightsail-resume
make lightsail-destroy
```

The allowlist variable is mandatory for `make lightsail-up`. The
`203.0.113.10/32` address above is a documentation-only example; replace it
with the actual approved IPv4 address before running the command.

Tunables (env): `LIGHTSAIL_NAME`, `LIGHTSAIL_REGION`, `AZ`, `BUNDLE`,
`BLUEPRINT`, `REPO_URL`, `REPO_BRANCH`, and `ALERT_RECIPIENT`. The script
now defaults `REPO_BRANCH` to `observability-assessment`; set it explicitly
when deploying another branch.

## Demo URLs

- API: `http://<public-ip>:8001/health`
- Grafana: `http://<public-ip>:3000` (user `admin`, password in
  `.lightsail-grafana-password`, written next to the scripts)
- SSH: the Lightsail console "Connect using SSH" button, or download the
  default key pair under Account → SSH keys → ap-southeast-2

## Required post-bootstrap work

The user-data template creates the Compose stack only. It does not install
MicroK8s or Grafana Alloy. It also writes `LOKI_BIND_IP=127.0.0.1` and leaves
SMTP credentials blank. Therefore, the Kubernetes log path and email alert
path are not complete immediately after `make lightsail-up`:

1. Configure Loki on the private interface reachable by the MicroK8s pods.
2. Keep TCP 3100 private and permit only the cluster traffic needed to push logs.
3. Install MicroK8s, deploy the workload, and install Alloy using the main README.
4. Add SMTP credentials through the protected `.env` file and recreate/restart
   Grafana before testing email delivery.

Do not copy a public/private IP address, password, or SMTP value into tracked
documentation or screenshots.

## Notes

- The dynamic public IP can change after stop/resume; `lightsail-resume`
  prints the current one. Re-evaluate `LIGHTSAIL_ALLOWED_CIDR` whenever the
  operator's public IP changes, or connectivity will be blocked.
- `infra/ec2/` documents the plain-EC2 Terraform approach for an unrestricted
  account (it needs subnets/SGs/key-pairs, which this sandbox denies).
- The EKS reference architecture (infra/cluster, AWS_DEPLOY.md) remains
  available for a future unrestricted account.
