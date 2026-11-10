# Alerting configuration

Grafana provisions the `email-oncall` contact point, root notification policy, and
two rules from the YAML files in `grafana/provisioning/alerting`. `ALERT_RECIPIENT`
is expanded from the Compose environment; no address is committed here. SMTP
credentials are supplied only through `.env`.

`OrderAPIDown` waits one minute after `up{job="order-api"}` falls below one and
is critical because the API is unavailable. `HighOrderFailureRate` uses a 20%
threshold and a two-minute pending period to avoid alerting on a single request.
The 30-second evaluation interval and short grouping delays make the controlled
demo observable; production systems should use team-approved intervals.

For a safe test, run `docker compose stop app`, wait about two minutes, verify
the alert is Firing and the email arrives, then run `docker compose start app`.
Operators should check `docker compose ps`, `docker compose logs app`, database
health, the metrics dashboard, and Loki logs before restarting or rolling back.
