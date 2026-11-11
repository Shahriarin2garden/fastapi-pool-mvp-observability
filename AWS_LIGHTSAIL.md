# AWS Lightsail demo (the path that works in the restricted sandbox)

The sandbox org SCP denies `ec2:*` creation (subnets, security groups, key
pairs) and EKS/ECS/IAM/ECR — but **Lightsail was left out of the deny list**,
so a bundled Lightsail VM is the working "simple instance instead of local
Ubuntu" path. Lightsail manages its own networking (public IP, firewall, SSH
keys), so no VPC/subnet/SG APIs are needed. All automation runs from AWS
CloudShell via plain `aws lightsail` commands (no Terraform state to lose).

## Architecture

Same Compose stack as the EC2/local target, on one Lightsail VM:

- **Blueprint**: Ubuntu 24.04
- **Bundle**: `small_3_0` (2 vCPU, 2 GiB, 60 GB SSD — ~$10/mo)
- cloud-init user-data installs Docker + Compose, clones the repo, writes
  `.env` (random DB/Grafana passwords) and runs `docker compose up` with the
  public-binding override (`COMPOSE_FILE=compose.yaml:compose.ec2.yaml`)
- Firewall opened for 22/80/8001/3000 via `put-instance-public-ports`

## Cost

`small_3_0` is ~$10/month running 24/7 — the builder account credits
(~$165) cover ~16 months. Stopping the instance between demos pauses
compute billing (disk storage stays billed at a few dollars a month).

## Daily loop (from CloudShell, inside the cloned repo)

```bash
make lightsail-up      # create VM + open ports + wait for /health (~10-15 min)
make lightsail-stop    # between demos: compute billing pauses
make lightsail-resume  # bring it back (public IP may change, script prints it)
make lightsail-destroy # full teardown
```

Tunables (env): `LIGHTSAIL_NAME`, `AZ`, `BUNDLE` (e.g. `medium_3_0` for 4 GiB),
`BLUEPRINT`, `REPO_URL`, `REPO_BRANCH`.

## Demo URLs

- API: `http://<public-ip>:8001/health`
- Grafana: `http://<public-ip>:3000` (user `admin`, password in
  `.lightsail-grafana-password`, written next to the scripts)
- SSH: the Lightsail console "Connect using SSH" button, or download the
  default key pair under Account → SSH keys → us-east-1

## Notes

- The dynamic public IP can change after stop/resume; `lightsail-resume`
  prints the current one. Attach a Lightsail **static IP** from the console
  (free while attached) for a stable demo address.
- `infra/ec2/` documents the plain-EC2 Terraform approach for an unrestricted
  account (it needs subnets/SGs/key-pairs, which this sandbox denies).
- The EKS reference architecture (infra/cluster, AWS_DEPLOY.md) remains
  available for a future unrestricted account.
