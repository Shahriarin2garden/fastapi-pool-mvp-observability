# Alerting configuration

Grafana provisions the `email-oncall` contact point, root notification policy,
and two rules from `grafana/provisioning/alerting`. `ALERT_RECIPIENT` supplies
the recipient from `.env`; no real address is committed here. SMTP variables
are configured by name only: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, and
`SMTP_FROM_ADDRESS`.

## OrderAPIDown

- Query: `up{job="order-api"}`
- Threshold: less than `1`
- Evaluation interval: `30s`
- Pending duration (`for`): `1m`
- Recipient: `ALERT_RECIPIENT` in `.env`

The recommended operator action is to check `docker compose ps`, inspect
`docker compose logs app`, verify database health, and restart the app with
`docker compose start app` after identifying the cause.

Grafana starts cleanly when `ALERT_RECIPIENT` or any SMTP variable is empty;
email delivery is simply unavailable until those values are configured.

`HighOrderFailureRate` uses a 20% threshold and a two-minute pending period to
avoid alerting on a single request. The 30-second evaluation interval and short
grouping delays make the controlled demo observable; production systems should
use team-approved intervals.
